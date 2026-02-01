import hashlib, bcrypt
from typing import Literal


def hash_password(password: str, sha_alg: Literal[1, 256, 384, 512, 224] = 256) -> str:
    def coding(code):
        return f'hashlib.sha{code}()'

    password_bytes = password.encode('utf-8')
    hashed = eval(coding(sha_alg))
    hashed.update(password_bytes)
    hashed_password = hashed.hexdigest()
    return hashed_password


def hash_password_bcrypt(password: str) -> str:
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_password.decode('utf-8')


def check_password_bcrypt(password: str, hashed_password: str) -> bool:
    password_bytes = password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)
