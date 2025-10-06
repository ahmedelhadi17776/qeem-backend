"""Repository tests for rate calculations."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.rate_calculation import RateCalculation
from app.repositories.rate_repository import RateRepository


def _create_user(db: Session, email: str) -> User:
    user = User(email=email, password_hash="hash")
    db.add(user)
    db.flush()
    return user


def _create_calc(db: Session, user_id: int, idx: int) -> RateCalculation:
    calc = RateCalculation(
        user_id=user_id,
        project_type="web_development",
        project_complexity="moderate",
        estimated_hours=10 + idx,
        experience_years=2,
        skills_count=3,
        location="Cairo, Egypt",
        minimum_rate=50.0 + idx,
        competitive_rate=75.0 + idx,
        premium_rate=100.0 + idx,
    )
    db.add(calc)
    db.flush()
    return calc


def test_rate_repository_crud_and_queries(db_session: Session):
    repo = RateRepository(db_session)

    user = _create_user(db_session, "repo_user@example.com")

    # create calculations
    calcs = [_create_calc(db_session, int(user.id), i) for i in range(5)]
    db_session.commit()

    # get_by_user_id with pagination
    page1 = repo.get_by_user_id(int(user.id), skip=0, limit=2)
    page2 = repo.get_by_user_id(int(user.id), skip=2, limit=2)
    assert len(page1) == 2 and len(page2) == 2

    # count_by_user
    assert repo.count_by_user(int(user.id)) == 5

    # set and get favorites
    repo.set_favorite(int(calcs[0].id), int(user.id), True)
    repo.set_favorite(int(calcs[1].id), int(user.id), True)
    favs = repo.get_favorites(int(user.id))
    assert len(favs) == 2

    # update calculation
    updated = repo.update(calcs[0], {"preferred_rate": 120.0})
    assert float(updated.preferred_rate or 0) == 120.0

    # delete calculation
    repo.delete(calcs[1])
    assert repo.count_by_user(int(user.id)) == 4
