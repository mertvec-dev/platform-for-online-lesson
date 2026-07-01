"""
Централизованные ключи Redis.

Все TTL и лимиты берутся из `settings` (config.py),
префиксы — константы внутри модуля.
"""

from .config import settings

# =============================================================================
# Префиксы
# =============================================================================

CHAT_ROOM = "chat:room"
VERIFY_CODE = "verify:code"
REGISTRATION = "registration"
EMAIL_VERIFIED = "email:verified"
RATELIMIT_SEND = "ratelimit:verify:send"
RATELIMIT_CHECK = "ratelimit:verify:check"
RATELIMIT_REGISTER_IP = "ratelimit:register:ip"
RATELIMIT_LOGIN_IP = "ratelimit:login:ip"
RATELIMIT_WEBHOOK_IP = "ratelimit:webhook:ip"
REFRESH_JTI = "refresh:jti"

# =============================================================================
# Буфер webhook
# =============================================================================

WEBHOOK_BUFFER = "webhook:buffer"
WEBHOOK_FLUSH_INTERVAL = settings.WEBHOOK_FLUSH_INTERVAL_SECONDS

# =============================================================================
# TTL (из settings)
# =============================================================================

CODE_TTL = settings.VERIFICATION_CODE_TTL_IN_MINUTES * 60

# =============================================================================
# Лимиты (из settings)
# =============================================================================

SEND_LIMIT = settings.RATE_LIMIT_SEND_LIMIT
SEND_WINDOW = settings.RATE_LIMIT_SEND_WINDOW

CHECK_LIMIT = settings.RATE_LIMIT_CHECK_LIMIT
CHECK_WINDOW = settings.RATE_LIMIT_CHECK_WINDOW

REGISTER_IP_LIMIT = settings.RATE_LIMIT_REGISTER_IP_LIMIT
REGISTER_IP_WINDOW = settings.RATE_LIMIT_REGISTER_IP_WINDOW

LOGIN_IP_LIMIT = settings.RATE_LIMIT_LOGIN_IP_LIMIT
LOGIN_IP_WINDOW = settings.RATE_LIMIT_LOGIN_IP_WINDOW

WEBHOOK_IP_LIMIT = settings.RATE_LIMIT_WEBHOOK_IP_LIMIT
WEBHOOK_IP_WINDOW = settings.RATE_LIMIT_WEBHOOK_IP_WINDOW

# =============================================================================
# Функции формирования ключей
# =============================================================================


def chat_channel(course_id: int) -> str:
    """`chat:room:<course_id>` — канал Pub/Sub для чата курса"""
    return f"{CHAT_ROOM}:{course_id}"


def verify_code_key(email: str) -> str:
    """`verify:code:<email>` — код верификации"""
    return f"{VERIFY_CODE}:{email}"


def email_verified_key(email: str) -> str:
    """`email:verified:<email>` — флаг, что почта подтверждена (TTL)"""
    return f"{EMAIL_VERIFIED}:{email}"


def ratelimit_send_key(email: str) -> str:
    """`ratelimit:verify:send:<email>` — счётчик отправок кода"""
    return f"{RATELIMIT_SEND}:{email}"


def ratelimit_check_key(email: str) -> str:
    """`ratelimit:verify:check:<email>` — счётчик попыток проверки кода"""
    return f"{RATELIMIT_CHECK}:{email}"


def refresh_jti_key(jti: str) -> str:
    """`refresh:jti:<uuid>` — whitelist валидных refresh-токенов"""
    return f"{REFRESH_JTI}:{jti}"


def registration_key(email: str) -> str:
    """`registration:<email>` — временные данные регистрации"""
    return f"{REGISTRATION}:{email}"


def ratelimit_register_ip_key(ip: str) -> str:
    """`ratelimit:register:ip:<ip>` — счётчик регистраций с IP"""
    return f"{RATELIMIT_REGISTER_IP}:{ip}"


def ratelimit_login_ip_key(ip: str) -> str:
    """`ratelimit:login:ip:<ip>` — счётчик попыток входа с IP"""
    return f"{RATELIMIT_LOGIN_IP}:{ip}"


def ratelimit_webhook_ip_key(ip: str) -> str:
    """`ratelimit:webhook:ip:<ip>` — счётчик webhook-запросов с IP"""
    return f"{RATELIMIT_WEBHOOK_IP}:{ip}"
