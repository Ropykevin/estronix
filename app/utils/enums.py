"""SQLAlchemy enum helpers for PostgreSQL compatibility."""


def enum_values(enum_cls):
    """Persist enum member values (lowercase) — for enterprise migrations."""
    return [member.value for member in enum_cls]


def enum_names(enum_cls):
    """Persist enum member names (UPPERCASE) — for initial migration enums."""
    return [member.name for member in enum_cls]
