"""
Аутентификация WebSocket через httponly куку

При WebSocket handshake браузер автоматически отправляет куки.
"""

from fastapi import WebSocket, WebSocketException, status

from .jwt_tokens import extract_user_id


async def get_user_id_from_cookie(websocket: WebSocket) -> int:
    """
    Извлекает user_id из JWT-токена, хранящегося в httponly куке access_token.
    """
    token = websocket.cookies.get("access_token")
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Нет access_token в куках",
        )

    user_id = extract_user_id(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Невалидный или истёкший токен",
        )

    return user_id
