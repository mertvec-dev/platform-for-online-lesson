"""
Централизованные ключи Redis, TTL и лимиты.

Все префиксы, таймауты и лимиты живут только здесь.
"""


def chat_channel(room_id: int) -> str:
    """chat:room:<room_id> — канал Pub/Sub для чата комнаты"""
    return f"{CHAT_ROOM}:{room_id}"


def verify_code_key(email: str) -> str:
    """verify:code:<email> — код верификации"""
    return f"{VERIFY_CODE}:{email}"


def email_verified_key(email: str) -> str:
    """email:verified:<email> — флаг, что почта подтверждена (TTL)"""
    return f"{EMAIL_VERIFIED}:{email}"


def ratelimit_send_key(email: str) -> str:
    """ratelimit:verify:send:<email> — счётчик отправок кода"""
    return f"{RATELIMIT_SEND}:{email}"


def ratelimit_check_key(email: str) -> str:
    """ratelimit:verify:check:<email> — счётчик попыток проверки кода"""
    return f"{RATELIMIT_CHECK}:{email}"


def refresh_jti_key(jti: str) -> str:
    """refresh:jti:<uuid> — whitelist валидных refresh-токенов"""
    return f"{REFRESH_JTI}:{jti}"


# =============================================================================
# Префиксы
# =============================================================================

CHAT_ROOM = "chat:room"
VERIFY_CODE = "verify:code"
EMAIL_VERIFIED = "email:verified"
RATELIMIT_SEND = "ratelimit:verify:send"
RATELIMIT_CHECK = "ratelimit:verify:check"
REFRESH_JTI = "refresh:jti"

# =============================================================================
# TTL (в секундах)
# =============================================================================

CODE_TTL = 300

# =============================================================================
# Лимиты
# =============================================================================

SEND_LIMIT = 1
SEND_WINDOW = 30  # не чаще 1 раза в 30 секунд

CHECK_LIMIT = 5
CHECK_WINDOW = 10  # 5 попыток за 10 секунд
