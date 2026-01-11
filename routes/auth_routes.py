from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from utils.db import users_collection
from models.user_model import User

auth_bp = Blueprint("auth", __name__)

# REGISTER
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json

    required_fields = [
        "name", "email", "password", "phone",
        "role", "address", "location"
    ]

    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"message": f"{field} is required"}), 400

    if not data["location"].get("lat") or not data["location"].get("lng"):
        return jsonify({"message": "Valid location is required"}), 400

    if users_collection.find_one({"email": data["email"]}):
        return jsonify({"message": "User already exists"}), 400

    user = User(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        phone=data["phone"],
        role=data["role"],
        address=data["address"],
        location=data["location"]
    )

    users_collection.insert_one(user.__dict__)
    return jsonify({"message": "User registered successfully"}), 201



# LOGIN
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    user = users_collection.find_one({"email": data["email"]})

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    if not User.verify_password(user["password"], data["password"]):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(
        identity=str(user["_id"]),
        additional_claims={"role": user["role"]}
    )

    return jsonify({
        "access_token": token,
        "role": user["role"],
        "name": user["name"]
    })
