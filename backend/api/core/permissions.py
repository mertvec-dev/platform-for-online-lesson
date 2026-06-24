"""Централизованные определения разрешений и ролевая матрица"""

from enum import Enum

from ...models.users import Role


class Permission(str, Enum):
    """Все возможные действия в системе."""

    # Комнаты
    ROOM_VIEW = "room:view"
    ROOM_CREATE = "room:create"
    ROOM_UPDATE = "room:update"
    ROOM_DELETE = "room:delete"
    ROOM_MANAGE_TEACHERS = "room:manage_teachers"
    ROOM_MANAGE_INVITES = "room:manage_invites"
    ROOM_VIEW_MEMBERS = "room:view_members"
    ROOM_REMOVE_MEMBERS = "room:remove_members"

    # Уроки
    LESSON_VIEW = "lesson:view"
    LESSON_CREATE = "lesson:create"
    LESSON_UPDATE = "lesson:update"
    LESSON_DELETE = "lesson:delete"
    LESSON_START = "lesson:start"
    LESSON_END = "lesson:end"
    LESSON_VIEW_LOGS = "lesson:view_logs"

    # Участники
    MEMBERSHIP_JOIN = "membership:join"
    MEMBERSHIP_LEAVE = "membership:leave"

    # Приглашения
    INVITE_JOIN = "invite:join"

    # Пользователи
    USER_MANAGE_ROLES = "user:manage_roles"


class RolePermissions:
    """
    Централизованная шина возможностей для каждой роли.

    Отвечает только на вопрос:
        «Может ли роль X в принципе выполнять действие Y?»

    Контекст ресурса (чья комната, состоит ли участник и т.п.)
    проверяется отдельно в доменных AccessPolicy.
    """

    _permissions_by_role: dict[Role, frozenset[Permission]] = {
        Role.STUDENT: frozenset(
            {
                Permission.ROOM_VIEW,
                Permission.ROOM_VIEW_MEMBERS,
                Permission.LESSON_VIEW,
                Permission.MEMBERSHIP_JOIN,
                Permission.MEMBERSHIP_LEAVE,
                Permission.INVITE_JOIN,
            }
        ),
        Role.TEACHER: frozenset(
            {
                Permission.ROOM_VIEW,
                Permission.ROOM_CREATE,
                Permission.ROOM_UPDATE,
                Permission.ROOM_MANAGE_TEACHERS,
                Permission.ROOM_MANAGE_INVITES,
                Permission.ROOM_VIEW_MEMBERS,
                Permission.ROOM_REMOVE_MEMBERS,
                Permission.LESSON_VIEW,
                Permission.LESSON_CREATE,
                Permission.LESSON_UPDATE,
                Permission.LESSON_START,
                Permission.LESSON_END,
                Permission.LESSON_VIEW_LOGS,
                Permission.MEMBERSHIP_JOIN,
                Permission.MEMBERSHIP_LEAVE,
                Permission.INVITE_JOIN,
            }
        ),
        Role.ADMIN: frozenset(permission for permission in Permission),
    }

    @classmethod
    def allows(cls, role: Role, permission: Permission) -> bool:
        """Проверяет, доступно ли действие указанной роли"""
        return permission in cls._permissions_by_role.get(role, frozenset())

    @classmethod
    def list_for_role(cls, role: Role) -> frozenset[Permission]:
        """Возвращает все разрешения для роли"""
        return cls._permissions_by_role.get(role, frozenset())
