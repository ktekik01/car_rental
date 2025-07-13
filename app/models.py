from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role     = db.Column(db.String(20), nullable=False)

class Car(db.Model):
    __tablename__ = 'cars'
    id           = db.Column(db.Integer, primary_key=True)
    model        = db.Column(db.String(120), nullable=False)
    plate        = db.Column(db.String(20), unique=True, nullable=False)
    daily_rate   = db.Column(db.Numeric(10,2), nullable=False)
    merchant_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    merchant     = db.relationship('User', backref='cars')

    def to_dict(self):
        return {
            'id': self.id,
            'model': self.model,
            'plate': self.plate,
            'daily_rate': str(self.daily_rate)
        }

class Rental(db.Model):
    __tablename__ = 'rentals'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    car_id       = db.Column(db.Integer, db.ForeignKey('cars.id'),    nullable=True)
    merchant_id  = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    start_date   = db.Column(db.DateTime, default=datetime.utcnow)
    end_date     = db.Column(db.DateTime, nullable=True)
    fee          = db.Column(db.Numeric(10,2), nullable=True)

    # explicitly tell SQLAlchemy which foreign key each relationship uses:
    user     = db.relationship(
        'User',
        foreign_keys=[user_id],
        backref=db.backref('rentals', lazy='dynamic'),
    )
    merchant = db.relationship(
        'User',
        foreign_keys=[merchant_id],
        backref=db.backref('merchant_rentals', lazy='dynamic'),
    )
    car      = db.relationship('Car', backref='rentals')

    def calculate_fee(self):
        if not self.end_date:
            return None
        delta = self.end_date - self.start_date
        days  = delta.days + 1
        return days * float(self.car.daily_rate)

    def to_dict(self):
        return {
            "id":         self.id,
            "user_id":    self.user_id,
            "merchant_id": self.merchant_id,
            "car_id":     self.car_id,
            "start_date": self.start_date.isoformat(),
            "end_date":   self.end_date.isoformat() if self.end_date else None,
            "fee":        str(self.fee) if self.fee is not None else None,
        }
