from sqlalchemy import select
from cm_customer_svc.models import User, Customer


def test_user_and_customer_models(db_session):
    # create a user
    user = User(employee_id="EMP00001", employee_name="Alice", password_hash="secret")
    db_session.add(user)
    db_session.commit()

    stmt = select(User).filter_by(employee_id="EMP00001")
    u = db_session.execute(stmt).scalar_one()
    assert u.employee_name == "Alice"

    # create a customer managed by the user
    customer = Customer(
        customer_name="Acme Corp",
        customer_contact="1234567890",
        customer_address="1 Main St",
        managed_by=u.employee_id,
    )
    db_session.add(customer)
    db_session.commit()

    stmt2 = select(Customer).filter_by(customer_name="Acme Corp")
    c = db_session.execute(stmt2).scalar_one()
    assert c.managed_by == u.employee_id
    assert c.customer_id is not None
