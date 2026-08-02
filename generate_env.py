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
EGRESS_CONFIG = ROOT / "livekit-egress.yaml"
MIN_PASSWORD_LENGTH = 12


def generate_secret() -> str:
    return secrets.token_hex(32)


def _read_env_value(lines: list[str], key: str) -> str:
    for line in lines:
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


def _write_egress_config(
    api_key: str,
    api_secret: str,
    redis_pass: str,
    s3_access: str,
    s3_secret: str,
    s3_bucket: str,
    s3_region: str,
    s3_endpoint: str,
) -> None:
    content = (
        f"# LiveKit Egress конфигурация — сгенерирован автоматически\n\n"
        f"api_port: 7881\n"
        f"api_key: {api_key}\n"
        f"api_secret: {api_secret}\n"
        f"ws_url: ws://livekit:7880\n\n"
        f"s3:\n"
        f"  access_key: {s3_access}\n"
        f"  secret: {s3_secret}\n"
        f"  bucket: {s3_bucket}\n"
        f"  region: {s3_region}\n"
        f"  endpoint: {s3_endpoint}\n\n"
        f"redis:\n"
        f"  address: redis:6379\n"
        f"  password: {redis_pass}\n"
    )
    EGRESS_CONFIG.write_text(content, encoding="utf-8")
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

        for key in ["POSTGRES_PASSWORD", "DEFAULT_ADMIN_PASSWORD"]:
            if f"{key}=" not in existing:
                print(f"  ⚠️  {key} не задан!")
            else:
                val = _read_env_value(lines, key)
                if len(val) < MIN_PASSWORD_LENGTH:
                    print(f"  ⚠️  {key} слишком короткий ({len(val)} < {MIN_PASSWORD_LENGTH})")
                else:
                    print(f"  • {key} уже задан")

        if "DEFAULT_ADMIN_EMAIL=" not in existing:
            email = input("Почта дефолтного админа [admin@example.com]: ").strip()
            lines.append(f"DEFAULT_ADMIN_EMAIL={email or 'admin@example.com'}")
            print("  + Установлен DEFAULT_ADMIN_EMAIL")

        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

        _write_egress_config(
            api_key=_read_env_value(lines, "LIVEKIT_API_KEY"),
            api_secret=_read_env_value(lines, "LIVEKIT_API_SECRET"),
            redis_pass=_read_env_value(lines, "REDIS_PASSWORD"),
            s3_access=_read_env_value(lines, "LIVEKIT_S3_ACCESS_KEY") or "minioadmin",
            s3_secret=_read_env_value(lines, "LIVEKIT_S3_SECRET_KEY") or "minioadmin",
            s3_bucket=_read_env_value(lines, "LIVEKIT_S3_BUCKET") or "recordings",
            s3_region=_read_env_value(lines, "LIVEKIT_S3_REGION") or "us-east-1",
            s3_endpoint=_read_env_value(lines, "LIVEKIT_S3_ENDPOINT") or "http://minio:9000",
        )
        print("Готово.")
        return

    # --- Новый .env ---
    print(f"Создаю {ENV_FILE}...\n")

    print("Выберите окружение:")
    print("  [1] development")
    print("  [2] production")
    env_choice = input("Ваш выбор [2]: ").strip() or "2"
    is_dev = env_choice == "1"

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

    lk_api_key = generate_secret()
    lk_api_secret = generate_secret()

    if is_dev:
        env_type = "development"
        smtp_host = "mailpit"
        smtp_port = "1025"
        smtp_password = "any"
        smtp_from = "noreply@example.com"
        lk_public_ws = "ws://localhost:7880"
        domain_line = ""
    else:
        env_type = "production"
        domain = input("Домен сайта (например, edu.example.com): ").strip()
        if not domain:
            print("Ошибка: домен не может быть пустым")
            sys.exit(1)
        smtp_host = input("SMTP-хост [smtp.yandex.ru]: ").strip() or "smtp.yandex.ru"
        smtp_port = input("SMTP-порт [465]: ").strip() or "465"
        smtp_from = input(f"SMTP-адрес отправителя [noreply@{domain}]: ").strip() or f"noreply@{domain}"
        smtp_password = input("SMTP-пароль: ").strip()
        if not smtp_password:
            print("⚠️  SMTP-пароль не задан. Почта не будет работать.")
        lk_public_ws = f"wss://{domain}:7881"
        domain_line = f"DOMAIN_NAME={domain}\n"

    content = (
        f"ENVIRONMENT={env_type}\n"
        f"{domain_line}"
        f"POSTGRES_USER=postgres\n"
        f"POSTGRES_PASSWORD={pg_pass}\n"
        f"POSTGRES_DB=db\n"
        f"REDIS_HOST=redis\n"
        f"REDIS_PORT=6379\n"
        f"REDIS_PASSWORD={redis_pass}\n"
        f"JWT_SECRET_KEY={generate_secret()}\n"
        f"WEBHOOK_SECRET={generate_secret()}\n"
        f"ACCESS_JWT_TOKEN_EXPIRES_IN_MINUTES=30\n"
        f"REFRESH_JWT_TOKEN_EXPIRES_IN_DAYS=7\n"
        f"DEFAULT_ADMIN_EMAIL={admin_email}\n"
        f"DEFAULT_ADMIN_PASSWORD={admin_pass}\n"
        f"SMTP_HOST={smtp_host}\n"
        f"SMTP_PORT={smtp_port}\n"
        f"SMTP_FROM_EMAIL={smtp_from}\n"
        f"SMTP_PASSWORD={smtp_password}\n"
        f"LIVEKIT_API_KEY={lk_api_key}\n"
        f"LIVEKIT_API_SECRET={lk_api_secret}\n"
        f"LIVEKIT_WS_URL=ws://livekit:7880\n"
        f"LIVEKIT_PUBLIC_WS_URL={lk_public_ws}\n"
        f"ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173\n"
        f"LIVEKIT_EGRESS_ENABLED=true\n"
        f"LIVEKIT_S3_ACCESS_KEY=minioadmin\n"
        f"LIVEKIT_S3_SECRET_KEY=minioadmin\n"
        f"LIVEKIT_S3_BUCKET=recordings\n"
        f"LIVEKIT_S3_REGION=us-east-1\n"
        f"LIVEKIT_S3_ENDPOINT=http://minio:9000\n"
    )

    ENV_FILE.write_text(content, encoding="utf-8")

    _write_egress_config(
        api_key=lk_api_key,
        api_secret=lk_api_secret,
        redis_pass=redis_pass,
        s3_access="minioadmin",
        s3_secret="minioadmin",
        s3_bucket="recordings",
        s3_region="us-east-1",
        s3_endpoint="http://minio:9000",
    )
    print(f"\nФайл {ENV_FILE} создан.")


if __name__ == "__main__":
    main()
