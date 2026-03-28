import hashlib

from app.models import ApiKey


def seed_api_key(db_session_factory, raw_key):
    """Create the seed API key if it doesn't already exist."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    session = db_session_factory()
    try:
        existing = session.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
        if existing:
            return
        api_key = ApiKey(
            name="seed-admin",
            key_hash=key_hash,
            scopes=["*"],
            is_active=True,
        )
        session.add(api_key)
        session.commit()
        print(f"Seed API key created. Plaintext key: {raw_key}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
