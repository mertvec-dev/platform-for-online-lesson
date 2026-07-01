"""Централизованные определения разрешений и ролевая матрица"""

from enum import Enum

from ...models.users import Role


class Permission(str, Enum):
    """Все возможные действия в системе."""

    # Курсы
    COURSE_VIEW = "course:view"
    COURSE_CREATE = "course:create"
    COURSE_UPDATE = "course:update"
    COURSE_DELETE = "course:delete"
    COURSE_MANAGE_TEACHERS = "course:manage_teachers"
    COURSE_MANAGE_INVITES = "course:manage_invites"
    COURSE_VIEW_MEMBERS = "course:view_members"
    COURSE_REMOVE_MEMBERS = "course:remove_members"

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

    Контекст ресурса (чей курс, состоит ли участник и т.п.)
    проверяется отдельно в доменных AccessPolicy.
    """

    _permissions_by_role: dict[Role, frozenset[Permission]] = {
        Role.STUDENT: frozenset(
            {
                Permission.COURSE_VIEW,
                Permission.COURSE_VIEW_MEMBERS,
                Permission.LESSON_VIEW,
                Permission.MEMBERSHIP_JOIN,
                Permission.MEMBERSHIP_LEAVE,
                Permission.INVITE_JOIN,
            }
        ),
        Role.TEACHER: frozenset(
            {
                Permission.COURSE_VIEW,
                Permission.COURSE_CREATE,
                Permission.COURSE_UPDATE,
                Permission.COURSE_MANAGE_TEACHERS,
                Permission.COURSE_MANAGE_INVITES,
                Permission.COURSE_VIEW_MEMBERS,
                Permission.COURSE_REMOVE_MEMBERS,
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
