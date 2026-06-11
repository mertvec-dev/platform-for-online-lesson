"""
[LEGACY] Файл содержит корутины для рассылки сообщений с кодом авторизации

@deprecated — функционал не используется. Регистрация переехала на email.
Код сохранён на случай перехода к SMS-верификации.
"""

# from random import randint

# from fastapi import HTTPException, status

# from ..core import redis_client

# import smsaero

# async def send_sms(phone: int, message: str) -> None:
#     """
#     Пример вызова:
#         ```python
#         asyncio.run(send_sms(7000000000, "Где деньги, Лебовски?"))
#         ```
#     """
#     api = smsaero.SmsAero(SMSAERO_EMAIL, SMSAERO_API_KEY)
#     try:
#         result = await api.send_sms(phone, message)
#     finally:
#         await api.close_session()


# async def put_code_at_redis(phone_number: str) -> None:
#     if await redis_client.is_rate_limited(
#         key=phone_number, limit=1, window=30, scope="sms"
#     ):
#         raise HTTPException(
#             status_code=status.HTTP_429_TOO_MANY_REQUESTS,
#             detail="Слишком много запросов! Попробуйте позже",
#         )
#     else:
#         await redis_client.set_cache(
#             key=phone_number, value=randint(1000, 9999), expire=300
#         )


# async def verify_code(phone_number: str, code: int) -> bool:
#     """
#     Проверяет введенный пользователем код с кодом из Redis

#     Возвращает `True`, если код верен и вход разрешен, а иначе `False`
#     """
#     if await redis_client.is_rate_limited(
#         key=phone_number, limit=5, window=10, scope="verify"
#     ):
#         raise HTTPException(
#             status_code=status.HTTP_429_TOO_MANY_REQUESTS,
#             detail="Слишком много запросов! Попробуйте позже",
#         )
#     else:
#         redis_code = await redis_client.get_cache(key=phone_number)
#         if str(code) == redis_code:
#             await redis_client.delete_cache(key=phone_number)
#             return True
#         else:
#             return False
