from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from svcs import Container
from wheke import WhekeSettings, get_service, get_settings

from ._settings import SQLModelSettings


class SQLModelService:
    engine: AsyncEngine

    def __init__(self, *, settings: SQLModelSettings) -> None:
        self.engine = create_async_engine(
            settings.connection_string,
            connect_args={
                "check_same_thread": False,
            },
            echo=settings.echo_operations,
        )

    @property
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        async with AsyncSession(self.engine) as _session:
            yield _session

    async def create_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def drop_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

    async def dispose(self) -> None:
        await self.engine.dispose()


def sqlmodel_service_factory(container: Container) -> SQLModelService:
    settings = get_settings(container, WhekeSettings).get_feature(SQLModelSettings)

    return SQLModelService(settings=settings)


def get_sqlmodel_service(container: Container) -> SQLModelService:
    return get_service(container, SQLModelService)
