"""
Генератор .env файла для платформы онлайн-занятий.

Запрашивает пароли у пользователя, генерирует секреты, создаёт .env.

Использование:
    python generate_env.py
"""

import secrets
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"
MIN_PASSWORD_LENGTH = 12


def generate_secret() -> str:
    return secrets.token_hex(32)


def main() -> None:
    if ENV_FILE.exists():
        print(f"Файл {ENV_FILE} уже существует.")
        print("Проверяю недостающие секреты...")

        existing = ENV_FILE.read_text(encoding="utf-8")
        lines = existing.splitlines()

        secret_vars = [
            "JWT_SECRET_KEY",
            "WEBHOOK_SECRET",
            "REDIS_PASSWORD",
            "LIVEKIT_API_KEY",
            "LIVEKIT_API_SECRET",
        ]

        for var in secret_vars:
            if f"{var}=" not in existing:
                secret = generate_secret()
                lines.append(f"{var}={secret}")
                print(f"  + Сгенерирован {var}")
            else:
                for i, line in enumerate(lines):
                    if line.startswith(f"{var}=") and line.strip() == f"{var}=":
                        secret = generate_secret()
                        lines[i] = f"{var}={secret}"
                        print(f"  + Заполнен пустой {var}")
                        break
                else:
                    print(f"  • {var} уже задан, пропускаю")

        # POSTGRES_PASSWORD
        if "POSTGRES_PASSWORD=" not in existing:
            print("  ⚠️  POSTGRES_PASSWORD не задан! Укажи его вручную.")
        else:
            for line in lines:
                if line.startswith("POSTGRES_PASSWORD="):
                    val = line.split("=", 1)[1]
                    if len(val) < MIN_PASSWORD_LENGTH:
                        print(
                            f"  ⚠️  POSTGRES_PASSWORD слишком короткий "
                            f"({len(val)} < {MIN_PASSWORD_LENGTH})"
                        )
                    else:
                        print("  • POSTGRES_PASSWORD уже задан")
                    break

        # DEFAULT_ADMIN_EMAIL
        if "DEFAULT_ADMIN_EMAIL=" not in existing:
            email = input("Почта дефолтного админа [admin@example.com]: ").strip()
            email = email or "admin@example.com"
            lines.append(f"DEFAULT_ADMIN_EMAIL={email}")
            print("  + Установлен DEFAULT_ADMIN_EMAIL")

        # DEFAULT_ADMIN_PASSWORD
        if "DEFAULT_ADMIN_PASSWORD=" not in existing:
            print("  ⚠️  DEFAULT_ADMIN_PASSWORD не задан!")
        else:
            for line in lines:
                if line.startswith("DEFAULT_ADMIN_PASSWORD="):
                    val = line.split("=", 1)[1]
                    if len(val) < MIN_PASSWORD_LENGTH:
                        print(
                            f"  ⚠️  DEFAULT_ADMIN_PASSWORD слишком короткий "
                            f"({len(val)} < {MIN_PASSWORD_LENGTH})"
                        )
                    else:
                        print("  • DEFAULT_ADMIN_PASSWORD уже задан")
                    break

        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("Готово.")
        return

    print(f"Создаю {ENV_FILE}...")
    print()

    while True:
        pg_pass = input("Пароль для PostgreSQL (минимум 12 символов): ").strip()
        if not pg_pass:
            print("Ошибка: пароль не может быть пустым")
            continue
        if len(pg_pass) < MIN_PASSWORD_LENGTH:
            print(f"Ошибка: пароль слишком короткий (минимум {MIN_PASSWORD_LENGTH})")
            continue
        break

    while True:
        redis_pass = input("Пароль для Redis (минимум 12 символов): ").strip()
        if not redis_pass:
            print("Ошибка: пароль не может быть пустым")
            continue
        if len(redis_pass) < MIN_PASSWORD_LENGTH:
            print(f"Ошибка: пароль слишком короткий (минимум {MIN_PASSWORD_LENGTH})")
            continue
        if pg_pass == redis_pass:
            print("⚠️  Пароли не должны совпадать. Придумай другой.")
            continue
        break

    admin_email = input("Почта дефолтного админа [admin@example.com]: ").strip()
    admin_email = admin_email or "admin@example.com"

    while True:
        admin_pass = input("Пароль дефолтного админа (минимум 12 символов): ").strip()
        if not admin_pass:
            print("Ошибка: пароль не может быть пустым")
            continue
        if len(admin_pass) < MIN_PASSWORD_LENGTH:
            print(f"Ошибка: пароль слишком короткий (минимум {MIN_PASSWORD_LENGTH})")
            continue
        break

    content = f"""\
# === Окружение ===
ENVIRONMENT=development

# === База данных ===
POSTGRES_USER=postgres
POSTGRES_PASSWORD={pg_pass}
POSTGRES_DB=db

# === Redis ===
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD={redis_pass}

# === Безопасность API ===
JWT_SECRET_KEY={generate_secret()}
WEBHOOK_SECRET={generate_secret()}
ACCESS_JWT_TOKEN_EXPIRES_IN_MINUTES=30
REFRESH_JWT_TOKEN_EXPIRES_IN_DAYS=7

# === Дефолтный админ (создаётся при первом запуске) ===
DEFAULT_ADMIN_EMAIL={admin_email}
DEFAULT_ADMIN_PASSWORD={admin_pass}

# === LiveKit (видео/аудио) ===
LIVEKIT_API_KEY={generate_secret()}
LIVEKIT_API_SECRET={generate_secret()}
LIVEKIT_WS_URL=ws://livekit:7880
"""

    ENV_FILE.write_text(content, encoding="utf-8")
    print()
    print(f"Файл {ENV_FILE} создан.")


if __name__ == "__main__":
    main()
