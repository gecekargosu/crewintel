from app.db.database import Base, engine


def init_db():
    Base.metadata.create_all(bind=engine)
    print("CREWINTEL DATABASE TABLOLARI HAZIR")


if __name__ == "__main__":
    init_db()