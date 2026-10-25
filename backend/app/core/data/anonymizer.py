import hashlib
from backend.app.config import settings

def hash_student_id(student_id: str, salt: str = None) -> str:
    """
    Computes a deterministic, salted SHA-256 hash of a student ID
    to protect student privacy and ensure PII compliance.
    """
    used_salt = salt or settings.STUDENT_HASH_SALT
    salted_value = f"{used_salt}:{student_id.strip().upper()}"
    return hashlib.sha256(salted_value.encode("utf-8")).hexdigest()
