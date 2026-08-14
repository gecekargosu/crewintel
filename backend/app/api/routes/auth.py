from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.user import User
from app.services.audit import log_event


router = APIRouter(prefix="/api/auth", tags=["Auth"])


# ── Brute-force koruması: basit in-memory pencere (10 HATALI deneme / 5 dk / IP) ──
# Not: Yalnızca başarısız giriş denemeleri sayılır; başarılı giriş sayaçı sıfırlar.
_login_attempts: dict[str, deque] = defaultdict(deque)
_login_lock = Lock()
LOGIN_MAX_ATTEMPTS = 10
LOGIN_WINDOW_SECONDS = 300


def _login_failed_attempt(client_ip: str) -> bool:
    """Hatalı bir deneme kaydeder; pencere içinde limit aşıldıysa True döner."""
    now = datetime.now(UTC)
    with _login_lock:
        window = _login_attempts[client_ip]
        while window and (now - window[0]) > timedelta(seconds=LOGIN_WINDOW_SECONDS):
            window.popleft()
        window.append(now)
        if len(window) > LOGIN_MAX_ATTEMPTS:
            return True
        return False


def _login_success(client_ip: str) -> None:
    """Başarılı girişte sayaç sıfırlanır."""
    with _login_lock:
        _login_attempts.pop(client_ip, None)


def reset_login_attempts() -> None:
    """Test / yönetim aracı: deneme sayacını temizler."""
    with _login_lock:
        _login_attempts.clear()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    crew_member_id: int | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)
    role: str = Field(default="viewer", pattern="^(admin|hr|viewer|crew)$")
    crew_member_id: int | None = Field(default=None, gt=0)


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    role: str | None = Field(default=None, pattern="^(admin|hr|viewer|crew)$")
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8)
    crew_member_id: int | None = Field(default=None, gt=0)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class ChangeEmailRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_email: EmailStr


def _serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        crew_member_id=user.crew_member_id,
    )


@router.post("/login", response_model=LoginResponse)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    # Reverse proxy arkasında (nginx/cloudflared) gerçek IP X-Forwarded-For'dan gelir.
    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if user is None or not verify_password(payload.password, user.password_hash or ""):
        # Yalnızca hatalı denemeler sayaçta; limit aşıldıysa 429 döner.
        if _login_failed_attempt(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Çok fazla hatalı giriş denemesi. Lütfen 5 dakika sonra tekrar deneyin.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    # Başarılı giriş: hatalı deneme sayaçı sıfırlanır.
    _login_success(client_ip)

    log_event(
        db,
        "login",
        "user",
        user.id,
        f"User logged in: {user.email}",
        metadata={"email": user.email},
    )
    db.commit()

    token = create_access_token(user.email, extra_claims={"role": user.role})
    return LoginResponse(access_token=token, user=_serialize_user(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return _serialize_user(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    current_user.password_hash = hash_password(payload.new_password)
    log_event(db, "password_changed", "user", current_user.id, f"Password changed: {current_user.email}")
    db.commit()


@router.post("/change-email", status_code=status.HTTP_204_NO_CONTENT)
def change_email(
    payload: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    new_email = payload.new_email.lower().strip()
    if new_email == current_user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email is the same as the current one.")
    exists = db.query(User).filter(User.email == new_email).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")
    current_user.email = new_email
    log_event(db, "email_changed", "user", current_user.id, f"Email changed: {current_user.email}",
              user_email=current_user.email)
    db.commit()


# ── Admin: user management ───────────────────────────────────────────────────


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    from app.models.crew_member import CrewMember

    if payload.role == "crew" and payload.crew_member_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Crew rolü için önce personele bağlantı seçilmelidir (crew_member_id).",
        )
    if payload.crew_member_id is not None and db.get(CrewMember, payload.crew_member_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seçilen personel bulunamadı.",
        )
    user = User(
        email=payload.email.lower().strip(),
        full_name=payload.full_name.strip(),
        role=payload.role,
        crew_member_id=payload.crew_member_id,
        is_active=True,
        password_hash=hash_password(payload.password),
    )
    try:
        db.add(user)
        db.flush()
        log_event(db, "user_created", "user", user.id, f"User created: {user.email} (role: {user.role})",
                  metadata={"created_by": admin.email},
                  user_email=admin.email)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")
    return _serialize_user(user)


@router.get("/users", response_model=list[UserResponse])
def list_users(
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id).all()
    return [_serialize_user(user) for user in users]


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    from app.models.crew_member import CrewMember

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if "crew_member_id" in payload.model_fields_set:
        if payload.crew_member_id is not None and db.get(CrewMember, payload.crew_member_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seçilen personel bulunamadı.",
            )
        user.crew_member_id = payload.crew_member_id

    log_event(db, "user_updated", "user", user.id, f"User updated: {user.email}",
              metadata={"updated_by": admin.email},
              user_email=admin.email)
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account.")
    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin hesabı silinemez. Önce rolünü değiştirin (örn. viewer) veya hesabı pasife alın.",
        )
    email = user.email
    db.delete(user)
    log_event(db, "user_deleted", "user", user_id, f"User deleted: {email}",
              metadata={"deleted_by": admin.email},
              user_email=admin.email)
    db.commit()


# ── M1 Mobile: self-registration + admin onayı + deaktivasyon ───────────────


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=30)
    password: str = Field(min_length=8)
    nationality: str | None = None
    date_of_birth: str | None = None


class RegisterResponse(BaseModel):
    status: str
    message: str


# Basit in-memory kayıt limitleyici (5 kayıt / saat / IP)
_register_attempts: dict[str, deque] = defaultdict(deque)
_register_lock = Lock()
REGISTER_MAX_ATTEMPTS = 5
REGISTER_WINDOW_SECONDS = 3600


def _register_rate_limited(client_ip: str) -> bool:
    now = datetime.now(UTC)
    with _register_lock:
        window = _register_attempts[client_ip]
        while window and (now - window[0]) > timedelta(seconds=REGISTER_WINDOW_SECONDS):
            window.popleft()
        if len(window) >= REGISTER_MAX_ATTEMPTS:
            return True
        window.append(now)
        return False


def reset_register_attempts() -> None:
    """Test / yönetim aracı: kayıt deneme sayacını temizler."""
    with _register_lock:
        _register_attempts.clear()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    """Mobil self-registration: minimum alanlarla crew hesabı oluşturur.

    CrewMember (position='Aday') + User(role='crew', is_active=False) oluşturulur.
    Admin onayı (PATCH /api/auth/users/{id}/approve) olmadan giriş yapılamaz.
    """
    from datetime import date as date_type

    from app.models.crew_member import CrewMember

    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    if _register_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla kayıt denemesi. Lütfen daha sonra tekrar deneyin.",
        )

    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu e-posta zaten kayıtlı.")

    dob = None
    if payload.date_of_birth:
        try:
            dob = date_type.fromisoformat(payload.date_of_birth)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                                detail="date_of_birth YYYY-MM-DD formatında olmalı.") from None

    crew = CrewMember(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        phone=payload.phone.strip(),
        nationality=payload.nationality,
        date_of_birth=dob,
        position="Aday",
        status="active",
        availability="available",
        job_seeking=False,
    )
    db.add(crew)
    db.flush()

    user = User(
        email=email,
        full_name=f"{payload.first_name.strip()} {payload.last_name.strip()}",
        role="crew",
        crew_member_id=crew.id,
        is_active=False,  # admin onayı bekliyor
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    log_event(db, "crew_registered", "crew_member", crew.id,
              f"Mobil kayıt bekliyor: {user.full_name} <{email}>", user_email=email)
    db.commit()
    return RegisterResponse(status="pending_review",
                            message="Kaydınız alındı. Yönetici onayından sonra giriş yapabilirsiniz.")


@router.patch("/users/{user_id}/approve", response_model=UserResponse)
def approve_user(
    user_id: int,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """Mobil kaydı onaylar: user aktif olur, giriş açılır."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.role != "crew" or user.crew_member_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Yalnızca crew bağlantılı hesaplar onaylanabilir.")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hesap zaten aktif.")
    user.is_active = True
    log_event(db, "crew_registration_approved", "user", user.id,
              f"Mobil kayıt onaylandı: {user.email}", metadata={"approved_by": admin.email},
              user_email=admin.email)
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.patch("/me/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hesabı kapat (silme değil): is_active=false, veriler korunur."""
    current_user.is_active = False
    log_event(db, "user_deactivated", "user", current_user.id,
              f"Hesap kapatıldı (deaktivasyon): {current_user.email}", user_email=current_user.email)
    db.commit()
