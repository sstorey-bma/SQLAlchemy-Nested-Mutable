from functools import reduce
from typing import List
from typing import Optional

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Session
from sqlalchemy_nested_mutable import MutablePydanticBaseModel
from sqlalchemy_nested_mutable import TrackedList
from sqlalchemy_nested_mutable import TrackedPydanticBaseModel
from sqlalchemy_nested_mutable._compat import pydantic


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return reduce(_getattr, attr.split("."), obj)


class Base(DeclarativeBase):
    pass


class Addresses(MutablePydanticBaseModel):
    class AddressItem(pydantic.BaseModel):
        street: str
        city: str
        area: Optional[str] = None

    preferred: Optional[AddressItem] = None
    work: List[AddressItem] = []
    home: List[AddressItem] = []
    updated_time: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)


@pytest.fixture(scope="module")
def user1():
    return User(name="foo", addresses={"preferred": {"street": "bar", "city": "baz", "area": None}})


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    addresses: Mapped[Optional[Addresses]] = mapped_column(Addresses.as_mutable(JSON()), nullable=True)


@pytest.fixture(scope="module", autouse=True)
def _with_tables(session: Session):
    Base.metadata.create_all(session.bind)  # type: ignore
    yield
    session.execute(sa.text("""
    DROP TABLE user_account CASCADE;
    """))
    session.commit()


def test_mutable_pydantic_type(session: Session, user1: User):

    # Arrange
    u = user1

    # Act
    session.add(u)
    session.commit()

    # Assert
    assert isinstance(u.addresses, MutablePydanticBaseModel)
    assert isinstance(u.addresses.preferred, Addresses.AddressItem)
    assert isinstance(u.addresses.preferred, TrackedPydanticBaseModel)
    assert isinstance(u.addresses.home, TrackedList)
    assert type(u.addresses.preferred).__name__ == "TrackedAddressItem"


def test_mutable_pydantic_type_shallow_change(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act - Shallow change
    a = u.addresses
    assert a is not None

    a.updated_time = "2021-01-01T00:00:00"
    session.commit()

    # Assert
    assert a.updated_time == "2021-01-01T00:00:00"


def test_mutable_pydantic_type_deep_change(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act - Deep change (assert to avoid type check errors)
    a = u.addresses
    assert a is not None
    p = a.preferred
    assert p is not None
    p.street = "bar2"
    session.commit()

    # Assert
    assert a is not None
    assert p is not None
    assert p.model_dump(exclude_none=True) == {"street": "bar2", "city": "baz"}


def test_mutable_pydantic_type_deep_append(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act - Append item
    assert u.addresses is not None
    u.addresses.home.append(Addresses.AddressItem.model_validate({"street": "bar3", "city": "baz"}))
    session.commit()

    # Assert
    assert u.addresses.home[0].model_dump(exclude_none=True) == {"street": "bar3", "city": "baz"}
    assert isinstance(u.addresses.home[0], TrackedPydanticBaseModel)
    assert isinstance(u.addresses.home[0], Addresses.AddressItem)


def test_mutable_pydantic_type_deep_pop(session: Session, user1: User):

    # Arrange
    u = user1
    assert u.addresses is not None
    u.addresses.home.append(Addresses.AddressItem.model_validate({"street": "bar3", "city": "baz"}))
    u.addresses.home.append(Addresses.AddressItem.model_validate({"street": "bar4", "city": "baz"}))
    u.addresses.home.append(Addresses.AddressItem.model_validate({"street": "bar5", "city": "baz"}))
    session.add(u)
    session.commit()

    # Act - Append item
    u.addresses.home.pop()
    session.commit()

    # Assert
    assert u.addresses.home[0].model_dump(exclude_none=True) == {"street": "bar3", "city": "baz"}
    assert u.addresses.home[1].model_dump(exclude_none=True) == {"street": "bar4", "city": "baz"}
    assert len(u.addresses.home) == 2
