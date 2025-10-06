"""Repository tests for user and profile operations."""

from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository


def test_user_repository_crud(db_session: Session):
    repo = UserRepository(db_session)

    # create user
    user = repo.create({
        "email": "userrepo@example.com",
        "password_hash": "hash",
        "is_active": True,
        "is_verified": False,
    })
    assert user.id is not None

    # get by email/id
    assert repo.get_by_email("userrepo@example.com").id == user.id
    assert repo.get_by_id(int(user.id)).email == "userrepo@example.com"

    # update user
    updated = repo.update(user, {"is_verified": True})
    assert updated.is_verified is True

    # profile create/update/get
    profile = repo.create_profile({
        "user_id": int(user.id),
        "first_name": "A",
        "last_name": "B",
        "country": "Egypt",
        "preferred_currency": "EGP",
    })
    assert profile.user_id == user.id
    profile2 = repo.update_profile(profile, {"first_name": "Ahmed"})
    assert profile2.first_name == "Ahmed"
    assert repo.get_profile(int(user.id)) is not None

    # counts and list
    assert repo.count_users() >= 1
    actives = repo.list_active_users(limit=10)
    assert any(u.id == user.id for u in actives)

    # delete
    repo.delete(user)
    assert repo.get_by_id(int(user.id)) is None
