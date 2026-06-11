"""Зависимости и политики для предметных проверок доступа"""

from enum import Enum

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..core import db
from ..models import Lesson, Room, RoomMembership, RoomTeacher, User
from ..models.users import Role
from .rbac import get_current_user


class Permission(str, Enum):
    """Все возможные действия в системе."""

    # Комнаты
    ROOM_VIEW = "room:view"  # просмотр комнаты
    ROOM_CREATE = "room:create"  # создание комнаты
    ROOM_UPDATE = "room:update"  # редактирование комнаты
    ROOM_DELETE = "room:delete"  # удаление комнаты
    ROOM_MANAGE_TEACHERS = "room:manage_teachers"  # назначение / снятие преподавателей
    ROOM_MANAGE_INVITES = "room:manage_invites"  # создание / удаление приглашений
    ROOM_VIEW_MEMBERS = "room:view_members"  # просмотр списка участников
    ROOM_REMOVE_MEMBERS = "room:remove_members"  # исключение участников

    # Уроки
    LESSON_VIEW = "lesson:view"  # просмотр урока
    LESSON_CREATE = "lesson:create"  # создание урока
    LESSON_UPDATE = "lesson:update"  # редактирование урока
    LESSON_DELETE = "lesson:delete"  # удаление урока
    LESSON_START = "lesson:start"  # старт урока
    LESSON_END = "lesson:end"  # завершение урока
    LESSON_VIEW_LOGS = "lesson:view_logs"  # просмотр логов посещаемости

    # Участники
    MEMBERSHIP_JOIN = "membership:join"  # вступить в комнату
    MEMBERSHIP_LEAVE = "membership:leave"  # покинуть комнату

    # Приглашения
    INVITE_JOIN = "invite:join"  # войти по приглашению

    # Пользователи
    USER_MANAGE_ROLES = "user:manage_roles"  # назначать роли (админ / преподаватель)


class RolePermissions:
    """
    Централизованная шина возможностей для каждой роли

    Отвечает только на вопрос:
        «Может ли роль X в принципе выполнять действие Y?»

    Контекст ресурса (чья комната, состоит ли участник и т.п.)
    проверяется отдельно в AccessPolicy.
    """

    _permissions_by_role: dict[Role, frozenset[Permission]] = {
        # === ученик: только просмотр, участие и выход ===
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
        # === учитель: создавать и редактировать комнаты / уроки, но не удалять ===
        Role.TEACHER: frozenset(
            {
                # Комнаты
                Permission.ROOM_VIEW,
                Permission.ROOM_CREATE,
                Permission.ROOM_UPDATE,
                # ROOM_DELETE — нет (только админ)
                Permission.ROOM_MANAGE_TEACHERS,
                Permission.ROOM_MANAGE_INVITES,
                Permission.ROOM_VIEW_MEMBERS,
                Permission.ROOM_REMOVE_MEMBERS,
                # Уроки
                Permission.LESSON_VIEW,
                Permission.LESSON_CREATE,
                Permission.LESSON_UPDATE,
                # LESSON_DELETE — нет (только админ)
                Permission.LESSON_START,
                Permission.LESSON_END,
                Permission.LESSON_VIEW_LOGS,
                # Участники
                Permission.MEMBERSHIP_JOIN,
                Permission.MEMBERSHIP_LEAVE,
                # Приглашения
                Permission.INVITE_JOIN,
            }
        ),
        # === админ: суперпользователь, всё включая управление ролями ===
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


class AccessPolicy:
    """
    Правила доступа, объединяющие роль и контекст ресурса

    Каждый метод отвечает на вопрос:
        «Может ли конкретный пользователь выполнить действие
         над конкретным ресурсом?»
    """

    @staticmethod
    def can_view_room(
        user: User,
        room: Room,
        *,
        has_membership: bool,
    ) -> bool:
        """Просмотр комнаты"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_VIEW):
            return False
        return room.created_by_user_id == user.id or has_membership

    @staticmethod
    def can_create_room(user: User) -> bool:
        """Создание комнаты (глобальное действие, ресурса ещё нет)"""
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.ROOM_CREATE)

    @staticmethod
    def can_update_room(user: User, room: Room) -> bool:
        """Редактирование комнаты"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_UPDATE):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_delete_room(user: User, room: Room) -> bool:
        """Удаление комнаты"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_DELETE):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_manage_room_teachers(user: User, room: Room) -> bool:
        """Управление преподавателями комнаты"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_MANAGE_TEACHERS):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_manage_room_invites(user: User, room: Room) -> bool:
        """Управление приглашениями комнаты"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_MANAGE_INVITES):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_view_room_members(
        user: User,
        room: Room,
        *,
        has_membership: bool,
    ) -> bool:
        """Просмотр списка участников комнаты"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_VIEW_MEMBERS):
            return False
        return room.created_by_user_id == user.id or has_membership

    @staticmethod
    def can_remove_room_members(user: User, room: Room) -> bool:
        """Исключение участников из комнаты"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.ROOM_REMOVE_MEMBERS):
            return False
        return room.created_by_user_id == user.id

    @staticmethod
    def can_view_lesson(
        user: User,
        room: Room,
        *,
        has_membership: bool,
    ) -> bool:
        """Просмотр урока"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_VIEW):
            return False
        return room.created_by_user_id == user.id or has_membership

    @staticmethod
    def can_create_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        """Создание урока в комнате"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_CREATE):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_update_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        """Редактирование урока"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_UPDATE):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_delete_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        """Удаление урока"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_DELETE):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_start_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        """Старт урока"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_START):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_end_lesson(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        """Завершение урока"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_END):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_view_lesson_logs(
        user: User,
        room: Room,
        *,
        is_room_teacher: bool,
    ) -> bool:
        """Просмотр логов посещаемости урока"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.LESSON_VIEW_LOGS):
            return False
        return room.created_by_user_id == user.id or is_room_teacher

    @staticmethod
    def can_join_room(user: User) -> bool:
        """Вступление в комнату (глобальное действие)"""
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.MEMBERSHIP_JOIN)

    @staticmethod
    def can_leave_room(
        user: User,
        *,
        has_membership: bool,
    ) -> bool:
        """Выход из комнаты"""
        if user.role == Role.ADMIN:
            return True
        if not RolePermissions.allows(user.role, Permission.MEMBERSHIP_LEAVE):
            return False
        return has_membership

    @staticmethod
    def can_join_by_invite(user: User) -> bool:
        """Вход в комнату по приглашению (глобальное действие)"""
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.INVITE_JOIN)

    # === пользователи ===

    @staticmethod
    def can_manage_roles(user: User) -> bool:
        """Управление ролями пользователей (только админ)"""
        if user.role == Role.ADMIN:
            return True
        return RolePermissions.allows(user.role, Permission.USER_MANAGE_ROLES)


async def _room_membership_exists(
    session: AsyncSession,
    room_id: int,
    user_id: int,
) -> bool:
    """Проверяет, есть ли у пользователя активное участие в комнате"""
    statement = select(RoomMembership).where(
        RoomMembership.room_id == room_id,
        RoomMembership.user_id == user_id,
        RoomMembership.is_active,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def _room_teacher_assignment_exists(
    session: AsyncSession,
    room_id: int,
    user_id: int,
) -> bool:
    """Проверяет, назначен ли пользователь преподавателем комнаты"""
    statement = select(RoomTeacher).where(
        RoomTeacher.room_id == room_id,
        RoomTeacher.user_id == user_id,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def get_room_or_404(
    room_id: int,
    session: AsyncSession = Depends(db.get_session),
) -> Room:
    """Возвращает комнату по `room_id` или выбрасывает 404"""
    statement = select(Room).where(Room.id == room_id)
    result = await session.execute(statement)
    room = result.scalar_one_or_none()

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комната не найдена",
        )

    return room


async def get_lesson_or_404(
    lesson_id: int,
    session: AsyncSession = Depends(db.get_session),
) -> Lesson:
    """Возвращает урок по `lesson_id` или выбрасывает 404"""
    statement = select(Lesson).where(Lesson.id == lesson_id)
    result = await session.execute(statement)
    lesson = result.scalar_one_or_none()

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Урок не найден",
        )

    return lesson


async def ensure_can_create_room(
    current_user: User = Depends(get_current_user),
) -> User:
    """Разрешает создание комнаты"""
    if not AccessPolicy.can_create_room(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания комнаты",
        )
    return current_user


async def ensure_room_creator_or_admin(
    room: Room = Depends(get_room_or_404),
    current_user: User = Depends(get_current_user),
) -> Room:
    """Разрешает доступ создателю комнаты или администратору"""
    if AccessPolicy.can_update_room(current_user, room):
        return room

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Только создатель комнаты или администратор может выполнить это действие",
    )


async def ensure_can_delete_room(
    room: Room = Depends(get_room_or_404),
    current_user: User = Depends(get_current_user),
) -> Room:
    """Разрешает удаление комнаты (создатель-учитель не может, только админ)"""
    if AccessPolicy.can_delete_room(current_user, room):
        return room

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Только администратор может удалить комнату",
    )


async def ensure_room_member_or_admin(
    room: Room = Depends(get_room_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Room:
    """Разрешает доступ участнику комнаты или администратору"""
    assert current_user.id is not None
    assert room.id is not None
    has_membership = await _room_membership_exists(session, room.id, current_user.id)

    if AccessPolicy.can_view_room(current_user, room, has_membership=has_membership):
        return room

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не состоит в этой комнате",
    )


async def ensure_room_teacher_or_admin(
    room: Room = Depends(get_room_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Room:
    """Разрешает доступ преподавателю комнаты, её создателю или администратору"""
    assert current_user.id is not None
    assert room.id is not None
    is_room_teacher = await _room_teacher_assignment_exists(
        session,
        room.id,
        current_user.id,
    )

    if AccessPolicy.can_create_lesson(
        current_user,
        room,
        is_room_teacher=is_room_teacher,
    ):
        return room

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не является преподавателем этой комнаты",
    )


async def ensure_lesson_room_member_or_admin(
    lesson: Lesson = Depends(get_lesson_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Lesson:
    """Разрешает доступ к уроку участнику его комнаты или администратору"""
    room = await _get_room_of_lesson(session, lesson)

    assert current_user.id is not None
    has_membership = await _room_membership_exists(
        session,
        lesson.room_id,
        current_user.id,
    )

    if AccessPolicy.can_view_lesson(current_user, room, has_membership=has_membership):
        return lesson

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не имеет доступа к этому уроку",
    )


async def ensure_lesson_teacher_or_admin(
    lesson: Lesson = Depends(get_lesson_or_404),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
) -> Lesson:
    """Разрешает управление уроком преподавателю комнаты, её создателю или администратору"""
    room = await _get_room_of_lesson(session, lesson)

    assert current_user.id is not None
    is_room_teacher = await _room_teacher_assignment_exists(
        session,
        lesson.room_id,
        current_user.id,
    )

    if AccessPolicy.can_start_lesson(
        current_user,
        room,
        is_room_teacher=is_room_teacher,
    ):
        return lesson

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Пользователь не может управлять этим уроком",
    )


# === пользователи ===


async def ensure_can_manage_roles(
    current_user: User = Depends(get_current_user),
) -> User:
    """Разрешает управление ролями (только админ)."""
    if not AccessPolicy.can_manage_roles(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор может управлять ролями",
        )
    return current_user


async def _get_room_of_lesson(
    session: AsyncSession,
    lesson: Lesson,
) -> Room:
    """Возвращает комнату урока или выбрасывает 404"""
    statement = select(Room).where(Room.id == lesson.room_id)
    result = await session.execute(statement)
    room = result.scalar_one_or_none()

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комната урока не найдена",
        )

    return room
