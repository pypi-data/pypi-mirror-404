from typing import ClassVar

from wheke import FeatureSettings

SQLITE_DRIVER = "sqlite+aiosqlite"


class SQLModelSettings(FeatureSettings):
    __feature_name__: ClassVar[str] = "sqlmodel"

    connection_string: str = f"{SQLITE_DRIVER}:///database.db"

    echo_operations: bool = False
