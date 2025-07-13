from flask import Blueprint, request, jsonify, url_for
from app.auth import basic_auth_required, roles_required
from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import joinedload
from app.utils import paginate_query
from app.models import Car, User, Rental


rentals_bp = Blueprint('rentals', __name__)

# Create rental
@rentals_bp.route('/rentals', methods=['POST'])
@basic_auth_required
@roles_required('user')
def create_rental():
    data = request.get_json() or {}
    car_id = data.get('car_id')
    if not car_id:
        return jsonify({'error': 'car_id required'}), 400

    # 1) one active rental per user
    active = Rental.query.filter_by(
        user_id=request.current_user.id,
        end_date=None
    ).first()
    if active:
        return jsonify({'error': 'already have active', 'rental_id': active.id}), 400

    # 2) car must be free
    busy = Rental.query.filter_by(car_id=car_id, end_date=None).first()
    if busy:
        return jsonify({'error': 'car busy', 'rental_id': busy.id}), 400

    # 3) load the Car so we can get its merchant_id
    car = Car.query.get_or_404(car_id)

    # 4) create the rental including merchant_id
    r = Rental(
        user_id=request.current_user.id,
        car_id=car_id,
        merchant_id=car.merchant_id
    )
    db.session.add(r)
    db.session.commit()

    return jsonify({
        'id': r.id,
        'start_date': r.start_date.isoformat()
    }), 201

# Return rental
@rentals_bp.route('/<int:rid>/return', methods=['PUT'])
@basic_auth_required
@roles_required('user')
def return_rental(rid):
    r = Rental.query.get_or_404(rid)
    if r.user_id != request.current_user.id:
        return jsonify({'error':'forbidden'}),403
    if r.end_date:
        return jsonify({'error':'already returned'}),400
    r.end_date = datetime.utcnow()
    r.fee      = r.calculate_fee()
    db.session.commit()
    return jsonify({'rental_id':r.id,'end_date':r.end_date.isoformat(),'fee':r.fee})



# View your own rental history (authenticated merchant only)
@rentals_bp.route("/merchants/me/rentals", methods=["GET"])
@basic_auth_required
@roles_required("merchant")
def merchant_rentals_self():
    """
    Return all rentals (active + past) for cars owned by the authenticated merchant,
    paginated and with next/prev URLs.
    """
    merchant_id = request.current_user.id

    # now that Rental has its own merchant_id column, we can filter directly
    q = (
        Rental.query
        .filter_by(merchant_id=merchant_id)
        .options(joinedload(Rental.car))   # if you still want the car relationship loaded
    )

    return jsonify(
        paginate_query(
            q,
            endpoint="rentals.merchant_rentals_self",
            merchant_id=merchant_id
        )
    )


# List all rentals for a specific user (user only)
@rentals_bp.route("/users/<int:user_id>/rentals", methods=["GET"])
@basic_auth_required
@roles_required("user")  # both users and merchants can view rentals
def user_rentals(user_id):
    if user_id != request.current_user.id:
        return jsonify({"error":"forbidden"}), 403
    q = Rental.query.filter_by(user_id=user_id)
    return jsonify(paginate_query(
    q,
    "user_rentals",
    serializer=lambda r: {
        "id":         r.id,
        "user_id":    r.user_id,
        "car_id":     r.car_id,
        "start_date": r.start_date.isoformat(),
        "end_date":   r.end_date.isoformat() if r.end_date else None,
        "fee":        str(r.fee) if r.fee is not None else None
    },
    user_id=user_id
    ))
