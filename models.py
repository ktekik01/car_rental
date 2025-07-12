from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # hashed!
    role     = db.Column(db.Enum("merchant", "user", name="user_roles"), nullable=False, default="user")

    rentals  = db.relationship("Rental", back_populates="customer")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role
        }

class Car(db.Model):
    __tablename__ = "cars"
    id          = db.Column(db.Integer, primary_key=True)
    model       = db.Column(db.String(120), nullable=False)
    plate       = db.Column(db.String(20), unique=True, nullable=False)
    daily_rate  = db.Column(db.Numeric(10, 2), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    rentals     = db.relationship("Rental", back_populates="car")
    merchant    = db.relationship("User", backref="cars")

    def to_dict(self):
        return {
            "id": self.id,
            "model": self.model,
            "plate": self.plate,
            "daily_rate": str(self.daily_rate),
            "merchant_id": self.merchant_id
        }

class Rental(db.Model):
    __tablename__ = "rentals"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), index=True, nullable=False)
    car_id     = db.Column(db.Integer, db.ForeignKey("cars.id", ondelete="SET NULL"), index=True,
nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date   = db.Column(db.DateTime, index=True)
    fee        = db.Column(db.Numeric(10, 2))

    customer   = db.relationship("User", back_populates="rentals")
    car        = db.relationship("Car", back_populates="rentals")

    def calculate_fee(self):
        """Simple price logic: days * car.daily_rate"""
        if not self.end_date:
            return None
        days = (self.end_date - self.start_date).days or 1
        return float(days) * float(self.car.daily_rate)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "car_id": self.car_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "fee": float(self.fee) if self.fee is not None else None
        }
