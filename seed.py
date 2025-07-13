# seed.py

from app import create_app
from app.extensions import db
from app.models import User, Car, Rental
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, timezone

def seed():
    app = create_app()
    with app.app_context():
        # wipe existing data
        Rental.query.delete()
        Car.query.delete()
        User.query.delete()
        db.session.commit()

        # 1) Merchants
        m1 = User(username="rent_co_alpha",
                  password=generate_password_hash("AlphaPass1"),
                  role="merchant")
        m2 = User(username="rent_co_bravo",
                  password=generate_password_hash("BravoPass2"),
                  role="merchant")
        db.session.add_all([m1, m2])
        db.session.commit()

        # 2) Users
        u1 = User(username="alice",
                  password=generate_password_hash("alice123"),
                  role="user")
        u2 = User(username="bob",
                  password=generate_password_hash("bob123"),
                  role="user")
        u3 = User(username="carol",
                  password=generate_password_hash("carol123"),
                  role="user")
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        # 3) Cars
        cars = [
            Car(model="Toyota Corolla", plate="ABC-1001", daily_rate=40.00, merchant_id=m1.id),
            Car(model="Honda Civic",    plate="DEF-2002", daily_rate=45.50, merchant_id=m1.id),
            Car(model="Ford Focus",     plate="GHI-3003", daily_rate=38.25, merchant_id=m2.id),
            Car(model="Chevy Malibu",   plate="JKL-4004", daily_rate=50.00, merchant_id=m2.id),
        ]
        db.session.add_all(cars)
        db.session.commit()

        # 4) Rentals: two past, one active (now including merchant_id)
        now = datetime.now(timezone.utc)
        past1 = Rental(
            user_id     = u1.id,
            car_id      = cars[0].id,
            merchant_id = cars[0].merchant_id,
            start_date  = now - timedelta(days=5),
            end_date    = now - timedelta(days=2)
        )
        past2 = Rental(
            user_id     = u2.id,
            car_id      = cars[2].id,
            merchant_id = cars[2].merchant_id,
            start_date  = now - timedelta(days=3),
            end_date    = now - timedelta(days=1)
        )
        active = Rental(
            user_id     = u3.id,
            car_id      = cars[1].id,
            merchant_id = cars[1].merchant_id,
            start_date  = now - timedelta(hours=10)
        )

        db.session.add_all([past1, past2, active])
        db.session.flush()   # load relationships so calculate_fee works

        # calculate fees on returned ones
        past1.fee = past1.calculate_fee()
        past2.fee = past2.calculate_fee()
        db.session.commit()

        print("🟢 Seed data inserted:")
        print(f"  Merchants: {[m1.username, m2.username]}")
        print(f"  Users:     {[u1.username, u2.username, u3.username]}")
        print(f"  Cars:      {[c.plate for c in cars]}")
        print(f"  Rentals:   {[past1.id, past2.id, active.id]}")

if __name__ == "__main__":
    seed()
