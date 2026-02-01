from wheke import Pod, ServiceConfig

from ._cli import cli
from ._service import SQLModelService, sqlmodel_service_factory

sqlmodel_pod = Pod(
    "sqlmodel",
    services=[
        ServiceConfig(
            SQLModelService,
            sqlmodel_service_factory,
            is_singleton=True,
            singleton_cleanup_method="dispose",
        ),
    ],
    cli=cli,
)
