# API Specification

---

## Аутентификация

### Шаг 1/2: `/auth/register` — Регистрация

Сохраняет данные во временное хранилище (Redis) и отправляет 6-значный код подтверждения на почту.
Далее необходимо вызвать [`/auth/verify`](#шаг-22-authverify--подтверждение-почты).

**Метод:** `POST`

**Тело запроса:**
```json
{
    "email": "example@example.com",
    "password": "superstrongpassword",
    "first_name": "Иван",
    "last_name": "Петров"
}
```

**Ответы:**

| Код | Описание |
|-----|----------|
| `200` | Код подтверждения отправлен на почту. В теле: `{"message": "Код подтверждения отправлен на example@example.com"}` |
| `409` | Пользователь с таким email уже существует |
| `422` | Невалидное тело запроса (короткий пароль, не email и т.п.) |
| `429` | Превышен лимит: 5 запросов в минуту с одного IP |

**Rate-limiting (два уровня):**
1. **IP-based:** не более 5 регистраций с одного IP в минуту (`REGISTER_IP_LIMIT / REGISTER_IP_WINDOW`)
2. **Email-based:** не более 1 отправки кода на один email в 30 секунд (`SEND_LIMIT / SEND_WINDOW`)

---

### Шаг 2/2: `/auth/verify` — Подтверждение почты

Сверяет код из письма, создаёт пользователя в БД и возвращает пару JWT-токенов.
Токены также ставятся в httponly куки `access_token` и `refresh_token`.

**Метод:** `POST`

**Тело запроса:**
```json
{
    "email": "example@example.com",
    "code": "123456"
}
```

**Ответы:**

| Код | Описание |
|-----|----------|
| `201` | Регистрация завершена. В теле: `ApiResponse[TokenPair]` — access и refresh токены |
| `400` | Неверный или истёкший код подтверждения |
| `400` | Данные регистрации истекли (прошло более 5 минут). Нужно заново вызвать `/auth/register` |
| `429` | Превышен лимит: 5 попыток подбора кода за 10 секунд на один email |

**Пример ответа (201):**
```json
{
    "is_success": true,
    "message": "Регистрация завершена",
    "status_code": 201,
    "data": {
        "access_token": "eyJhbG...",
        "refresh_token": "eyJhbG...",
        "token_type": "bearer"
    }
}
```

---

### `/auth/login` — Вход

Аутентифицирует пользователя по email и паролю, возвращает пару JWT-токенов.
Токены также ставятся в httponly куки.

**Метод:** `POST`

**Тело запроса:**
```json
{
    "email": "user@example.com",
    "password": "superstrongandpowerfulpassword"
}
```

**Ответы:**

| Код | Описание |
|-----|----------|
| `200` | Вход выполнен. В теле: `ApiResponse[TokenPair]` |
| `401` | Неверные учётные данные (email, пароль или аккаунт деактивирован) |
| `429` | Превышен лимит: 10 попыток входа с одного IP в минуту |

---

### `/auth/refresh` — Обновление токенов

Выпускает новую пару токенов по действующему refresh-токену. Старый refresh-токен отзывается (jti удаляется из whitelist).

**Метод:** `POST`

**Тело запроса:**
```json
{
    "refresh_token": "eyJhbG..."
}
```

**Ответы:**

| Код | Описание |
|-----|----------|
| `200` | Токены обновлены. В теле: `ApiResponse[TokenPair]` |
| `401` | Невалидный, истёкший или уже отозванный refresh-токен |
| `404` | Пользователь из токена не найден в БД |

---

## Чат

### `/ws/chat/{course_id}` — WebSocket чата курса

WebSocket-соединение для обмена сообщениями в реальном времени во время занятия.
Сообщения сохраняются в БД (история будет доступна через эндпоинт просмотра записи занятия).

**Протокол:** WebSocket (`ws://` / `wss://`)

**Аутентификация:** через httponly куку `access_token`, которая автоматически отправляется браузером при handshake.

**Проверка доступа:** только участники курса. При отсутствии доступа соединение закрывается с кодом `4003`.

**Формат входящего сообщения (JSON):**
```json
{
    "course_id": 5,
    "text": "Вопрос по домашнему заданию"
}
```

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `course_id` | `int` | Обязательное |
| `text` | `string` | 1–500 символов |

При невалидном сообщении клиент получает ответ:
```json
{"error": "Невалидное сообщение. Ожидаются поля: course_id (int), text (str, 1-500)"}
```

**Формат исходящего сообщения (JSON):**
```json
{
    "id": 42,
    "course_id": 5,
    "author_id": 7,
    "text": "Вопрос по домашнему заданию",
    "created_at": "2026-06-24T12:00:00+00:00"
}
```

**Особенности:**
- Отправитель не получает эхо своего сообщения (фильтрация по `author_id`)
- Сообщения рассылаются всем подключённым участникам курса через Redis Pub/Sub
- При дисконнекте подписка автоматически отменяется

---

## Регистрация преподавателя

При регистрации можно передать `teacher_invite_token` — если токен валиден, пользователь получит роль `teacher`. Без токена — `student`.

Тело запроса `/auth/register` с токеном:
```json
{
    "email": "teacher@example.com",
    "password": "strongpassword123",
    "first_name": "Иван",
    "last_name": "Петров",
    "teacher_invite_token": "3ITTjZFWLXTq6kLRG..."
}
```

---

## Teacher Invites (администратор)

Управление токенами для регистрации преподавателей.

**Префикс:** `/admin/teacher-invites`
**Доступ:** `admin`

### `POST /` — создать токен
```json
{
    "max_uses": 10,
    "expires_at": "2026-12-31T23:59:59Z"
}
```
Оба поля опциональны.

### `GET /` — список всех токенов

### `PATCH /{token}` — обновить токен
```json
{"is_active": false, "max_uses": 5}
```

### `DELETE /{token}` — удалить токен

---

## Курсы

**Префикс:** `/courses`

### `POST /create` — создать курс
**Доступ:** `teacher`, `admin`
```json
{
    "title": "Python Basics",
    "description": "Изучение Python с нуля для начинающих"
}
```

### `GET /my` — мои курсы

### `GET /{slug}` — получить курс
**Доступ:** участник курса или admin

### `PATCH /{slug}` — обновить курс
**Доступ:** создатель курса или admin
```json
{"title": "Новое название", "description": "Описание", "is_active": true}
```

### `DELETE /{slug}` — удалить курс

---

## Уроки

**Префикс:** `/courses/{slug}/lessons`

### `POST /` — создать урок
**Доступ:** преподаватель курса или admin
```json
{
    "title": "Введение в Python",
    "description": "Первый урок по основам Python для начинающих",
    "scheduled_at": "2026-07-02T10:00:00Z",
    "max_participants": 50
}
```

### `GET /` — список уроков курса

### `GET /{lesson_id}` — получить урок

### `PATCH /{lesson_id}` — обновить урок

### `POST /{lesson_id}/start` — начать урок

Статус: `scheduled → running`.
```json
{"started_at": "2026-07-01T07:10:00Z"}
```

### `POST /{lesson_id}/end` — завершить урок

Статус: `running → ended`.
```json
{"ended_at": "2026-07-01T08:30:00Z"}
```

### `GET /{lesson_id}/token` — LiveKit-токен

Возвращает JWT-токен для подключения к комнате:
```json
{
    "token": "eyJhbG...",
    "room_name": "course_1_lesson_1",
    "ws_url": "ws://livekit:7880"
}
```

Имя комнаты: `course_{course_id}_lesson_{lesson_id}`.
Токен выдаётся с правами `join + publish + subscribe`, TTL — 1 час.

### `GET /{lesson_id}/logs` — логи посещения

**Доступ:** преподаватель курса или admin

Возвращает записи из `lessons_logs`: кто зашёл, когда вышел, длительность. Фронтенд считает статистику на клиенте.

Пример ответа:
```json
{
    "is_success": true,
    "message": "Логи посещения",
    "status_code": 200,
    "data": [
        {
            "id": 9,
            "lesson_id": 1,
            "user_id": 4,
            "session_id": "S_REAL",
            "joined_at": "2026-07-01T08:00:00Z",
            "left_at": null,
            "duration_seconds": null
        }
    ]
}
```

---

## Приглашения в курс

**Префикс:** `/courses/{slug}/invites`
**Доступ:** преподаватель курса или admin

### `POST /` — создать ссылку
```json
{"max_uses": 50, "expires_at": "2026-12-31T23:59:59Z"}
```

### `GET /` — активная ссылка курса

### `PATCH /{token}` — обновить

### `DELETE /{token}` — удалить

---

## Присоединение к курсу

### `POST /invites/join`
```json
{"token": "abc123..."}
```

---

## Преподаватели курса

**Префикс:** `/courses/{slug}/teachers`
**Доступ:** создатель курса или admin

### `POST /` — добавить
```json
{"user_ids": [5, 12]}
```

### `GET /` — список преподавателей

### `DELETE /` — удалить
```json
{"user_ids": [5]}
```

---

## Участники курса

**Префикс:** `/courses/{slug}/members`
**Доступ:** преподаватель курса или admin

### `GET /` — список участников

### `DELETE /` — удалить
```json
{"user_ids": [7, 9]}
```

---

## Пользователи

**Префикс:** `/users`

### `GET /me` — мой профиль

### `PATCH /me` — обновить профиль
```json
{"first_name": "Новое", "last_name": "Имя"}
```

### `GET /` — список пользователей
**Доступ:** admin. Параметры: `limit` (100), `offset` (0).

### `GET /{user_id}` — пользователь по ID
**Доступ:** admin.

### `PATCH /{user_id}` — изменить
**Доступ:** admin.
```json
{
    "first_name": "Новое", "last_name": "Имя",
    "email": "new@example.com", "role": "teacher",
    "is_active": true
}
```

### `POST /set-active` — активировать/деактивировать
```json
{"user_ids": [3, 4], "is_active": false}
```

### `POST /delete` — удалить
```json
{"user_ids": [5, 6]}
```

---

## LiveKit Webhook

### `POST /livekit/webhook`

Принимает события от LiveKit-сервера. Подпись SHA-256 (HMAC) проверяется всегда: заголовок `Authorization` сверяется с `WEBHOOK_SECRET`.

**Обрабатываемые события:**
- `participant_joined` → LPUSH в Redis-буфер
- `participant_left` → LPUSH в Redis-буфер
- `room_finished` → принудительный флаш буфера

**Фоновый воркер** раз в 5 секунд забирает всё из буфера и пишет батчем в `lessons_logs`.

**Формат события LiveKit:**
```json
{
    "event": "participant_joined",
    "room": {"name": "course_1_lesson_1"},
    "participant": {"identity": "4"},
    "id": "SESSION_abc123",
    "created_at": "2026-07-01T08:00:00Z"
}
```

**Identity участника** = строковое представление `user_id` из БД.

**Настройка LiveKit** (в `docker-compose-dev.yml`):
```yaml
LIVEKIT_CONFIG: |
  webhook:
    api_key: ${WEBHOOK_SECRET}
    urls:
      - http://backend:8000/livekit/webhook
```

**Архитектура:**
```
LiveKit → POST /livekit/webhook → LPUSH Redis (мгновенно, 200)
                                    ↓
                             Воркер (каждые 5 сек)
                                    ↓
                        LRANGE + DEL → батч INSERT/UPDATE в lessons_logs

room_finished → flush_now() вне очереди
```

---

## Общие правила

- Все ответы — в обёртке `ApiResponse`: `is_success`, `message`, `status_code`, `data`
- Аутентификация: JWT через заголовок `Authorization: Bearer <token>` или httponly куку
- Swagger: `/docs`, ReDoc: `/redoc`
- Дефолтный админ при первом запуске: `admin@example.com` / `admin123456`
- Почта в dev: Mailpit на `http://localhost:8025`
