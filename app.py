from flask import Flask, request, jsonify, current_app, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Car, Rental
from auth import basic_auth_required, roles_required
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy.orm import joinedload

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

migrate = Migrate(app, db)     


# User registration endpoint
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    role     = data.get("role", "user")

    # 1) basic validation
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    # 2) enforce allowed roles
    if role not in ("user", "merchant"):
        return jsonify({"error": "invalid role"}), 400

    # 3) username uniqueness
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username taken"}), 400

    # 4) create the user
    user = User(
        username=username,
        password=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "registered",
        "role": role
    }), 201


# basic auth login endpoint, not functional with Basic Auth but I coded it as a template for future auth methods
@app.route("/login")
def login():
    auth = request.authorization
    if not auth:
        return jsonify({"error": "missing credentials"}), 401

    user = User.query.filter_by(username=auth.username).first()
    if not user or not check_password_hash(user.password, auth.password):
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify({"message": f"welcome, {user.username}"})


# for performance, a simple pagination util 
def paginate_query(query, endpoint, **kwargs):
    page     = request.args.get("page",     1,  type=int)
    per_page = request.args.get("per_page", 1, type=int)
    pag      = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        "items":     [item.to_dict() for item in pag.items],
        "total":     pag.total,
        "pages":     pag.pages,
        "page":      pag.page,
        "per_page":  pag.per_page,
        "has_next":  pag.has_next,
        "has_prev":  pag.has_prev,
        "next_url":  url_for(endpoint, page=pag.page+1, per_page=pag.per_page, _external=True, **kwargs) if pag.has_next else None,
        "prev_url":  url_for(endpoint, page=pag.page-1, per_page=pag.per_page, _external=True, **kwargs) if pag.has_prev else None
    }


# list all cars (anyone can view)
@app.route("/cars", methods=["GET"])
@basic_auth_required
def list_cars():
    q = Car.query
    return jsonify(paginate_query(q, "list_cars"))


# Create a rental (user only)
@app.route("/rentals", methods=["POST"])
@basic_auth_required
@roles_required("user")
def create_rental():
    data = request.get_json() or {}
    car_id = data.get("car_id")
    if not car_id:
        return jsonify({"error": "car_id is required"}), 400

    # 1) You can only have one active rental yourself
    existing_self = Rental.query.filter_by(
        user_id=request.current_user.id,
        end_date=None
    ).first()
    if existing_self:
        return jsonify({
            "error": "You already have an active rental",
            "rental_id": existing_self.id
        }), 400

    # 2) That car must be available (no other rental with end_date NULL)
    existing_car = Rental.query.filter_by(
        car_id=car_id,
        end_date=None
    ).first()
    if existing_car:
        return jsonify({
            "error": "Car is already rented",
            "rental_id": existing_car.id
        }), 400

    # 3) create the rental
    rental = Rental(
        user_id=request.current_user.id,
        car_id=car_id
    )
    db.session.add(rental)
    db.session.commit()

    return jsonify({
        "id": rental.id,
        "start_date": rental.start_date.isoformat()
    }), 201


# CRUD operations for cars (merchant only)
@app.route("/cars", methods=["POST"])
@basic_auth_required
@roles_required("merchant")
def create_car():
    data = request.get_json() or {}
    model      = data.get("model")
    plate      = data.get("plate")
    daily_rate = data.get("daily_rate")

    # Basic validation
    if not all([model, plate, daily_rate]):
        return jsonify({"error": "model, plate and daily_rate are required"}), 400

    # Prevent duplicate plates
    if Car.query.filter_by(plate=plate).first():
        return jsonify({"error": "plate already exists"}), 400

    car = Car(
        model=model,
        plate=plate,
        daily_rate=daily_rate,
        merchant_id=request.current_user.id
    )
    db.session.add(car)
    db.session.commit()

    return jsonify({
        "id":         car.id,
        "model":      car.model,
        "plate":      car.plate,
        "daily_rate": str(car.daily_rate)
    }), 201

@app.route("/cars/<int:car_id>", methods=["PUT"])
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




@app.route("/cars/<int:car_id>", methods=["DELETE"])
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


# Return a rental (user only)
@app.route("/rentals/<int:rental_id>/return", methods=["PUT"])
@basic_auth_required
@roles_required("user")
def return_rental(rental_id):
    rental = Rental.query.get_or_404(rental_id)

    # 1) Only the user who created this rental can return it
    if rental.user_id != request.current_user.id:
        return jsonify({"error": "forbidden"}), 403

    # 2) Check if it's already returned
    if rental.end_date:
        return jsonify({"error": "Car already returned"}), 400

    # 3) Close out the rental
    rental.end_date = datetime.utcnow()
    rental.fee      = rental.calculate_fee()
    db.session.commit()

    return jsonify({
        "rental_id": rental.id,
        "end_date":  rental.end_date.isoformat(),
        "fee":       rental.fee
    })



# View your own rental history (authenticated merchant only)
@app.route("/merchants/me/rentals", methods=["GET"])
@basic_auth_required
@roles_required("merchant")
def merchant_rentals_self():
    """
    Return all rentals (active + past) for cars owned by the authenticated merchant.
    """
    merchant_id = request.current_user.id
    page        = request.args.get("page",     1,  type=int)
    per_page    = request.args.get("per_page", 20, type=int)

    query = (
        Rental.query
        .join(Car, Rental.car_id == Car.id)
        .options(joinedload(Rental.car))
        .filter(Car.merchant_id == merchant_id)
    )
    pag = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [
            {
                "rental_id": r.id,
                "car": {
                    "id":    r.car.id,
                    "model": r.car.model,
                    "plate": r.car.plate,
                    "daily_rate": str(r.car.daily_rate)
                },
                "user_id":    r.user_id,
                "start_date": r.start_date.isoformat(),
                "end_date":   r.end_date.isoformat() if r.end_date else None,
                "fee":        r.fee
            }
            for r in pag.items
        ],
        "total": pag.total,
        "pages": pag.pages,
        "page":  pag.page
    })

# List all cars for a specific merchant (anyone can view)
@app.route("/merchants/<int:merchant_id>/cars", methods=["GET"])
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

# List all rentals for a specific user (user only)
@app.route("/users/<int:user_id>/rentals", methods=["GET"])
@basic_auth_required
@roles_required("user")  # both users and merchants can view rentals
def user_rentals(user_id):
    if user_id != request.current_user.id:
        return jsonify({"error":"forbidden"}), 403
    q = Rental.query.filter_by(user_id=user_id)
    return jsonify(paginate_query(q, "user_rentals", user_id=user_id))




if __name__ == "__main__":
    app.run(debug=True)
