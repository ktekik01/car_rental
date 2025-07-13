from flask import Blueprint, request, jsonify, url_for
from app.auth import basic_auth_required, roles_required
from app.models import Car, Rental
from app.extensions import db
from app.utils import paginate_query
from datetime import datetime

cars_bp = Blueprint('cars', __name__)




# List all cars
@cars_bp.route('/cars', methods=['GET'])
@basic_auth_required
def list_cars():
    q = Car.query
    return jsonify(paginate_query(q, 'cars.list_cars'))

# Create car
@cars_bp.route('/cars', methods=['POST'])
@basic_auth_required
@roles_required('merchant')
def create_car():
    data = request.get_json() or {}
    model, plate, rate = data.get('model'), data.get('plate'), data.get('daily_rate')
    if not all([model,plate,rate]):
        return jsonify({'error':'model, plate and daily_rate required'}),400
    if Car.query.filter_by(plate=plate).first():
        return jsonify({'error':'plate exists'}),400
    car = Car(model=model, plate=plate, daily_rate=rate, merchant_id=request.current_user.id)
    db.session.add(car)
    db.session.commit()
    return jsonify(car.to_dict()),201


@cars_bp.route("/cars/<int:car_id>", methods=["PUT"])
@basic_auth_required
@roles_required("merchant")
def update_car(car_id):
    car = Car.query.get_or_404(car_id)
    # Ownership check
    if car.merchant_id != request.current_user.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json() or {}
    # Only update provided fields
    if "model" in data:
        car.model = data["model"]
    if "plate" in data:
        # ensure unique
        if Car.query.filter(Car.plate==data["plate"], Car.id!=car_id).first():
            return jsonify({"error": "plate already exists"}), 400
        car.plate = data["plate"]
    if "daily_rate" in data:
        car.daily_rate = data["daily_rate"]

    db.session.commit()
    return jsonify({
        "id":         car.id,
        "model":      car.model,
        "plate":      car.plate,
        "daily_rate": str(car.daily_rate)
    })



@cars_bp.route("/cars/<int:car_id>", methods=["DELETE"])
@basic_auth_required
@roles_required("merchant")
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    if car.merchant_id != request.current_user.id:
        return jsonify({"error": "forbidden"}), 403

    # 1) Close out any active rental
    active = Rental.query.filter_by(car_id=car.id, end_date=None).first()
    if active:
        active.end_date = datetime.utcnow()
        active.fee = active.calculate_fee()
        db.session.commit()  # persist the end/fee

    # 2) Now drop the car — rental.car_id will be set to NULL automatically
    db.session.delete(car)
    db.session.commit()

    return "", 204


# List all cars for a specific merchant (anyone can view)
@cars_bp.route("/merchants/<int:merchant_id>/cars", methods=["GET"])
@basic_auth_required
def merchant_cars(merchant_id):
    """
    List all cars for the given merchant_id, paginated.
    Anyone with Basic-Auth (user or merchant) may view.
    """
    q = Car.query.filter_by(merchant_id=merchant_id)
    return jsonify(
        paginate_query(
            q,
            "merchant_cars",
            merchant_id=merchant_id
        )
    )
