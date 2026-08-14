from datetime import date

from app.models.crew_member import CrewMember
from app.services.document_processing import match_crew


def make_crew(**kwargs):
    defaults = {
        "first_name": "John",
        "last_name": "Smith",
        "position": "Captain",
    }
    defaults.update(kwargs)
    return CrewMember(**defaults)


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows

    def query(self, model):
        return FakeQuery(self.rows)


def test_match_by_passport():
    crew = make_crew(
        passport_number="P123456",
        email="other@example.com",
    )

    session = FakeSession([crew])

    result, status, confidence = match_crew(
        session,
        "random.pdf",
        "",
        {
            "passport_number": "P123456",
            "seaman_book_number": None,
            "email": None,
            "date_of_birth": None,
        },
    )

    assert result is crew
    assert status == "matched"
    assert confidence == 100


def test_match_by_seaman_book():
    crew = make_crew(
        first_name="Different",
        last_name="Person",
        seaman_book_number="SB12345",
    )

    session = FakeSession([crew])

    result, status, confidence = match_crew(
        session,
        "random.pdf",
        "",
        {
            "passport_number": None,
            "seaman_book_number": "SB12345",
            "email": None,
            "date_of_birth": None,
        },
    )

    assert result is crew
    assert status == "matched"
    assert confidence == 100


def test_match_by_email_plus_name():
    crew = make_crew(
        first_name="John",
        last_name="Smith",
        email="john.smith@example.com",
    )

    session = FakeSession([crew])

    result, status, confidence = match_crew(
        session,
        "John_Smith_CV.pdf",
        "",
        {
            "passport_number": None,
            "seaman_book_number": None,
            "email": "john.smith@example.com",
            "date_of_birth": None,
        },
    )

    assert result is crew
    assert status == "matched"
    assert confidence == 100


def test_match_by_exact_name_and_dob():
    crew = make_crew(
        first_name="John",
        last_name="Smith",
        date_of_birth=date(1980, 7, 21),
    )

    session = FakeSession([crew])

    result, status, confidence = match_crew(
        session,
        "John_Smith_CV.pdf",
        "",
        {
            "passport_number": None,
            "seaman_book_number": None,
            "email": None,
            "date_of_birth": date(1980, 7, 21),
        },
    )

    assert result is crew
    assert status == "matched"
    assert confidence == 100


def test_unmatched_when_no_candidate_information_matches():
    crew = make_crew(
        first_name="John",
        last_name="Smith",
        passport_number="P111111",
        seaman_book_number="SB11111",
        email="john@example.com",
    )

    session = FakeSession([crew])

    result, status, confidence = match_crew(
        session,
        "Michael_Jones_CV.pdf",
        "",
        {
            "passport_number": "P999999",
            "seaman_book_number": "SB99999",
            "email": "michael@example.com",
            "date_of_birth": None,
        },
    )

    assert result is None
    assert status == "unmatched"
    assert confidence == 0


def test_pending_when_two_candidates_are_too_close():
    crew1 = make_crew(
        first_name="John",
        last_name="Smith",
        email="john@example.com",
    )

    crew2 = make_crew(
        first_name="John",
        last_name="Smith",
        email="different@example.com",
    )

    session = FakeSession([crew1, crew2])

    result, status, confidence = match_crew(
        session,
        "John_Smith_CV.pdf",
        "",
        {
            "passport_number": None,
            "seaman_book_number": None,
            "email": None,
            "date_of_birth": None,
        },
    )

    assert result is None
    assert status == "pending"
    assert confidence == 95


def test_exact_name_match_is_enough_for_high_confidence():
    crew = make_crew(
        first_name="John",
        last_name="Smith",
    )

    session = FakeSession([crew])

    result, status, confidence = match_crew(
        session,
        "John_Smith_CV.pdf",
        "",
        {
            "passport_number": None,
            "seaman_book_number": None,
            "email": None,
            "date_of_birth": None,
        },
    )

    assert result is crew
    assert status == "matched"
    assert confidence == 95

