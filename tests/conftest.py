import pytest
import sqlalchemy as sa
from pytest_docker_service import docker_container
from sqlalchemy.orm import sessionmaker

from tests.config import settings
from tests.utils import wait_pg_ready

container = docker_container(
    scope="session",
    image_name=settings.POSTGRES_IMAGE_NAME,
    container_name=settings.POSTGRES_CONTAINER_NAME,
    ports={settings.POSTGRES_PORT: settings.POSTGRES_FWD_PORT},
    environment={
        "POSTGRES_USER": settings.POSTGRES_USER,
        "POSTGRES_PASSWORD": settings.POSTGRES_PASSWORD,
        "POSTGRES_DB": settings.POSTGRES_DB,
    },
)


@pytest.fixture(scope="session")
def pg_dbinfo(container):
    port = container.port_map[settings.POSTGRES_PORT]
    port = int(port[0] if isinstance(port, list) else port)
    dbinfo = {
        "port": port,
        "host": settings.POSTGRES_HOST,
        "user": settings.POSTGRES_USER,
        "password": settings.POSTGRES_PASSWORD,
        "database": settings.POSTGRES_DB,
    }
    wait_pg_ready(dbinfo)
    print(f"Prepared PostgreSQL: {dbinfo}")
    yield dbinfo


@pytest.fixture(scope="session")
def session(pg_dbinfo):
    engine = sa.create_engine("postgresql://{user}:{password}@{host}:{port}/{database}".format(**pg_dbinfo))
    with sessionmaker(bind=engine)() as session:
        yield session
