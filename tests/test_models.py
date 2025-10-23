import uuid
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from cm_customer_svc.models import User, Customer


def test_user_create_and_retrieve_by_employee_id(db_session):
    user = User(employee_id="EMP00001", employee_name="Alice", password_hash="secret")
    db_session.add(user)
    db_session.commit()

    stmt = select(User).filter_by(employee_id="EMP00001")
    retrieved_user = db_session.execute(stmt).scalar_one()

    assert retrieved_user.employee_name == "Alice"
    assert isinstance(retrieved_user.created_at, datetime)
    assert isinstance(retrieved_user.updated_at, datetime)


def test_user_update_updates_timestamp(db_session):
    user = User(employee_id="EMP00002", employee_name="Carol", password_hash="pw")
    db_session.add(user)
    db_session.commit()

    stmt = select(User).filter_by(employee_id="EMP00002")
    retrieved_user = db_session.execute(stmt).scalar_one()

    # Avoid time.sleep by setting an old timestamp, then performing an update
    old_timestamp = datetime(2000, 1, 1)
    retrieved_user.updated_at = old_timestamp
    db_session.add(retrieved_user)
    db_session.commit()
    db_session.refresh(retrieved_user)

    # Perform an update that should trigger updated_at change
    retrieved_user.employee_name = "Carol-Updated"
    db_session.add(retrieved_user)
    db_session.commit()
    db_session.refresh(retrieved_user)

    assert retrieved_user.updated_at > old_timestamp


def test_user_delete(db_session):
    user = User(employee_id="EMP00003", employee_name="Dave", password_hash="pw")
    db_session.add(user)
    db_session.commit()

    stmt = select(User).filter_by(employee_id="EMP00003")
    retrieved_user = db_session.execute(stmt).scalar_one()

    db_session.delete(retrieved_user)
    db_session.commit()

    stmt2 = select(User).filter_by(employee_id="EMP00003")
    res = db_session.execute(stmt2).scalar_one_or_none()
    assert res is None


def test_user_employee_id_uniqueness(db_session):
    user1 = User(employee_id="EMP00004", employee_name="Eve", password_hash="pw")
    db_session.add(user1)
    db_session.commit()

    user2 = User(employee_id="EMP00004", employee_name="Eve2", password_hash="pw2")
    db_session.add(user2)
    # depending on DB, this should raise IntegrityError on commit
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_employee_id_length_schema(db_session):
    # Schema-level length enforcement can be inspected on the Column type
    assert getattr(User.__table__.c.employee_id.type, "length", None) == 8


def test_customer_create_linked_to_user_and_retrieve_by_customer_id(db_session):
    manager = User(employee_id="EMP10001", employee_name="Manager", password_hash="pw")
    db_session.add(manager)
    db_session.commit()

    customer = Customer(
        customer_name="Acme Corp",
        customer_contact="1234567890",
        customer_address="1 Main St",
        managed_by=manager.employee_id,
    )
    db_session.add(customer)
    db_session.commit()

    stmt = select(Customer).filter_by(customer_name="Acme Corp")
    retrieved_customer = db_session.execute(stmt).scalar_one()

    assert retrieved_customer.managed_by == manager.employee_id
    assert isinstance(retrieved_customer.created_at, datetime)
    assert isinstance(retrieved_customer.updated_at, datetime)

    # customer_id should be present and parseable as UUID
    parsed = uuid.UUID(str(retrieved_customer.customer_id))
    assert isinstance(parsed, uuid.UUID)


def test_customer_update_updates_timestamp(db_session):
    manager = User(employee_id="EMP10002", employee_name="Manager2", password_hash="pw")
    db_session.add(manager)
    db_session.commit()

    customer = Customer(
        customer_name="Beta LLC",
        customer_contact="000",
        customer_address="Old Addr",
        managed_by=manager.employee_id,
    )
    db_session.add(customer)
    db_session.commit()

    stmt = select(Customer).filter_by(customer_name="Beta LLC")
    retrieved_customer = db_session.execute(stmt).scalar_one()

    # Avoid time.sleep by setting an old timestamp first
    old_timestamp = datetime(2000, 1, 1)
    retrieved_customer.updated_at = old_timestamp
    db_session.add(retrieved_customer)
    db_session.commit()
    db_session.refresh(retrieved_customer)

    # Update a field to trigger updated_at change
    retrieved_customer.customer_address = "New Addr"
    db_session.add(retrieved_customer)
    db_session.commit()
    db_session.refresh(retrieved_customer)

    assert retrieved_customer.updated_at > old_timestamp


def test_customer_delete(db_session):
    manager = User(employee_id="EMP10003", employee_name="Manager3", password_hash="pw")
    db_session.add(manager)
    db_session.commit()

    customer = Customer(
        customer_name="Gamma Inc",
        managed_by=manager.employee_id,
    )
    db_session.add(customer)
    db_session.commit()

    stmt = select(Customer).filter_by(customer_name="Gamma Inc")
    retrieved_customer = db_session.execute(stmt).scalar_one()

    db_session.delete(retrieved_customer)
    db_session.commit()

    stmt2 = select(Customer).filter_by(customer_name="Gamma Inc")
    res = db_session.execute(stmt2).scalar_one_or_none()
    assert res is None


def test_customer_creation_with_existing_user_employee_id(db_session):
    manager = User(employee_id="EMP10004", employee_name="Manager4", password_hash="pw")
    db_session.add(manager)
    db_session.commit()

    customer = Customer(customer_name="Delta Co", managed_by=manager.employee_id)
    db_session.add(customer)
    db_session.commit()

    stmt = select(Customer).filter_by(customer_name="Delta Co")
    retrieved_customer = db_session.execute(stmt).scalar_one_or_none()
    assert retrieved_customer is not None
    assert retrieved_customer.managed_by == manager.employee_id
