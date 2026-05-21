from app.database import get_db, Base, engine


def test_base_has_metadata():
    assert Base.metadata is not None


def test_get_db_yields_session():
    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass
