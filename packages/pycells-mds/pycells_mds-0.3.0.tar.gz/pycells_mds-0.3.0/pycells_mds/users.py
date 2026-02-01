# pycells_mds/users.py

import hashlib
from sqlalchemy import or_
from .session import db
from .models import UserModel


# --- Хэширование пароля ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hash_: str) -> bool:
    return hash_password(password) == hash_


# --- Регистрация пользователя ---
def register_user(username: str, password: str, email: str | None = None) -> UserModel:
    email = email.strip() if email else None
    if email == "":
        email = None

    # Проверяем username
    existing = db.session.query(UserModel).filter_by(username=username).first()
    if existing:
        raise ValueError(f"Пользователь '{username}' уже существует.")

    # Проверяем email
    if email:
        e = db.session.query(UserModel).filter_by(email=email).first()
        if e:
            raise ValueError(f"Email '{email}' уже используется.")

    user = UserModel(
        username=username,
        password_hash=hash_password(password),
        email=email
    )

    db.session.add(user)
    db.session.commit()
    return user


# --- Авторизация ---
def login_user(username: str, password: str) -> int | None:
    user = db.session.query(UserModel).filter_by(username=username).first()
    if user and verify_password(password, user.password_hash):
        return user.id
    return None


# --- Безопасная регистрация ---
def safe_register_user(username: str, password: str, email: str | None = None):
    exists = (
        db.session.query(UserModel)
        .filter(or_(UserModel.username == username,
                    UserModel.email == email))
        .first()
    )

    if exists:
        print(f"[INFO] Пользователь '{username}' или email '{email}' уже существует.")
        user_id = login_user(username, password)
        return exists, user_id

    # создаём нового
    user = register_user(username, password, email)
    user_id = login_user(username, password)
    return user, user_id
