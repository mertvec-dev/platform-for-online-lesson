#!/usr/bin/env python3
"""
Генератор .env и livekit-egress.yaml для платформы онлайн-занятий.

Использование:
    python generate_env.py
"""

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
EGRESS_TEMPLATE = ROOT / "livekit-egress.yaml.template"
EGRESS_CONFIG = ROOT / "livekit-egress.yaml"
MIN_PASSWORD_LENGTH = 12


def generate_secret() -> str:
    return secrets.token_hex(32)


def _read_env_value(lines: list[str], key: str) -> str | None:
    for line in lines:
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None


def _generate_egress_config(env_lines: list[str]) -> None:
    """Генерирует livekit-egress.yaml из шаблона, подставляя значения из .env."""
    if not EGRESS_TEMPLATE.exists():
        print("  ⚠️  livekit-egress.yaml.template не найден — пропускаю Egress-конфиг")
        return

    template = EGRESS_TEMPLATE.read_text(encoding="utf-8")

    replacements = {
        "LIVEKIT_API_KEY_PLACEHOLDER": _read_env_value(env_lines, "LIVEKIT_API_KEY") or "",
        "LIVEKIT_API_SECRET_PLACEHOLDER": _read_env_value(env_lines, "LIVEKIT_API_SECRET") or "",
        "REDIS_PASSWORD_PLACEHOLDER": _read_env_value(env_lines, "REDIS_PASSWORD") or "",
        "S3_ACCESS_KEY_PLACEHOLDER": _read_env_value(env_lines, "LIVEKIT_S3_ACCESS_KEY") or "minioadmin",
        "S3_SECRET_KEY_PLACEHOLDER": _read_env_value(env_lines, "LIVEKIT_S3_SECRET_KEY") or "minioadmin",
        "S3_BUCKET_PLACEHOLDER": _read_env_value(env_lines, "LIVEKIT_S3_BUCKET") or "recordings",
        "S3_REGION_PLACEHOLDER": _read_env_value(env_lines, "LIVEKIT_S3_REGION") or "us-east-1",
        "S3_ENDPOINT_PLACEHOLDER": _read_env_value(env_lines, "LIVEKIT_S3_ENDPOINT") or "http://minio:9000",
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    EGRESS_CONFIG.write_text(template, encoding="utf-8")
    print("  + livekit-egress.yaml сгенерирован")


def main() -> None:
    if ENV_FILE.exists():
        print(f"Файл {ENV_FILE} уже существует.")
        print("Проверяю недостающие секреты...")

        existing = ENV_FILE.read_text(encoding="utf-8")
        lines = existing.splitlines()

        for var in [
            "JWT_SECRET_KEY", "WEBHOOK_SECRET", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET",
        ]:
            if f"{var}=" not in existing:
                lines.append(f"{var}={generate_secret()}")
                print(f"  + Сгенерирован {var}")
            else:
                for i, line in enumerate(lines):
                    if line.startswith(f"{var}=") and line.strip() == f"{var}=":
                        lines[i] = f"{var}={generate_secret()}"
                        print(f"  + Заполнен пустой {var}")
                        break
                else:
                    print(f"  • {var} уже задан, пропускаю")

        for key, label in [("POSTGRES_PASSWORD", "POSTGRES_PASSWORD"), ("DEFAULT_ADMIN_PASSWORD", "DEFAULT_ADMIN_PASSWORD")]:
            if f"{key}=" not in existing:
                print(f"  ⚠️  {label} не задан!")
            else:
                val = _read_env_value(lines, key) or ""
                if len(val) < MIN_PASSWORD_LENGTH:
                    print(f"  ⚠️  {label} слишком короткий ({len(val)} < {MIN_PASSWORD_LENGTH})")
                else:
                    print(f"  • {label} уже задан")

        if "DEFAULT_ADMIN_EMAIL=" not in existing:
            email = input("Почта дефолтного админа [admin@example.com]: ").strip()
            lines.append(f"DEFAULT_ADMIN_EMAIL={email or 'admin@example.com'}")
            print("  + Установлен DEFAULT_ADMIN_EMAIL")

        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _generate_egress_config(lines)
        print("Готово.")
        return

    # --- Новый .env ---
    print(f"Создаю {ENV_FILE}...\n")

    while True:
        pg_pass = input("Пароль для PostgreSQL (мин. 12 символов): ").strip()
        if len(pg_pass) >= MIN_PASSWORD_LENGTH:
            break
        print(f"Ошибка: минимум {MIN_PASSWORD_LENGTH} символов")

    while True:
        redis_pass = input("Пароль для Redis (мин. 12 символов): ").strip()
        if len(redis_pass) < MIN_PASSWORD_LENGTH:
            print(f"Ошибка: минимум {MIN_PASSWORD_LENGTH} символов")
            continue
        if pg_pass == redis_pass:
            print("⚠️  Пароли не должны совпадать.")
            continue
        break

    admin_email = input("Почта дефолтного админа [admin@example.com]: ").strip() or "admin@example.com"

    while True:
        admin_pass = input("Пароль дефолтного админа (мин. 12 символов): ").strip()
        if len(admin_pass) >= MIN_PASSWORD_LENGTH:
            break
        print(f"Ошибка: минимум {MIN_PASSWORD_LENGTH} символов")

    domain = input("Домен сайта (например, edu.example.com): ").strip()
    if not domain:
        print("Ошибка: домен не может быть пустым")
        sys.exit(1)

    lk_api_key = generate_secret()
    lk_api_secret = generate_secret()

    content = f"""\
ENVIRONMENT=production
DOMAIN_NAME={domain}
POSTGRES_USER=postgres
POSTGRES_PASSWORD={pg_pass}
POSTGRES_DB=db
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD={redis_pass}
JWT_SECRET_KEY={generate_secret()}
WEBHOOK_SECRET={generate_secret()}
ACCESS_JWT_TOKEN_EXPIRES_IN_MINUTES=30
REFRESH_JWT_TOKEN_EXPIRES_IN_DAYS=7
DEFAULT_ADMIN_EMAIL={admin_email}
DEFAULT_ADMIN_PASSWORD={admin_pass}
LIVEKIT_API_KEY={lk_api_key}
LIVEKIT_API_SECRET={lk_api_secret}
LIVEKIT_WS_URL=ws://livekit:7880
LIVEKIT_PUBLIC_WS_URL=wss://{domain}:7881
LIVEKIT_EGRESS_ENABLED=true
LIVEKIT_S3_ACCESS_KEY=minioadmin
LIVEKIT_S3_SECRET_KEY=minioadmin
LIVEKIT_S3_BUCKET=recordings
LIVEKIT_S3_REGION=us-east-1
LIVEKIT_S3_ENDPOINT=http://minio:9000
"""

    ENV_FILE.write_text(content, encoding="utf-8")
    _generate_egress_config(content.splitlines())
    print(f"\nФайл {ENV_FILE} создан.")


if __name__ == "__main__":
    main()
