import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import axios from "axios";
import LanguageSelector from "./components/LanguageSelector";
import {
  Activity,
  Anchor,
  Bell,
  CheckCircle,
  ChevronDown,
  ClipboardList,
  Download,
  FileText,
  Filter,
  Folder,
  LayoutDashboard,
  Menu,
  Search,
  Ship,
  Target,
  Upload,
  UserPlus,
  Users,
  X,
  XCircle,
  Trash2,
  Settings,
  AlertCircle,
  Mail,
  Briefcase,
  MessageCircle,
  Phone,
  Send,
  Clock,
  Image as ImageIcon
} from "lucide-react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// ==========================================
// BOŞ FORM ŞABLONLARI
// ==========================================
const emptyCrewForm = {
  first_name: "",
  last_name: "",
  position: "",
  nationality: "",
  availability: "available",
};

const emptyShipForm = {
  name: "",
  imo_number: "",
  ship_type: "",
  flag: "",
};

const emptyContractForm = {
  crew_member_id: "",
  ship_id: "",
  contract_number: "",
  contract_type: "Employment",
  start_date: "",
  end_date: "",
};

const emptyFilters = {
  name: "",
  position: "",
  nationality: "",
  rank: "",
  languages: "",
  experience_years_min: "",
  sea_service_months_min: "",
  availability: "",
  showProblematic: false,
};

const FILTER_POSITIONS = ["Kaptan", "Başmühendis", "2. Kaptan", "3. Kaptan", "Elektrik Zabiti", "Yağcı", "Usta Gemici", "Gemici", "Aşçı", "Kamarot"];

const FILTER_NATIONALITIES = ["Türkiye", "Mısır", "Rusya", "Gürcistan", "Ukrayna", "Azerbaycan", "Bulgaristan", "Romanya", "Filipinler", "Japon", "Hindistan", "Endonezya", "Çin", "Yunanistan", "Almanya", "İngiltere", "ABD", "Polonya"];

function App() {
  const { t, i18n } = useTranslation();
  
  // Position name translation helper — maps Turkish backend names to translation keys
  const POSITION_MAP = {
    'Kaptan': 'positions.captain',
    'Başmühendis': 'positions.chief_engineer',
    '2. Kaptan': 'positions.second_officer',
    '3. Kaptan': 'positions.third_officer',
    'Elektrik Zabiti': 'positions.electric_officer',
    'Yağcı': 'positions.oiler',
    'Usta Gemici': 'positions.able_seaman',
    'Gemici': 'positions.ordinary_seaman',
    'Aşçı': 'positions.cook',
    'Kamarot': 'positions.steward',
  };
  const translatePosition = (pos) => POSITION_MAP[pos] ? t(POSITION_MAP[pos]) : pos;
  
  // Role label translation
  const ROLE_MAP = {
    'admin': 'settings.admin',
    'hr': 'settings.hr',
    'viewer': 'settings.viewer',
    'crew': 'settings.crew',
    'Yönetici': 'settings.admin',
    'İK Uzmanı': 'settings.hr',
    'Görüntüleyici': 'settings.viewer',
    'Personel': 'settings.crew',
  };
  const translateRole = (role) => ROLE_MAP[role] ? t(ROLE_MAP[role]) : role;
  
  // Task text translation — parses backend Turkish task text and translates known patterns
  const translateTaskText = (text) => {
    if (!text) return text;
    let result = text;
    // Replace document type patterns
    result = result.replace(/belgesi DOLDU/g, `${t('documents.expired')}`);
    result = result.replace(/belgesi DOLMAK ÜZERE/g, `${t('documents.urgent')}`);
    result = result.replace(/belgesi yaklaşıyor/gi, `${t('documents.approaching')}`);
    // Replace position gap patterns
    result = result.replace(/pozisyon açığı/g, t('dashboard.openPositions').toLowerCase());
    // Replace doc type names
    Object.keys(DOC_TYPE_MAP).forEach(key => {
      const regex = new RegExp(`\b${key}\b`, 'gi');
      result = result.replace(regex, t(DOC_TYPE_MAP[key]));
    });
    // Replace position names
    Object.keys(POSITION_MAP).forEach(key => {
      const regex = new RegExp(key.replace(/[.]/g, '\.'), 'g');
      result = result.replace(regex, t(POSITION_MAP[key]));
    });
    return result;
  };
  
  // Document type translation for task text
  const DOC_TYPE_MAP = {
    'stcw': 'documentTypes.stcw',
    'passport': 'documentTypes.passport',
    'medical': 'documentTypes.medical',
    'seaman_book': 'documentTypes.seaman_book',
    'other': 'documentTypes.other',
    'contract': 'documentTypes.contract',
    'certificate': 'documentTypes.certificate',
    'cv': 'documentTypes.cv',
    'license': 'documentTypes.license',
    'visa': 'documentTypes.visa',
    'work_permit': 'documentTypes.work_permit',
    'id_card': 'documentTypes.id_card',
  };
  
  // ==========================================
  // VERİTABANI STATELERİ
  // ==========================================
  const [crew, setCrew] = useState([]);
  const [ships, setShips] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [allDocuments, setAllDocuments] = useState([]); 
  const [documents, setDocuments] = useState([]);
  const [totalCrewStats, setTotalCrewStats] = useState({ 
    total: 0, 
    active: 0 
  });
  const [expirySummary, setExpirySummary] = useState(null);

  // ==========================================
  // ARAYÜZ (UI) STATELERİ
  // ==========================================
  const [apiStatus, setApiStatus] = useState(t('common.loading'));
  const [isSystemHealthy, setIsSystemHealthy] = useState(true);
  const [menuOpen, setMenuOpen] = useState(() => typeof window !== "undefined" && window.innerWidth > 900);
  const [activePage, setActivePage] = useState("dashboard");
  const [navStack, setNavStack] = useState([]); // Geri butonu için sayfa geçmişi
  const [selectedCrewId, setSelectedCrewId] = useState(null);
  const [selectedShipId, setSelectedShipId] = useState(null);
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [crewLoading, setCrewLoading] = useState(false);
  
  // Form Toggles & Datas
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [crewForm, setCrewForm] = useState(emptyCrewForm);
  const [isShipFormOpen, setIsShipFormOpen] = useState(false);
  const [shipForm, setShipForm] = useState(emptyShipForm);
  const [isContractFormOpen, setIsContractFormOpen] = useState(false);
  const [contractForm, setContractForm] = useState(emptyContractForm);
  const [editingContractId, setEditingContractId] = useState(null);
  const [selectedContractId, setSelectedContractId] = useState(null);

  // Modallar (Atama & {t('common.confirm')}me)
  const [assignmentModal, setAssignmentModal] = useState({ 
    isOpen: false, 
    crew_member_id: "", 
    ship_id: "", 
    position: "",
    start_date: "",
    end_date: ""
  });
  const [matchingModalOpen, setMatchingModalOpen] = useState(false);
  
  // Doküman Yükleme & Detay Stateleri
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState(null);
  const [docPage, setDocPage] = useState(0);
  const [docTotal, setDocTotal] = useState(0);
  const DOC_PAGE_SIZE = 50;
  const [crewDetailDocuments, setCrewDetailDocuments] = useState([]);
  const [crewDetailDocumentsLoading, setCrewDetailDocumentsLoading] = useState(false);
  
  // Yükleme (Upload) Bölümü Stateleri
  const [stagedFiles, setStagedFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({});
  const [uploadResults, setUploadResults] = useState({});
  const [uploadProgress, setUploadProgress] = useState({});
  const [isUploading, setIsUploading] = useState(false);
  const [lastBatchSummary, setLastBatchSummary] = useState(null);
  const [batchProgress, setBatchProgress] = useState(null); // {batch_id, total, processed, ...}
  const [reviewQueue, setReviewQueue] = useState([]);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [candidateData, setCandidateData] = useState(null); // seçili belgenin adayları
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const fileInputRef = useRef(null);

  // Phase 4B — Operasyon merkezi / bildirim / uygunluk / kadro
  const [opsSummary, setOpsSummary] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [eligibilityQuery, setEligibilityQuery] = useState({ position: "", min_score: 50 });
  const [eligibilityResults, setEligibilityResults] = useState(null);
  const [eligibilityLoading, setEligibilityLoading] = useState(false);
  const [shipStaffing, setShipStaffing] = useState([]);
  const [staffingLoading, setStaffingLoading] = useState(false);
  const [positionForm, setPositionForm] = useState({ position: "", required_count: 1 });
  const [candidatesFor, setCandidatesFor] = useState(null);
  const [importPreview, setImportPreview] = useState(null);
  const [importCsvText, setImportCsvText] = useState("");
  const [importMsg, setImportMsg] = useState(null);
  const [showImport, setShowImport] = useState(false);

  // Toplu e-posta + bildirim ayarları (Phase 6)
  const [selectedCrewIds, setSelectedCrewIds] = useState([]);
  const [emailModal, setEmailModal] = useState({ isOpen: false, crewIds: [], subject: "", body: "" });
  const [emailMsg, setEmailMsg] = useState(null);
  const [notifSettings, setNotifSettings] = useState({});
  const [notifSettingsMsg, setNotifSettingsMsg] = useState(null);
  const notifFields = ["smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_from", "whatsapp_admin_number", "whatsapp_api_token", "whatsapp_phone_id"];

  // Filtreler
  const [docFilters, setDocFilters] = useState({ 
    document_type: "", 
    match_status: "", 
    expiry_status: "" 
  });
  const [crewFilters, setCrewFilters] = useState(emptyFilters);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [activeFilterCount, setActiveFilterCount] = useState(0);

  // Kontrat filtreleri (dashboard kartları → kontrat sayfası)
  const [contractsFilter, setContractsFilter] = useState(""); // "" | "ending_7" | "ending_30"

  // İş ilanları + başvuru havuzu + Yayın Sistemi (Phase 7/8)
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobApplications, setJobApplications] = useState([]);
  const [jobForm, setJobForm] = useState({ title: "", position: "", ship_id: "", vessel_type: "", flag: "", location: "", currency: "USD", salary: "", salary_period: "monthly", contract_duration: "", join_date: "", application_deadline: "", description: "", duties: "", requirements: "", certificates_required: "", experience_required: "", languages_required: "", age_min: "", age_max: "", notes: "", contact_info: "", start_date: "", status: "open" });
  const [showJobForm, setShowJobForm] = useState(false);
  const [showJobApps, setShowJobApps] = useState(false);
  const [jobMsg, setJobMsg] = useState(null);
  const [jobApplyCrewId, setJobApplyCrewId] = useState({}); // { postingId: crewId }
  const [jobApplyOpen, setJobApplyOpen] = useState({}); // { postingId: bool }
  // Yayın sistemi
  const [jobTemplates, setJobTemplates] = useState([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [templateForm, setTemplateForm] = useState({ name: "", body: "", is_default: false });
  const [jobPublications, setJobPublications] = useState({}); // jobId -> [{channel,status,error,...}]
  const [whatsappQueue, setWhatsappQueue] = useState([]);
  const [showWhatsappQueue, setShowWhatsappQueue] = useState(false);
  const [publishOpen, setPublishOpen] = useState({}); // jobId -> bool
  const [publishChannels, setPublishChannels] = useState({}); // jobId -> {crew_portal,whatsapp,instagram,facebook}
  const [publishCrewIds, setPublishCrewIds] = useState({}); // jobId -> [crewIds]
  const [publishTemplateId, setPublishTemplateId] = useState({}); // jobId -> templateId
  const [jobImagePreview, setJobImagePreview] = useState({}); // jobId -> dataURL
  const [publishing, setPublishing] = useState({}); // jobId -> bool
  // Crew portal — iş arıyorum + ilanlar
  const [portalJobs, setPortalJobs] = useState([]);

  // İletişim (WhatsApp) — yönetici numarası + personel telefon listesi
  const [waManagerNumber, setWaManagerNumber] = useState("");

  // Personel detayı — uygunluk skoru (backend eligibility motorundan)
  const [crewEligibility, setCrewEligibility] = useState(null);

  // Belge kategori detay modalı (expired/urgent/approaching/valid)
  const [docCategoryModal, setDocCategoryModal] = useState({ isOpen: false, status: '', title: '', docs: [], loading: false });
  const [docCategorySelected, setDocCategorySelected] = useState([]);

  // ==========================================
  // AYARLAR (LocalStorage)
  // ==========================================
  const [appSettings, setAppSettings] = useState(() => {
    try {
      const saved = localStorage.getItem("crewintel_settings");
      return saved ? JSON.parse(saved) : { companyName: "CREWINTEL", logoUrl: "" };
    } catch (e) {
      return { companyName: "CREWINTEL", logoUrl: "" };
    }
  });

  // ==========================================
  // AUTH (GİRİŞ) DURUMU
  // ==========================================
  const [auth, setAuth] = useState(() => {
    try {
      const saved = localStorage.getItem("crewintel_auth");
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [loginError, setLoginError] = useState("");
  // Ayarlar: hesap + kullanıcı yönetimi
  const [accForm, setAccForm] = useState({ current_password: "", new_email: "" });
  const [pwdForm, setPwdForm] = useState({ current_password: "", new_password: "", confirm: "" });
  const [users, setUsers] = useState([]);
  const [newUserForm, setNewUserForm] = useState({ email: "", password: "", full_name: "", role: "viewer" });
  const [settingsMsg, setSettingsMsg] = useState(null);
  const canWrite = auth?.user?.role !== "viewer";
  const isAdmin = auth?.user?.role === "admin";
  const roleLabel = ({ admin: t('settings.admin'), hr: t('settings.hr'), viewer: t('settings.viewer'), crew: t('settings.crew') })[auth?.user?.role] || '';

  // ── Geri butonu: sayfa geçmişi yığını ────────────────────────────────────
  const navigate = (page) => {
    setNavStack((s) => [...s.slice(-29), { page: activePage, crewId: selectedCrewId, shipId: selectedShipId }]);
    setActivePage(page);
  };
  const goBack = () => {
    if (navStack.length === 0) return;
    const prev = navStack[navStack.length - 1];
    setActivePage(prev.page);
    setSelectedCrewId(prev.crewId ?? null);
    setSelectedShipId(prev.shipId ?? null);
    setNavStack(navStack.slice(0, -1));
  };

  // Hızlı Erişim Referansları
  const crewById = useMemo(
    () => Object.fromEntries(crew.map((member) => [member.id, member])),
    [crew]
  );
  
  const shipById = useMemo(
    () => Object.fromEntries(ships.map((ship) => [ship.id, ship])),
    [ships]
  );
  
  const selectedCrew = crewById[selectedCrewId];
  const selectedShip = shipById[selectedShipId];

  // ==========================================
  // API DATA YÜKLEME
  // ==========================================
  // Token'ı her isteğe ekle; 401 dönerse oturumu kapat ve giriş ekranına dön.
  useEffect(() => {
    const requestInterceptor = axios.interceptors.request.use((config) => {
      const saved = localStorage.getItem("crewintel_auth");
      if (saved) {
        try {
          const { token } = JSON.parse(saved);
          if (token) config.headers.Authorization = `Bearer ${token}`;
        } catch (e) { /* bozuk kayıt: yok say */ }
      }
      return config;
    });
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        const url = error.config?.url || "";
        if (error.response?.status === 401 && !url.includes("/api/auth/login")) {
          localStorage.removeItem("crewintel_auth");
          setAuth(null);
        }
        return Promise.reject(error);
      }
    );
    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  useEffect(() => {
    if (auth) {
      loadData();
      loadOpsSummary();
      loadNotifications();
    }
  }, []);

  async function loadData() {
    setCrewLoading(true);
    try {
      // API Hatası fırlatılırsa diğerlerinin de çökmemesi için catch eklendi.
      const [
        health, 
        crewRes, 
        shipsRes, 
        assignRes, 
        contractsRes, 
        expiryRes, 
        docsRes,
        jobsRes
      ] = await Promise.all([
        axios.get(`${API_URL}/health`).catch(() => ({ data: { status: "error" } })),
        axios.get(`${API_URL}/api/crew/?limit=200`).catch(() => ({ data: [], headers: {} })),
        axios.get(`${API_URL}/api/ships/`).catch(() => ({ data: [] })),
        axios.get(`${API_URL}/api/assignments/`).catch(() => ({ data: [] })),
        axios.get(`${API_URL}/api/contracts/`).catch(() => ({ data: [] })),
        axios.get(`${API_URL}/api/expiration/summary`).catch(() => ({ data: null })),
        // Dashboard 500KB+ tüm belgeyi çekmesin — ilk 100 yeterli (pending uyarısı için).
        // Personel sayfası matrisi tam listeyi sayfa açılınca yükler (aşağıdaki effect).
        axios.get(`${API_URL}/api/documents/?limit=100`).catch(() => ({ data: [] })),
        axios.get(`${API_URL}/api/jobs/?include_closed=true`).catch(() => ({ data: [] })),
      ]);
      
      setIsSystemHealthy(health.data.status === "healthy");
      setApiStatus(health.data.status === "healthy" ? t('dashboard.systemActive') : t('dashboard.systemDown'));
      
      setCrew(crewRes.data);
      
      // Gerçek toplam, sayfalama üstbilgisinden (X-Total-Count) gelir —
      // limit=200 yüzünden eksik sayı gösterilmesini önler.
      const totalCrew = parseInt(crewRes.headers?.["x-total-count"] ?? crewRes.data.length, 10);
      setTotalCrewStats({
        total: Number.isFinite(totalCrew) ? totalCrew : crewRes.data.length,
        active: crewRes.data.filter(m => m.status === "active").length
      });
      
      setShips(shipsRes.data);
      setAssignments(assignRes.data);
      setContracts(contractsRes.data);
      setExpirySummary(expiryRes.data);
      
      // Tek Merkezi Doküman Kaynağı
      setAllDocuments(docsRes.data);
      setJobs(jobsRes.data);
      
      setActiveFilterCount(0);
    } catch {
      setIsSystemHealthy(false);
      setApiStatus(t('dashboard.systemDown'));
    } finally {
      setCrewLoading(false);
    }
  }

  // ==========================================
  // FİLTRELEME VE FORMLAR (PERSONEL)
  // ==========================================
  async function loadFilteredCrew(filtersOverride = null) {
    const f = filtersOverride || crewFilters;
    setCrewLoading(true);
    try {
      const params = new URLSearchParams();
      
      if (f.name) {
        params.append("name", f.name);
      }
      if (f.position) {
        params.append("position", f.position);
      }
      if (f.nationality) {
        params.append("nationality", f.nationality);
      }
      if (f.rank) {
        params.append("rank", f.rank);
      }
      if (f.languages) {
        params.append("languages", f.languages);
      }
      if (f.experience_years_min) {
        params.append("experience_years_min", f.experience_years_min);
      }
      if (f.sea_service_months_min) {
        params.append("sea_service_months_min", f.sea_service_months_min);
      }
      if (f.availability) {
        params.append("availability", f.availability);
      }
      
      // Problematic backend'e gönderilir
      if (f.showProblematic) {
        params.append("show_problematic", "true");
      }

      const response = await axios.get(`${API_URL}/api/crew/?${params.toString()}&limit=200`);
      setCrew(response.data);

      let count = 0;
      if (f.name) count++;
      if (f.position) count++;
      if (f.nationality) count++;
      if (f.rank) count++;
      if (f.languages) count++;
      if (f.experience_years_min) count++;
      if (f.sea_service_months_min) count++;
      if (f.availability) count++;
      if (f.showProblematic) count++;
      
      setActiveFilterCount(count);

    } catch (err) {
      console.error("Filtreleme hatası:", err);
    } finally {
      setCrewLoading(false);
    }
  }

  function handleFilterChange(event) {
    const { name, value, type, checked } = event.target;
    setCrewFilters((prev) => ({ 
      ...prev, 
      [name]: type === "checkbox" ? checked : value 
    }));
  }

  function applyFilters(e) {
    e.preventDefault();
    loadFilteredCrew();
  }

  function clearFilters() {
    setCrewFilters(emptyFilters);
    loadData();
  }

  // ==========================================
  // FORM GÜNCELLEME İŞLEYİCİLERİ
  // ==========================================
  function handleCrewFormChange(event) {
    const { name, value } = event.target;
    setCrewForm((currentForm) => ({ 
      ...currentForm, 
      [name]: value 
    }));
  }

  function handleShipFormChange(event) {
    const { name, value } = event.target;
    setShipForm((currentForm) => ({ 
      ...currentForm, 
      [name]: value 
    }));
  }

  function handleContractFormChange(event) {
    const { name, value } = event.target;
    setContractForm((currentForm) => ({ 
      ...currentForm, 
      [name]: value 
    }));
  }

  // ==========================================
  // SUBMITS (KAYIT İŞLEMLERİ)
  // ==========================================
  async function handleCrewSubmit(event) {
    event.preventDefault();
    if (!requireWrite()) return;
    setFormError("");
    setIsSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/crew/`, {
        ...crewForm,
        nationality: crewForm.nationality || null,
      });
      
      setCrewForm(emptyCrewForm);
      setIsFormOpen(false);
      await loadData();
    } catch {
      setFormError(t('crew.saveError'));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleShipSubmit(event) {
    event.preventDefault();
    if (!requireWrite()) return;
    setIsSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/ships/`, {
        ...shipForm,
        status: "active"
      });
      
      setShipForm(emptyShipForm);
      setIsShipFormOpen(false);
      await loadData();
    } catch {
      alert(t('vessels.saveError'));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleContractSubmit(event) {
    event.preventDefault();
    if (!requireWrite()) return;
    setIsSubmitting(true);
    try {
      const payload = {
        crew_member_id: parseInt(contractForm.crew_member_id),
        ship_id: parseInt(contractForm.ship_id),
        contract_number: contractForm.contract_number,
        contract_type: contractForm.contract_type || "Employment",
        start_date: contractForm.start_date || new Date().toISOString().split("T")[0],
        end_date: contractForm.end_date || null,
        status: "active"
      };
      if (editingContractId) {
        await axios.put(`${API_URL}/api/contracts/${editingContractId}`, payload);
        setEditingContractId(null);
      } else {
        await axios.post(`${API_URL}/api/contracts/`, payload);
      }
      
      setContractForm(emptyContractForm);
      setIsContractFormOpen(false);
      await loadData();
    } catch {
      alert(t('contracts.saveError'));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function deleteContract(contractId) {
    if (!requireWrite()) return;
    if (!window.confirm(t('contracts.deleteConfirm'))) return;
    try {
      await axios.delete(`${API_URL}/api/contracts/${contractId}`);
      if (selectedContractId === contractId) setSelectedContractId(null);
      await loadData();
    } catch {
      alert(t('contracts.deleteError'));
    }
  }

  // ==========================================
  // DETAY SAYFASI AÇICILAR
  // ==========================================
  async function openCrewDetail(crewId) {
    setSelectedCrewId(crewId);
    navigate("crew-detail");
    setCrewDetailDocumentsLoading(true);
    setCrewEligibility(null);
    try {
      const response = await axios.get(`${API_URL}/api/documents/?crew_member_id=${crewId}`);
      setCrewDetailDocuments(response.data);
    } catch (err) {
      console.error("Personel belgeleri yüklenemedi:", err);
      setCrewDetailDocuments([]);
    } finally {
      setCrewDetailDocumentsLoading(false);
    }
    // Uygunluk motorundan bu personelin skorunu çek (staff roller)
    if (auth?.user?.role !== "crew") {
      const crewObj = crewById[crewId];
      if (crewObj?.position) {
        try {
          const eligRes = await axios.get(`${API_URL}/api/crew/eligible?position=${encodeURIComponent(crewObj.position)}&min_score=0&limit=200`);
          const found = (eligRes.data || []).find((r) => r.crew_id === crewId);
          setCrewEligibility(found || null);
        } catch {
          setCrewEligibility(null);
        }
      }
    }
  }

  function openShipDetail(shipId) {
    setSelectedShipId(shipId);
    navigate("ship-detail");
    loadShipStaffing(shipId);
  }

  function openDocumentsPage() {
    navigate("documents");
    loadDocuments();
  }

  // ==========================================
  // DOKÜMAN FİLTRELEME VE LİSTELEME
  // ==========================================
  async function loadDocuments(filters = docFilters, page = 0) {
    setDocumentsLoading(true);
    setDocumentsError(null);
    try {
      const params = new URLSearchParams();
      if (filters.document_type) params.append("document_type", filters.document_type);
      if (filters.match_status) params.append("match_status", filters.match_status);
      if (filters.expiry_status) params.append("expiry_status", filters.expiry_status);
      params.append("offset", page * DOC_PAGE_SIZE);
      params.append("limit", DOC_PAGE_SIZE);

      const response = await axios.get(`${API_URL}/api/documents/?${params.toString()}`);
      setDocuments(response.data);
      const total = parseInt(response.headers?.["x-total-count"] ?? "0", 10);
      setDocTotal(Number.isFinite(total) ? total : response.data.length);
      setDocPage(page);
    } catch {
      setDocumentsError(t('documents.uploadError'));
    } finally {
      setDocumentsLoading(false);
    }
  }
  
  function handleDocFilterChange(e) {
    const { name, value } = e.target;
    setDocFilters((prev) => ({ ...prev, [name]: value }));
  }

  function applyDocFilters() {
    loadDocuments(docFilters, 0);
  }

  function clearDocFilters() {
    const cleared = { document_type: "", match_status: "", expiry_status: "" };
    setDocFilters(cleared);
    loadDocuments(cleared, 0);
  }

  function goToFilteredDocs(status) {
    const newFilters = { document_type: "", match_status: "", expiry_status: status };
    setDocFilters(newFilters);
    navigate("documents");
    loadDocuments(newFilters);
  }

  // Belge kategori detay modalını aç
  async function openDocCategoryModal(status) {
    const titles = { expired: t('documents.expired'), urgent: t('documents.urgent') + ' (≤30)', approaching: t('documents.approaching') + ' (≤90)', valid: t('documents.valid') };
    setDocCategoryModal({ isOpen: true, status, title: titles[status] || status, docs: [], loading: true });
    setDocCategorySelected([]);
    try {
      const res = await axios.get(`${API_URL}/api/expiration/${status}`);
      setDocCategoryModal(prev => ({ ...prev, docs: res.data, loading: false }));
    } catch {
      setDocCategoryModal(prev => ({ ...prev, loading: false }));
    }
  }

  // Belge kategorisi toplu e-posta gönder
  function sendDocCategoryEmail() {
    const crewIds = [...new Set(docCategorySelected.map(d => d.crew_member_id).filter(Boolean))];
    if (crewIds.length === 0) return;
    const statusLabels = { expired: t('documents.expired'), urgent: t('documents.urgent'), approaching: t('documents.approaching'), valid: t('documents.valid') };
    setEmailModal({ isOpen: true, crewIds, subject: `${statusLabels[docCategoryModal.status]} - ${t('documents.title')}`, body: '' });
    setDocCategoryModal(prev => ({ ...prev, isOpen: false }));
  }

  // Belge kategorisi toplu WhatsApp
  function sendDocCategoryWhatsApp() {
    const selectedDocs = docCategorySelected.filter(d => d.crew_member_id);
    selectedDocs.forEach(doc => {
      const member = crew.find(c => c.id === doc.crew_member_id);
      if (member && member.phone) {
        const docLabel = translateTaskText(`${member.first_name} ${member.last_name} — ${doc.document_type} ${t('documents.expired')}`);
        const msg = encodeURIComponent(`${docLabel}`);
        window.open(`https://wa.me/${member.phone.replace(/[^0-9]/g, '')}?text=${msg}`, '_blank');
      }
    });
  }

  // ==========================================
  // SİLME İŞLEMLERİ (ÇÖP TENEKESİ)
  // ==========================================
  async function deleteCrew(id, e) {
    e.stopPropagation();
    if (!requireWrite()) return;
    if (!window.confirm(t('crew.deleteConfirm'))) return;
    try {
      await axios.delete(`${API_URL}/api/crew/${id}`);
      await loadData();
    } catch (err) {
      alert(t('crew.deleteError'));
    }
  }

  async function deleteDocument(id) {
    if (!requireWrite()) return;
    if (!window.confirm(t('common.confirm'))) return;
    try {
      await axios.delete(`${API_URL}/api/documents/${id}`);
      await loadDocuments();
      await loadData();
    } catch (err) {
      alert(t('documents.deleteError'));
    }
  }

  // ==========================================
  // ATAMA (ASSIGNMENT) İŞLEMLERİ
  // ==========================================
  async function handleAssignmentSubmit(e) {
    e.preventDefault();
    if (!requireWrite()) return;
    try {
      await axios.post(`${API_URL}/api/assignments/`, {
        crew_member_id: parseInt(assignmentModal.crew_member_id),
        ship_id: parseInt(assignmentModal.ship_id),
        position: assignmentModal.position,
        start_date: assignmentModal.start_date || new Date().toISOString().split("T")[0],
        end_date: assignmentModal.end_date || null,
        status: "active"
      });
      
      setAssignmentModal({ 
        isOpen: false, 
        crew_member_id: "", 
        ship_id: "", 
        position: "",
        start_date: "",
        end_date: ""
      });
      
      alert(t('vesselStaff.saved'));
      await loadData();
    } catch (err) {
      console.error(err);
      alert(t('errors.generic'));
    }
  }

  // ==========================================
  // ÖNCELİK 2 - BELGE EŞLEŞTİRME (MANUEL)
  // ==========================================
  async function handleMatchDocument(docId, crewId) {
    if (!requireWrite()) return;
    if (!crewId) { 
      alert(t('crew.selectPerson')); 
      return; 
    }
    try {
      await axios.put(`${API_URL}/api/documents/${docId}/match`, {
        crew_member_id: parseInt(crewId),
      });
      
      alert(t('documents.matched'));
      await loadData(); 
      if (activePage === "documents") await loadDocuments();
      if (selectedCrewId) {
        const response = await axios.get(`${API_URL}/api/documents/?crew_member_id=${selectedCrewId}`);
        setCrewDetailDocuments(response.data);
      }
    } catch (err) {
      console.error(err);
      alert(t('errors.generic'));
    }
  }

  // ==========================================
  // DOSYA YÜKLEME (DRAG & DROP) BÖLÜMÜ
  // ==========================================
  function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function addStagedFiles(newFiles) {
    setStagedFiles((prev) => {
      const existingKeys = new Set(prev.map((file) => `${file.name}_${file.size}`));
      // Sadece PDF ve TXT dosyalarını kabul et (drag-and-drop'ta da).
      const ALLOWED_EXT = [".pdf", ".txt"];
      const filtered = newFiles.filter((file) => {
        const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
        return ALLOWED_EXT.includes(ext);
      });
      const rejected = newFiles.length - filtered.length;
      if (rejected > 0) {
        setUploadStatus({});
        // Geçersiz dosyalar hakkında bilgilendir.
        setLastBatchSummary({
          total: 0, matched: 0, pending: 0, duplicate: 0, error: rejected,
          detail: `${rejected} file(s) rejected — only PDF and TXT files are supported.`,
        });
      }
      const deduped = filtered.filter((file) => !existingKeys.has(`${file.name}_${file.size}`));
      return [...prev, ...deduped];
    });
  }

  function removeStagedFile(index) {
    setStagedFiles((prev) => prev.filter((_, i) => i !== index));
  }

  function clearStagedFiles() {
    setStagedFiles([]);
    setUploadStatus({});
    setUploadResults({});
    setUploadProgress({});
    setLastBatchSummary(null);
  }

  function handleFileInputChange(event) {
    addStagedFiles(Array.from(event.target.files));
    event.target.value = "";
  }

  function handleDragOver(event) {
    event.preventDefault();
    setDragActive(true);
  }

  function handleDragLeave(event) {
    event.preventDefault();
    setDragActive(false);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragActive(false);
    addStagedFiles(Array.from(event.dataTransfer.files));
  }

  function fileKey(file) {
    return `${file.name}_${file.size}`;
  }

  async function uploadSingleFile(file) {
    const key = fileKey(file);
    
    setUploadStatus((prev) => ({ ...prev, [key]: "uploading" }));
    setUploadProgress((prev) => ({ ...prev, [key]: null }));

    const formData = new FormData();
    formData.append("files", file);
    const requestSentAt = Date.now();

    try {
      const response = await axios.post(`${API_URL}/api/documents/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
            setUploadProgress((prev) => ({ ...prev, [key]: percent }));
          }
        },
      });
      
      const document = response.data[0];
      
      const DUPLICATE_THRESHOLD_MS = 3000;
      const createdAtMs = new Date(`${document.created_at}Z`).getTime();
      const isDuplicate = !Number.isNaN(createdAtMs) && (requestSentAt - createdAtMs) > DUPLICATE_THRESHOLD_MS;
      const finalStatus = isDuplicate ? "duplicate" : "success";
      
      setUploadStatus((prev) => ({ ...prev, [key]: finalStatus }));
      setUploadResults((prev) => ({ ...prev, [key]: { document, duplicate: isDuplicate } }));
      
      return { status: finalStatus, document };
      
    } catch (error) {
      const httpStatus = error.response?.status ?? null;
      const backendDetail = error.response?.data?.detail;
      const hasBackendDetail = typeof backendDetail === "string";
      const isNetworkError = !error.response;
      
      const message = hasBackendDetail
        ? backendDetail
        : isNetworkError
          ? t('errors.network')
          : (error.message || t('errors.uploadFailed'));
      
      setUploadStatus((prev) => ({ ...prev, [key]: "error" }));
      setUploadResults((prev) => ({
        ...prev,
        [key]: { error: message, httpStatus, source: isNetworkError ? "network" : "backend" },
      }));
      
      return { status: "error", error: message, httpStatus };
    }
  }

  async function uploadStagedFiles() {
    if (isUploading) return;
    if (!requireWrite()) return;
    setIsUploading(true);
    setBatchProgress({ status: "starting", total: stagedFiles.length, processed: 0 });

    try {
      const formData = new FormData();
      for (const file of stagedFiles) {
        formData.append("files", file);
      }

      // Bulk upload: backend dosyaları kabul eder, arka planda işler.
      // NOT: Content-Type manuel ayarlanmaz; axios FormData ile otomatik
      // multipart boundary ekler.
      const response = await axios.post(`${API_URL}/api/documents/batch`, formData);

      const { batch_id, total } = response.data;
      setBatchProgress((prev) => ({ ...prev, batch_id, status: "processing", total: total || stagedFiles.length }));

      // İşleme ilerlemesini yokla.
      const poll = async () => {
        try {
          const statusRes = await axios.get(`${API_URL}/api/documents/batch/${batch_id}`);
          const data = statusRes.data;
          setBatchProgress(data);
          if (data.status !== "done" && data.processed < data.total) {
            setTimeout(poll, 1200);
          } else {
            // Bitti: özeti göster, staged dosyaları temizle.
            setLastBatchSummary({
              total: data.total,
              matched: data.matched,
              pending: data.review,
              review: data.review,
              conflict: data.conflict,
              unmatched: data.unmatched,
              duplicate: data.duplicate,
              error: data.failed,
            });
            setStagedFiles([]);
            setUploadStatus({});
            setIsUploading(false);
            await loadDocuments();
            await loadData();
          }
        } catch (e) {
          console.error("Batch durumu alınamadı:", e);
          setBatchProgress((prev) => ({ ...prev, status: "error" }));
          setIsUploading(false);
        }
      };
      poll();
    } catch (error) {
      console.error("Batch yükleme başarısız:", error);
      const backendDetail = error.response?.data?.detail;
      setLastBatchSummary({
        total: stagedFiles.length,
        matched: 0,
        pending: 0,
        duplicate: 0,
        error: stagedFiles.length,
        detail: typeof backendDetail === 'string' ? backendDetail : t('errors.uploadFailed'),
      });
      setIsUploading(false);
      setBatchProgress(null);
    }
  }

  // ── Match Review (İnceleme Kuyruğu) ────────────────────────────────────────
  async function openReviewQueue() {
    setReviewOpen(true);
    setReviewLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/documents/review?limit=200`);
      setReviewQueue(response.data);
    } catch (e) {
      console.error("Review kuyruğu yüklenemedi:", e);
      setReviewQueue([]);
    } finally {
      setReviewLoading(false);
    }
  }

  async function loadCandidates(docId) {
    setCandidatesLoading(true);
    setCandidateData(null);
    try {
      const response = await axios.get(`${API_URL}/api/documents/${docId}/candidates`);
      setCandidateData(response.data);
    } catch (e) {
      console.error("Adaylar yüklenemedi:", e);
      setCandidateData({ candidates: [], error: t('errors.loadingFailed') });
    } finally {
      setCandidatesLoading(false);
    }
  }

  async function confirmMatchFromReview(docId, crewId) {
    if (!requireWrite()) return;
    try {
      await axios.put(`${API_URL}/api/documents/${docId}/match`, {
        crew_member_id: parseInt(crewId, 10),
      });
      alert(t('documents.matched'));
      await openReviewQueue();
      await loadDocuments();
      await loadData();
    } catch (err) {
      console.error(err);
      alert(t('errors.generic'));
    }
  }

  async function approvePendingDoc(docId) {
    if (!requireWrite()) return;
    try {
      await axios.post(`${API_URL}/api/documents/${docId}/approve`);
      alert(t('status.valid'));
      await openReviewQueue();
      await loadDocuments();
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || t('errors.generic'));
    }
  }

  async function rejectPendingDoc(docId) {
    if (!requireWrite()) return;
    if (!window.confirm(t('common.confirm'))) return;
    try {
      await axios.post(`${API_URL}/api/documents/${docId}/reject`);
      alert(t('status.rejected'));
      await openReviewQueue();
      await loadDocuments();
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || t('errors.generic'));
    }
  }

  async function retryUpload(file) {
    const key = fileKey(file);
    if (uploadStatus[key] !== "error") return;
    
    const result = await uploadSingleFile(file);
    if (result.status === "success" || result.status === "duplicate") {
      setStagedFiles((prev) => prev.filter((f) => fileKey(f) !== key));
    }
    await loadDocuments();
  }

  function saveSettings(e) {
    e.preventDefault();
    localStorage.setItem("crewintel_settings", JSON.stringify(appSettings));
    alert(t('settings.settingsSaved'));
  }

  // ==========================================
  // AUTH İŞLEMLERİ (LOGIN / LOGOUT)
  // ==========================================
  async function handleLogin(e) {
    e.preventDefault();
    setLoginError("");
    try {
      const response = await axios.post(`${API_URL}/api/auth/login`, {
        email: loginForm.email.trim(),
        password: loginForm.password,
      });
      const { access_token: token, user } = response.data;
      const authData = { token, user };
      localStorage.setItem("crewintel_auth", JSON.stringify(authData));
      setAuth(authData);
      setLoginForm({ email: "", password: "" });
      loadData();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setLoginError(typeof detail === "string" ? detail : t('auth.invalidCredentials'));
    }
  }

  function handleLogout() {
    localStorage.removeItem("crewintel_auth");
    setAuth(null);
    setActivePage("dashboard");
  }

  function requireWrite() {
    if (!canWrite) {
      alert(t('errors.unauthorized'));
      return false;
    }
    return true;
  }


  // ==========================================
  // GÖRSEL RENDER FONKSİYONLARI (COMPONENTS)
  // ==========================================

  function renderCrewMatrix(crewId) {
    const reqTypes = [
      { id: 'passport', label: 'P', title: 'Pasaport' },
      { id: 'seaman_book', label: 'SB', title: 'Seaman Book' },
      { id: 'stcw', label: 'ST', title: 'STCW' },
      { id: 'medical', label: 'M', title: 'Sağlık Raporu' },
      { id: 'contract', label: 'C', title: 'Sözleşme' }
    ];
    
    return (
      <div style={{ display: 'flex', gap: '6px', marginLeft: '20px' }}>
        {reqTypes.map(reqType => {
          const myDocs = allDocuments.filter(d => d.crew_member_id === crewId && d.document_type === reqType.id);
          let bg = "#f1f5f9";
          let text = "#94a3b8";
          let pulse = false;
          
          if (myDocs.length > 0) {
            const hasExpired = myDocs.some(d => d.expiry_status === "expired");
            const hasUrgent = myDocs.some(d => d.expiry_status === "urgent");
            const hasAppr = myDocs.some(d => d.expiry_status === "approaching");
            
            if (hasExpired) { 
              bg = "#fee2e2"; 
              text = "#dc2626"; 
              pulse = true; 
            } else if (hasUrgent) { 
              bg = "#ffedd5"; 
              text = "#ea580c"; 
              pulse = true; 
            } else if (hasAppr) { 
              bg = "#fef9c3"; 
              text = "#ca8a04"; 
            } else { 
              bg = "#dcfce3"; 
              text = "#16a34a"; 
            }
          } else {
            bg = "#fee2e2"; 
            text = "#dc2626"; 
            pulse = true; 
          }
          
          return (
            <div 
              key={reqType.id} 
              title={reqType.title} 
              className={pulse ? "pulse-soft" : ""} 
              style={{ 
                width: '28px', 
                height: '28px', 
                borderRadius: '4px', 
                background: bg, 
                color: text, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                fontSize: '12px', 
                fontWeight: 'bold', 
                border: `1px solid ${text}40` 
              }}
            >
              {reqType.label}
            </div>
          );
        })}
      </div>
    );
  }

  function renderCrewFilters() {
    return (
      <div style={{ marginBottom: "20px" }}>
        <button
          className="secondary-button"
          onClick={() => setIsFilterOpen(!isFilterOpen)}
          style={{ width: "100%", justifyContent: "space-between", background: "#f8fafc", border: "1px solid #cbd5e1" }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "8px", color: "#0f172a", fontWeight: "bold" }}>
            <Filter size={16} /> {t('crew.advancedFilters')}
            {activeFilterCount > 0 && (
              <span className="nav-badge" style={{background: "#ea580c"}}>
                {activeFilterCount}
              </span>
            )}
          </span>
          <ChevronDown 
            size={16} 
            style={{ transform: isFilterOpen ? "rotate(180deg)" : "none", transition: "0.2s", color: "#0f172a" }} 
          />
        </button>

        {isFilterOpen && (
          <form 
            className="panel" 
            style={{ marginTop: "10px", padding: "20px", background: "#ffffff", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.05)" }} 
            onSubmit={applyFilters}
          >
            <div className="detail-grid" style={{ marginBottom: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span className="section-label">{t('crew.nameSearch')}</span>
                <input className="form-input" name="name" value={crewFilters.name} onChange={handleFilterChange} placeholder="Örn: Ahmet" />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span className="section-label">Uyruk (Nereli)</span>
                <select className="form-input" name="nationality" value={crewFilters.nationality} onChange={handleFilterChange}>
                  <option value="">Tüm uyruklar</option>
                  {FILTER_NATIONALITIES.map((n) => <option key={n} value={n}>🌍 {t(`nationalities.${n === 'Türkiye' ? 'turkey' : n === 'Mısır' ? 'egypt' : n === 'Rusya' ? 'russia' : n === 'Gürcistan' ? 'georgia' : n === 'Ukrayna' ? 'ukraine' : n === 'Azerbaycan' ? 'azerbaijan' : n === 'Bulgaristan' ? 'bulgaria' : n === 'Romanya' ? 'romania' : n === 'Filipinler' ? 'philippines' : n === 'Japon' ? 'japan' : n === 'Hindistan' ? 'india' : n === 'Endonezya' ? 'indonesia' : n === 'Çin' ? 'china' : n === 'Yunanistan' ? 'greece' : n === 'Almanya' ? 'germany' : n === 'İngiltere' ? 'uk' : n === 'ABD' ? 'usa' : n === 'Polonya' ? 'poland' : 'turkey'}`)}</option>)},
                </select>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span className="section-label">{t('crew.position')}</span>
                <select className="form-input" name="position" value={crewFilters.position} onChange={handleFilterChange}>
                  <option value="">Tüm pozisyonlar</option>
                  {FILTER_POSITIONS.map((p) => <option key={p} value={p}>⚓ {t(`positions.${p === 'Kaptan' ? 'captain' : p === 'Başmühendis' ? 'chief_engineer' : p === '2. Kaptan' ? 'second_officer' : p === '3. Kaptan' ? 'third_officer' : p === 'Elektrik Zabiti' ? 'electric_officer' : p === 'Yağcı' ? 'oiler' : p === 'Usta Gemici' ? 'able_seaman' : p === 'Gemici' ? 'ordinary_seaman' : p === 'Aşçı' ? 'cook' : p === 'Kamarot' ? 'steward' : 'captain'}`)}</option>)}
                </select>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span className="section-label">Rütbe</span>
                <input className="form-input" name="rank" value={crewFilters.rank} onChange={handleFilterChange} placeholder="Örn: Master, Cook" />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span className="section-label">Dil</span>
                <input className="form-input" name="languages" value={crewFilters.languages} onChange={handleFilterChange} placeholder="Örn: English" />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span className="section-label">Min. Tecrübe (Yıl)</span>
                <input className="form-input" type="number" min="0" name="experience_years_min" value={crewFilters.experience_years_min} onChange={handleFilterChange} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span className="section-label">Min. Deniz Hizmeti (Ay)</span>
                <input className="form-input" type="number" min="0" name="sea_service_months_min" value={crewFilters.sea_service_months_min} onChange={handleFilterChange} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span className="section-label">{t('crew.availability')}</span>
                <select className="form-input" name="availability" value={crewFilters.availability} onChange={handleFilterChange}>
                  <option value="">Tümü</option>
                  <option value="available">🟢 Müsait</option>
                  <option value="on_leave">🟡 İzinli</option>
                  <option value="on_board">⚫ {t('crew.onboard')}</option>
                  <option value="not_available">🔴 Müsait değil</option>
                </select>
              </div>
            </div>
            
            <label style={{ display: "flex", alignItems: "center", gap: "10px", fontWeight: "700", color: "#dc2626", marginTop: "16px", cursor: "pointer", background: "#fef2f2", padding: "12px", borderRadius: "8px", border: "1px solid #fecaca" }}>
              <input 
                type="checkbox" 
                name="showProblematic" 
                checked={crewFilters.showProblematic} 
                onChange={handleFilterChange} 
                style={{ width: "20px", height: "20px", cursor: "pointer" }} 
              />
              <AlertCircle size={20} /> Sadece Eksik veya Sorunlu Evrağı Olanları Göster
            </label>

            <div className="form-actions" style={{ justifyContent: "flex-start", marginTop: "20px" }}>
              <button className="primary-button" type="submit" disabled={crewLoading}><Search size={16} /> FİLTRELE</button>
              <button className="secondary-button" type="button" onClick={clearFilters} disabled={crewLoading}>TEMİZLE</button>
            </div>
          </form>
        )}
      </div>
    );
  }

  function renderCrewList() {
    let displayedCrew = crew;
    
    // Front-end filter fallback
    if (crewFilters.showProblematic) {
      displayedCrew = crew.filter(member => {
        const mDocs = allDocuments.filter(d => d.crew_member_id === member.id);
        const mTypes = mDocs.map(d => d.document_type);
        const reqDocs = ["passport", "seaman_book", "stcw", "medical", "contract"];
        const isMissing = reqDocs.some(rt => !mTypes.includes(rt));
        const hasIssues = mDocs.some(d => d.expiry_status === "expired" || d.expiry_status === "urgent");
        return isMissing || hasIssues;
      });
    }

    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('crew.title')}</h2>
            <p>
              {activeFilterCount > 0
                ? `${displayedCrew.length} sonuç bulundu (${activeFilterCount} filtre aktif)`
                : t('crew.title')}
            </p>
          </div>
          {canWrite && (
            <button 
              className="primary-button" 
              onClick={() => { setFormError(""); setIsFormOpen(true); }}
            >
              <UserPlus size={18} /> {t('crew.addNew')}
            </button>
          )}
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "16px" }}>
          <button className="secondary-button" onClick={exportCsv} title="Tüm personeli CSV olarak indir">
            <Download size={16} /> CSV Dışa Aktar
          </button>
          {canWrite && (
            <button className="secondary-button" onClick={() => { setImportPreview(null); setImportCsvText(""); setImportMsg(null); setShowImport(!showImport); }}>
              <Upload size={16} /> CSV İçe Aktar
            </button>
          )}
          {canWrite && (
            <button
              className="secondary-button"
              onClick={() => {
                if (selectedCrewIds.length === 0) {
                  window.alert("Önce listeden en az bir personel seçin (satır başındaki kutu).");
                  return;
                }
                openEmailModal(selectedCrewIds);
              }}
              title="Seçilen personellere toplu e-posta gönder"
            >
              <Mail size={16} /> {t('email.bulkSend')} {selectedCrewIds.length > 0 ? `(${selectedCrewIds.length})` : ""}
            </button>
          )}
        </div>

        {showImport && (
          <div style={{ padding: "18px", border: "1px solid #e2e8f0", borderRadius: "12px", background: "#f8fafc", marginBottom: "18px" }}>
            <p className="section-label">CSV İçe Aktar (sütunlar: first_name,last_name,position,rank,nationality,email,phone,date_of_birth,experience_years)</p>
            <textarea className="form-input" rows="5" style={{ width: "100%", padding: "10px", boxSizing: "border-box", fontFamily: "monospace", fontSize: "12px" }}
              placeholder={"first_name,last_name,position,rank,nationality\nAhmet,Yılmaz,Kaptan,Kaptan,Türk"}
              value={importCsvText} onChange={(e) => setImportCsvText(e.target.value)} />
            <div style={{ display: "flex", gap: "10px", marginTop: "10px", flexWrap: "wrap" }}>
              <button className="primary-button" onClick={handleCsvPreview} disabled={!importCsvText.trim()}><Search size={16} /> Önizle</button>
              {importMsg && <span style={{ fontSize: "13px", fontWeight: "600", color: importMsg.type === "success" ? "#15803d" : "#b91c1c", alignSelf: "center" }}>{importMsg.text}</span>}
            </div>
            {importPreview && (
              <div style={{ marginTop: "14px", padding: "14px", background: "#fff", border: "1px solid #e2e8f0", borderRadius: "10px" }}>
                <p style={{ margin: "0 0 8px 0", fontSize: "13px", color: "#475569" }}>
                  <strong>{importPreview.total}</strong> kayıt bulundu · <strong style={{ color: "#15803d" }}>{importPreview.new_count} yeni</strong> · <strong style={{ color: "#b45309" }}>{importPreview.duplicate_count} mevcut/çakışma</strong>
                </p>
                <button className="primary-button" onClick={confirmImport} style={{ background: "#15803d", border: "none" }}>İçe Aktar ({importPreview.new_count} yeni kayıt)</button>
              </div>
            )}
          </div>
        )}
        
        {renderCrewFilters()}
        
        {isFormOpen && (
          <form className="crew-form" onSubmit={handleCrewSubmit}>
            <label>Ad<input name="first_name" value={crewForm.first_name} onChange={handleCrewFormChange} required /></label>
            <label>Soyad<input name="last_name" value={crewForm.last_name} onChange={handleCrewFormChange} required /></label>
            <label>{t('crew.position')}<input name="position" value={crewForm.position} onChange={handleCrewFormChange} required /></label>
            <label>Uyruk<input name="nationality" value={crewForm.nationality} onChange={handleCrewFormChange} /></label>
            
            {formError && <p className="form-error">{formError}</p>}
            
            <div className="form-actions">
              <button className="secondary-button" type="button" onClick={() => setIsFormOpen(false)}>{t('common.cancel')}</button>
              <button className="primary-button" type="submit" disabled={isSubmitting}>{isSubmitting ? t('common.saving') : t('common.save')}</button>
            </div>
          </form>
        )}
        
        {crewLoading ? (
          <p className="crew-loading">{t('common.loading')}</p>
        ) : (
          <div className="table-wrapper">
            <div className="entity-list" style={{ minWidth: "800px" }}>
              {displayedCrew.map((member, idx) => (
                <div 
                  className="entity-row" 
                  key={member.id} 
                  onClick={() => openCrewDetail(member.id)} 
                  style={{cursor: "pointer", display: "flex", alignItems: "center", background: "#fff", borderBottom: "1px solid #e2e8f0"}}
                >
                  {canWrite && (
                    <input
                      type="checkbox"
                      checked={selectedCrewIds.includes(member.id)}
                      onClick={(e) => e.stopPropagation()}
                      onChange={() => toggleCrewSelection(member.id)}
                      style={{ width: "16px", height: "16px", marginRight: "8px", cursor: "pointer" }}
                      title={t('email.selectForEmail')}
                    />
                  )}
                  <div style={{ width: "30px", fontWeight: "bold", color: "#64748b" }}>
                    {String(idx + 1).padStart(2, '0')}
                  </div>
                  <div style={{ flex: 1, textAlign: "left", paddingLeft: "10px" }}>
                    <strong style={{ fontSize: "16px", color: "#0f172a" }}>
                      {member.first_name} {member.last_name}
                    </strong>
                    <span style={{ display: "block", color: "#475569", marginTop: "4px" }}>
                      {translatePosition(member.position)} {member.rank ? ` · ${member.rank}` : ''} · {member.status}
                    </span>
                  </div>
                  
                  {renderCrewMatrix(member.id)}
                  
                  {canWrite && (
                    <button 
                      className="icon-button" 
                      onClick={(e) => deleteCrew(member.id, e)} 
                      title={t('crew.delete')} 
                      style={{ padding: "8px", marginLeft: "16px" }}
                    >
                      <Trash2 size={20} color="#ef4444" />
                    </button>
                  )}
                </div>
              ))}
              
              {displayedCrew.length === 0 && (
                <div className="empty" style={{ padding: "40px" }}>
                  <Users size={48} color="#94a3b8" />
                  <h3 style={{ color: "#0f172a" }}>{t('crew.noResults')}</h3>
                </div>
              )}
            </div>
          </div>
        )}
      </section>
    );
  }

  function renderCrewDetail() {
    return (
      <section className="panel detail-panel">
        <button className="back-button" onClick={() => setActivePage("crew")}>
          {t('crew.backToList')}
        </button>
        
        {selectedCrew ? (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
              <h2 style={{ fontSize: "28px", color: "#0f172a", margin: 0 }}>
                {selectedCrew.first_name} {selectedCrew.last_name}
              </h2>
              {canWrite && (
                <>
                  <button 
                    className="primary-button" 
                    onClick={() => setAssignmentModal({ isOpen: true, crew_member_id: selectedCrew.id, ship_id: "", position: selectedCrew.position || "", start_date: "", end_date: "" })}
                  >
                    <Ship size={18} /> {t('vesselStaff.assign')}
                  </button>
                  <button 
                    className="secondary-button" 
                    onClick={() => openEmailModal([selectedCrew.id])}
                    title="Bu personele e-posta gönder"
                  >
                    <Mail size={18} /> {t('email.send')}
                  </button>
                </>
              )}
            </div>

            {/* UYGUNLUK SKORU (backend eligibility motoru) */}
            {auth?.user?.role !== "crew" && (
              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "18px" }}>
                {crewEligibility ? (
                  <span style={{ padding: "8px 16px", borderRadius: "999px", fontWeight: "700", fontSize: "14px", background: crewEligibility.score >= 90 ? "#f0fdf4" : crewEligibility.score >= 70 ? "#fffbeb" : "#fef2f2", color: crewEligibility.score >= 90 ? "#15803d" : crewEligibility.score >= 70 ? "#b45309" : "#b91c1c", border: `1px solid ${crewEligibility.score >= 90 ? "#bbf7d0" : crewEligibility.score >= 70 ? "#fde68a" : "#fecaca"}` }}>
                    🎯 Uygunluk: %{crewEligibility.score} {crewEligibility.availability === "available" ? "· 🟢 Müsait" : ""}
                  </span>
                ) : (
                  <span style={{ padding: "8px 16px", borderRadius: "999px", fontWeight: "600", fontSize: "13px", background: "#f8fafc", color: "#64748b", border: "1px solid #e2e8f0" }}>
                    🎯 Uygunluk: — (pozisyon için hesaplanamadı)
                  </span>
                )}
              </div>
            )}
            
            {/* AKILLI UYARI PANOSU */}
            {!crewDetailDocumentsLoading && (() => {
              const typeLabels = { passport: t('documentTypes.passport'), seaman_book: t('documentTypes.seaman_book'), stcw: t('documentTypes.stcw'), medical: t('documentTypes.medical'), contract: t('documentTypes.contract') };
              const reqDocs = ["passport", "seaman_book", "stcw", "medical", "contract"];
              
              const foundTypes = crewDetailDocuments.map(d => d.document_type);
              const missing = reqDocs.filter(t => !foundTypes.includes(t));
              const problems = crewDetailDocuments.filter(d => d.expiry_status === "expired" || d.expiry_status === "urgent");
              
              let contractText = t('contracts.noContracts');
              const contractDoc = crewDetailDocuments.find(d => d.document_type === "contract" && d.expiry_date);
              
              if (contractDoc) {
                  const diffTime = new Date(contractDoc.expiry_date) - new Date();
                  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                  if (diffDays > 0) {
                      contractText = `Sözleşme ${contractDoc.expiry_date} tarihinde bitecek (${diffDays} gün var).`;
                  } else {
                      contractText = `Sözleşme süresi ${contractDoc.expiry_date} tarihinde dolmuş!`;
                  }
              }

              if (missing.length > 0 || problems.length > 0) {
                  return (
                    <div className="pulse-soft" style={{ background: "#fef2f2", borderLeft: "6px solid #ef4444", padding: "20px", marginBottom: "24px", borderRadius: "0 12px 12px 0" }}>
                        <h4 style={{ margin: "0 0 12px 0", color: "#b91c1c", display: "flex", alignItems: "center", gap: "8px", fontSize: "16px", textTransform: "uppercase" }}>
                          <AlertCircle size={22}/> Eksik Veya Sorunlu Evraklar Var!
                        </h4>
                        <ul style={{ margin: 0, paddingLeft: "28px", color: "#991b1b", fontSize: "15px", lineHeight: "1.8" }}>
                          {missing.map(m => <li key={m}><strong>{typeLabels[m] || m}</strong> belgesi eksik veya onay bekliyor.</li>)}
                          {problems.map(p => <li key={p.id}><strong>{p.original_filename}</strong> {p.expiry_status === 'expired' ? t('documents.expired') : t('documents.urgent')}</li>)}
                        </ul>
                        <p style={{ margin: "16px 0 0 0", fontSize: "15px", color: "#991b1b", fontWeight: "700" }}>{contractText}</p>
                    </div>
                  );
              } else if (crewDetailDocuments.length > 0) {
                  return (
                    <div style={{ background: "#f0fdf4", borderLeft: "6px solid #22c55e", padding: "20px", marginBottom: "24px", borderRadius: "0 12px 12px 0" }}>
                        <h4 style={{ margin: "0 0 8px 0", color: "#15803d", display: "flex", alignItems: "center", gap: "8px", fontSize: "16px", textTransform: "uppercase" }}>
                          <Activity size={22}/> {t('crew.completeProfile')}
                        </h4>
                        <p style={{ margin: 0, color: "#166534", fontSize: "15px", fontWeight: "600" }}>Zorunlu evrakların tamamı yüklü ve geçerli. {contractText}</p>
                    </div>
                  );
              }
              return null;
            })()}

            <p className="section-label">Temel Bilgiler</p>
            <table className="detail-table" style={{ width: "100%", borderCollapse: "collapse", marginBottom: "22px", border: "1px solid #e2e8f0", borderRadius: "10px", overflow: "hidden" }}>
              <tbody>
                {[[t('crew.position'), selectedCrew.position || "—"], [t('crew.rank'), selectedCrew.rank || "—"], [t('crew.nationality'), selectedCrew.nationality || "—"], [t('common.status'), selectedCrew.status], [t('auth.email'), selectedCrew.email || "—"], [t('common.phone'), selectedCrew.phone || "—"]].map(([k, v]) => (
                  <tr key={k} style={{ borderBottom: "1px solid #eef2f7" }}>
                    <td style={{ padding: "10px 14px", width: "220px", fontWeight: "600", color: "#475569", background: "#f8fafc", fontSize: "13px", borderRight: "1px solid #eef2f7" }}>{k}</td>
                    <td style={{ padding: "10px 14px", color: "#0f172a", fontSize: "14px", fontWeight: "500" }}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <p className="section-label">Kişisel Bilgiler</p>
            <table className="detail-table" style={{ width: "100%", borderCollapse: "collapse", marginBottom: "22px", border: "1px solid #e2e8f0", borderRadius: "10px", overflow: "hidden" }}>
              <tbody>
                {[[t('crew.nationality'), selectedCrew.birth_place || "—"], [t('crew.nationality'), selectedCrew.hometown || "—"], [t('crew.nationality'), selectedCrew.marital_status || "—"], [t('crew.experience'), selectedCrew.experience_years != null ? selectedCrew.experience_years : "—"], [t('crew.seaService'), selectedCrew.sea_service_months != null ? selectedCrew.sea_service_months : "—"], [t('crew.language'), selectedCrew.languages || "—"]].map(([k, v]) => (
                  <tr key={k} style={{ borderBottom: "1px solid #eef2f7" }}>
                    <td style={{ padding: "10px 14px", width: "220px", fontWeight: "600", color: "#475569", background: "#f8fafc", fontSize: "13px", borderRight: "1px solid #eef2f7" }}>{k}</td>
                    <td style={{ padding: "10px 14px", color: "#0f172a", fontSize: "14px", fontWeight: "500" }}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <p className="section-label">Ek Bilgiler</p>
            <table className="detail-table" style={{ width: "100%", borderCollapse: "collapse", marginBottom: "22px", border: "1px solid #e2e8f0", borderRadius: "10px", overflow: "hidden" }}>
              <tbody>
                {[[t('profile.maritimeInfo'), selectedCrew.education_summary || "—"], [t('common.notes'), selectedCrew.notes || "—"]].map(([k, v]) => (
                  <tr key={k} style={{ borderBottom: "1px solid #eef2f7" }}>
                    <td style={{ padding: "10px 14px", width: "220px", fontWeight: "600", color: "#475569", background: "#f8fafc", fontSize: "13px", borderRight: "1px solid #eef2f7" }}>{k}</td>
                    <td style={{ padding: "10px 14px", color: "#0f172a", fontSize: "14px", fontWeight: "500" }}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            <p className="section-label" style={{ marginTop: "30px" }}>{t('vesselStaff.title')} ({assignments.filter(a => a.crew_member_id === selectedCrew.id).length})</p>
            {(() => {
              const crewAssigns = assignments.filter(a => a.crew_member_id === selectedCrew.id);
              if (crewAssigns.length === 0) {
                return (
                  <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "12px", color: "#64748b", border: "2px dashed #cbd5e1", fontSize: "14px" }}>
                    {t('vesselStaff.noAssignments')}
                  </div>
                );
              }
              return (
                <div className="table-wrapper">
                  <div className="entity-list" style={{ minWidth: "700px" }}>
                    {crewAssigns.map((assignment) => (
                      <div 
                        className="entity-row" 
                        key={assignment.id} 
                        onClick={() => openShipDetail(assignment.ship_id)}
                        title={t('vessels.detail')}
                        style={{ cursor: "pointer", display: "flex", alignItems: "center", background: "#fff", borderBottom: "1px solid #e2e8f0" }}
                      >
                        <strong style={{ color: "#0f172a" }}>{shipById[assignment.ship_id]?.name || t('vessels.name') + ' #' + assignment.ship_id}</strong>
                        <span>{assignment.position || "—"} · {assignment.status} · {assignment.start_date || "—"} → {assignment.end_date || "devam"}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
            
            <p className="section-label" style={{ marginTop: "30px" }}>{t('contracts.title')} ({contracts.filter(c => c.crew_member_id === selectedCrew.id).length})</p>
            {(() => {
              const crewContracts = contracts.filter(c => c.crew_member_id === selectedCrew.id);
              if (crewContracts.length === 0) {
                return (
                  <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "12px", color: "#64748b", border: "2px dashed #cbd5e1", fontSize: "14px" }}>
                    {t('contracts.noContracts')}
                  </div>
                );
              }
              return (
                <div className="table-wrapper">
                  <div className="entity-list" style={{ minWidth: "700px" }}>
                    {crewContracts.map((contract) => {
                      const today = new Date();
                      const end = contract.end_date ? new Date(contract.end_date) : null;
                      const daysLeft = end ? Math.ceil((end - today) / 86400000) : null;
                      return (
                        <div className="entity-row static-row" key={contract.id}>
                          <strong>{contract.contract_number}</strong>
                          <span>
                            {shipById[contract.ship_id]?.name || t('vessels.name') + ' #' + contract.ship_id} · {contract.status}
                            {daysLeft !== null && daysLeft >= 0 && ` · ${daysLeft} gün kaldı`}
                            {daysLeft !== null && daysLeft < 0 && " · süresi doldu"}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}
            
            <p className="section-label" style={{ marginTop: "30px" }}>{t('crew.documentCount', { count: crewDetailDocuments.length })}</p>
            
            {crewDetailDocumentsLoading && <p>{t('common.loading')}</p>}
            
            {!crewDetailDocumentsLoading && crewDetailDocuments.length === 0 && (
              <div style={{ background: "#f8fafc", padding: "30px", borderRadius: "12px", textAlign: "center", color: "#64748b", border: "2px dashed #cbd5e1" }}>
                <Folder size={48} style={{ margin: "0 auto 16px auto", opacity: 0.6 }} />
                <p style={{ margin: 0, fontSize: "16px", fontWeight: "500" }}>{t('documents.noDocuments')}</p>
              </div>
            )}
            
            {!crewDetailDocumentsLoading && crewDetailDocuments.length > 0 && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "20px" }}>
                {crewDetailDocuments.map((doc) => {
                  const typeLabels = { passport: t('documentTypes.passport'), seaman_book: t('documentTypes.seaman_book'), stcw: t('documentTypes.stcw'), goc: 'GOC', medical: t('documentTypes.medical'), contract: t('documentTypes.contract'), cv: t('documentTypes.cv'), other: t('documentTypes.other') };
                  let cardPulse = doc.expiry_status === "expired" || doc.expiry_status === "urgent";
                  
                  return (
                    <div 
                      key={doc.id} 
                      className={`doc-card ${cardPulse ? "pulse-soft" : ""}`}
                      onClick={() => window.open(`${API_URL}/api/documents/${doc.id}/file`, '_blank')}
                      style={{ 
                        border: "1px solid #e2e8f0", 
                        borderRadius: "16px", 
                        padding: "20px", 
                        cursor: "pointer", 
                        backgroundColor: "#fff", 
                        transition: "all 0.2s ease", 
                        boxShadow: "0 4px 6px rgba(0,0,0,0.05)", 
                        display: "flex", 
                        flexDirection: "column"
                      }}
                      onMouseEnter={(e) => { 
                        e.currentTarget.style.borderColor = "#ea580c"; 
                        e.currentTarget.style.transform = "translateY(-4px)"; 
                      }}
                      onMouseLeave={(e) => { 
                        e.currentTarget.style.borderColor = "#e2e8f0"; 
                        e.currentTarget.style.transform = "none"; 
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                        <span className={`badge badge-type-${doc.document_type}`}>
                          {typeLabels[doc.document_type] || doc.document_type}
                        </span>
                        {doc.expiry_status && (
                          <span className={`badge badge-${doc.expiry_status.replace(/_/g, "-")}`}>
                            {doc.expiry_status}
                          </span>
                        )}
                      </div>
                      
                      <h4 style={{ fontSize: "15px", margin: "0 0 16px 0", color: "#0f172a", wordBreak: "break-all", flex: 1, lineHeight: "1.4" }}>
                        {doc.original_filename}
                      </h4>
                      
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid #f1f5f9", paddingTop: "16px", marginTop: "auto" }}>
                        {doc.expiry_date ? (
                          <span style={{ fontSize: "13px", color: "#475569", fontWeight: "600" }}>Bitiş: {doc.expiry_date}</span>
                        ) : (
                          <span style={{ fontSize: "13px", color: "#94a3b8", fontStyle: "italic" }}>{t('documents.noDate')}</span>
                        )}
                        <span style={{ fontSize: "13px", color: "#ea580c", fontWeight: "700", display: "flex", alignItems: "center", gap: "6px", textTransform: "uppercase" }}>
                          <FileText size={16} /> Görüntüle
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        ) : (
          <p>{t('crew.noPersonnel')}</p>
        )}
      </section>
    );
  }

  function renderDocumentsList() {
    // `documents` state holds the server-paginated page; `allDocuments` is only
    // used for the crew document matrix and the pending-match modal.
    const filteredDocs = documents;
    const totalPages = Math.max(1, Math.ceil(docTotal / DOC_PAGE_SIZE));

    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('documents.title')}</h2>
            <p>{t('documents.subtitle')}</p>
          </div>
          <div style={{ display: "flex", gap: "10px" }}>
            {canWrite && (
              <button className="secondary-button" onClick={openReviewQueue}>
                {t('documents.reviewRequired')} {reviewQueue.length > 0 && `(${reviewQueue.length})`}
              </button>
            )}
          </div>
        </div>

        {batchProgress && batchProgress.status !== "done" && (
          <div className="panel" style={{ marginBottom: "16px", padding: "16px", background: "#fffbeb", border: "1px solid #fcd34d" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong style={{ color: "#92400e" }}>
                {batchProgress.status === "starting"
                  ? t('common.processing')
                  : `İşleniyor: ${batchProgress.processed || 0} / ${batchProgress.total || 0}`}
              </strong>
              {batchProgress.batch_id && <span style={{ color: "#b45309", fontSize: "12px" }}>Batch: {batchProgress.batch_id}</span>}
            </div>
            {batchProgress.total > 0 && (
              <div className="upload-progress-bar" style={{ marginTop: "10px", height: "8px" }}>
                <div className="upload-progress-fill" style={{ width: `${Math.round(((batchProgress.processed || 0) / batchProgress.total) * 100)}%` }} />
              </div>
            )}
          </div>
        )}

        {reviewOpen && (
          <div className="panel" style={{ marginBottom: "16px", padding: "20px", background: "#fffbeb", border: "1px solid #fcd34d" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h3 style={{ color: "#92400e", margin: 0 }}>{t('documents.reviewRequired')}</h3>
              <button className="icon-button" onClick={() => setReviewOpen(false)}>
                <X size={18} />
              </button>
            </div>
            {reviewLoading ? (
              <p>İnceleniyor...</p>
            ) : reviewQueue.length === 0 ? (
              <p style={{ color: "#475569" }}>İnceleme bekleyen belge yok.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "420px", overflowY: "auto" }}>
                {reviewQueue.map((doc) => (
                  <div key={doc.id} style={{ border: "1px solid #e2e8f0", borderRadius: "8px", padding: "12px", background: "#fff" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                      <div>
                        <strong style={{ color: "#0f172a" }}>{doc.original_filename}</strong>
                        <div style={{ color: "#64748b", fontSize: "13px" }}>
                          {t('common.type')}: {doc.document_type} · {t('common.status')}: <span className={`badge badge-${doc.match_status}"`}>{doc.match_status}</span>
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                        {doc.match_status === "pending_approval" && (
                          <>
                            <button className="primary-button" style={{ padding: "6px 12px", fontSize: "13px", background: "#15803d", border: "none" }} onClick={() => approvePendingDoc(doc.id)}>
                              <CheckCircle size={14} /> Onayla
                            </button>
                            <button className="secondary-button" style={{ padding: "6px 12px", fontSize: "13px" }} onClick={() => rejectPendingDoc(doc.id)}>
                              <XCircle size={14} /> Reddet
                            </button>
                          </>
                        )}
                        <button
                          className="secondary-button"
                          onClick={() => loadCandidates(doc.id)}
                          disabled={candidatesLoading}
                        >
                          {t('common.view')}
                        </button>
                      </div>
                    </div>
                    {candidateData && candidateData.document_id === doc.id && (
                      <div style={{ marginTop: "10px", borderTop: "1px dashed #cbd5e1", paddingTop: "10px" }}>
                        {candidateData.decision && (
                          <p style={{ margin: "0 0 8px 0", color: "#475569", fontSize: "13px" }}>
                            Motor kararı: <strong>{candidateData.decision}</strong> — {candidateData.reason}
                          </p>
                        )}
                        {candidateData.candidates && candidateData.candidates.length > 0 ? (
                          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                            {candidateData.candidates.map((c) => (
                              <div key={c.crew_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#f8fafc", padding: "8px 12px", borderRadius: "6px" }}>
                                <div>
                                  <strong>{c.first_name} {c.last_name}</strong>
                                  <span style={{ marginLeft: "10px", color: "#2563eb", fontWeight: "bold" }}>{c.score}%</span>
                                  <span style={{ marginLeft: "8px", color: "#64748b", fontSize: "12px" }}>{c.signals.join(", ")}</span>
                                </div>
                                {canWrite && (
                                  <button
                                    className="primary-button"
                                    style={{ padding: "6px 12px", fontSize: "13px" }}
                                    onClick={() => confirmMatchFromReview(doc.id, c.crew_id)}
                                  >
                                    {t('common.confirm')}
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p style={{ color: "#64748b" }}>{t('crew.noResults')}</p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        <div className="detail-grid" style={{ marginBottom: "24px", background: "#f8fafc", padding: "20px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <span className="section-label">{t('documents.documentType')}</span>
            <select className="form-input" name="document_type" value={docFilters.document_type} onChange={handleDocFilterChange}>
              <option value="">Tümü</option>
              <option value="passport">Pasaport</option>
              <option value="seaman_book">Seaman Book</option>
              <option value="stcw">STCW</option>
              <option value="goc">GOC</option>
              <option value="medical">{t('documentTypes.medical')}</option>
              <option value="contract">Sözleşme</option>
              <option value="cv">CV</option>
              <option value="other">Diğer</option>
            </select>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <span className="section-label">{t('documents.matchStatusFilter')}</span>
            <select className="form-input" name="match_status" value={docFilters.match_status} onChange={handleDocFilterChange}>
              <option value="">Tümü</option>
              <option value="matched">{t('documents.matched')}</option>
              <option value="review_required">İnceleme Gerekli</option>
              <option value="conflict">Çelişki</option>
              <option value="pending_approval">Onay Bekliyor</option>
              <option value="unmatched">Eşleşmedi</option>
            </select>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <span className="section-label">{t('documents.expiryFilter')}</span>
            <select className="form-input" name="expiry_status" value={docFilters.expiry_status} onChange={handleDocFilterChange}>
              <option value="">Tümü</option>
              <option value="valid">{t('documents.valid')}</option>
              <option value="approaching">{t('documents.approaching')}</option>
              <option value="urgent">{t('documents.urgent')}</option>
              <option value="expired">{t('documents.expired')}</option>
              <option value="no_date">{t('documents.noDate')}</option>
            </select>
          </div>
          <div style={{ display: "flex", gap: "12px", alignItems: "flex-end" }}>
            <button 
              className="primary-button" 
              onClick={applyDocFilters}
              style={{ flex: 1 }}
            >
              <Search size={16} /> FİLTRELE
            </button>
            <button 
              className="secondary-button" 
              onClick={clearDocFilters} 
            >
              {t('common.clear')}
            </button>
          </div>
        </div>

        {lastBatchSummary && (
          <div className="upload-summary">
            <div className="upload-stat matched">
              <strong>{lastBatchSummary.matched}</strong><span>{t('documents.matched')}</span>
            </div>
            <div className="upload-stat pending">
              <strong>{lastBatchSummary.pending}</strong><span>{t('documents.pending')}</span>
            </div>
            <div className="upload-stat duplicate">
              <strong>{lastBatchSummary.duplicate}</strong><span>{t('documents.duplicate')}</span>
            </div>
            <div className="upload-stat error">
              <strong>{lastBatchSummary.error}</strong><span>{t('common.error')}</span>
            </div>
          </div>
        )}
        
        {canWrite ? (
          <div
            className={`upload-zone ${dragActive ? "drag-over" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={42} color="#ea580c" style={{marginBottom: "10px"}} />
            <h3 style={{color: "#0f172a"}}>{t('documents.dragDrop')}</h3>
            <p>veya tıklayarak seçin — PDF, TXT</p>
            <input 
              ref={fileInputRef} 
              type="file" 
              multiple 
              accept=".pdf,.txt" 
              style={{ display: "none" }} 
              onChange={handleFileInputChange} 
            />
          </div>
        ) : (
          <div className="upload-zone" style={{ opacity: 0.6, cursor: "not-allowed" }}>
            <Upload size={42} color="#94a3b8" style={{marginBottom: "10px"}} />
            <h3 style={{color: "#475569"}}>{t('errors.unauthorized')}</h3>
            <p>{t('errors.unauthorized')}</p>
          </div>
        )}
        
        {stagedFiles.length > 0 && (
          <div className="file-list" style={{marginTop: "20px"}}>
            {stagedFiles.map((file, index) => {
              const key = fileKey(file);
              const status = uploadStatus[key] || "pending";
              return (
                <div className="file-item" key={`${key}_${index}`}>
                  <span className="file-item-name">{file.name}</span>
                  <span className="file-item-status">{status}</span>
                  <button className="icon-button" type="button" onClick={() => removeStagedFile(index)}>
                    <X size={16} />
                  </button>
                </div>
              );
            })}
            <div style={{ display: "flex", gap: "12px", marginTop: "16px" }}>
              <button className="primary-button" type="button" onClick={uploadStagedFiles} disabled={isUploading}>
                {isUploading ? t('common.loading') : t('common.upload') + ` (${stagedFiles.length})`}
              </button>
              <button className="danger-button" type="button" onClick={() => clearStagedFiles()} disabled={isUploading}>
                {t('common.cancel')}
              </button>
            </div>
          </div>
        )}

        {documentsLoading ? (
          <p style={{marginTop: "20px"}}>{t('common.loading')}</p>
        ) : (
          <div className="table-wrapper">
            <table className="data-table" style={{marginTop: "30px", minWidth: "900px", width: "100%"}}>
              <thead>
                <tr>
                  <th style={{ width: "40px", textAlign: "center" }}>#</th>
                  <th>{t('common.name')}</th>
                  <th>{t('documents.documentType')}</th>
                  <th>{t('documents.matchStatusFilter')}</th>
                  <th>{t('documents.expiryFilter')}</th>
                  <th>{t('crew.title')}</th>
                  <th style={{ textAlign: "center", width: "60px" }}>İşlem</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.map((doc, idx) => {
                  const matchedCrew = doc.crew_member_id ? crewById[doc.crew_member_id] : null;
                  return (
                    <tr key={doc.id}>
                      <td style={{ textAlign: "center", fontWeight: "bold", color: "#64748b" }}>
                        {String(idx + 1).padStart(2, '0')}
                      </td>
                      <td>
                        <a 
                          href={`${API_URL}/api/documents/${doc.id}/file`} 
                          target="_blank" 
                          rel="noreferrer" 
                          style={{ color: "#2563eb", textDecoration: "none", fontWeight: "600" }}
                        >
                          {doc.original_filename}
                        </a>
                      </td>
                      <td>
                        <span className={`badge badge-type-${doc.document_type}`}>{doc.document_type}</span>
                      </td>
                      <td>
                        <span className={`badge badge-${doc.match_status}`}>{doc.match_status}</span>
                      </td>
                      <td>
                        {doc.expiry_status ? <span className={`badge badge-${doc.expiry_status.replace(/_/g, "-")}`}>{doc.expiry_status}</span> : "—"}
                      </td>
                      <td style={{ fontWeight: "600", color: "#0f172a" }}>
                        {matchedCrew ? `${matchedCrew.first_name} ${matchedCrew.last_name}` : "—"}
                      </td>
                      <td style={{ textAlign: "center" }}>
                        {canWrite && (
                          <button className="icon-button" onClick={() => deleteDocument(doc.id)} title={t('common.delete')}>
                            <Trash2 size={18} color="#ef4444" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {filteredDocs.length === 0 && (
                  <tr>
                    <td colSpan="7" style={{textAlign:"center", padding:"20px"}}>
                      {t('common.notFound')}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {docTotal > DOC_PAGE_SIZE && (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "16px", flexWrap: "wrap", gap: "10px" }}>
            <span style={{ color: "#64748b", fontSize: "14px", fontWeight: "600" }}>
              {docTotal} belge · Sayfa {docPage + 1} / {totalPages}
            </span>
            <div style={{ display: "flex", gap: "10px" }}>
              <button
                className="secondary-button"
                disabled={docPage === 0}
                onClick={() => loadDocuments(docFilters, docPage - 1)}
              >
                ← Önceki
              </button>
              <button
                className="secondary-button"
                disabled={(docPage + 1) * DOC_PAGE_SIZE >= docTotal}
                onClick={() => loadDocuments(docFilters, docPage + 1)}
              >
                Sonraki →
              </button>
            </div>
          </div>
        )}
      </section>
    );
  }

  function renderShips() {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('vessels.title')}</h2>
            <p>{t('vessels.title')}</p>
          </div>
          {canWrite && (
            <button 
              className="primary-button" 
              onClick={() => { setFormError(""); setIsShipFormOpen(true); }}
            >
              <Ship size={18} /> {t('vessels.addNew')}
            </button>
          )}
        </div>
        
        {isShipFormOpen && (
          <form className="crew-form" onSubmit={handleShipSubmit} style={{marginBottom: "20px"}}>
            <label>{t('vessels.name')}
              <input name="name" value={shipForm.name} onChange={handleShipFormChange} required />
            </label>
            <label>IMO Numarası
              <input name="imo_number" value={shipForm.imo_number} onChange={handleShipFormChange} />
            </label>
            <label>{t('vessels.type')}
              <input name="ship_type" value={shipForm.ship_type} onChange={handleShipFormChange} placeholder="Örn: Bulk Carrier" />
            </label>
            <label>{t('vessels.flag')}
              <input name="flag" value={shipForm.flag} onChange={handleShipFormChange} placeholder="Örn: Panama" />
            </label>
            <div className="form-actions">
              <button className="secondary-button" type="button" onClick={() => setIsShipFormOpen(false)}>{t('common.cancel')}</button>
              <button className="primary-button" type="submit" disabled={isSubmitting}>{isSubmitting ? t('common.saving') : t('common.save')}</button>
            </div>
          </form>
        )}
        
        <div className="table-wrapper">
          <div className="entity-list" style={{ minWidth: "500px" }}>
            {ships.map((ship, idx) => (
              <div 
                className="entity-row" 
                key={ship.id} 
                onClick={() => openShipDetail(ship.id)} 
                style={{cursor: "pointer", display: "flex"}}
              >
                <strong>{String(idx + 1).padStart(2, '0')}. {ship.name}</strong>
                <span>{ship.imo_number || "IMO belirtilmemiş"} · {ship.status}</span>
              </div>
            ))}
            {ships.length === 0 && (
              <div className="empty">
                <Ship size={42} />
                <h3>{t('vessels.noVessels')}</h3>
              </div>
            )}
          </div>
        </div>
      </section>
    );
  }

  function renderAssignments() {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('vesselStaff.title')}</h2>
            <p>{t('vesselStaff.title')}</p>
          </div>
          <button 
            className="primary-button" 
            onClick={() => setAssignmentModal({ isOpen: true, crew_member_id: "", ship_id: "", position: "", start_date: "", end_date: "" })}
          >
            <ClipboardList size={18} /> Manuel Atama Yap
          </button>
        </div>
        
        <div className="table-wrapper">
          <div className="entity-list" style={{ minWidth: "800px" }}>
            {assignments.map((assignment, idx) => (
              <div 
                className="entity-row" 
                key={assignment.id} 
                onClick={() => openCrewDetail(assignment.crew_member_id)}
                title={t('crew.detail')}
                style={{ cursor: "pointer", display: "flex", alignItems: "center", background: "#fff", borderBottom: "1px solid #e2e8f0" }}
              >
                <strong style={{ color: "#0f172a" }}>
                  {String(idx + 1).padStart(2, '0')}. {crewById[assignment.crew_member_id]?.first_name} {crewById[assignment.crew_member_id]?.last_name}
                </strong>
                <span>{shipById[assignment.ship_id]?.name} · {assignment.position} · {assignment.status}</span>
              </div>
            ))}
            {assignments.length === 0 && (
              <div className="empty">
                <ClipboardList size={42} />
                <h3>{t('vesselStaff.noAssignments')}</h3>
              </div>
            )}
          </div>
        </div>
      </section>
    );
  }

  function renderContracts() {
    const now = new Date();
    let displayedContracts = contracts;
    if (contractsFilter === "ending_7" || contractsFilter === "ending_30") {
      const days = contractsFilter === "ending_7" ? 7 : 30;
      displayedContracts = contracts.filter((c) => {
        if (!c.end_date || c.status !== "active") return false;
        const diff = Math.ceil((new Date(c.end_date) - now) / 86400000);
        return diff >= 0 && diff <= days;
      });
    }
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('contracts.title')}</h2>
            <p>{t('contracts.title')}</p>
          </div>
          {canWrite && (
            <button 
              className="primary-button" 
              onClick={() => { setFormError(""); setEditingContractId(null); setContractForm(emptyContractForm); setIsContractFormOpen(true); }}
            >
              <FileText size={18} /> {t('contracts.addNew')}
            </button>
          )}
        </div>
        
        {contractsFilter !== "" && (
          <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "12px 16px", marginBottom: "16px", background: "#fffbeb", border: "1px solid #fcd34d", borderRadius: "10px" }}>
            <AlertCircle size={18} color="#b45309" />
            <span style={{ color: "#92400e", fontWeight: "600", fontSize: "14px" }}>
              {contractsFilter === "ending_7" ? "7 gün içinde bitecek aktif kontratlar" : "30 gün içinde bitecek aktif kontratlar"} ({displayedContracts.length} kayıt)
            </span>
            <button className="secondary-button" style={{ marginLeft: "auto", padding: "6px 12px", fontSize: "13px" }} onClick={() => setContractsFilter("")}>
              {t('common.clear')}
            </button>
          </div>
        )}
        
        {isContractFormOpen && (
          <form className="crew-form" onSubmit={handleContractSubmit} style={{marginBottom: "20px"}}>
            <div style={{display: "flex", flexDirection: "column", gap: "8px", flex: 1}}>
               <label style={{fontSize: "12px", fontWeight: "bold", color: "#64748b"}}>{t('vesselStaff.person')}</label>
               <select name="crew_member_id" required className="form-input" value={contractForm.crew_member_id} onChange={handleContractFormChange} style={{padding: "10px"}}>
                 <option value="">-- {t('crew.title')} --</option>
                 {crew.map(c => <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>)}
               </select>
            </div>
            <div style={{display: "flex", flexDirection: "column", gap: "8px", flex: 1}}>
               <label style={{fontSize: "12px", fontWeight: "bold", color: "#64748b"}}>{t('vesselStaff.vessel')}</label>
               <select name="ship_id" required className="form-input" value={contractForm.ship_id} onChange={handleContractFormChange} style={{padding: "10px"}}>
                 <option value="">-- {t('vessels.title')} --</option>
                 {ships.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
               </select>
            </div>
            <label>{t('contracts.number')}
              <input name="contract_number" value={contractForm.contract_number} onChange={handleContractFormChange} required />
            </label>
            <label>{t('contracts.type')}
              <input name="contract_type" value={contractForm.contract_type} onChange={handleContractFormChange} placeholder="Örn: Employment" />
            </label>
            <label>{t('contracts.startDate')}
              <input type="date" name="start_date" value={contractForm.start_date} onChange={handleContractFormChange} />
            </label>
            <label>{t('contracts.endDate')}
              <input type="date" name="end_date" value={contractForm.end_date} onChange={handleContractFormChange} />
            </label>
            
            <div className="form-actions">
              <button className="secondary-button" type="button" onClick={() => { setIsContractFormOpen(false); setEditingContractId(null); setContractForm(emptyContractForm); }}>{t('common.cancel')}</button>
              <button className="primary-button" type="submit" disabled={isSubmitting}>{editingContractId ? t('common.edit') : t('common.save')}</button>
            </div>
          </form>
        )}
        
        <div className="table-wrapper">
          <div className="entity-list" style={{ minWidth: "800px" }}>
            {displayedContracts.map((contract, idx) => {
              const crewName = `${crewById[contract.crew_member_id]?.first_name || ""} ${crewById[contract.crew_member_id]?.last_name || ""}`.trim() || "—";
              const shipName = ships.find((s) => s.id === contract.ship_id)?.name || "—";
              return (
                <div className="entity-row" key={contract.id} onClick={() => setSelectedContractId(contract.id)}
                  style={{ cursor: "pointer", background: selectedContractId === contract.id ? "#eff6ff" : "#fff", borderLeft: selectedContractId === contract.id ? "4px solid #0284c7" : "4px solid transparent" }}>
                  <strong>{String(idx + 1).padStart(2, '0')}. {contract.contract_number}</strong>
                  <span style={{ flex: 1, color: "#475569" }}>{crewName} · {shipName} · {contract.status}</span>
                  {selectedContractId === contract.id && (
                    <span style={{ display: "flex", gap: "6px" }}>
                      <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px" }} onClick={(e) => {
                        e.stopPropagation();
                        setContractForm({
                          crew_member_id: String(contract.crew_member_id || ""),
                          ship_id: String(contract.ship_id || ""),
                          contract_number: contract.contract_number || "",
                          contract_type: contract.contract_type || "",
                          start_date: contract.start_date || "",
                          end_date: contract.end_date || "",
                        });
                        setEditingContractId(contract.id);
                        setIsContractFormOpen(true);
                      }}>{t('common.edit')}</button>
                      <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px", color: "#b91c1c" }} onClick={(e) => { e.stopPropagation(); deleteContract(contract.id); }}>{t('common.delete')}</button>
                    </span>
                  )}
                </div>
              );
            })}
            {contracts.length === 0 && (
              <div className="empty">
                <FileText size={42} />
                <h3>{t('contracts.noContracts')}</h3>
              </div>
            )}
          </div>
        </div>

        {selectedContractId && (() => {
          const contract = contracts.find((c) => c.id === selectedContractId);
          if (!contract) return null;
          const crewName = `${crewById[contract.crew_member_id]?.first_name || ""} ${crewById[contract.crew_member_id]?.last_name || ""}`.trim() || "—";
          const shipName = ships.find((s) => s.id === contract.ship_id)?.name || "—";
          return (
            <div style={{ marginTop: "18px", padding: "20px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
                <h3 style={{ margin: 0, color: "#0f172a" }}>{t('contracts.detail')} — {contract.contract_number}</h3>
                <button className="secondary-button" style={{ padding: "6px 12px", fontSize: "13px" }} onClick={() => setSelectedContractId(null)}>Kapat</button>
              </div>
              <div className="detail-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px" }}>
                <div><span className="section-label">{t('crew.title')}</span><p style={{ margin: "4px 0 0 0", fontWeight: "600", color: "#0f172a", cursor: "pointer" }} onClick={() => contract.crew_member_id && openCrewDetail(contract.crew_member_id)}>{crewName} →</p></div>
                <div><span className="section-label">{t('vessels.title')}</span><p style={{ margin: "4px 0 0 0", fontWeight: "600", color: "#0f172a" }}>{shipName}</p></div>
                <div><span className="section-label">{t('contracts.type')}</span><p style={{ margin: "4px 0 0 0", color: "#475569" }}>{contract.contract_type || "—"}</p></div>
                <div><span className="section-label">Başlangıç</span><p style={{ margin: "4px 0 0 0", color: "#475569" }}>{contract.start_date || "—"}</p></div>
                <div><span className="section-label">Bitiş</span><p style={{ margin: "4px 0 0 0", color: "#475569" }}>{contract.end_date || "—"}</p></div>
                <div><span className="section-label">{t('common.status')}</span><p style={{ margin: "4px 0 0 0" }}><span className={`badge ${contract.status === "active" ? "badge-success" : "badge-neutral"}"`}>{contract.status}</span></p></div>
              </div>
            </div>
          );
        })()}
      </section>
    );
  }

  function renderShipDetail() {
    const shipAssignments = assignments.filter((assignment) => assignment.ship_id === selectedShipId); 
    
    return (
      <section className="panel detail-panel">
        <button className="back-button" onClick={() => setActivePage("ships")}>{t('vessels.title') + ' ' + t('common.backToList')}</button>
        {selectedShip ? (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap:"10px" }}>
              <h2 style={{ margin: 0 }}>{selectedShip.name}</h2>
              {canWrite && (
                <button 
                  className="primary-button" 
                  onClick={() => setAssignmentModal({ isOpen: true, crew_member_id: "", ship_id: selectedShip.id, position: "", start_date: "", end_date: "" })}
                >
                  <UserPlus size={18} /> {t('crew.addNew')}
                </button>
              )}
            </div>
            
            <div className="detail-grid">
              <span>IMO</span><strong>{selectedShip.imo_number || "—"}</strong>
              <span>{t('vessels.flag')}</span><strong>{selectedShip.flag || "—"}</strong>
              <span>{t('vessels.type')}</span><strong>{selectedShip.ship_type || "—"}</strong>
              <span>Şirket</span><strong>{selectedShip.company || "—"}</strong>
              <span>{t('common.status')}</span><strong>{selectedShip.status}</strong>
            </div>
            
            <h3 style={{ marginTop: "30px", marginBottom: "15px", color: "#0f172a" }}>{t('vesselStaff.title')}</h3>
            
            <div className="table-wrapper">
              <div className="entity-list" style={{ minWidth: "800px" }}>
                {shipAssignments.map((assignment, idx) => (
                  <div 
                    className="entity-row" 
                    key={assignment.id} 
                    onClick={() => openCrewDetail(assignment.crew_member_id)}
                    title={t('crew.detail')}
                    style={{ cursor: "pointer", display: "flex", alignItems: "center", background: "#fff", borderBottom: "1px solid #e2e8f0" }}
                  >
                    <strong style={{ color: "#0f172a" }}>{String(idx + 1).padStart(2, '0')}. {crewById[assignment.crew_member_id]?.first_name} {crewById[assignment.crew_member_id]?.last_name}</strong>
                    <span>{assignment.position} · {assignment.status}</span>
                  </div>
                ))}
                {shipAssignments.length === 0 && <p>{t('vesselStaff.noAssignments')}</p>}
              </div>
            </div>

            <h3 style={{ marginTop: "30px", marginBottom: "8px", color: "#0f172a" }}>Kadro Planı</h3>
            <p style={{ margin: "0 0 12px 0", color: "#64748b", fontSize: "13px" }}>{t('vesselStaff.title')}</p>
            {staffingLoading ? (
              <p style={{ color: "#64748b" }}>Kadro yükleniyor...</p>
            ) : (
              <div className="table-wrapper">
                <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ textAlign: "left", color: "#64748b" }}>
                      <th>{t('crew.position')}</th><th>{t('common.count')}</th><th>{t('common.active')}</th><th>{t('common.pending')}</th><th>{t('common.view')}</th>{canWrite && <th></th>}
                    </tr>
                  </thead>
                  <tbody>
                    {shipStaffing.map((p) => (
                      <tr key={p.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                        <td style={{ padding: "10px 8px", fontWeight: "600", color: "#0f172a" }}>{p.position}</td>
                        <td style={{ padding: "10px 8px", textAlign: "center" }}>{p.required}</td>
                        <td style={{ padding: "10px 8px", textAlign: "center" }}>{p.filled}</td>
                        <td style={{ padding: "10px 8px", textAlign: "center" }}>{p.open > 0 ? <strong style={{ color: "#b91c1c" }}>🔴 {p.open}</strong> : <span style={{ color: "#15803d" }}>✅ Tam</span>}</td>
                        <td style={{ padding: "10px 8px" }}>
                          {p.open > 0 && (
                            <button className="secondary-button" style={{ padding: "5px 10px", fontSize: "12px" }} onClick={() => showCandidates(p.position)}>
                              {t('crew.search')}
                            </button>
                          )}
                        </td>
                        {canWrite && (
                          <td style={{ padding: "10px 8px", textAlign: "right" }}>
                            <button className="icon-button danger" title={t('common.delete')} onClick={() => handleDeletePosition(p.id)} style={{ padding: "6px" }}>
                              <Trash2 size={15} />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {shipStaffing.length === 0 && (
                      <tr><td colSpan={6} style={{ padding: "20px", textAlign: "center", color: "#64748b" }}>Henüz kadro planı yok. Aşağıdan pozisyon ekleyin.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
            {canWrite && (
              <form onSubmit={handleAddPosition} style={{ display: "flex", gap: "10px", marginTop: "14px", flexWrap: "wrap", alignItems: "flex-end" }}>
                <div style={{ flex: "1", minWidth: "200px" }}>
                  <label className="section-label">{t('crew.position')}</label>
                  <input className="form-input" style={{ width: "100%", padding: "9px", marginTop: "4px" }} placeholder="Örn: Elektrik Zabiti" value={positionForm.position}
                    onChange={(e) => setPositionForm({ ...positionForm, position: e.target.value })} required />
                </div>
                <div style={{ width: "110px" }}>
                  <label className="section-label">İhtiyaç</label>
                  <input className="form-input" type="number" min="1" max="100" style={{ width: "100%", padding: "9px", marginTop: "4px" }} value={positionForm.required_count}
                    onChange={(e) => setPositionForm({ ...positionForm, required_count: Number(e.target.value) })} />
                </div>
                <button className="primary-button" type="submit" style={{ padding: "10px 16px" }}><UserPlus size={16} /> {t('common.add')}</button>
              </form>
            )}
            {candidatesFor && (
              <div style={{ marginTop: "20px", padding: "16px", border: "1px solid #e2e8f0", borderRadius: "12px", background: "#f8fafc" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <strong style={{ color: "#0f172a" }}>“{candidatesFor.position}” için uygun adaylar</strong>
                  <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px" }} onClick={() => setCandidatesFor(null)}>Kapat</button>
                </div>
                {candidatesFor.results.length === 0 && <p style={{ color: "#64748b" }}>{t('crew.noResults')}</p>}
                {candidatesFor.results.map((r) => (
                  <div key={r.crew_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderTop: "1px solid #e2e8f0" }}>
                    <span style={{ color: "#0f172a", fontWeight: "600" }}>{r.first_name} {r.last_name} <span style={{ color: "#64748b", fontWeight: "400", fontSize: "13px" }}>· {r.position} · {r.experience_years || 0} yıl</span></span>
                    <strong style={{ color: r.score >= 90 ? "#15803d" : "#b45309" }}>%{r.score}</strong>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <p>{t('vessels.noVessels')}</p>
        )}
      </section>
    );
  }

  async function loadUsers() {
    if (!isAdmin) return;
    try {
      const response = await axios.get(`${API_URL}/api/auth/users`);
      setUsers(response.data);
    } catch (e) { console.error("Kullanıcılar yüklenemedi:", e); }
  }

  async function loadNotifSettings() {
    if (!isAdmin) return;
    try {
      const response = await axios.get(`${API_URL}/api/settings`);
      setNotifSettings(response.data.values || {});
    } catch (e) { console.error("Bildirim ayarları yüklenemedi:", e); }
  }

  async function saveNotifSettings(e) {
    e.preventDefault();
    setNotifSettingsMsg(null);
    try {
      await axios.put(`${API_URL}/api/settings`, { values: notifSettings });
      setNotifSettingsMsg({ type: "success", text: t('settings.settingsSaved') });
      await loadNotifSettings(); // gizli alanları tekrar maskele
    } catch (err) {
      setNotifSettingsMsg({ type: "error", text: err.response?.data?.detail || t('settings.settingsError') });
    }
  }

  function openEmailModal(crewIds) {
    setEmailMsg(null);
    setEmailModal({ isOpen: true, crewIds, subject: "", body: "" });
  }

  async function sendEmail(e) {
    e.preventDefault();
    setEmailMsg(null);
    if (!emailModal.subject.trim()) {
      setEmailMsg({ type: "error", text: t('errors.validationFailed') });
      return;
    }
    try {
      const payload = { subject: emailModal.subject.trim(), body: emailModal.body };
      const endpoint = emailModal.crewIds.length === 1
        ? `/api/notifications/send-email`
        : `/api/notifications/send-bulk`;
      const body = emailModal.crewIds.length === 1
        ? { ...payload, crew_member_id: emailModal.crewIds[0] }
        : { ...payload, crew_ids: emailModal.crewIds };
      const response = await axios.post(`${API_URL}${endpoint}`, body);
      const data = response.data;
      if (data.smtp_configured) {
        setEmailMsg({ type: "success", text: `Gönderildi: ${data.sent ?? data.status} kişi.` });
      } else {
        setEmailMsg({ type: "success", text: `Kuyrukta: ${data.recipients ?? 1} kişi için bekliyor (SMTP henüz tanımlı değil).` });
      }
      setEmailModal((m) => ({ ...m, subject: "", body: "" }));
    } catch (err) {
      setEmailMsg({ type: "error", text: err.response?.data?.detail || t('email.sendFailed') });
    }
  }

  function toggleCrewSelection(id) {
    setSelectedCrewIds((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  }

  // ==========================================
  // İŞ İLANLARI + BAŞVURU HAVUZU (Phase 7)
  // ==========================================
  async function loadJobs() {
    setJobsLoading(true);
    try {
      const res = await axios.get(`${API_URL}/api/jobs/?include_closed=true`);
      setJobs(res.data);
    } catch (err) {
      console.error("İlanlar yüklenemedi:", err);
    } finally {
      setJobsLoading(false);
    }
  }

  async function loadJobApplications() {
    try {
      const res = await axios.get(`${API_URL}/api/jobs/applications/all`);
      setJobApplications(res.data);
    } catch (err) {
      console.error("Başvurular yüklenemedi:", err);
    }
  }

  function handleJobFormChange(e) {
    const { name, value } = e.target;
    setJobForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleJobSubmit(e) {
    e.preventDefault();
    setJobMsg(null);
    try {
      const payload = {
        ...jobForm,
        ship_id: jobForm.ship_id ? parseInt(jobForm.ship_id, 10) : null,
        age_min: jobForm.age_min ? parseInt(jobForm.age_min, 10) : null,
        age_max: jobForm.age_max ? parseInt(jobForm.age_max, 10) : null,
        join_date: jobForm.join_date || jobForm.start_date || null,
        start_date: null,
      };
      await axios.post(`${API_URL}/api/jobs/`, payload);
      setShowJobForm(false);
      setJobForm({ title: "", position: "", ship_id: "", vessel_type: "", flag: "", location: "", currency: "USD", salary: "", salary_period: "monthly", contract_duration: "", join_date: "", application_deadline: "", description: "", duties: "", requirements: "", certificates_required: "", experience_required: "", languages_required: "", age_min: "", age_max: "", notes: "", contact_info: "", start_date: "", status: "open" });
      setJobMsg({ type: "success", text: t('jobs.saved') });
      await loadJobs();
    } catch (err) {
      setJobMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') });
    }
  }

  async function applyToJob(postingId, crewMemberId) {
    try {
      const body = crewMemberId ? { crew_member_id: crewMemberId } : {};
      await axios.post(`${API_URL}/api/jobs/${postingId}/apply`, body);
      setJobMsg({ type: "success", text: t('applications.applied') });
      await loadJobs();
      if (auth?.user?.role !== "crew") await loadJobApplications();
    } catch (err) {
      setJobMsg({ type: "error", text: err.response?.data?.detail || t('jobs.applyError') });
    }
  }

  async function updateApplicationStatus(applicationId, status) {
    try {
      await axios.patch(`${API_URL}/api/jobs/applications/${applicationId}`, { status });
      setJobMsg({ type: "success", text: t('common.success') });
      await loadJobApplications();
    } catch (err) {
      setJobMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') });
    }
  }

  async function toggleJobStatus(postingId, status) {
    try {
      await axios.patch(`${API_URL}/api/jobs/${postingId}`, { status });
      await loadJobs();
    } catch (err) {
      setJobMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') });
    }
  }

  async function deleteJob(postingId) {
    if (!window.confirm(t('common.confirm'))) return;
    try {
      await axios.delete(`${API_URL}/api/jobs/${postingId}`);
      setJobMsg({ type: "success", text: t('jobs.deleted') });
      await loadJobs();
      await loadJobApplications();
    } catch (err) {
      setJobMsg({ type: "error", text: err.response?.data?.detail || t('errors.deleteFailed') });
    }
  }

  async function loadWaManagerNumber() {
    try {
      const res = await axios.get(`${API_URL}/api/settings/contact`);
      setWaManagerNumber(res.data?.whatsapp_admin_number || "");
    } catch (err) {
      setWaManagerNumber("");
    }
  }

  // ==========================================
  // YAYIN SİSTEMİ — ŞABLON / YAYINLA / WHATSAPP KUYRUĞU (Phase 8)
  // ==========================================
  async function loadJobTemplates() {
    try {
      const res = await axios.get(`${API_URL}/api/job-templates`);
      setJobTemplates(res.data || []);
    } catch (err) { console.error("Şablonlar yüklenemedi:", err); }
  }

  async function handleTemplateSubmit(e) {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/job-templates`, {
        name: templateForm.name,
        body: templateForm.body,
        is_default: templateForm.is_default,
      });
      setTemplateForm({ name: "", body: "", is_default: false });
      setJobMsg({ type: 'success', text: t('common.success') });
      await loadJobTemplates();
    } catch (err) {
      setJobMsg({ type: 'error', text: err.response?.data?.detail || t('errors.generic') });
    }
  }

  async function deleteTemplate(templateId) {
    if (!window.confirm(t('common.confirm'))) return;
    try {
      await axios.delete(`${API_URL}/api/job-templates/${templateId}`);
      await loadJobTemplates();
    } catch (err) { setJobMsg({ type: 'error', text: t('errors.deleteFailed') }); }
  }

  async function loadPublications(jobId) {
    try {
      const res = await axios.get(`${API_URL}/api/jobs/${jobId}/publications`);
      setJobPublications((prev) => ({ ...prev, [jobId]: res.data || [] }));
    } catch (err) { console.error("Yayın geçmişi yüklenemedi:", err); }
  }

  async function loadWhatsappQueue() {
    try {
      const res = await axios.get(`${API_URL}/api/whatsapp/queue?limit=100`);
      setWhatsappQueue(res.data || []);
    } catch (err) { console.error("WhatsApp kuyruğu yüklenemedi:", err); }
  }

  async function processWhatsappQueue() {
    setJobMsg(null);
    try {
      const res = await axios.post(`${API_URL}/api/whatsapp/process`);
      setJobMsg({ type: "success", text: `Kuyruk işlendi: ${JSON.stringify(res.data)}` });
      await loadWhatsappQueue();
    } catch (err) { setJobMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') }); }
  }

  async function publishJob(jobId) {
    setPublishing((p) => ({ ...p, [jobId]: true }));
    setJobMsg(null);
    try {
      const channels = Object.entries(publishChannels[jobId] || { crew_portal: true })
        .filter(([, on]) => on).map(([c]) => c);
      if (channels.length === 0) {
        setJobMsg({ type: "error", text: t('errors.validationFailed') });
        return;
      }
      const res = await axios.post(`${API_URL}/api/jobs/${jobId}/publish`, {
        channels,
        crew_ids: publishCrewIds[jobId] || [],
        template_id: publishTemplateId[jobId] || null,
      });
      const summary = (res.data?.results || []).map((r) => `${r.channel}: ${r.status}`).join(" · ");
      setJobMsg({ type: "success", text: `Yayın tamamlandı — ${summary}` });
      await loadPublications(jobId);
      await loadWhatsappQueue();
      await loadJobs();
    } catch (err) {
      setJobMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') });
    } finally {
      setPublishing((p) => ({ ...p, [jobId]: false }));
    }
  }

  async function retryPublication(jobId, channel) {
    try {
      const res = await axios.post(`${API_URL}/api/jobs/${jobId}/publications/${channel}/retry`);
      setJobMsg({ type: "success", text: `${channel} yeniden denendi: ${JSON.stringify(res.data)}` });
      await loadPublications(jobId);
      await loadWhatsappQueue();
    } catch (err) { setJobMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') }); }
  }

  function generateJobImage(job) {
    // Canvas ile şablon görseli üret → backend'e yükle (şablon dosyası değişmez)
    const canvas = document.createElement("canvas");
    canvas.width = 1080; canvas.height = 1350;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#0f172a"; ctx.fillRect(0, 0, 1080, 1350);
    ctx.fillStyle = "#ea580c"; ctx.fillRect(0, 0, 1080, 16);
    ctx.textAlign = "center";
    ctx.fillStyle = "#fff";
    ctx.font = "bold 56px Arial";
    ctx.fillText("CREWINTEL", 540, 120);
    ctx.font = "bold 88px Arial";
    ctx.fillStyle = "#fb923c";
    ctx.fillText((job.position || job.title || "İLAN").toUpperCase() + " ARANIYOR", 540, 240);
    ctx.fillStyle = "#fff"; ctx.font = "bold 40px Arial";
    const lines = [
      `GEMİ: ${job.ship_name || "—"}${job.flag ? " · " + job.flag : ""}`,
      `MAAŞ: ${job.salary || "—"} ${job.currency || ""}${job.salary_period === "monthly" ? " / ay" : ""}`,
      `KONTRAT: ${job.contract_duration || "—"}`,
      `BAŞLANGIÇ: ${job.join_date || "—"}`,
      `SON BAŞVURU: ${job.application_deadline || "—"}`,
      `İLETİŞİM: ${job.contact_info || "—"}`,
    ];
    let y = 380;
    ctx.textAlign = "left";
    for (const line of lines) {
      ctx.fillText(line, 140, y);
      y += 72;
    }
    if (job.requirements) {
      ctx.fillStyle = "#cbd5e1"; ctx.font = "32px Arial";
      const req = job.requirements.length > 60 ? job.requirements.slice(0, 60) + "..." : job.requirements;
      ctx.fillText("GEREKSİNİMLER: " + req, 140, y + 40);
    }
    ctx.textAlign = "center";
    ctx.fillStyle = "#fb923c"; ctx.font = "bold 34px Arial";
    ctx.fillText(t('jobs.apply') + ': CREWINTEL', 540, 1290);

    const dataUrl = canvas.toDataURL("image/png");
    setJobImagePreview((prev) => ({ ...prev, [job.id]: dataUrl }));
    // backend'e yükle
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const formData = new FormData();
      formData.append("file", blob, `ilan_${job.id}.png`);
      try {
        await axios.post(`${API_URL}/api/jobs/${job.id}/image`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setJobMsg({ type: "success", text: t('common.success') });
      } catch (err) {
        setJobMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') });
      }
    }, "image/png");
  }

  async function loadPortalJobs() {
    try {
      const res = await axios.get(`${API_URL}/api/portal/jobs`);
      setPortalJobs(res.data || []);
    } catch (err) { console.error("Portal ilanları yüklenemedi:", err); }
  }

  async function portalApplyToJob(jobId) {
    try {
      await axios.post(`${API_URL}/api/portal/jobs/${jobId}/apply`, {});
      await loadPortalJobs();
      setJobMsg({ type: "success", text: t('applications.applied') });
    } catch (err) { setJobMsg({ type: "error", text: err.response?.data?.detail || t('jobs.applyError') }); }
  }

  async function toggleJobSeeking(value) {
    try {
      await axios.patch(`${API_URL}/api/portal/job-seeking`, { job_seeking: value });
      setJobMsg({ type: "success", text: value ? "İş Arıyorum açıldı." : "İş Arıyorum kapatıldı." });
    } catch (err) { setJobMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') }); }
  }

  async function handleChangeEmail(e) {
    e.preventDefault();
    setSettingsMsg(null);
    try {
      await axios.post(`${API_URL}/api/auth/change-email`, accForm);
      setAccForm({ current_password: "", new_email: "" });
      const updated = { ...auth, user: { ...auth.user, email: accForm.new_email.toLowerCase().trim() } };
      setAuth(updated);
      localStorage.setItem("crewintel_auth", JSON.stringify(updated));
      setSettingsMsg({ type: 'success', text: t('email.addressUpdated') });
    } catch (err) {
      setSettingsMsg({ type: 'error', text: err.response?.data?.detail || t('email.updateFailed') });
    }
  }

  async function handleChangePassword(e) {
    e.preventDefault();
    setSettingsMsg(null);
    if (pwdForm.new_password !== pwdForm.confirm) {
      setSettingsMsg({ type: "error", text: t('validation.passwordMismatch') });
      return;
    }
    if (pwdForm.new_password.length < 8) {
      setSettingsMsg({ type: "error", text: t('validation.invalidPassword') });
      return;
    }
    try {
      await axios.post(`${API_URL}/api/auth/change-password`, { current_password: pwdForm.current_password, new_password: pwdForm.new_password });
      setPwdForm({ current_password: "", new_password: "", confirm: "" });
      setSettingsMsg({ type: "success", text: t('profile.passwordChanged') });
    } catch (err) {
      setSettingsMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') });
    }
  }

  async function handleCreateUser(e) {
    e.preventDefault();
    setSettingsMsg(null);
    try {
      await axios.post(`${API_URL}/api/auth/users`, newUserForm);
      setNewUserForm({ email: "", password: "", full_name: "", role: "viewer", crew_member_id: undefined });
      setSettingsMsg({ type: "success", text: t('common.success') });
      await loadUsers();
    } catch (err) {
      setSettingsMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') });
    }
  }

  async function handleUpdateUser(user, field, value) {
    setSettingsMsg(null);
    try {
      await axios.patch(`${API_URL}/api/auth/users/${user.id}`, { [field]: value });
      await loadUsers();
    } catch (err) {
      setSettingsMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') });
    }
  }

  async function handleDeleteUser(user) {
    if (!window.confirm(`${user.email} kullanıcısını silmek istediğinize emin misiniz?`)) return;
    setSettingsMsg(null);
    try {
      await axios.delete(`${API_URL}/api/auth/users/${user.id}`);
      await loadUsers();
    } catch (err) {
      setSettingsMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') });
    }
  }

  useEffect(() => {
    if (activePage === "settings" && isAdmin) {
      loadUsers();
      loadNotifSettings();
    }
    if (activePage === "ship-detail" && selectedShipId) {
      loadShipStaffing(selectedShipId);
    }
    if (activePage === "jobs" && auth?.user?.role !== "crew") {
      loadJobs();
      loadJobApplications();
      loadJobTemplates();
      loadWhatsappQueue();
    }
    if (activePage === "jobs" && auth?.user?.role === "crew") {
      loadPortalJobs();
    }
    if (activePage === "communication") {
      loadWaManagerNumber();
    }
    // Personel listesi matrisi (P/SB/ST/M/C) tüm belgeleri ister —
    // dashboard 495KB yüklenmesin diye tam liste sadece bu sayfada çekilir.
    if (activePage === "crew" && auth?.user?.role !== "crew") {
      axios.get(`${API_URL}/api/documents/?limit=5000`)
        .then((res) => setAllDocuments(res.data))
        .catch(() => { /* yok say */ });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePage, isAdmin, selectedShipId]);

  // ==========================================
  // İŞ İLANLARI + BAŞVURU HAVUZU (Phase 7)
  // ==========================================
  function renderJobs() {
    const availabilityLabel = { available: '🟢 ' + t('crew.available'), on_leave: '🟡 ' + t('crew.onLeave'), on_board: '⚫ ' + t('crew.onboard'), not_available: '🔴 ' + t('crew.unavailable') };
    const statusLabel = { draft: t('status.draft'), open: t('jobs.open'), published: t('jobs.published'), closed: t('jobs.closed'), expired: t('status.expired') };
    const crewWithPhone = crew.filter((c) => c.phone && c.phone.trim());

    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('jobs.title')}</h2>
            <p>{t('jobs.title')}</p>
          </div>
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            {canWrite && (
              <button className="secondary-button" onClick={() => { setShowWhatsappQueue(!showWhatsappQueue); if (!showWhatsappQueue) loadWhatsappQueue(); }}>
                <MessageCircle size={16} /> WhatsApp Kuyruğu ({whatsappQueue.filter((m) => m.status === "pending").length})
              </button>
            )}
            {canWrite && (
              <button className="secondary-button" onClick={() => { setShowTemplates(!showTemplates); if (!showTemplates) loadJobTemplates(); }}>
                <FileText size={16} /> {t('jobs.title')} ({jobTemplates.length})
              </button>
            )}
            {canWrite && (
              <button className="secondary-button" onClick={() => { setShowJobApps(!showJobApps); if (!showJobApps) loadJobApplications(); }}>
                <ClipboardList size={16} /> {t('applications.title')} ({jobApplications.length})
              </button>
            )}
            {canWrite && (
              <button className="primary-button" onClick={() => setShowJobForm(!showJobForm)}>
                <Briefcase size={18} /> {t('jobs.addNew')}
              </button>
            )}
          </div>
        </div>

        {jobMsg && <p style={{ padding: "10px 14px", borderRadius: "8px", marginBottom: "14px", background: jobMsg.type === "success" ? "#f0fdf4" : "#fef2f2", color: jobMsg.type === "success" ? "#15803d" : "#b91c1c", fontWeight: "600", fontSize: "13px" }}>{jobMsg.text}</p>}

        {/* ── ŞABLONLAR ── */}
        {showTemplates && canWrite && (
          <div style={{ marginBottom: "20px", padding: "18px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", marginBottom: "8px", flexWrap: "wrap" }}>
              <p className="section-label" style={{ margin: 0 }}>{t('jobs.templates')} ({jobTemplates.length}) — {"{{position}}"}, {"{{vessel}}"}, {"{{salary}}"}, {"{{currency}}"}, {"{{contract_duration}}"}, {"{{join_date}}"}, {"{{deadline}}"}, {"{{contact}}"} {t('jobs.templateVariables')}</p>
              <button className="secondary-button" style={{ padding: "6px 12px", fontSize: "13px" }} onClick={() => setShowTemplates(false)}>Kapat</button>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "14px" }}>
              {jobTemplates.map((template) => (
                <div key={template.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', padding: '10px 14px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
                  <div style={{ flex: 1 }}>
                    <strong style={{ color: '#0f172a', fontSize: '14px' }}>{template.name} {template.is_default && <span style={{ color: '#15803d', fontSize: '12px' }}>★ Default</span>}</strong>
                    <div style={{ color: '#64748b', fontSize: '12px', whiteSpace: 'pre-wrap', marginTop: '4px' }}>{template.body.slice(0, 220)}{template.body.length > 220 ? '...' : ''}</div>
                  </div>
                  <button className='secondary-button' style={{ padding: '6px 10px', fontSize: '12px', color: '#b91c1c' }} onClick={() => deleteTemplate(template.id)}>{t('common.delete')}</button>
                </div>
              ))}
              {jobTemplates.length === 0 && <p style={{ color: "#64748b", fontSize: "13px" }}>Henüz şablon yok — aşağıdan ekleyin.</p>}
            </div>
            <form onSubmit={handleTemplateSubmit} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                <input className="form-input" placeholder={t('jobs.templateName')} style={{ flex: 1, minWidth: "200px", padding: "10px" }} value={templateForm.name} onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })} required />
                <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", fontWeight: "600", color: "#0f172a" }}>
                  <input type="checkbox" checked={templateForm.is_default} onChange={(e) => setTemplateForm({ ...templateForm, is_default: e.target.checked })} /> Varsayılan
                </label>
              </div>
              <textarea className="form-input" rows="5" style={{ width: "100%", padding: "10px", boxSizing: "border-box", fontFamily: "monospace", fontSize: "12px" }} placeholder={"{{position}} ARANIYOR\nGEMİ: {{vessel}}\nMAAŞ: {{salary}} {{currency}}\nKONTRAT: {{contract_duration}}\nBAŞLANGIÇ: {{join_date}}\nSON BAŞVURU: {{deadline}}\nİLETİŞİM: {{contact}}\n\nCREWINTEL"} value={templateForm.body} onChange={(e) => setTemplateForm({ ...templateForm, body: e.target.value })} required />
              <div><button className="primary-button" type="submit" style={{ padding: "10px 18px" }}>{t('common.save')}</button></div>
            </form>
          </div>
        )}

        {/* ── WHATSAPP KUYRUĞU ── */}
        {showWhatsappQueue && canWrite && (
          <div style={{ marginBottom: "20px", padding: "18px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px" }}>
              <p className="section-label" style={{ margin: 0 }}>WhatsApp Gönderim Kuyruğu ({whatsappQueue.length})</p>
              <button className="primary-button" style={{ padding: "8px 16px", fontSize: "13px" }} onClick={processWhatsappQueue}>Kuyruğu İşle</button>
            </div>
            <div className="table-wrapper">
              <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead><tr style={{ textAlign: "left", color: "#64748b" }}><th>{t('crew.title')}</th><th>{t('common.phone')}</th><th>{t('common.status')}</th><th>{t('common.count')}</th><th>{t('common.error')}</th></tr></thead>
                <tbody>
                  {whatsappQueue.map((m) => (
                    <tr key={m.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                      <td style={{ padding: "9px 8px", fontWeight: "600", color: "#0f172a" }}>{m.crew_name || "—"}</td>
                      <td style={{ padding: "9px 8px", color: "#475569" }}>{m.phone}</td>
                      <td style={{ padding: "9px 8px" }}>
                        <span className={`badge ${m.status === "sent" ? "badge-success" : m.status === "failed" ? "badge-danger" : "badge-warning"}"`} style={{ fontSize: "12px" }}>{m.status}</span>
                      </td>
                      <td style={{ padding: "9px 8px", color: "#64748b" }}>{m.attempts}</td>
                      <td style={{ padding: "9px 8px", color: "#b91c1c", fontSize: "12px" }}>{m.last_error || "—"}</td>
                    </tr>
                  ))}
                  {whatsappQueue.length === 0 && <tr><td colSpan={5} style={{ padding: "20px", textAlign: "center", color: "#64748b" }}>Kuyruk boş.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── İLAN OLUŞTURMA FORMU ── */}
        {showJobForm && canWrite && (
          <form className="crew-form" onSubmit={handleJobSubmit} style={{ marginBottom: "20px" }}>
            <div className="detail-grid" style={{ marginBottom: "8px" }}>
              <label>{t('jobs.title')}<input name="title" value={jobForm.title} onChange={handleJobFormChange} required placeholder="Örn: Elektrikçi aranıyor" /></label>
              <label>{t('crew.position')}<input name="position" value={jobForm.position} onChange={handleJobFormChange} required placeholder="Örn: Elektrikçi" /></label>
              <label>{t('vessels.title')}
                <select name="ship_id" value={jobForm.ship_id} onChange={handleJobFormChange} className="form-input">
                  <option value="">-- {t('vessels.title')} --</option>
                  {ships.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </label>
              <label>{t('jobs.vesselType')}<input name="vessel_type" value={jobForm.vessel_type} onChange={handleJobFormChange} placeholder="Örn: General Cargo, Tanker" /></label>
              <label>{t('vessels.flag')}<input name="flag" value={jobForm.flag} onChange={handleJobFormChange} placeholder="Örn: TR, PA" /></label>
              <label>Lokasyon<input name="location" value={jobForm.location} onChange={handleJobFormChange} placeholder="Örn: İstanbul" /></label>
              <label>Maaş<input name="salary" value={jobForm.salary} onChange={handleJobFormChange} placeholder="Örn: 1800" /></label>
              <label>{t('jobs.currency')}
                <select name="currency" value={jobForm.currency} onChange={handleJobFormChange} className="form-input">
                  <option value="USD">USD</option><option value="EUR">EUR</option><option value="TRY">TRY</option>
                </select>
              </label>
              <label>{t('jobs.salaryPeriod')}
                <select name="salary_period" value={jobForm.salary_period} onChange={handleJobFormChange} className="form-input">
                  <option value="monthly">{t('jobs.monthly')}</option><option value="daily">{t('jobs.daily')}</option><option value="per_contract">{t('contracts.type')}</option>
                </select>
              </label>
              <label>{t('jobs.contractDuration')}<input name="contract_duration" value={jobForm.contract_duration} onChange={handleJobFormChange} placeholder="Örn: 6 ay" /></label>
              <label>Katılış Tarihi<input type="date" name="join_date" value={jobForm.join_date} onChange={handleJobFormChange} /></label>
              <label>{t('jobs.deadline')}<input type='date' name='application_deadline' value={jobForm.application_deadline} onChange={handleJobFormChange} /></label>
              <label>Deneyim<input name="experience_required" value={jobForm.experience_required} onChange={handleJobFormChange} placeholder="Örn: 3 yıl" /></label>
              <label>Dil Gereksinimi<input name="languages_required" value={jobForm.languages_required} onChange={handleJobFormChange} placeholder="Örn: İngilizce" /></label>
              <label>{t('jobs.ageRange')}<input name="age_range" value={jobForm.age_min ? `${jobForm.age_min}-${jobForm.age_max || ""}` : ""} placeholder="Örn: 25-45" onChange={(e) => { const m = e.target.value.split("-"); setJobForm((p) => ({ ...p, age_min: m[0] || "", age_max: m[1] || "" })); }} /></label>
              <label>{t('common.phone')}<input name="contact_info" value={jobForm.contact_info} onChange={handleJobFormChange} placeholder="Örn: +90 532 327 61 21" /></label>
            </div>
            <label>İş Tanımı / Görevler<textarea name="duties" rows="2" value={jobForm.duties} onChange={handleJobFormChange} className="form-input" /></label>
            <label>Açıklama<textarea name="description" rows="2" value={jobForm.description} onChange={handleJobFormChange} className="form-input" /></label>
            <label>Gereksinimler<textarea name="requirements" rows="2" value={jobForm.requirements} onChange={handleJobFormChange} className="form-input" placeholder="Örn: STCW, Medical, 5 yıl deneyim" /></label>
            <label>Sertifika Gereksinimleri<textarea name="certificates_required" rows="2" value={jobForm.certificates_required} onChange={handleJobFormChange} className="form-input" /></label>
            <label>Notlar<textarea name="notes" rows="2" value={jobForm.notes} onChange={handleJobFormChange} className="form-input" /></label>
            <div className="form-actions">
              <button className="secondary-button" type="button" onClick={() => setShowJobForm(false)}>{t('common.cancel')}</button>
              <button className="primary-button" type="submit">{t('common.save')}</button>
            </div>
          </form>
        )}

        {/* ── BAŞVURU HAVUZU ── */}
        {showJobApps && canWrite && (
          <div style={{ marginBottom: "20px", padding: "18px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px" }}>
            <p className="section-label">{t('jobs.applicationPool')} ({jobApplications.length})</p>
            <div className="table-wrapper">
              <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ textAlign: "left", color: "#64748b" }}>
                    <th>{t('common.name')}</th><th>{t('crew.position')}</th><th>{t('jobs.title')}</th><th>{t('crew.availability')}</th><th>{t('common.phone')}</th><th>{t('common.status')}</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {jobApplications.map((a) => (
                    <tr key={a.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                      <td style={{ padding: "10px 8px", fontWeight: "600", color: "#0f172a", cursor: "pointer" }} onClick={() => openCrewDetail(a.crew_member_id)}>{a.crew_name}</td>
                      <td style={{ padding: "10px 8px", color: "#475569" }}>{a.crew_position || "—"}</td>
                      <td style={{ padding: "10px 8px", color: "#475569" }}>{a.job_title}</td>
                      <td style={{ padding: "10px 8px", fontSize: "13px" }}>{availabilityLabel[a.availability] || a.availability || "—"}</td>
                      <td style={{ padding: "10px 8px", color: "#475569" }}>{a.crew_phone || "—"}</td>
                      <td style={{ padding: "10px 8px" }}><span className={`badge badge-${a.status}"`}>{a.status}</span></td>
                      <td style={{ padding: "10px 8px", textAlign: "right", whiteSpace: "nowrap" }}>
                        <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px" }} onClick={() => updateApplicationStatus(a.id, "reviewing")}>İncele</button>{' '}
                        <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px", background: "#15803d", color: "#fff", border: "none" }} onClick={() => updateApplicationStatus(a.id, "accepted")}>Onayla</button>{' '}
                        <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px", color: "#b91c1c" }} onClick={() => updateApplicationStatus(a.id, "rejected")}>Reddet</button>
                      </td>
                    </tr>
                  ))}
                  {jobApplications.length === 0 && (
                    <tr><td colSpan={7} style={{ padding: "24px", textAlign: "center", color: "#64748b" }}>Henüz başvuru yok.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── İLAN LİSTESİ ── */}
        {jobsLoading ? (
          <p className="crew-loading">{t('common.loading')}</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "18px" }}>
            {jobs.map((job) => (
              <div key={job.id} style={{ border: `1px solid ${job.status === "open" || job.status === "published" ? "#e2e8f0" : "#cbd5e1"}`, borderRadius: "12px", padding: "18px", background: job.status === "open" || job.status === "published" ? "#fff" : "#f8fafc" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                  <div>
                    <strong style={{ fontSize: "16px", color: "#0f172a" }}>{job.title}</strong>
                    <div style={{ color: "#64748b", fontSize: "13px", marginTop: "4px" }}>
                      {job.ship_name ? `🚢 ${job.ship_name}` : '🚢 ' + t('vessels.name')} · {job.position}
                    </div>
                    <div style={{ color: "#94a3b8", fontSize: "12px", marginTop: "2px" }}>
                      {[job.vessel_type, job.flag, job.location].filter(Boolean).join(" · ") || ""}
                    </div>
                  </div>
                  <span className={`badge ${job.status === "open" || job.status === "published" ? "badge-success" : "badge-neutral"}"`} style={{ fontSize: "12px", padding: "4px 10px", borderRadius: "999px" }}>
                    {statusLabel[job.status] || job.status}
                  </span>
                </div>
                {job.salary && <p style={{ margin: "10px 0 0 0", color: "#0f172a", fontWeight: "600" }}>💰 {job.salary} {job.currency}{job.salary_period === "monthly" ? " / ay" : ""}</p>}
                {(job.contract_duration || job.join_date) && (
                  <p style={{ margin: "4px 0 0 0", color: "#64748b", fontSize: "13px" }}>
                    {[job.contract_duration && `${t('contracts.type')}: ${job.contract_duration}`, job.join_date && `${t('contracts.startDate')}: ${job.join_date}`, job.application_deadline && `${t('jobs.deadline')}: ${job.application_deadline}`].filter(Boolean).join(" · ")}
                  </p>
                )}
                {job.requirements && <p style={{ margin: "10px 0 0 0", color: "#475569", fontSize: "13px" }}><strong>Gereksinimler:</strong> {job.requirements}</p>}
                {job.description && <p style={{ margin: "6px 0 0 0", color: "#64748b", fontSize: "13px" }}>{job.description}</p>}
                {jobImagePreview[job.id] && (
                  <img src={jobImagePreview[job.id]} alt={t('jobs.title')} style={{ width: "100%", maxHeight: "260px", objectFit: "cover", borderRadius: "8px", marginTop: "10px", border: "1px solid #e2e8f0" }} />
                )}
                <p style={{ margin: "10px 0 0 0", color: "#64748b", fontSize: "12px" }}>{job.application_count} başvuru</p>
                <div style={{ display: "flex", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
                  {canWrite && (
                    <>
                      <button className="primary-button" style={{ padding: "8px 14px", fontSize: "13px", background: "#0284c7", border: "none" }} onClick={() => { setPublishOpen((p) => ({ ...p, [job.id]: !p[job.id] })); if (!publishOpen[job.id]) { loadPublications(job.id); if (!jobTemplates.length) loadJobTemplates(); } }}>
                        <Send size={14} /> Yayınla
                      </button>
                      <button className="secondary-button" style={{ padding: "8px 14px", fontSize: "13px" }} onClick={() => generateJobImage(job)} title="Şablondan görsel üret">
                        <ImageIcon size={14} /> Görsel Oluştur
                      </button>
                      <button className="secondary-button" style={{ padding: "8px 14px", fontSize: "13px" }} onClick={() => setJobApplyOpen((p) => ({ ...p, [job.id]: !p[job.id] }))}>
                        {t('jobs.apply')}
                      </button>
                      <button className="secondary-button" style={{ padding: "8px 14px", fontSize: "13px", color: "#b45309" }} onClick={() => toggleJobStatus(job.id, job.status === "open" || job.status === "published" ? "closed" : "open")}>
                        {job.status === "open" || job.status === "published" ? t('common.close') : t('common.open')}
                      </button>
                    </>
                  )}
                  {isAdmin && (
                    <button className="secondary-button" style={{ padding: "8px 14px", fontSize: "13px", color: "#b91c1c" }} onClick={() => deleteJob(job.id)}>
                      <Trash2 size={14} /> {t('common.delete')}
                    </button>
                  )}
                </div>

                {/* YAYIN PANELİ */}
                {publishOpen[job.id] && canWrite && (
                  <div style={{ marginTop: "14px", padding: "14px", background: "#fffbeb", border: "1px solid #fcd34d", borderRadius: "10px" }}>
                    <p className="section-label" style={{ margin: "0 0 10px 0" }}>Yayın Kanalları</p>
                    <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "12px" }}>
                      {[
                        ["crew_portal", "🖥️ Crew Portal"],
                        ["whatsapp", "💬 WhatsApp"],
                        ["instagram", "📸 Instagram"],
                        ["facebook", "📘 Facebook"],
                      ].map(([ch, label]) => (
                        <label key={ch} style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", fontWeight: "600", color: "#0f172a", cursor: "pointer" }}>
                          <input type="checkbox" checked={publishChannels[job.id]?.[ch] ?? (ch === "crew_portal")} onChange={(e) => setPublishChannels((p) => ({ ...p, [job.id]: { ...(p[job.id] || { crew_portal: true }), [ch]: e.target.checked } }))} />
                          {label}
                        </label>
                      ))}
                    </div>
                    <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "12px" }}>
                      <div style={{ flex: 1, minWidth: "220px" }}>
                        <span className="section-label">Şablon</span>
                        <select className="form-input" style={{ width: "100%", padding: "8px" }} value={publishTemplateId[job.id] || ""} onChange={(e) => setPublishTemplateId((p) => ({ ...p, [job.id]: e.target.value ? parseInt(e.target.value, 10) : null }))}>
                          <option value="">Varsayılan şablonu kullan</option>
                          {jobTemplates.map((tpl) => <option key={tpl.id} value={tpl.id}>{tpl.name}{tpl.is_default ? ' ★' : ''}</option>)}
                        </select>
                      </div>
                      <div style={{ flex: 2, minWidth: "280px" }}>
                        <span className="section-label">WhatsApp Alıcıları ({publishCrewIds[job.id]?.length || 0} seçili — {crewWithPhone.length} telefona sahip personel)</span>
                        <div style={{ maxHeight: "140px", overflowY: "auto", border: "1px solid #e2e8f0", borderRadius: "8px", background: "#fff", padding: "8px" }}>
                          {crewWithPhone.map((c) => (
                            <label key={c.id} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", color: "#0f172a", padding: "4px 6px", cursor: "pointer" }}>
                              <input type="checkbox" checked={(publishCrewIds[job.id] || []).includes(c.id)} onChange={(e) => setPublishCrewIds((p) => { const cur = p[job.id] || []; const next = e.target.checked ? [...cur, c.id] : cur.filter((x) => x !== c.id); return { ...p, [job.id]: next }; })} />
                              {c.first_name} {c.last_name} · {c.position || "—"} · {c.phone}
                            </label>
                          ))}
                          {crewWithPhone.length === 0 && <p style={{ color: "#64748b", fontSize: "12px" }}>{t('crew.noPersonnel')}</p>}
                        </div>
                      </div>
                    </div>
                    <button className="primary-button" style={{ padding: "10px 20px", fontSize: "14px" }} disabled={publishing[job.id]} onClick={() => publishJob(job.id)}>
                      <Send size={16} /> {publishing[job.id] ? t('common.processing') : t('jobs.publishToSocial')}
                    </button>

                    {(jobPublications[job.id]?.length > 0) && (
                      <div style={{ marginTop: "14px" }}>
                        <p className="section-label">Yayın Geçmişi</p>
                        <table className="data-table" style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                          <thead><tr style={{ textAlign: "left", color: "#64748b" }}><th>{t('messages.to')}</th><th>{t('common.status')}</th><th>{t('messages.to')}</th><th>{t('common.error')}</th><th></th></tr></thead>
                          <tbody>
                            {(jobPublications[job.id] || []).map((p) => (
                              <tr key={p.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                                <td style={{ padding: "8px", fontWeight: "600", color: "#0f172a" }}>{p.channel}</td>
                                <td style={{ padding: "8px" }}>
                                  <span className={`badge ${p.status === "sent" ? "badge-success" : p.status === "skipped" ? "badge-neutral" : "badge-warning"}"`}>{p.status}</span>
                                </td>
                                <td style={{ padding: "8px", color: "#64748b" }}>{p.recipient_count}</td>
                                <td style={{ padding: "8px", color: p.error ? "#b91c1c" : "#15803d", fontSize: "12px" }}>{p.error ? String(p.error).slice(0, 90) : "—"}</td>
                                <td style={{ padding: "8px" }}>
                                  {(p.status === "queued" || p.status === "skipped") && (
                                    <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px" }} onClick={() => retryPublication(job.id, p.channel)}>Retry</button>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}

                {/* PERSONEL İÇİN BAŞVURU */}
                {jobApplyOpen[job.id] && canWrite && (
                  <div style={{ display: "flex", gap: "8px", marginTop: "10px", alignItems: "center", flexWrap: "wrap" }}>
                    <select
                      className="form-input"
                      style={{ flex: 1, minWidth: "160px", padding: "8px" }}
                      value={jobApplyCrewId[job.id] || ""}
                      onChange={(e) => setJobApplyCrewId((p) => ({ ...p, [job.id]: e.target.value }))}
                    >
                      <option value="">-- {t('crew.title')} --</option>
                      {crew.filter((c) => c.status === "active").map((c) => (
                        <option key={c.id} value={c.id}>{c.first_name} {c.last_name} · {c.position || "—"}</option>
                      ))}
                    </select>
                    <button className="primary-button" style={{ padding: "8px 14px", fontSize: "13px" }} onClick={() => {
                      if (!jobApplyCrewId[job.id]) { setJobMsg({ type: "error", text: "Önce personel seçin." }); return; }
                      applyToJob(job.id, parseInt(jobApplyCrewId[job.id], 10));
                    }}>{t('jobs.apply')}</button>
                  </div>
                )}
              </div>
            ))}
            {jobs.length === 0 && (
              <div style={{ gridColumn: "1 / -1", textAlign: "center", padding: "40px", color: "#64748b", background: "#f8fafc", border: "2px dashed #cbd5e1", borderRadius: "12px" }}>
                <Briefcase size={48} style={{ margin: "0 auto 12px auto", opacity: 0.6 }} />
                <p>{t('jobs.noJobs')}</p>
              </div>
            )}
          </div>
        )}
      </section>
    );
  }

  // ==========================================
  // İLETİŞİM — WhatsApp (Phase 7)
  // ==========================================
  function renderCommunication() {
    const withPhone = crew.filter((c) => c.phone && c.phone.trim());
    const withoutPhone = crew.filter((c) => !c.phone || !c.phone.trim());
    const normalize = (phone) => phone.replace(/[^0-9]/g, "").replace(/^00/, "").replace(/^0/, "90");
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('messages.title')}</h2>
            <p>{t('messages.title')}</p>
          </div>
        </div>

        <div style={{ padding: "18px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "12px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <strong style={{ color: "#15803d", fontSize: "16px" }}>📱 Yönetici WhatsApp: {waManagerNumber || "tanımlı değil"}</strong>
            <p style={{ margin: "4px 0 0 0", color: "#166534", fontSize: "13px" }}>{t('documents.upload')}</p>
          </div>
          {waManagerNumber && (
            <a href={`https://wa.me/${normalize(waManagerNumber)}?text=${encodeURIComponent("Merhaba, CREWINTEL üzerinden yazıyorum.")}`} target="_blank" rel="noreferrer" className="primary-button" style={{ textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "8px" }}>
              <MessageCircle size={16} /> WhatsApp'ta Aç
            </a>
          )}
        </div>

        <p className="section-label">{t('crew.title')} ({withPhone.length})</p>
        <div className="table-wrapper">
          <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", color: "#64748b" }}>
                <th>{t('crew.title')}</th><th>{t('crew.position')}</th><th>{t('vessels.title')}</th><th>{t('common.phone')}</th><th>{t('common.status')}</th><th></th>
              </tr>
            </thead>
            <tbody>
              {withPhone.map((c) => {
                const activeAssign = assignments.find((a) => a.crew_member_id === c.id && a.status === "active");
                const shipName = activeAssign ? (shipById[activeAssign.ship_id]?.name || "—") : "—";
                const phoneLink = `https://wa.me/${normalize(c.phone)}?text=${encodeURIComponent(`Merhaba ${c.first_name}, CREWINTEL üzerinden yazıyorum.`)}`;
                return (
                  <tr key={c.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "10px 8px", fontWeight: "600", color: "#0f172a", cursor: "pointer" }} onClick={() => openCrewDetail(c.id)}>{c.first_name} {c.last_name}</td>
                    <td style={{ padding: "10px 8px", color: "#475569" }}>{c.position || "—"}</td>
                    <td style={{ padding: "10px 8px", color: "#475569" }}>{shipName}</td>
                    <td style={{ padding: "10px 8px", color: "#475569" }}>{c.phone}</td>
                    <td style={{ padding: "10px 8px", fontSize: "13px" }}>{c.availability === "available" ? '🟢 ' + t('crew.available') : c.availability === "on_leave" ? '🟡 ' + t('crew.onLeave') : c.availability === "on_board" ? '⚫ ' + t('crew.onboard') : c.availability === "not_available" ? '🔴 ' + t('crew.unavailable') : c.availability || "—"}</td>
                    <td style={{ padding: "10px 8px", textAlign: "right" }}>
                      <a href={phoneLink} target="_blank" rel="noreferrer" className="secondary-button" style={{ textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 12px", fontSize: "13px" }}>
                        <MessageCircle size={14} /> {t('jobs.whatsappMessage')}
                      </a>
                    </td>
                  </tr>
                );
              })}
              {withPhone.length === 0 && (
                <tr><td colSpan={6} style={{ padding: "24px", textAlign: "center", color: "#64748b" }}>{t('crew.noPersonnel')}</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <p className="section-label" style={{ marginTop: "24px" }}>{t('crew.title')} ({withoutPhone.length})</p>
        <div className="table-wrapper">
          <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
            <tbody>
              {withoutPhone.map((c) => (
                <tr key={c.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "10px 8px", fontWeight: "600", color: "#0f172a", cursor: "pointer" }} onClick={() => openCrewDetail(c.id)}>{c.first_name} {c.last_name}</td>
                  <td style={{ padding: "10px 8px", color: "#64748b", fontSize: "13px" }}>{t('common.notFound')}</td>
                </tr>
              ))}
              {withoutPhone.length === 0 && (
                <tr><td colSpan={2} style={{ padding: "24px", textAlign: "center", color: "#64748b" }}>Hepsinin telefonu kayıtlı.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    );
  }

  function renderEligibility() {
    const availabilityLabel = { available: '🟢 ' + t('crew.available'), on_leave: '🟡 ' + t('crew.onLeave'), on_board: '⚫ ' + t('crew.onboard'), not_available: '🔴 ' + t('crew.unavailable') };
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('crew.eligibility')}</h2>
            <p>{t('crew.search')}</p>
          </div>
        </div>
        <form onSubmit={runEligibility} style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "20px", alignItems: "flex-end" }}>
          <div style={{ flex: "1", minWidth: "220px" }}>
            <label className="section-label">{t('crew.position')}</label>
            <input className="form-input" style={{ width: "100%", padding: "11px", marginTop: "6px" }} required placeholder="Örn: Kaptan, Başmühendis, Elektrik Zabiti" value={eligibilityQuery.position}
              onChange={(e) => setEligibilityQuery({ ...eligibilityQuery, position: e.target.value })} />
          </div>
          <div style={{ width: "150px" }}>
            <label className="section-label">Min. Skor</label>
            <select className="form-input" style={{ width: "100%", padding: "11px", marginTop: "6px" }} value={eligibilityQuery.min_score}
              onChange={(e) => setEligibilityQuery({ ...eligibilityQuery, min_score: Number(e.target.value) })}>
              <option value="40">40+ (tümü)</option>
              <option value="60">60+ (orta)</option>
              <option value="75">75+ (yüksek)</option>
              <option value="90">90+ (çok yüksek)</option>
            </select>
          </div>
          <button className="primary-button" type="submit" style={{ padding: "12px 22px" }} disabled={eligibilityLoading}>
            <Search size={18} /> {eligibilityLoading ? t('common.loading') : t('crew.search')}
          </button>
        </form>

        {eligibilityResults !== null && (
          <div className="table-wrapper">
            <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", color: "#64748b" }}>
                  <th>{t('crew.title')}</th><th>{t('crew.position')}</th><th>{t('crew.availability')}</th><th>{t('documents.title')}</th><th>{t('contracts.endDate')}</th><th>{t('crew.experience')}</th><th>{t('applications.matchScore')}</th>
                </tr>
              </thead>
              <tbody>
                {eligibilityResults.map((r) => (
                  <tr key={r.crew_id} style={{ borderTop: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "10px 8px", fontWeight: "600", color: "#0f172a" }}>{r.first_name} {r.last_name}</td>
                    <td style={{ padding: "10px 8px", color: "#475569" }}>{r.position}</td>
                    <td style={{ padding: "10px 8px", fontSize: "13px" }}>{availabilityLabel[r.availability] || r.availability}</td>
                    <td style={{ padding: "10px 8px", fontSize: "13px" }}>
                      {Object.entries(r.documents_status || {}).map(([docType, docStatus]) => (
                        <span key={docType} title={docType + ": " + docStatus} style={{ marginRight: "4px", cursor: "default" }}>
                          {docStatus === "valid" ? "🟢" : docStatus === "expired" ? "🔴" : docStatus === "missing" ? "⚪" : "🟡"}{docType[0].toUpperCase()}
                        </span>
                      ))}
                    </td>
                    <td style={{ padding: "10px 8px", fontSize: "13px", color: (r.breakdown?.expiry || 0) >= 15 ? "#15803d" : "#b45309" }}>{r.breakdown?.expiry}/20</td>
                    <td style={{ padding: "10px 8px", fontSize: "13px", color: "#475569" }}>{r.experience_years || 0} yıl</td>
                    <td style={{ padding: "10px 8px" }}>
                      <strong style={{ fontSize: "18px", color: r.score >= 90 ? "#15803d" : r.score >= 70 ? "#b45309" : "#b91c1c" }}>%{r.score}</strong>
                    </td>
                  </tr>
                ))}
                {eligibilityResults.length === 0 && (
                  <tr><td colSpan={7} style={{ padding: "24px", textAlign: "center", color: "#64748b" }}>{t('crew.noResults')}</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    );
  }

  function RenderPortal() {
    const [portalData, setPortalData] = useState(null);
    const [portalMsg, setPortalMsg] = useState(null);
    const [contactForm, setContactForm] = useState({ phone: "", email: "" });
    useEffect(() => {
      axios.get(`${API_URL}/api/portal/me`).then((res) => {
        setPortalData(res.data);
        setContactForm({ phone: res.data.profile.phone || "", email: res.data.profile.email || "" });
      }).catch(() => setPortalMsg({ type: 'error', text: t('errors.loadingFailed') }));
      loadPortalJobs();
    }, []);
    if (!portalData) {
      return <section className="panel" style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>Portal yükleniyor...</section>;
    }
    const requiredTypes = { passport: t('documentTypes.passport'), seaman_book: t('documentTypes.seaman_book'), stcw: t('documentTypes.stcw'), medical: t('documentTypes.medical') };
    const foundTypes = portalData.documents.filter((d) => !d.archived).map((d) => d.document_type);
    const missing = Object.keys(requiredTypes).filter((t) => !foundTypes.includes(t));
    const submitContact = async (e) => {
      e.preventDefault();
      try {
        await axios.put(`${API_URL}/api/portal/contact`, contactForm);
        setPortalMsg({ type: "success", text: t('profile.profileUpdated') });
      } catch (err) { setPortalMsg({ type: "error", text: err.response?.data?.detail || t('errors.generic') }); }
    };
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('profile.title')}</h2>
            <p>{t('profile.personalInfo')}</p>
          </div>
        </div>
        {portalMsg && <div style={{ padding: "10px 14px", borderRadius: "8px", marginBottom: "14px", fontWeight: "600", fontSize: "13px", background: portalMsg.type === "success" ? "#f0fdf4" : "#fef2f2", color: portalMsg.type === "success" ? "#15803d" : "#b91c1c" }}>{portalMsg.text}</div>}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px" }}>
          <div style={{ background: "#f8fafc", padding: "20px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
            <h3 style={{ margin: "0 0 14px 0", color: "#0f172a" }}>{t('profile.title')}</h3>
            <p style={{ margin: "0 0 6px 0", color: "#0f172a" }}><strong>{portalData.profile.first_name} {portalData.profile.last_name}</strong></p>
            <p style={{ margin: "0 0 4px 0", color: "#475569", fontSize: "13px" }}>{portalData.profile.position}{portalData.profile.rank ? " · " + portalData.profile.rank : ""}</p>
            <p style={{ margin: "0 0 4px 0", color: "#475569", fontSize: "13px" }}>{portalData.profile.nationality || ""} · {t('crew.experience')}: {portalData.profile.experience_years || 0}</p>
            {missing.length > 0 ? (
              <p style={{ margin: "12px 0 0 0", color: "#b45309", fontWeight: "600", fontSize: "13px" }}>{t('documents.missingDocuments')}: {missing.map((docType) => requiredTypes[docType]).join(', ')}</p>
            ) : (
              <p style={{ margin: "12px 0 0 0", color: "#15803d", fontWeight: "700", fontSize: "13px" }}>✅ {t('documents.allDocumentsPresent')}</p>
            )}
            <div style={{ marginTop: "16px", padding: "14px", background: portalData.profile.job_seeking ? "#f0fdf4" : "#f8fafc", border: `1px solid ${portalData.profile.job_seeking ? "#bbf7d0" : "#e2e8f0"}`, borderRadius: "10px" }}>
              <p style={{ margin: "0 0 8px 0", fontSize: "13px", fontWeight: "700", color: portalData.profile.job_seeking ? "#15803d" : "#64748b" }}>
                {portalData.profile.job_seeking ? "🟢 İş Arıyorum — AÇIK" : "⚪ İş Arıyorum — KAPALI"}
              </p>
              <button
                className={portalData.profile.job_seeking ? "secondary-button" : "primary-button"}
                style={{ padding: "8px 14px", fontSize: "13px" }}
                onClick={async () => {
                  const next = !portalData.profile.job_seeking;
                  await toggleJobSeeking(next);
                  setPortalData((p) => ({ ...p, profile: { ...p.profile, job_seeking: next } }));
                }}
              >
                {portalData.profile.job_seeking ? "İş Arıyorum'u Kapat" : "İş Arıyorum'u Aç"}
              </button>
              <p style={{ margin: "8px 0 0 0", fontSize: "12px", color: "#64748b" }}>{t('crew.jobSeekingHint')}</p>
            </div>
            <form onSubmit={submitContact} style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "10px" }}>
              <label style={{ fontSize: "12px", fontWeight: "bold", color: "#475569" }}>{t('common.phone')}
                <input className="form-input" style={{ width: "100%", padding: "9px", marginTop: "4px" }} value={contactForm.phone} onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })} />
              </label>
              <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#475569' }}>{t('common.email')}
                <input className="form-input" type="email" style={{ width: "100%", padding: "9px", marginTop: "4px" }} value={contactForm.email} onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })} />
              </label>
              <button className="primary-button" type="submit" style={{ padding: "10px" }}>{t('profile.saveProfile')}</button>
            </form>
          </div>
          <div style={{ background: "#f8fafc", padding: "20px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
            <h3 style={{ margin: "0 0 14px 0", color: "#0f172a" }}>{t('documents.title')} ({portalData.documents.length})</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {portalData.documents.map((d) => (
                <div key={d.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 12px", background: "#fff", border: "1px solid #e2e8f0", borderRadius: "8px" }}>
                  <div>
                    <strong style={{ fontSize: "13px", color: "#0f172a" }}>{d.document_type}</strong>
                    <span style={{ display: "block", fontSize: "12px", color: "#64748b" }}>{d.original_filename}{d.expiry_date ? " · Bitiş: " + d.expiry_date : ""}</span>
                  </div>
                  <span style={{ fontSize: "12px", fontWeight: "600", color: d.archived ? "#94a3b8" : d.match_status === "matched" ? "#15803d" : "#b45309" }}>{d.archived ? t('common.archived') : d.match_status === 'matched' ? '✓ ' + t('documents.valid') : t('documents.pending')}</span>
                </div>
              ))}
              {portalData.documents.length === 0 && <p style={{ color: "#64748b" }}>Henüz belgeniz yok.</p>}
            </div>
          </div>
        </div>

        {/* ── İŞ İLANLARI (portal) ── */}
        <div style={{ marginTop: "24px" }}>
          <h3 style={{ margin: "0 0 14px 0", color: "#0f172a" }}>{t('jobs.title')} ({portalJobs.length})</h3>
          {portalJobs.length === 0 && (
            <div style={{ padding: "24px", textAlign: "center", color: "#64748b", background: "#f8fafc", border: "2px dashed #cbd5e1", borderRadius: "12px" }}>
              Şu anda yayında ilan yok.
            </div>
          )}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "16px" }}>
            {portalJobs.map((job) => (
              <div key={job.id} style={{ background: "#f8fafc", padding: "18px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
                <strong style={{ fontSize: "15px", color: "#0f172a" }}>{job.title}</strong>
                <div style={{ color: "#64748b", fontSize: "13px", marginTop: "4px" }}>
                  {job.ship_name ? `🚢 ${job.ship_name}` : '🚢 ' + t('vessels.name')} · {job.position}
                </div>
                {job.salary && <p style={{ margin: "8px 0 0 0", color: "#0f172a", fontWeight: "600", fontSize: "13px" }}>💰 {job.salary} {job.currency}</p>}
                {(job.contract_duration || job.join_date) && (
                  <p style={{ margin: "4px 0 0 0", color: "#64748b", fontSize: "12px" }}>
                    {[job.contract_duration && `${t('contracts.type')}: ${job.contract_duration}`, job.join_date && `${t('contracts.startDate')}: ${job.join_date}`, job.application_deadline && `${t('jobs.deadline')}: ${job.application_deadline}`].filter(Boolean).join(" · ")}
                  </p>
                )}
                {job.requirements && <p style={{ margin: "8px 0 0 0", color: "#475569", fontSize: "12px" }}><strong>Gereksinimler:</strong> {job.requirements}</p>}
                {job.application_status ? (
                  <p style={{ margin: "10px 0 0 0", fontSize: "13px", fontWeight: "700", color: "#15803d" }}>✓ Başvurdunuz ({job.application_status})</p>
                ) : (
                  <button className="primary-button" style={{ padding: "9px 16px", fontSize: "13px", marginTop: "10px" }} onClick={() => portalApplyToJob(job.id)}>
                    Başvur
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  function renderSettings() {
    const inputStyle = { width: "100%", padding: "11px", marginTop: "6px", boxSizing: "border-box" };
    const cardStyle = { background: "#f8fafc", padding: "22px", borderRadius: "12px", border: "1px solid #e2e8f0" };
    const labelStyle = { display: "block", marginBottom: "4px", fontWeight: "bold", color: "#0f172a", fontSize: "13px" };
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('settings.title')}</h2>
            <p>{t('settings.title')}</p>
          </div>
        </div>

        {settingsMsg && (
          <div style={{ padding: "12px 16px", borderRadius: "8px", marginBottom: "16px", fontWeight: "600", fontSize: "13px", background: settingsMsg.type === "success" ? "#f0fdf4" : "#fef2f2", color: settingsMsg.type === "success" ? "#15803d" : "#b91c1c", border: `1px solid ${settingsMsg.type === "success" ? "#bbf7d0" : "#fecaca"}` }}>
            {settingsMsg.text}
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
          {/* HESABIM */}
          <div>
            <h3 style={{ margin: "0 0 12px 0", color: "#0f172a" }}>Hesabım</h3>
            <div style={{ ...cardStyle, marginBottom: "16px" }}>
              <p style={{ margin: "0 0 4px 0", fontSize: "13px", color: "#64748b" }}>{t('auth.loggedInAs')}</p>
              <strong style={{ color: "#0f172a" }}>{auth?.user?.full_name}</strong>
              <span style={{ display: "block", color: "#475569", fontSize: "13px", marginTop: "2px" }}>{auth?.user?.email} · {roleLabel}</span>
            </div>
            <form onSubmit={handleChangeEmail} style={{ ...cardStyle, marginBottom: "16px" }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#0f172a' }}>{t('email.changeEmail')}</h4>
              <div style={{ marginBottom: "12px" }}>
                <label style={labelStyle}>{t('password.current')}</label>
                <input type="password" className="form-input" required style={inputStyle} value={accForm.current_password} onChange={(e) => setAccForm({ ...accForm, current_password: e.target.value })} />
              </div>
              <div style={{ marginBottom: "14px" }}>
                <label style={labelStyle}>{t('email.newEmail')}</label>
                <input type="email" className="form-input" required style={inputStyle} value={accForm.new_email} onChange={(e) => setAccForm({ ...accForm, new_email: e.target.value })} placeholder="yeni@sirket.com" />
              </div>
              <button className="primary-button" type="submit" style={{ width: '100%', padding: '12px' }}>{t('password.update')}</button>
            </form>
            <form onSubmit={handleChangePassword} style={cardStyle}>
              <h4 style={{ margin: '0 0 12px 0', color: '#0f172a' }}>{t('password.change')}</h4>
              <div style={{ marginBottom: "12px" }}>
                <label style={labelStyle}>{t('password.current')}</label>
                <input type="password" className="form-input" required style={inputStyle} value={pwdForm.current_password} onChange={(e) => setPwdForm({ ...pwdForm, current_password: e.target.value })} />
              </div>
              <div style={{ marginBottom: "12px" }}>
                <label style={labelStyle}>{t('password.minLength')}</label>
                <input type="password" className="form-input" required minLength={8} style={inputStyle} value={pwdForm.new_password} onChange={(e) => setPwdForm({ ...pwdForm, new_password: e.target.value })} />
              </div>
              <div style={{ marginBottom: "14px" }}>
                <label style={labelStyle}>{t('password.confirm')}</label>
                <input type="password" className="form-input" required style={inputStyle} value={pwdForm.confirm} onChange={(e) => setPwdForm({ ...pwdForm, confirm: e.target.value })} />
              </div>
              <button className="primary-button" type="submit" style={{ width: '100%', padding: '12px' }}>{t('password.update')}</button>
            </form>
          </div>

          {/* ŞİRKET AYARLARI */}
          <div>
            <h3 style={{ margin: '0 0 12px 0', color: '#0f172a' }}>{t('settings.companyAppearance')}</h3>
            <form onSubmit={saveSettings} style={cardStyle}>
              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>{t('settings.companyNameLabel')}</label>
                <input type="text" className="form-input" value={appSettings.companyName} onChange={(e) => setAppSettings({ ...appSettings, companyName: e.target.value })} placeholder="Örn: KILIÇ DENİZCİLİK" required style={inputStyle} />
              </div>
              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>{t('settings.logoUrlLabel')}</label>
                <input type="url" className="form-input" value={appSettings.logoUrl} onChange={(e) => setAppSettings({ ...appSettings, logoUrl: e.target.value })} placeholder="https://ornek.com/logo.png" style={inputStyle} />
              </div>
              <button type="submit" className="primary-button" style={{ width: "100%", padding: "12px" }}>{t('settings.saveSettings')}</button>
            </form>

          </div>
        </div>

        {isAdmin && (
          <div style={{ marginTop: "28px", background: "#f8fafc", padding: "22px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
            <h3 style={{ margin: "0 0 12px 0", color: "#0f172a" }}>{t('settings.notifications')}</h3>
                <form onSubmit={saveNotifSettings} style={cardStyle}>
                  {notifSettingsMsg && (
                    <p style={{ margin: "0 0 12px 0", padding: "10px 12px", borderRadius: "8px", fontSize: "13px", fontWeight: "600", background: notifSettingsMsg.type === "success" ? "#f0fdf4" : "#fef2f2", color: notifSettingsMsg.type === "success" ? "#15803d" : "#b91c1c" }}>{notifSettingsMsg.text}</p>
                  )}
                  <p style={{ margin: "0 0 12px 0", fontSize: "13px", color: "#64748b" }}>
                    {t('smtp.info')}
                    {t('whatsapp.metaInfo')}
                  </p>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "18px" }}>
                    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "10px", padding: "16px" }}>
                      <h4 style={{ margin: "0 0 12px 0", color: "#0f172a", fontSize: "14px" }}>✉️ {t('settings.emailSettings')}</h4>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px" }}>
                    <div>
                      <label style={labelStyle}>{t('smtp.server')}</label>
                      <input className="form-input" style={inputStyle} placeholder="smtp.sirket.com" value={notifSettings.smtp_host || ""} onChange={(e) => setNotifSettings({ ...notifSettings, smtp_host: e.target.value })} />
                    </div>
                    <div>
                      <label style={labelStyle}>{t('smtp.port')}</label>
                      <input className="form-input" style={inputStyle} placeholder="587" value={notifSettings.smtp_port || ""} onChange={(e) => setNotifSettings({ ...notifSettings, smtp_port: e.target.value })} />
                    </div>
                    <div>
                      <label style={labelStyle}>{t('smtp.user')}</label>
                      <input className="form-input" style={inputStyle} placeholder="bildirim@sirket.com" value={notifSettings.smtp_user || ""} onChange={(e) => setNotifSettings({ ...notifSettings, smtp_user: e.target.value })} />
                    </div>
                    <div>
                      <label style={labelStyle}>{t('smtp.password')}</label>
                      <input type="password" className="form-input" style={inputStyle} placeholder="••••••••" value={notifSettings.smtp_password || ""} onChange={(e) => setNotifSettings({ ...notifSettings, smtp_password: e.target.value })} />
                    </div>
                    <div>
                      <label style={labelStyle}>{t('smtp.senderAddress')}</label>
                      <input className="form-input" style={inputStyle} placeholder="bildirim@sirket.com" value={notifSettings.smtp_from || ""} onChange={(e) => setNotifSettings({ ...notifSettings, smtp_from: e.target.value })} />
                    </div>
                      </div>
                    </div>
                    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "10px", padding: "16px" }}>
                      <h4 style={{ margin: "0 0 12px 0", color: "#0f172a", fontSize: "14px" }}>💬 WhatsApp Business API</h4>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px" }}>
                    <div>
                      <label style={labelStyle}>{t('whatsapp.targetNumber')}</label>
                      <input className="form-input" style={inputStyle} placeholder="+90 5XX XXX XX XX" value={notifSettings.whatsapp_admin_number || ""} onChange={(e) => setNotifSettings({ ...notifSettings, whatsapp_admin_number: e.target.value })} />
                    </div>
                    <div>
                      <label style={labelStyle}>{t('whatsapp.apiToken')}</label>
                      <input type="password" className="form-input" style={inputStyle} placeholder="Meta'dan gelecek" value={notifSettings.whatsapp_api_token || ""} onChange={(e) => setNotifSettings({ ...notifSettings, whatsapp_api_token: e.target.value })} />
                    </div>
                    <div>
                      <label style={labelStyle}>WhatsApp Phone ID</label>
                      <input className="form-input" style={inputStyle} placeholder="Meta'dan gelecek" value={notifSettings.whatsapp_phone_id || ""} onChange={(e) => setNotifSettings({ ...notifSettings, whatsapp_phone_id: e.target.value })} />
                    </div>
                    <div>
                      <label style={labelStyle}>WhatsApp Business Account ID</label>
                      <input className="form-input" style={inputStyle} placeholder="Meta'dan gelecek" value={notifSettings.whatsapp_business_account_id || ""} onChange={(e) => setNotifSettings({ ...notifSettings, whatsapp_business_account_id: e.target.value })} />
                    </div>
                    <div>
                      <label style={labelStyle}>WhatsApp Sender Number</label>
                      <input className="form-input" style={inputStyle} placeholder="+90 5XX XXX XX XX" value={notifSettings.whatsapp_sender_number || ""} onChange={(e) => setNotifSettings({ ...notifSettings, whatsapp_sender_number: e.target.value })} />
                    </div>
                    <div>
                      <label style={labelStyle}>Webhook Verify Token</label>
                      <input type="password" className="form-input" style={inputStyle} placeholder="Meta webhook doğrulama token'ı" value={notifSettings.whatsapp_webhook_verify_token || ""} onChange={(e) => setNotifSettings({ ...notifSettings, whatsapp_webhook_verify_token: e.target.value })} />
                    </div>
                    <div style={{ gridColumn: "1 / -1" }}>
                      <label style={labelStyle}>API Base URL (opsiyonel)</label>
                      <input className="form-input" style={inputStyle} placeholder="https://graph.facebook.com/v21.0" value={notifSettings.whatsapp_api_base_url || ""} onChange={(e) => setNotifSettings({ ...notifSettings, whatsapp_api_base_url: e.target.value })} />
                    </div>
                    <div style={{ gridColumn: "1 / -1" }}>
                      <label style={labelStyle}>Webhook URL (Meta panelinden bu adrese abone olun)</label>
                      <input className="form-input" style={{ ...inputStyle, background: "#f1f5f9", color: "#334155" }} readOnly value={`${window.location.origin}/api/webhooks/whatsapp`} onFocus={(e) => e.target.select()} />
                      </div>
                      </div>
                    </div>
                  </div>
                  <button type="submit" className="primary-button" style={{ marginTop: "14px", width: "100%", padding: "12px" }}>{t('settings.saveSettings')}</button>
                </form>

            </div>
          )}

          {isAdmin && (
            <div style={{ marginTop: "28px", background: "#f8fafc", padding: "22px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
              <h3 style={{ margin: "0 0 12px 0", color: "#0f172a" }}>Kullanıcı Yönetimi</h3>
              <div style={cardStyle}>
                  <div className="table-wrapper" style={{ marginBottom: "14px" }}>
                    <table className="data-table" style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                      <thead>
                        <tr style={{ textAlign: "left", color: "#64748b" }}>
                          <th>{t('settings.userManagement')}</th><th>{t('auth.email')}</th><th>{t('settings.role')}</th><th>{t('crew.title')}</th><th>{t('common.status')}</th><th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((u) => (
                          <tr key={u.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                            <td style={{ padding: "8px 6px", fontWeight: "600", color: "#0f172a" }}>{u.full_name}</td>
                            <td style={{ padding: "8px 6px", color: "#475569" }}>{u.email}</td>
                            <td style={{ padding: "8px 6px" }}>
                              <select className="form-input" style={{ padding: "4px 6px", fontSize: "12px" }} value={u.role} disabled={u.id === auth?.user?.id} onChange={(e) => handleUpdateUser(u, "role", e.target.value)}>
                                <option value="admin">Yönetici</option>
                                <option value="hr">İK Uzmanı</option>
                                <option value="viewer">Görüntüleyici</option>
                                <option value="crew">{t('settings.crew')}</option>
                              </select>
                            </td>
                            <td style={{ padding: "8px 6px" }}>
                              <select className="form-input" style={{ padding: "4px 6px", fontSize: "12px", maxWidth: "170px" }} value={u.crew_member_id ?? ""} onChange={(e) => handleUpdateUser(u, "crew_member_id", e.target.value === "" ? null : Number(e.target.value))}>
                                <option value="">— Bağlı Değil —</option>
                                {crew.map((m) => (
                                  <option key={m.id} value={m.id}>{m.first_name} {m.last_name} (#{m.id})</option>
                                ))}
                              </select>
                            </td>
                            <td style={{ padding: "8px 6px" }}>
                              <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px" }} disabled={u.id === auth?.user?.id} onClick={() => handleUpdateUser(u, "is_active", !u.is_active)}>
                                {u.is_active ? '🟢 ' + t('settings.active') : '🔴 ' + t('settings.inactive')}
                              </button>
                            </td>
                            <td style={{ padding: "8px 6px" }}>
                              {u.id !== auth?.user?.id && (
                                <>
                                  <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px", marginRight: "6px" }} onClick={async () => {
                                    const newPw = window.prompt(`${u.full_name} için yeni şifre (en az 8 karakter):`);
                                    if (!newPw) return;
                                    if (newPw.length < 8) { alert(t('validation.invalidPassword')); return; }
                                    try {
                                      await handleUpdateUser(u, "password", newPw);
                                      alert(t('profile.passwordChanged'));
                                    } catch { alert(t('errors.generic')); }
                                  }} title={t('profile.changePassword')}>{t('auth.password')}</button>
                                  <button className="icon-button" onClick={() => handleDeleteUser(u)} title={t('settings.deleteUser')} style={{ padding: "6px" }}>
                                    <Trash2 size={16} color="#ef4444" />
                                  </button>
                                </>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <form onSubmit={handleCreateUser} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "10px" }}>
                    <input type="text" className="form-input" required placeholder="Ad Soyad" value={newUserForm.full_name} onChange={(e) => setNewUserForm({ ...newUserForm, full_name: e.target.value })} style={{ padding: "10px" }} />
                    <input type="email" className="form-input" required placeholder="email@sirket.com" value={newUserForm.email} onChange={(e) => setNewUserForm({ ...newUserForm, email: e.target.value })} style={{ padding: "10px" }} />
                    <input type="password" className="form-input" required minLength={8} placeholder={t('auth.password')} value={newUserForm.password} onChange={(e) => setNewUserForm({ ...newUserForm, password: e.target.value })} style={{ padding: "10px" }} />
                    <select className="form-input" value={newUserForm.role} onChange={(e) => setNewUserForm({ ...newUserForm, role: e.target.value, crew_member_id: e.target.value === "crew" ? newUserForm.crew_member_id : undefined })} style={{ padding: "10px" }}>
                      <option value="viewer">Görüntüleyici</option>
                      <option value="hr">İK Uzmanı</option>
                      <option value="admin">Yönetici</option>
                      <option value="crew">{t('settings.crew')}</option>
                    </select>
                    {newUserForm.role === "crew" && (
                      <select className="form-input" required value={newUserForm.crew_member_id ?? ""} onChange={(e) => setNewUserForm({ ...newUserForm, crew_member_id: Number(e.target.value) })} style={{ padding: "10px" }}>
                        <option value="" disabled>— {t('crew.title')} —</option>
                        {crew.map((m) => (
                          <option key={m.id} value={m.id}>{m.first_name} {m.last_name} (#{m.id})</option>
                        ))}
                      </select>
                    )}
                    <button className="primary-button" type="submit" style={{ padding: "10px" }}>{t('settings.addUser')}</button>
                </form>
              </div>
            </div>
          )}
      </section>
    );
  }

  // ── Phase 4B: operasyon merkezi / bildirim / uygunluk / kadro ────────────
  async function loadOpsSummary() {
    try {
      const response = await axios.get(`${API_URL}/api/dashboard/summary`);
      setOpsSummary(response.data);
    } catch (e) { console.error("Özet yüklenemedi:", e); }
  }

  async function loadNotifications() {
    try {
      const response = await axios.get(`${API_URL}/api/notifications/?unread_only=false`);
      setNotifications(response.data);
    } catch (e) { console.error("Bildirimler yüklenemedi:", e); }
  }

  async function markNotificationRead(id) {
    try {
      await axios.post(`${API_URL}/api/notifications/${id}/read`);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    } catch (e) { /* yok say */ }
  }

  async function runEligibility(e) {
    e.preventDefault();
    if (!eligibilityQuery.position.trim()) return;
    setEligibilityLoading(true);
    try {
      const params = new URLSearchParams({ position: eligibilityQuery.position, min_score: eligibilityQuery.min_score, limit: 25 });
      const response = await axios.get(`${API_URL}/api/crew/eligible?${params.toString()}`);
      setEligibilityResults(response.data);
    } catch (err) {
      setEligibilityResults([]);
    } finally {
      setEligibilityLoading(false);
    }
  }

  async function loadShipStaffing(shipId) {
    setStaffingLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/ships/${shipId}/staffing`);
      setShipStaffing(response.data);
    } catch (e) { setShipStaffing([]); } finally { setStaffingLoading(false); }
  }

  async function handleAddPosition(e) {
    e.preventDefault();
    if (!selectedShipId || !positionForm.position.trim()) return;
    try {
      await axios.post(`${API_URL}/api/ships/${selectedShipId}/positions`, {
        position: positionForm.position.trim(),
        required_count: Number(positionForm.required_count) || 1,
      });
      setPositionForm({ position: "", required_count: 1 });
      await loadShipStaffing(selectedShipId);
      await loadOpsSummary();
    } catch (err) {
      alert(t('errors.generic'));
    }
  }

  async function handleDeletePosition(positionId) {
    if (!window.confirm(t('common.confirm'))) return;
    try {
      await axios.delete(`${API_URL}/api/ships/positions/${positionId}`);
      await loadShipStaffing(selectedShipId);
      await loadOpsSummary();
    } catch (err) { alert(t('errors.generic')); }
  }

  async function showCandidates(position) {
    try {
      const params = new URLSearchParams({ position, min_score: 50, limit: 10 });
      if (selectedShipId) params.append("ship_id", selectedShipId);
      const response = await axios.get(`${API_URL}/api/crew/eligible?${params.toString()}`);
      setCandidatesFor({ position, results: response.data });
    } catch (err) {
      setCandidatesFor({ position, results: [] });
    }
  }

  async function handleCsvPreview() {
    setImportMsg(null);
    if (!importCsvText.trim()) { setImportMsg({ type: "error", text: "CSV içeriği boş." }); return; }
    try {
      const response = await axios.post(`${API_URL}/api/crew/import/preview`, { content: importCsvText });
      setImportPreview(response.data);
    } catch (err) {
      setImportMsg({ type: "error", text: err.response?.data?.detail || "CSV analiz edilemedi." });
    }
  }

  async function confirmImport() {
    setImportMsg(null);
    if (!importPreview) return;
    try {
      const response = await axios.post(`${API_URL}/api/crew/import/confirm`, { rows: importPreview.rows });
      setImportMsg({ type: "success", text: `${response.data.created} personel içe aktarıldı.` });
      setImportPreview(null);
      setImportCsvText("");
      await loadData();
    } catch (err) {
      setImportMsg({ type: "error", text: err.response?.data?.detail || "İçe aktarma başarısız." });
    }
  }

  function exportCsv() {
    window.open(`${API_URL}/api/crew/export`, "_blank");
  }

  async function approveDocument(doc) {
    try {
      await axios.post(`${API_URL}/api/documents/${doc.id}/approve`);
      await loadDocuments();
      if (reviewOpen) loadReviewQueue();
    } catch (err) { alert(t('errors.generic')); }
  }

  async function rejectDocument(doc) {
    try {
      await axios.post(`${API_URL}/api/documents/${doc.id}/reject`);
      await loadDocuments();
      if (reviewOpen) loadReviewQueue();
    } catch (err) { alert(t('errors.generic')); }
  }

  function renderPage() {
    if (auth?.user?.role === "crew") return <RenderPortal />;
    if (activePage === "crew") return renderCrewList();
    if (activePage === "ships") return renderShips();
    if (activePage === "assignments") return renderAssignments();
    if (activePage === "contracts") return renderContracts();
    if (activePage === "documents") return renderDocumentsList();
    if (activePage === "eligibility") return renderEligibility();
    if (activePage === "jobs") return renderJobs();
    if (activePage === "communication") return renderCommunication();
    if (activePage === "crew-detail") return renderCrewDetail();
    if (activePage === "ship-detail") return renderShipDetail();
    if (activePage === "settings") return renderSettings();

    // ==========================================
    // DASHBOARD EKRANI
    // ==========================================
    const pendingCount = allDocuments.filter(d => d.match_status === "pending").length;

    return (
      <>
        {/* YENİ: TURUNCU HOŞ GELDİNİZ KUTUSU */}
        <div className="welcome" style={{
          background: 'linear-gradient(135deg, #ea580c 0%, #c2410c 100%)', 
          color: 'white', 
          padding: '30px', 
          borderRadius: '12px', 
          marginBottom: '20px', 
          boxShadow: '0 10px 15px -3px rgba(234, 88, 12, 0.3)'
        }}>
          <div>
            <h2 style={{fontSize: "28px", color: "white", margin: "0 0 10px 0"}}>{t('dashboard.welcome', { name: auth?.full_name || '' })}</h2>
            <p style={{fontSize: "16px", color: "#ffedd5", margin: 0}}>{t('dashboard.welcome', { name: '' })}</p>
          </div>
        </div>
        
        {/* YENİ: ÖNCELİK 2 - EŞLEŞTİRME BEKLEYEN BELGELER UYARISI */}
        {pendingCount > 0 && (
          <div className="pulse-soft" style={{ background: "#fffbeb", borderLeft: "6px solid #f59e0b", padding: "20px", marginBottom: "20px", borderRadius: "12px", display: "flex", justifyContent: "space-between", alignItems: "center", boxShadow: "0 4px 6px rgba(0,0,0,0.05)", flexWrap: "wrap", gap: "10px" }}>
            <div>
              <h3 style={{ margin: "0 0 8px 0", color: "#b45309", display: "flex", alignItems: "center", gap: "8px", fontSize: "18px" }}>
                <AlertCircle size={24} /> {pendingCount} {t('documents.reviewRequired')}
              </h3>
              <p style={{ margin: 0, color: "#92400e", fontWeight: "500" }}>{t('documents.reviewRequired')}</p>
            </div>
            {canWrite && (
              <button className="primary-button" onClick={() => setMatchingModalOpen(true)} style={{ background: "#ea580c", border: "none" }}>{t('documents.reviewRequired')}</button>
            )}
          </div>
        )}

        <div className="cards">
          <div className="card">
            <div className="card-icon" style={{background: "#e0f2fe", color: "#0284c7"}}><Users size={28} /></div>
            <div><span>{t('dashboard.totalCrew')}</span><strong style={{fontSize:"24px", color:"#0f172a"}}>{totalCrewStats.total}</strong></div>
          </div>
          <div className="card">
            <div className="card-icon" style={{background: "#e0f2fe", color: "#0284c7"}}><Ship size={28} /></div>
            <div><span>{t('dashboard.vessels')}</span><strong style={{fontSize:"24px", color:"#0f172a"}}>{ships.length} / {ships.filter(s=>s.status==="active").length}</strong></div>
          </div>
          <div className="card">
            <div className="card-icon" style={{background: "#e0f2fe", color: "#0284c7"}}><Activity size={28} /></div>
            <div><span>{t('dashboard.activeCrew')}</span><strong style={{fontSize:"24px", color:"#0f172a"}}>{totalCrewStats.active}</strong></div>
          </div>
        </div>
        
        {expirySummary !== null && (
          <>
            <p className="section-label" style={{marginTop: "30px"}}>{t('documents.expiryFilter')}</p>
            <div className="cards">
              <div className="card" style={{cursor: "pointer", border: "1px solid #fecaca"}} onClick={() => openDocCategoryModal("expired")}>
                <div className="card-icon danger pulse-soft"><FileText size={28} /></div>
                <div><span style={{color:"#dc2626", fontWeight:"bold"}}>{t('documents.expired')}</span><strong style={{color:"#b91c1c", fontSize:"26px"}}>{expirySummary.expired}</strong></div>
              </div>
              <div className="card" style={{cursor: "pointer", border: "1px solid #fed7aa"}} onClick={() => openDocCategoryModal("urgent")}>
                <div className="card-icon warning pulse-soft"><FileText size={28} /></div>
                <div><span style={{color:"#ea580c", fontWeight:"bold"}}>{t('documents.urgent')} (≤30)</span><strong style={{color:"#c2410c", fontSize:"26px"}}>{expirySummary.urgent}</strong></div>
              </div>
              <div className="card" style={{cursor: "pointer", border: "1px solid #fef08a"}} onClick={() => openDocCategoryModal("approaching")}>
                <div className="card-icon purple"><FileText size={28} /></div>
                <div><span style={{color:"#ca8a04", fontWeight:"bold"}}>{t('documents.approaching')} (≤90)</span><strong style={{color:"#a16207", fontSize:"26px"}}>{expirySummary.approaching}</strong></div>
              </div>
              <div className="card" style={{cursor: "pointer", border: "1px solid #bbf7d0"}} onClick={() => openDocCategoryModal("valid")}>
                <div className="card-icon success"><FileText size={28} /></div>
                <div><span style={{color:"#16a34a", fontWeight:"bold"}}>{t('documents.valid')}</span><strong style={{color:"#15803d", fontSize:"26px"}}>{expirySummary.valid}</strong></div>
              </div>
            </div>
          </>
        )}

        {opsSummary && (
          <div style={{ marginTop: "30px" }}>
            <div className="panel" style={{ borderLeft: "6px solid #0284c7", padding: "22px" }}>
              <div className="panel-header" style={{ marginBottom: "16px" }}>
                <div>
                  <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#0f172a' }}><Anchor size={24} color='#0284c7' /> {t('dashboard.operationsCenter')}</h2>
                  <p>{t('dashboard.todaysTasks')}</p>
                </div>
              </div>

              <div className="cards" style={{ marginBottom: "18px" }}>
                <div className="card" style={{ cursor: "pointer", border: "1px solid #e2e8f0" }} onClick={() => { setContractsFilter("ending_7"); navigate("contracts"); }} title={t('contracts.ending7Days')}>
                  <div className="card-icon warning"><FileText size={28} /></div>
                  <div><span>{t('contracts.ending7Days')}</span><strong style={{ color: opsSummary.contracts.ending_7_days > 0 ? "#c2410c" : "#15803d" }}>{opsSummary.contracts.ending_7_days}</strong><span style={{ color: "#0284c7", fontWeight: "700", fontSize: "12px" }}>{t('common.view')} →</span></div>
                </div>
                <div className="card" style={{ cursor: "pointer", border: "1px solid #e2e8f0" }} onClick={() => { setContractsFilter("ending_30"); navigate("contracts"); }} title={t('contracts.ending30Days')}>
                  <div className="card-icon purple"><FileText size={28} /></div>
                  <div><span>{t('contracts.ending30Days')}</span><strong style={{ color: opsSummary.contracts.ending_30_days > 0 ? "#b45309" : "#15803d" }}>{opsSummary.contracts.ending_30_days}</strong><span style={{ color: "#0284c7", fontWeight: "700", fontSize: "12px" }}>{t('common.view')} →</span></div>
                </div>
                <div className="card" style={{ cursor: "pointer", border: "1px solid #e2e8f0" }} onClick={() => navigate("ships")} title={t('vesselStaff.title')}>
                  <div className="card-icon" style={{ background: "#fef2f2", color: "#b91c1c" }}><AlertCircle size={28} /></div>
                  <div><span>{t('dashboard.openPositions')}</span><strong style={{ color: opsSummary.ships.open_positions_total > 0 ? '#b91c1c' : '#15803d' }}>{opsSummary.ships.open_positions_total}</strong><span style={{ color: '#0284c7', fontWeight: '700', fontSize: '12px' }}>{t('common.view')} →</span></div>
                </div>
                <div className="card" style={{ cursor: "pointer", border: "1px solid #e2e8f0" }} onClick={() => { const f = { document_type: "", match_status: "pending_approval", expiry_status: "" }; setDocFilters(f); navigate("documents"); loadDocuments(f); }} title={t('documents.reviewRequired')}>
                  <div className="card-icon" style={{ background: "#fff7ed", color: "#ea580c" }}><ClipboardList size={28} /></div>
                  <div><span>{t('dashboard.pendingReview')}</span><strong style={{ color: opsSummary.documents.pending_review > 0 ? '#ea580c' : '#15803d' }}>{opsSummary.documents.pending_review}</strong><span style={{ color: '#0284c7', fontWeight: '700', fontSize: '12px' }}>{t('common.view')} →</span></div>
                </div>
                <div className="card" style={{ cursor: "pointer", border: "1px solid #e2e8f0" }} onClick={() => { setCrewFilters({ ...emptyFilters, availability: "available" }); navigate("crew"); loadFilteredCrew({ ...emptyFilters, availability: "available" }); }} title={t('crew.available')}>
                  <div className="card-icon success"><Users size={28} /></div>
                  <div><span>{t('crew.available')}</span><strong style={{ color: "#0f172a" }}>{opsSummary.availability.available}</strong><span style={{ color: "#0284c7", fontWeight: "700", fontSize: "12px" }}>{t('common.view')} →</span></div>
                </div>
                {/* Yeni: Süresi Dolmuş Belgeler */}
                <div className="card" style={{ cursor: "pointer", border: "1px solid #fecaca" }} onClick={() => openDocCategoryModal("expired")} title={t('documents.expired')}>
                  <div className="card-icon danger pulse-soft"><FileText size={28} /></div>
                  <div><span>{t('documents.expired')}</span><strong style={{ color: opsSummary.documents.expired > 0 ? '#b91c1c' : '#15803d' }}>{opsSummary.documents.expired}</strong><span style={{ color: '#0284c7', fontWeight: '700', fontSize: '12px' }}>{t('common.view')} →</span></div>
                </div>
                {/* Yeni: Acil Belgeler (≤30) */}
                <div className="card" style={{ cursor: "pointer", border: "1px solid #fed7aa" }} onClick={() => openDocCategoryModal("urgent")} title={t('documents.urgent')}>
                  <div className="card-icon warning pulse-soft"><Clock size={28} /></div>
                  <div><span>{t('documents.urgent')} (≤30)</span><strong style={{ color: opsSummary.documents.urgent > 0 ? '#c2410c' : '#15803d' }}>{opsSummary.documents.urgent}</strong><span style={{ color: '#0284c7', fontWeight: '700', fontSize: '12px' }}>{t('common.view')} →</span></div>
                </div>
                {/* Yeni: Yaklaşıyor (≤90) */}
                <div className="card" style={{ cursor: "pointer", border: "1px solid #fef08a" }} onClick={() => openDocCategoryModal("approaching")} title={t('documents.approaching')}>
                  <div className="card-icon purple"><Clock size={28} /></div>
                  <div><span>{t('documents.approaching')} (≤90)</span><strong style={{ color: opsSummary.documents.approaching > 0 ? '#a16207' : '#15803d' }}>{opsSummary.documents.approaching}</strong><span style={{ color: '#0284c7', fontWeight: '700', fontSize: '12px' }}>{t('common.view')} →</span></div>
                </div>
              </div>

              {opsSummary.tasks.length > 0 && (
                <div style={{ marginBottom: "20px" }}>
                  <p className="section-label">{t('dashboard.todaysTasks')}</p>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {opsSummary.tasks.map((task, i) => (
                      <button key={i} onClick={() => {
                        if (task.crew_id && (task.type === 'document' || task.type === 'contract')) {
                          openCrewDetail(task.crew_id);
                        } else if (task.link.startsWith('/ship-detail')) {
                          const id = task.link.split('/').pop();
                          const ship = ships.find((s) => String(s.id) === id);
                          setSelectedShip(ship || null);
                          setSelectedShipId(Number(id));
                          setActivePage('ship-detail');
                        } else if (task.link === '/documents') {
                          setActivePage('documents');
                        } else if (task.link === '/contracts') {
                          setActivePage('contracts');
                        }
                      }} style={{ display: 'flex', alignItems: 'center', gap: '10px', textAlign: 'left', width: '100%', padding: '12px 14px', borderRadius: '10px', border: '1px solid #e2e8f0', background: task.priority === 'red' ? '#fef2f2' : task.priority === 'orange' ? '#fff7ed' : '#f8fafc', cursor: 'pointer', fontSize: '14px', color: '#0f172a' }}>
                        <span style={{ fontSize: '16px' }}>{task.priority === 'red' ? '🔴' : task.priority === 'orange' ? '🟠' : '🟡'}</span>
                        <span style={{ flex: 1 }}>{translateTaskText(task.text)}</span>
                        <span style={{ color: '#0284c7', fontWeight: '700' }}>{t('common.view')} →</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {opsSummary.ship_status.filter((s) => s.positions.length > 0).length > 0 && (
                <div>
                  <p className="section-label">{t('vesselStaff.title')}</p>
                  <div className="table-wrapper">
                    <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
                      <thead>
                        <tr style={{ textAlign: "left", color: "#64748b" }}>
                          <th>{t('vessels.title')}</th><th>{t('crew.position')}</th><th>{t('common.count')}</th><th>{t('common.active')}</th><th>{t('common.pending')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {opsSummary.ship_status.flatMap((s) => s.positions.map((p) => ({ ship: s.name, ...p }))).map((r, i) => (
                          <tr key={i} style={{ borderTop: "1px solid #e2e8f0" }}>
                            <td style={{ padding: "9px 8px", fontWeight: "600", color: "#0f172a" }}>{r.ship}</td>
                            <td style={{ padding: '9px 8px', color: '#475569' }}>{translatePosition(r.position)}</td>
                            <td style={{ padding: '9px 8px', textAlign: 'center' }}>{r.required}</td>
                            <td style={{ padding: "9px 8px", textAlign: "center" }}>{r.filled}</td>
                            <td style={{ padding: "9px 8px", textAlign: "center" }}>{r.open > 0 ? <strong style={{ color: "#b91c1c" }}>🔴 {r.open}</strong> : <span style={{ color: "#15803d" }}>✅</span>}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </>
    );
  }

  const navigation = [
    ["dashboard", LayoutDashboard, t('nav.dashboard')], 
    ["crew", Users, t('nav.crew')], 
    ["ships", Ship, t('nav.vessels')], 
    ["assignments", ClipboardList, t('nav.vesselStaff')], 
    ["contracts", FileText, t('nav.contracts')], 
    ["documents", Folder, t('nav.documents')],
    ["eligibility", Target, t('crew.eligibility')],
    ["jobs", Briefcase, t('nav.jobs')],
    ["communication", MessageCircle, t('messages.title')],
    ["settings", Settings, t('nav.settings')]
  ];

  // ==========================================
  // GİRİŞ EKRANI (OTURUM YOKSA)
  // ==========================================
  if (!auth) {
    return (
      <div className="app" style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", position: "relative", overflow: "hidden", animation: "skyShift 40s ease-in-out infinite" }}>
        {/* ═══ GÖKYÜZÜ + ATMOSFER ═══ */}
        <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }}>
          {/* Yıldızlar — büyük ve küçük, farklı parlaklık */}
          {[...Array(28)].map((_, i) => {
            const isBig = i % 5 === 0;
            return (
              <div key={`star-${i}`} style={{
                position: "absolute",
                width: isBig ? 3 : 1.5,
                height: isBig ? 3 : 1.5,
                background: isBig ? '#e8e8f0' : '#ffffff',
                borderRadius: "50%",
                top: `${3 + (i * 3.7) % 42}%`,
                left: `${2 + (i * 11.3) % 96}%`,
                animation: `${isBig ? 'twinkleBright' : 'twinkle'} ${2 + (i % 4)}s ease-in-out infinite ${(i * 0.4)}s`,
                opacity: 0.6,
              }} />
            );
          })}

          {/* Güneş — gün içinde belirip kaybolur */}
          <div style={{
            position: "absolute", top: "12%", left: "15%",
            width: 60, height: 60, borderRadius: "50%",
            background: "radial-gradient(circle, #fcd34d 0%, #f59e0b 40%, #d97706 70%, transparent 100%)",
            animation: "sunCycle 30s ease-in-out infinite",
            boxShadow: "0 0 60px rgba(252,211,77,0.4), 0 0 120px rgba(245,158,11,0.2)",
          }} />
          {/* Güneş ışınları */}
          <div style={{
            position: "absolute", top: "10%", left: "13%",
            width: 80, height: 80, borderRadius: "50%",
            border: "1px solid rgba(252,211,77,0.15)",
            animation: "sunRays 30s ease-in-out infinite",
          }} />

          {/* Ay */}
          <div style={{
            position: "absolute", top: "6%", right: "10%",
            width: 55, height: 55, borderRadius: "50%",
            background: "radial-gradient(circle at 35% 35%, #fff 0%, #e8e8ed 30%, #d1d1d6 60%, #aeaeb2 100%)",
            boxShadow: "0 0 50px rgba(255,255,255,0.25), 0 0 100px rgba(255,255,255,0.1)",
            animation: "moonGlow 8s ease-in-out infinite",
          }} />

          {/* Bulutlar — farklı hız ve boyutta */}
          {[
            { top: '8%', dur: '35s', delay: '0s', w: 60, o: 0.5 },
            { top: '14%', dur: '45s', delay: '10s', w: 45, o: 0.35 },
            { top: '5%', dur: '55s', delay: '20s', w: 70, o: 0.4 },
            { top: '18%', dur: '40s', delay: '5s', w: 35, o: 0.3 },
            { top: '11%', dur: '50s', delay: '15s', w: 55, o: 0.25 },
          ].map((c, i) => (
            <div key={`cloud-${i}`} style={{
              position: "absolute", top: c.top, left: 0,
              width: c.w, height: c.w * 0.35,
              background: `rgba(255,255,255,${c.o})`,
              borderRadius: '20px',
              animation: `${i % 2 === 0 ? 'cloudDrift' : 'cloudDriftSlow'} ${c.dur} linear ${c.delay} infinite`,
            }}>
              <div style={{ position: 'absolute', width: c.w * 0.4, height: c.w * 0.4, background: `rgba(255,255,255,${c.o})`, borderRadius: '50%', top: -c.w * 0.2, left: c.w * 0.2 }} />
              <div style={{ position: 'absolute', width: c.w * 0.3, height: c.w * 0.3, background: `rgba(255,255,255,${c.o})`, borderRadius: '50%', top: -c.w * 0.12, right: c.w * 0.15 }} />
            </div>
          ))}

          {/* Yağmur damlaları — zaman zaman yağmur yağar */}
          {[...Array(20)].map((_, i) => (
            <div key={`rain-${i}`} style={{
              position: "absolute", left: `${(i * 5.3) % 100}%`,
              width: 1.5, height: 14,
              background: 'linear-gradient(to bottom, rgba(148,163,184,0.6), rgba(148,163,184,0.1))',
              borderRadius: '2px',
              animation: `rainFall ${0.8 + (i % 4) * 0.15}s linear ${(i * 0.3)}s infinite`,
              opacity: 0.4,
            }} />
          ))}

          {/* Kuş sürüsü — zaman zaman geçer */}
          {[0, 1, 2].map((i) => (
            <div key={`bird-${i}`} style={{
              position: "absolute", top: `${12 + i * 4}%`, left: 0,
              animation: `birdFly ${18 + i * 4}s linear ${i * 6}s infinite`,
              opacity: 0.5,
            }}>
              <svg width="20" height="10" viewBox="0 0 20 10" style={{ animation: `wingFlap 0.6s ease-in-out infinite ${i * 0.2}s` }}>
                <path d="M0,8 Q5,2 10,5 Q15,2 20,8" fill="none" stroke="rgba(200,200,210,0.7)" strokeWidth="1.5"/>
              </svg>
            </div>
          ))}

          {/* ═══ DENİZ ALANI — gökyüzünden net ayrışmış ═══ */}
          {/* Su çizgisi: %60 yukarıdan */}
          <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "42%", background: "linear-gradient(180deg, rgba(10,30,60,0.7) 0%, rgba(8,22,45,0.85) 30%, rgba(5,15,35,0.95) 100%)" }} />

          {/* Dalga katmanları — doğal hareket */}
          <svg style={{ position: "absolute", bottom: 0, left: 0, width: "200%", height: "42%" }} viewBox="0 0 2880 400" preserveAspectRatio="none">
            {/* Arka dalga — koyu mavi */}
            <path fill="rgba(12,28,55,0.5)" d="M0,120 Q180,80 360,120 T720,120 T1080,100 T1440,120 T1800,110 T2160,120 T2520,100 T2880,120 L2880,400 L0,400Z">
              <animateTransform attributeName="transform" type="translate" values="0,0; -720,0; 0,0" dur="18s" repeatCount="indefinite"/>
            </path>
            {/* Orta dalga — orta mavi */}
            <path fill="rgba(15,35,65,0.4)" d="M0,160 Q240,120 480,160 T960,150 T1440,160 T1920,140 T2400,160 T2880,155 L2880,400 L0,400Z">
              <animateTransform attributeName="transform" type="translate" values="0,0; -480,0; 0,0" dur="14s" repeatCount="indefinite"/>
            </path>
            {/* Ön dalga — en koyu */}
            <path fill="rgba(8,20,42,0.6)" d="M0,200 Q200,170 400,200 T800,190 T1200,200 T1600,185 T2000,200 T2400,195 T2880,200 L2880,400 L0,400Z">
              <animateTransform attributeName="transform" type="translate" values="0,0; -600,0; 0,0" dur="22s" repeatCount="indefinite"/>
            </path>
            {/* Köpük/dalga ucu */}
            <path fill="rgba(30,60,100,0.2)" d="M0,230 Q300,210 600,230 T1200,225 T1800,230 T2400,220 T2880,230 L2880,400 L0,400Z">
              <animateTransform attributeName="transform" type="translate" values="0,0; -500,0; 0,0" dur="26s" repeatCount="indefinite"/>
            </path>
          </svg>

          {/* ═══ DENİZ FENERİ — sahilde, ışık saçar ═══ */}
          <div style={{ position: "absolute", bottom: "40%", left: "6%" }}>
            {/* Fener kulesi */}
            <svg width="30" height="80" viewBox="0 0 30 80">
              <rect x="11" y="20" width="8" height="60" fill="#475569" rx="2"/>
              <rect x="8" y="15" width="14" height="12" fill="#64748b" rx="3"/>
              <circle cx="15" cy="12" r="6" fill="#fbbf24" style={{ animation: 'lighthousePulse 3s ease-in-out infinite' }} />
            </svg>
            {/* Dönen ışık huzmesi */}
            <div style={{ position: "absolute", top: "8px", left: "8px", width: 0, height: 0, transformOrigin: '7px 4px', animation: 'lighthouseBeam 4s linear infinite' }}>
              <div style={{ position: "absolute", width: 120, height: 2, background: "linear-gradient(90deg, rgba(251,191,36,0.6), transparent)", transformOrigin: "0 50%" }} />
            </div>
          </div>

          {/* ═══ GEMİLER — Farklı tür ve boyutlarda ═══ */}
          {/* Gemi 1 — Büyük Konteyner Gemisi (sola doğru) */}
          <div style={{ position: "absolute", bottom: "30%", animation: "shipSailLarge 40s linear infinite" }}>
            <div style={{ animation: "shipBob 4s ease-in-out infinite" }}>
              <svg width="220" height="70" viewBox="0 0 220 70">
                {/* Gövde */}
                <path d="M10,45 L30,55 L190,55 L210,45 L200,35 L20,35Z" fill="#1e3a5f" stroke="#2a5580" strokeWidth="0.5"/>
                {/* Güverte */}
                <rect x="25" y="28" width="170" height="8" fill="#234b6d" rx="2"/>
                {/* Köprü */}
                <rect x="170" y="8" width="25" height="22" fill="#2d5a80" rx="2"/>
                <rect x="173" y="5" width="19" height="6" fill="#3a6d94" rx="1"/>
                {/* Konteynerler */}
                <rect x="40" y="18" width="18" height="12" fill="#c2410c" rx="1"/>
                <rect x="60" y="18" width="18" height="12" fill="#1d4ed8" rx="1"/>
                <rect x="80" y="18" width="18" height="12" fill="#15803d" rx="1"/>
                <rect x="100" y="18" width="18" height="12" fill="#c2410c" rx="1"/>
                <rect x="120" y="18" width="18" height="12" fill="#1d4ed8" rx="1"/>
                <rect x="40" y="8" width="18" height="10" fill="#15803d" rx="1"/>
                <rect x="60" y="8" width="18" height="10" fill="#c2410c" rx="1"/>
                <rect x="80" y="8" width="18" height="10" fill="#1d4ed8" rx="1"/>
                <rect x="100" y="8" width="18" height="10" fill="#15803d" rx="1"/>
                {/* Pencere ışıkları */}
                {[173, 178, 183, 188].map((x, i) => (
                  <rect key={i} x={x} y="13" width="3" height="3" fill="#fbbf24" opacity="0.8" style={{ animation: `windowFlicker ${3 + i * 0.5}s ease-in-out infinite` }} />
                ))}
                {/* BUTON */}
                <circle cx="208" cy="22" r="2" fill="#ef4444" opacity="0.9"/>
              </svg>
            </div>
          </div>

          {/* Gemi 2 — Tanker (sağa doğru, daha yavaş) */}
          <div style={{ position: "absolute", bottom: "34%", animation: "shipSailMed 50s linear infinite 12s" }}>
            <div style={{ animation: "shipBob 5s ease-in-out infinite 0.5s" }}>
              <svg width="190" height="55" viewBox="0 0 190 55">
                {/* Gövde */}
                <path d="M5,35 L20,42 L170,42 L185,35 L175,28 L15,28Z" fill="#2a3a4f" stroke="#3a5060" strokeWidth="0.5"/>
                {/* Güverte */}
                <rect x="18" y="22" width="155" height="7" fill="#334860" rx="1"/>
                {/* Tank kubbeleri */}
                <ellipse cx="55" cy="20" rx="20" ry="5" fill="#3d5570"/>
                <ellipse cx="100" cy="20" rx="20" ry="5" fill="#3d5570"/>
                <ellipse cx="145" cy="20" rx="15" ry="4" fill="#3d5570"/>
                {/* Köprü */}
                <rect x="5" y="12" width="15" height="18" fill="#4a6070" rx="2"/>
                <rect x="3" y="8" width="19" height="6" fill="#557080" rx="1"/>
                {/* Pencere ışıkları */}
                <rect x="7" y="14" width="3" height="2.5" fill="#fbbf24" opacity="0.7" style={{ animation: 'windowFlicker 4s ease-in-out infinite' }} />
                <rect x="13" y="14" width="3" height="2.5" fill="#fbbf24" opacity="0.7" style={{ animation: 'windowFlicker 3.5s ease-in-out infinite 0.5s' }} />
              </svg>
            </div>
          </div>

          {/* Gemi 3 — Yolcu Gemisi (soldan sağa) */}
          <div style={{ position: "absolute", bottom: "32%", animation: "shipSailSmall 55s linear infinite 20s" }}>
            <div style={{ animation: "shipSway 6s ease-in-out infinite" }}>
              <svg width="160" height="60" viewBox="0 0 160 60">
                {/* Gövde */}
                <path d="M5,38 L15,44 L145,44 L155,38 L148,30 L12,30Z" fill="#f0f0f0" stroke="#d0d0d0" strokeWidth="0.5"/>
                {/* Güverte katları */}
                <rect x="18" y="22" width="125" height="9" fill="#e8e8e8" rx="2"/>
                <rect x="25" y="15" width="110" height="8" fill="#f5f5f5" rx="2"/>
                <rect x="32" y="9" width="95" height="7" fill="#fafafa" rx="2"/>
                {/* Bacalar */}
                <rect x="45" y="3" width="8" height="8" fill="#c2410c" rx="1"/>
                <rect x="60" y="3" width="8" height="8" fill="#c2410c" rx="1"/>
                {/* Pencereler — çok katlı */}
                {[20,28,36,44,52,60,68,76,84,92,100,108,116,124,132].map((x, i) => (
                  <rect key={i} x={x} y="24" width="4" height="3" fill="#93c5fd" opacity="0.6" rx="0.5" style={{ animation: `windowFlicker ${2.5 + (i % 4) * 0.3}s ease-in-out infinite ${i * 0.2}s` }} />
                ))}
                {/* Köprü */}
                <rect x="130" y="10" width="18" height="12" fill="#e0e0e0" rx="2"/>
                <rect x="133" y="13" width="4" height="3" fill="#93c5fd" opacity="0.7" rx="0.5"/>
              </svg>
            </div>
          </div>

          {/* Gemi 4 — Küçük Kargo/Tahta gemi (yavaş, uzakta) */}
          <div style={{ position: "absolute", bottom: "37%", animation: "shipSailSlow 65s linear infinite 5s" }}>
            <div style={{ animation: "shipBob 7s ease-in-out infinite 1s" }}>
              <svg width="80" height="35" viewBox="0 0 80 35" opacity="0.6">
                <path d="M5,22 L12,27 L68,27 L75,22 L70,18 L10,18Z" fill="#5a4a3a" stroke="#6a5a4a" strokeWidth="0.5"/>
                <rect x="12" y="14" width="55" height="5" fill="#6a5a4a" rx="1"/>
                <rect x="8" y="6" width="12" height="10" fill="#7a6a5a" rx="1"/>
                {/* Dümen */}
                <line x1="72" y1="15" x2="78" y2="10" stroke="#8a7a6a" strokeWidth="1"/>
              </svg>
            </div>
          </div>

          {/* Gemi 5 — Römorkör (yakın, küçük) */}
          <div style={{ position: "absolute", bottom: "29%", animation: "shipSailLarge 30s linear infinite 18s" }}>
            <div style={{ animation: "shipBob 3s ease-in-out infinite 0.3s" }}>
              <svg width="50" height="28" viewBox="0 0 50 28">
                <path d="M3,16 L8,20 L42,20 L47,16 L43,12 L7,12Z" fill="#4a4a4a" stroke="#5a5a5a" strokeWidth="0.5"/>
                <rect x="10" y="8" width="15" height="6" fill="#5a5a5a" rx="2"/>
                <rect x="28" y="6" width="12" height="4" fill="#6a6a6a" rx="1"/>
                {/* Işık */}
                <circle cx="46" cy="10" r="2" fill="#fbbf24" opacity="0.8" style={{ animation: 'windowFlicker 2s ease-in-out infinite' }} />
              </svg>
            </div>
          </div>

          {/* Uzaktaki kıyı/siluet */}
          <svg style={{ position: "absolute", bottom: "40%", left: 0, width: "100%", height: "8%" }} viewBox="0 0 1200 60" preserveAspectRatio="none">
            <path d="M0,60 L0,35 Q100,15 200,30 Q300,10 400,25 Q500,5 600,20 Q700,8 800,22 Q900,12 1000,28 Q1100,18 1200,32 L1200,60Z" fill="rgba(8,18,38,0.5)" />
          </svg>
        </div>
        {/* Login Formu */}
        <div className="panel" style={{ width: "420px", maxWidth: "92%", padding: "40px", borderRadius: "16px", background: "rgba(255,255,255,0.95)", backdropFilter: "blur(20px)", boxShadow: "0 25px 50px -12px rgba(0,0,0,0.5)", zIndex: 10 }}>
          <div style={{ textAlign: "center", marginBottom: "28px" }}>
            <div style={{ width: 56, height: 56, background: "linear-gradient(135deg, #ea580c 0%, #c2410c 100%)", borderRadius: 14, display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: 14, boxShadow: "0 4px 15px rgba(234,88,12,0.3)" }}>
              <span style={{ fontSize: 28 }}>⚓</span>
            </div>
            <h1 style={{ fontSize: "24px", fontWeight: "900", margin: "0 0 6px 0", color: "#0f172a", letterSpacing: "1px" }}>
              {appSettings.companyName}
            </h1>
            <p style={{ margin: 0, color: "#64748b", fontSize: "14px" }}>
              {t('nav.vesselStaff')} & {t('nav.dashboard')}
            </p>
          </div>
          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontWeight: 800, color: "#1e293b", fontSize: "13px", marginBottom: "6px" }}>{t('auth.email')}</label>
              <input
                type="email"
                required
                autoFocus
                value={loginForm.email}
                onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                placeholder="ornek@sirket.com"
                style={{ width: "100%", padding: "12px", border: "2px solid #cbd5e1", borderRadius: "8px", fontSize: "14px", color: "#0f172a", background: "#fff", boxSizing: "border-box" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontWeight: 800, color: "#1e293b", fontSize: "13px", marginBottom: "6px" }}>{t('auth.password')}</label>
              <input
                type="password"
                required
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                placeholder="••••••••"
                style={{ width: "100%", padding: "12px", border: "2px solid #cbd5e1", borderRadius: "8px", fontSize: "14px", color: "#0f172a", background: "#fff", boxSizing: "border-box" }}
              />
            </div>
            {loginError && (
              <p style={{ color: "#dc2626", fontSize: "14px", margin: 0, fontWeight: "600", textAlign: "center" }}>
                {loginError}
              </p>
            )}
            <button className="primary-button" type="submit" style={{ width: "100%", padding: "14px", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              {t('auth.login')}
            </button>
          </form>
          <div style={{ textAlign: "center", marginTop: "20px", color: "#94a3b8", fontSize: "12px" }}>
            CREWINTEL v1.0 • Manning & Crew Management
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app"> 
      <style>{`
        :root { 
          --sidebar-bg: #0f172a; 
          --primary: #ea580c; 
          --primary-hover: #c2410c; 
        }
        body, .app { 
          color: #0f172a; 
          font-family: 'Inter', system-ui, sans-serif; 
          background-color: #f1f5f9; 
        }
        .sidebar { background-color: var(--sidebar-bg) !important; color: #f8fafc; }
        .nav-item { color: #cbd5e1 !important; transition: 0.2s; }
        .nav-item:hover, .nav-item.active { 
          background-color: #1e293b !important; 
          color: #fff !important; 
          border-left: 4px solid var(--primary); 
        }
        .primary-button { 
          background-color: var(--primary) !important; 
          color: white !important; 
          font-weight: 700; 
          text-transform: uppercase; 
          letter-spacing: 0.5px; 
          border: none; 
        }
        .primary-button:hover { 
          background-color: var(--primary-hover) !important; 
          box-shadow: 0 4px 6px -1px rgba(234,88,12,0.3); 
          transform: translateY(-1px); 
        }
        h1, h2, h3, h4, strong, span, p, td, th { color: #0f172a; }
        /* SIDEBAR YAZI RENGİ: koyu lacivert menüde TÜM yazılar beyaz olmalı */
        .sidebar, .sidebar * { color: #f8fafc !important; }
        .section-label { 
          font-weight: 800 !important; 
          color: #1e293b !important; 
          text-transform: none; 
          letter-spacing: 1px; 
        }
        input, select { 
          color: #0f172a !important; 
          background-color: #ffffff !important; 
          border: 2px solid #cbd5e1 !important; 
          font-weight: 500; 
          border-radius: 8px; 
        }
        input::placeholder { color: #94a3b8 !important; font-weight: normal; }
        input:focus, select:focus { 
          border-color: var(--primary) !important; 
          outline: none; 
          box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.2); 
        }
        
        /* TABLO TAŞMA SORUNU ÇÖZÜMÜ */
        .table-wrapper { 
          width: 100%; 
          overflow-x: auto; 
          padding-bottom: 10px; 
        }
        .table-wrapper::-webkit-scrollbar { height: 8px; }
        .table-wrapper::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 4px; }
        
        /* KALP ATIŞI (PULSE) */
        .pulse-soft { animation: pulseSoft 2.5s infinite; }
        @keyframes pulseSoft {
          0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
          70% { transform: scale(1.02); box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
          100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }

        /* ── ANİMASYONLU GEMİ SAHNESİ ──────────────────────────────── */
        .ship-scene {
          position: relative;
          width: 200px;
          height: 54px;
          border-radius: 12px;
          overflow: hidden;
          flex-shrink: 0;
        }
        .ship-scene .wave-layer {
          position: absolute;
          left: 0;
          bottom: 0;
          width: 200%;
          height: 62%;
          animation: waveDrift 5s linear infinite;
        }
        .ship-scene .wave-layer.w2 {
          animation-duration: 8s;
          animation-direction: reverse;
          opacity: 0.65;
          bottom: -5px;
        }
        @keyframes waveDrift {
          from { transform: translateX(0); }
          to   { transform: translateX(-50%); }
        }
        .ship-sail-wrap {
          position: absolute;
          left: 0;
          bottom: 30px;
          animation: shipSail 9s linear infinite;
        }
        @keyframes shipSail {
          from { transform: translateX(-70px); }
          to   { transform: translateX(280px); }
        }
        .ship-bob { animation: shipBob 2.4s ease-in-out infinite; }
        @keyframes shipBob {
          0%, 100% { transform: translateY(0) rotate(-2deg); }
          50%      { transform: translateY(-3px) rotate(2deg); }
        }
        .sun {
          position: absolute; top: 6px; right: 14px; width: 18px; height: 18px;
          border-radius: 50%; background: #fbbf24; box-shadow: 0 0 12px 4px rgba(251, 191, 36, 0.5);
        }
        .cloud {
          position: absolute; background: #ffffffcc; border-radius: 20px; height: 7px;
        }
        .cloud::before, .cloud::after {
          content: ""; position: absolute; background: #ffffffcc; border-radius: 50%;
        }
        .cloud::before { width: 12px; height: 12px; top: -6px; left: 6px; }
        .cloud::after  { width: 9px; height: 9px; top: -4px; right: 6px; }
        .c1 { top: 8px; left: 18px; width: 26px; animation: cloudDrift 14s linear infinite; }
        .c2 { top: 20px; left: 70px; width: 18px; opacity: 0.8; animation: cloudDrift 20s linear infinite; }
        @keyframes cloudDrift {
          from { transform: translateX(-40px); }
          to   { transform: translateX(240px); }
        }
        /* Kaza (çökme) sahnesi */
        .ship-wreck {
          position: absolute;
          bottom: 26px;
          right: 14px;
          transform: rotate(16deg);
          transform-origin: bottom center;
        }
        .rock {
          position: absolute; bottom: 20px; right: 4px;
        }
        .rain {
          position: absolute; top: 0; width: 2px; height: 12px;
          background: rgba(148, 163, 184, 0.6); border-radius: 2px;
          animation: rainFall 0.8s linear infinite;
        }
        @keyframes rainFall {
          from { transform: translateY(-16px); opacity: 0; }
          20% { opacity: 0.9; }
          to   { transform: translateY(58px); opacity: 0; }
        }
        .bucket-anim { animation: bucketToss 1.3s ease-in-out infinite; }
        @keyframes bucketToss {
          0%, 100% { transform: translate(0, 0) rotate(0deg); }
          50%      { transform: translate(22px, -13px) rotate(-35deg); }
        }
        .splash {
          position: absolute; bottom: 8px; right: 46px; color: #7dd3fc; font-size: 12px;
          animation: splashUp 1.2s ease-in-out infinite;
        }
        @keyframes splashUp {
          0%, 100% { transform: translateY(0) scale(0.8); opacity: 0.7; }
          50%      { transform: translateY(-8px) scale(1.15); opacity: 1; }
        }

        /* SİLME BUTONLARI: yatay kaydırmada sağda sabit kalsın (geniş menüde de görünsün) */
        .entity-row .icon-button {
          position: sticky;
          right: 8px;
          flex-shrink: 0;
          background: #fff;
          border-radius: 8px;
          z-index: 3;
          box-shadow: -4px 0 12px rgba(15, 23, 42, 0.10);
        }

        /* MOBİL UYUM */
        @media (max-width: 768px) {
          .ship-scene { width: 140px; }
          .status-text { display: none; }
          .topbar-subtitle { display: none; }
          .content { padding: 14px !important; }
          .cards { grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)) !important; gap: 10px !important; }
          .welcome h2 { font-size: 20px !important; }
          .topbar { padding: 10px 12px !important; gap: 8px; flex-wrap: wrap; }
          .topbar-user { display: none; }
        }
      `}</style>
      
      {/* ========================================================================= */}
      {/* 1. ATAMA YAPMA MODALI */}
      {/* ========================================================================= */}
      {assignmentModal.isOpen && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(15, 23, 42, 0.75)", zIndex: 9999, display: "flex", justifyContent: "center", alignItems: "center" }}>
          <div className="panel" style={{ width: "500px", maxWidth: "90%", padding: "24px", position: "relative", backgroundColor: "#fff", borderRadius: "12px" }}>
            <button 
              onClick={() => setAssignmentModal({ ...assignmentModal, isOpen: false })} 
              style={{ position: "absolute", top: "16px", right: "16px", background: "none", border: "none", cursor: "pointer" }}
            >
              <X size={24} color="#64748b" />
            </button>
            <h2 style={{ margin: "0 0 20px 0", color: "#0f172a", display: "flex", alignItems: "center", gap:"8px" }}>
              <Ship size={24} color="#ea580c"/> {t('vesselStaff.assign')}
            </h2>
            <form onSubmit={handleAssignmentSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <label className="section-label">{t('vesselStaff.person')}</label>
                <select 
                  className="form-input" 
                  required 
                  value={assignmentModal.crew_member_id} 
                  onChange={(e) => setAssignmentModal({...assignmentModal, crew_member_id: e.target.value})} 
                  style={{ width: "100%", padding: "12px", marginTop: "6px" }}
                >
                  <option value="">-- {t('crew.title')} --</option>
                  {crew.map(c => <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>)}
                </select>
              </div>
              <div>
                <label className="section-label">{t('vesselStaff.vessel')}</label>
                <select 
                  className="form-input" 
                  required 
                  value={assignmentModal.ship_id} 
                  onChange={(e) => setAssignmentModal({...assignmentModal, ship_id: e.target.value})} 
                  style={{ width: "100%", padding: "12px", marginTop: "6px" }}
                >
                  <option value="">-- {t('vessels.title')} --</option>
                  {ships.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="section-label">{t('crew.position')}</label>
                <input 
                  type="text" 
                  className="form-input" 
                  required 
                  value={assignmentModal.position} 
                  onChange={(e) => setAssignmentModal({...assignmentModal, position: e.target.value})} 
                  placeholder="Örn: Kaptan, Usta Gemici, Aşçı" 
                  style={{ width: "100%", padding: "12px", marginTop: "6px" }} 
                />
              </div>
              <div>
                <label className="section-label">{t('contracts.startDate')}</label>
                <input 
                  type="date" 
                  className="form-input" 
                  required 
                  value={assignmentModal.start_date || ""} 
                  onChange={(e) => setAssignmentModal({...assignmentModal, start_date: e.target.value})} 
                  style={{ width: "100%", padding: "12px", marginTop: "6px" }} 
                />
              </div>
              <div>
                <label className="section-label">{t('contracts.endDate')}</label>
                <input 
                  type="date" 
                  className="form-input" 
                  value={assignmentModal.end_date || ""} 
                  onChange={(e) => setAssignmentModal({...assignmentModal, end_date: e.target.value})} 
                  style={{ width: "100%", padding: "12px", marginTop: "6px" }} 
                />
              </div>
              <button type="submit" className="primary-button" style={{ padding: "14px", marginTop: "10px" }}>
                {t('vesselStaff.assign')}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. MANUEL EŞLEŞTİRME MODALI (ÖNCELİK 2) */}
      {/* ========================================================================= */}
      {matchingModalOpen && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(15, 23, 42, 0.8)", zIndex: 9999, display: "flex", justifyContent: "center", alignItems: "center" }}>
          <div className="panel" style={{ width: "650px", maxWidth: "95%", maxHeight: "85vh", overflowY: "auto", padding: "24px", position: "relative", backgroundColor: "#fff", borderRadius: "12px" }}>
            <button 
              onClick={() => setMatchingModalOpen(false)} 
              style={{ position: "absolute", top: "16px", right: "16px", background: "none", border: "none", cursor: "pointer" }}
            >
              <X size={24} color="#64748b" />
            </button>
            <h2 style={{ margin: "0 0 10px 0", color: "#0f172a", display: "flex", alignItems: "center", gap:"8px" }}>
              <FileText size={24} color="#ea580c"/> {t('documents.reviewRequired')}
            </h2>
            <p style={{ color: "#64748b", marginBottom: "20px", fontSize: "14px" }}>
              Aşağıdaki belgeler isminden veya içeriğinden anlaşılamadığı için sahipsiz kalmıştır. Lütfen listeden doğru personeli bularak eşleştirme işlemini tamamlayın.
            </p>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {allDocuments.filter(d => d.match_status === "pending").length === 0 ? (
                <div className="empty" style={{ padding: "30px", textAlign: "center", background: "#f8fafc", borderRadius: "8px", border: "2px dashed #cbd5e1" }}>
                  <Activity size={40} color="#10b981" style={{ margin: "0 auto 10px auto" }}/>
                  <h3 style={{ color: "#0f172a", margin: 0 }}>Harika İş Çıkardın!</h3>
                  <p style={{ margin: "5px 0 0 0", color: "#64748b" }}>Eşleşme bekleyen hiçbir belge kalmadı.</p>
                </div>
              ) : (
                allDocuments.filter(d => d.match_status === "pending").map(doc => (
                  <div key={doc.id} style={{ border: "1px solid #e2e8f0", padding: "16px", borderRadius: "8px", background: "#f8fafc", display: "flex", flexDirection: "column", gap: "12px" }}>
                    <div>
                      <strong style={{ display: "block", color: "#0f172a", fontSize: "15px", wordBreak: "break-all" }}>
                        {doc.original_filename}
                      </strong>
                      <span className={`badge badge-type-${doc.document_type}`} style={{ marginTop: "6px", display: "inline-block" }}>
                        {doc.document_type}
                      </span>
                    </div>
                    <div style={{ display: "flex", gap: "10px" }}>
                      <select className="form-input" style={{ flex: 1, padding: "10px" }} id={`match_select_${doc.id}`}>
                        <option value="">-- {t('crew.title')} --</option>
                        {crew.map(c => <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>)}
                      </select>
                      {canWrite && (
                        <button className="primary-button" onClick={() => {
                          const selectEl = document.getElementById(`match_select_${doc.id}`);
                          handleMatchDocument(doc.id, selectEl.value);
                        }}>
                          {t('common.confirm')}
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* BELGE KATEGORİ DETAY MODALI (expired/urgent/approaching/valid) */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      {docCategoryModal.isOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.8)', zIndex: 9999, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="panel" style={{ width: '820px', maxWidth: '95%', maxHeight: '85vh', overflowY: 'auto', padding: '24px', position: 'relative', backgroundColor: '#fff', borderRadius: '12px' }}>
            <button onClick={() => setDocCategoryModal({ isOpen: false, status: '', title: '', docs: [], loading: false })} style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', cursor: 'pointer' }}>
              <X size={24} color="#64748b" />
            </button>
            <h2 style={{ margin: '0 0 6px 0', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={22} color="#ea580c" /> {docCategoryModal.title}
            </h2>
            <p style={{ color: '#64748b', marginBottom: '14px', fontSize: '13px' }}>
              {docCategoryModal.docs.length} {t('documents.title').toLowerCase()}
            </p>

            {/* Toplu aksiyon但onları */}
            {docCategorySelected.length > 0 && (
              <div style={{ display: 'flex', gap: '8px', marginBottom: '14px', padding: '10px 14px', background: '#f0f9ff', borderRadius: '8px', border: '1px solid #bae6fd', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: '600', color: '#0369a1' }}>{docCategorySelected.length} {t('common.selected')}</span>
                <button className="primary-button" onClick={sendDocCategoryEmail} style={{ padding: '6px 14px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}><Mail size={14} /> {t('email.send')}</button>
                <button className="primary-button" onClick={sendDocCategoryWhatsApp} style={{ padding: '6px 14px', fontSize: '13px', background: '#25D366', display: 'flex', alignItems: 'center', gap: '6px' }}><Phone size={14} /> WhatsApp</button>
                <button onClick={() => setDocCategorySelected([])} style={{ padding: '6px 10px', fontSize: '13px', background: '#e2e8f0', border: 'none', borderRadius: '6px', cursor: 'pointer', color: '#475569' }}>{t('common.cancel')}</button>
              </div>
            )}

            {docCategoryModal.loading ? (
              <p style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>{t('common.loading')}</p>
            ) : docCategoryModal.docs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px', background: '#f0fdf4', borderRadius: '8px', border: '2px dashed #bbf7d0' }}>
                <CheckCircle size={36} color="#16a34a" style={{ margin: '0 auto 8px auto' }} />
                <p style={{ color: '#16a34a', fontWeight: '600', margin: 0 }}>{t('common.noData')}</p>
              </div>
            ) : (
              <div className="table-wrapper">
                <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ textAlign: 'left', color: '#64748b', borderBottom: '2px solid #e2e8f0' }}>
                      <th style={{ padding: '8px', width: '32px' }}>
                        <input type="checkbox" onChange={(e) => {
                          if (e.target.checked) setDocCategorySelected(docCategoryModal.docs);
                          else setDocCategorySelected([]);
                        }} checked={docCategorySelected.length === docCategoryModal.docs.length && docCategoryModal.docs.length > 0} style={{ cursor: 'pointer' }} />
                      </th>
                      <th style={{ padding: '8px' }}>{t('crew.title')}</th>
                      <th style={{ padding: '8px' }}>{t('documents.title')}</th>
                      <th style={{ padding: '8px' }}>{t('documents.expiryDate')}</th>
                      <th style={{ padding: '8px' }}>{t('common.email')}</th>
                      <th style={{ padding: '8px' }}>WhatsApp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {docCategoryModal.docs.map((doc) => {
                      const member = crew.find(c => c.id === doc.crew_member_id);
                      const isSelected = docCategorySelected.some(d => d.id === doc.id);
                      return (
                        <tr key={doc.id} style={{ borderTop: '1px solid #e2e8f0', background: isSelected ? '#f0f9ff' : 'transparent' }}>
                          <td style={{ padding: '8px' }}>
                            <input type="checkbox" checked={isSelected} onChange={() => {
                              setDocCategorySelected(prev =>
                                prev.some(d => d.id === doc.id)
                                  ? prev.filter(d => d.id !== doc.id)
                                  : [...prev, doc]
                              );
                            }} style={{ cursor: 'pointer' }} />
                          </td>
                          <td style={{ padding: '8px', fontWeight: '600', color: '#0f172a' }}>
                            {member ? `${member.first_name} ${member.last_name}` : '—'}
                          </td>
                          <td style={{ padding: '8px' }}>{doc.document_type}</td>
                          <td style={{ padding: '8px', color: doc.expiry_status === 'expired' ? '#b91c1c' : doc.expiry_status === 'urgent' ? '#c2410c' : '#a16207', fontWeight: '600' }}>
                            {doc.expiry_date || '—'}
                          </td>
                          <td style={{ padding: '8px' }}>
                            {member?.email ? (
                              <button onClick={() => {
                                const msg = encodeURIComponent(`${member.first_name} ${member.last_name},\n\n${doc.document_type} ${t('documents.expired')} — ${t('common.view')}: ${API_URL}/portal/${member.id}`);
                                window.open(`mailto:${member.email}?subject=${encodeURIComponent(doc.document_type + ' ' + t('documents.expired'))}&body=${msg}`, '_blank');
                              }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', borderRadius: '6px' }} title={member.email}>
                                <Mail size={18} color="#0284c7" />
                              </button>
                            ) : <span style={{ color: '#cbd5e1' }}>—</span>}
                          </td>
                          <td style={{ padding: '8px' }}>
                            {member?.phone ? (
                              <button onClick={() => {
                                const msg = encodeURIComponent(`${member.first_name} ${member.last_name}, ${doc.document_type} ${t('documents.expired')} — ${t('common.view')}: ${API_URL}/portal/${member.id}`);
                                window.open(`https://wa.me/${member.phone.replace(/[^0-9]/g, '')}?text=${msg}`, '_blank');
                              }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', borderRadius: '6px' }} title={member.phone}>
                                <Phone size={18} color="#25D366" />
                              </button>
                            ) : <span style={{ color: '#cbd5e1' }}>—</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {emailModal.isOpen && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(15, 23, 42, 0.8)", zIndex: 9999, display: "flex", justifyContent: "center", alignItems: "center" }}>
          <div className="panel" style={{ width: "560px", maxWidth: "95%", maxHeight: "85vh", overflowY: "auto", padding: "24px", position: "relative", backgroundColor: "#fff", borderRadius: "12px" }}>
            <button
              onClick={() => setEmailModal({ ...emailModal, isOpen: false })}
              style={{ position: "absolute", top: "16px", right: "16px", background: "none", border: "none", cursor: "pointer" }}
            >
              <X size={24} color="#64748b" />
            </button>
            <h2 style={{ margin: "0 0 10px 0", color: "#0f172a", display: "flex", alignItems: "center", gap: "8px" }}>
              <Mail size={22} color='#ea580c' /> {t('email.send')}
            </h2>
            <p style={{ color: "#64748b", marginBottom: "18px", fontSize: "14px" }}>
              {emailModal.crewIds.length === 1
                ? "1 personele e-posta gönderilecek."
                : `${emailModal.crewIds.length} personele e-posta gönderilecek.`}
            </p>
            {emailMsg && (
              <p style={{ margin: "0 0 12px 0", padding: "10px 12px", borderRadius: "8px", fontSize: "13px", fontWeight: "600", background: emailMsg.type === "success" ? "#f0fdf4" : "#fef2f2", color: emailMsg.type === "success" ? "#15803d" : "#b91c1c" }}>{emailMsg.text}</p>
            )}
            <form onSubmit={sendEmail}>
              <label style={{ display: "block", marginBottom: "4px", fontWeight: "bold", color: "#0f172a", fontSize: "13px" }}>Konu</label>
              <input className="form-input" required style={{ width: "100%", padding: "11px", marginTop: "6px", boxSizing: "border-box" }} value={emailModal.subject} onChange={(e) => setEmailModal({ ...emailModal, subject: e.target.value })} placeholder="Örn: Medical belgeniz yenilenmeli" />
              <label style={{ display: 'block', margin: '12px 0 4px 0', fontWeight: 'bold', color: '#0f172a', fontSize: '13px' }}>{t('messages.body')}</label>
              <textarea className="form-input" rows="6" style={{ width: "100%", padding: "11px", marginTop: "6px", boxSizing: "border-box" }} value={emailModal.body} onChange={(e) => setEmailModal({ ...emailModal, body: e.target.value })} placeholder="Merhaba, ..." />
              <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}>
                <button type="button" className="secondary-button" onClick={() => setEmailModal({ ...emailModal, isOpen: false })}>{t('common.cancel')}</button>
                <button type="submit" className="primary-button"><Mail size={18} /> Gönder</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SOL MENÜ (SIDEBAR) */}
      {/* ========================================================================= */}
      <aside className={`sidebar ${menuOpen ? "open" : "closed"}`}>
        <div className="logo" style={{ padding: menuOpen ? "20px" : "16px 8px", display: "flex", alignItems: "center", justifyContent: menuOpen ? "flex-start" : "center", gap: "12px", borderBottom: "1px solid #1e293b", marginBottom: "10px" }}>
          {appSettings.logoUrl ? (
            <img src={appSettings.logoUrl} alt="Logo" style={{height: "36px", width: "auto", borderRadius: "4px", flexShrink: 0}} />
          ) : (
            <Ship size={32} color="#ea580c" style={{ flexShrink: 0 }} />
          )}
          {menuOpen && (
            <span style={{fontWeight: "900", fontSize: "20px", letterSpacing: "1.5px", color: "#fff"}}>
              {appSettings.companyName}
            </span>
          )}
        </div>
        <nav style={{ padding: "0 10px" }}>
          {navigation.map(([page, Icon, label]) => (
            <button 
              className={`nav-item ${activePage === page ? "active" : ""}`} 
              key={page} 
              data-label={label}
              title={label}
              onClick={() => (page === "documents" ? openDocumentsPage() : navigate(page))} 
              style={{ padding: "14px", borderRadius: "8px", marginBottom: "4px" }}
            >
              <Icon size={22} />
              {menuOpen && <span style={{ fontSize: "15px", fontWeight: "600" }}>{label}</span>}
            </button>
          ))}
        </nav>
        <button 
          className="menu-button" 
          onClick={() => setMenuOpen(!menuOpen)} 
          style={{ color: "#fff", background: "#1e293b", borderRadius: "8px", margin: "10px" }}
        >
          <Menu size={24} />
        </button>
        {/* DİL SEÇİCİ */}
        <div style={{ padding: "10px", borderTop: "1px solid #1e293b", marginTop: "10px" }}>
          <LanguageSelector />
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* ANA İÇERİK BÖLÜMÜ */}
      {/* ========================================================================= */}
      <main className="main">
      <header className="topbar" style={{ background: "#fff", borderBottom: "1px solid #e2e8f0", padding: "0 30px", minHeight: "64px", display: "flex", alignItems: "center", gap: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px", minWidth: 0 }}>
            {navStack.length > 0 && (
              <button className="back-button" onClick={goBack} title="Önceki sayfaya dön" style={{ whiteSpace: "nowrap" }}>
                ← {t('common.back')}
              </button>
            )}
            <h1 style={{ fontSize: "21px", fontWeight: "900", margin: 0, color: "#0f172a", whiteSpace: "nowrap" }}>
              {appSettings.companyName}
            </h1>
          </div>

          {/* SİSTEM DURUMU — modern kompakt rozet */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginLeft: "auto" }}>
            <div
              title={isSystemHealthy ? t('dashboard.systemActive') : t('dashboard.systemDown')}
              style={{
                display: "flex", alignItems: "center", gap: "8px",
                background: isSystemHealthy ? "#f0fdf4" : "#fef2f2",
                border: `1px solid ${isSystemHealthy ? "#86efac" : "#fca5a5"}`,
                borderRadius: "999px", padding: "7px 14px", whiteSpace: "nowrap",
              }}
            >
              <span className="status-dot" style={{ background: isSystemHealthy ? "#16a34a" : "#dc2626" }} />
              <span style={{ fontSize: "13px", fontWeight: 800, color: isSystemHealthy ? "#15803d" : "#b91c1c" }}>
                {isSystemHealthy ? t('dashboard.systemActive') : t('dashboard.systemDown')}
              </span>
            </div>

            {/* BİLDİRİM ZİLİ */}
            <div style={{ position: "relative" }}>
              <button className="icon-button" onClick={() => { setShowNotifications(!showNotifications); loadNotifications(); }} title={t('nav.notifications')} style={{ padding: "9px", background: showNotifications ? "#f1f5f9" : "#fff", border: "1px solid #e2e8f0", borderRadius: "10px", cursor: "pointer" }}>
                <Bell size={20} color={notifications.filter((n) => !n.read).length > 0 ? "#ea580c" : "#475569"} />
                {notifications.filter((n) => !n.read).length > 0 && (
                  <span style={{ position: "absolute", top: "-4px", right: "-4px", background: "#ef4444", color: "#fff", fontSize: "10px", fontWeight: "700", borderRadius: "20px", minWidth: "18px", height: "18px", display: "flex", alignItems: "center", justifyContent: "center", padding: "0 4px" }}>
                    {notifications.filter((n) => !n.read).length}
                  </span>
                )}
              </button>
              {showNotifications && (
                <div style={{ position: "absolute", top: "46px", right: "0", width: "360px", maxHeight: "420px", overflowY: "auto", background: "#fff", border: "1px solid #e2e8f0", borderRadius: "12px", boxShadow: "0 20px 40px -12px rgba(15,23,42,0.25)", zIndex: 100, padding: "8px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 10px" }}>
                    <strong style={{ color: "#0f172a" }}>{t('nav.notifications')}</strong>
                    <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px" }} onClick={() => { axios.post(`${API_URL}/api/notifications/generate`).then(loadNotifications); }}>Yenile</button>
                  </div>
                  {notifications.length === 0 && <p style={{ padding: "16px", color: "#64748b", textAlign: "center" }}>Bildirim yok.</p>}
                  {notifications.map((n) => (
                    <div key={n.id} onClick={() => markNotificationRead(n.id)} style={{ padding: "10px 12px", borderBottom: "1px solid #f1f5f9", cursor: "pointer", borderRadius: "8px", background: n.read ? "transparent" : "#fffbeb" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                        <strong style={{ fontSize: "13px", color: "#0f172a" }}>{n.title}</strong>
                        {!n.read && <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#ea580c", flexShrink: 0, marginTop: "4px" }} />}
                      </div>
                      {n.message && <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#64748b" }}>{n.message}</p>}
                      <span style={{ fontSize: "11px", color: "#94a3b8" }}>{n.channel === 'email' ? `✉️ ${t('channel.email')}` : n.channel === 'whatsapp' ? `💬 ${t('channel.whatsapp')}` : `🔔 ${t('channel.system')}`} · {new Date(n.created_at).toLocaleString("tr-TR")}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* KULLANICI BİLGİSİ + ÇIKIŞ */}
            {auth?.user && (
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div style={{ width: 34, height: 34, borderRadius: "50%", background: "#0f172a", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: "14px", flexShrink: 0 }}>
                  {(auth.user.full_name || "?").trim().charAt(0).toUpperCase()}
                </div>
                <div className="user-name" style={{ textAlign: "left", lineHeight: 1.2, minWidth: 0 }}>
                  <strong style={{ display: "block", fontSize: "13px", color: "#0f172a", whiteSpace: "nowrap" }}>
                    {auth.user.full_name}
                  </strong>
                  <span style={{ display: "inline-block", marginTop: "2px", fontSize: "11px", fontWeight: 700, padding: "2px 8px", borderRadius: "999px", background: auth.user.role === "admin" ? "#fee2e2" : auth.user.role === "hr" ? "#ffedd5" : "#e2e8f0", color: auth.user.role === "admin" ? "#b91c1c" : auth.user.role === "hr" ? "#c2410c" : "#475569" }}>
                    {roleLabel}
                  </span>
                </div>
                <button className="secondary-button" onClick={handleLogout} style={{ whiteSpace: "nowrap", padding: "8px 14px" }}>
                  {t('auth.logout')}
                </button>
              </div>
            )}
          </div>
        </header>
        
        <section className="content" style={{ padding: "30px", overflowX: "hidden" }}>
          {renderPage()}
        </section>
      </main>
    </div>
  );
}

export default App;