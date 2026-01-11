from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.food_model import Food
from utils.db import foods_collection, users_collection
from utils.role_required import role_required
from bson import ObjectId

food_bp = Blueprint("food", __name__)

# =========================
# GET MY FOODS (DONOR)
# =========================
@food_bp.route("/my-foods", methods=["GET"])
@jwt_required()
@role_required(["donor"])
def get_my_foods():
    donor_id = get_jwt_identity()

    foods = list(
        foods_collection.find(
            {"donorId": donor_id},
            {
                "_id": 1,
                "foodName": 1,
                "quantity": 1,
                "foodType": 1,
                "itemCategory": 1,
                "expiryTime": 1,
                "status": 1,
                "address": 1,
                "image": 1,
                "isSameAsLocation": 1
            }
        ).sort("createdAt", -1)
    )

    for food in foods:
        food["_id"] = str(food["_id"])

    return jsonify(foods), 200


# =========================
# GET ALL FOODS (COMMUNITY)
# =========================
"""
@food_bp.route("/all-foods", methods=["GET"])
@jwt_required()
@role_required(["donor"])
def get_all_foods():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 5))
    skip = (page - 1) * limit

    foods = list(
        foods_collection.find(
            {},
            {
                "foodName": 1,
                "quantity": 1,
                "itemCategory": 1,
                "status": 1,
                "expiryTime": 1,
                "address": 1,
                "image": 1
            }
        )
        .sort("createdAt", -1)
        .skip(skip)
        .limit(limit)
    )

    total = foods_collection.count_documents({})

    for f in foods:
        f["_id"] = str(f["_id"])

    return jsonify({
        "foods": foods,
        "total": total
    }), 200"""



# =========================
# ADD FOOD
# =========================
@food_bp.route("/add", methods=["POST"])
@jwt_required()
@role_required(["donor"])
def add_food():
    data = request.json

    required_fields = [
        "foodName",
        "quantity",
        "foodType",
        "itemCategory",
        "expiryTime",
        "location",
        "address",
        "isSameAsLocation",
        "image"
    ]

    for field in required_fields:
        if field not in data or data[field] in ["", None]:
            return jsonify({"message": f"{field} is required"}), 400

    if data["itemCategory"] not in ["cooked", "packed"]:
        return jsonify({"message": "Invalid item category"}), 400

    donor_id = get_jwt_identity()

    food = Food(
        donor_id=donor_id,
        food_name=data["foodName"],
        quantity=data["quantity"],
        food_type=data["foodType"],
        item_category=data["itemCategory"],
        expiry_time=datetime.fromisoformat(data["expiryTime"]),
        location=data["location"],
        address=data["address"],
        is_same_as_location=data["isSameAsLocation"],
        image=data["image"]
    )

    foods_collection.insert_one(food.__dict__)

    return jsonify({"message": "Item added successfully"}), 201


# =========================
# UPDATE FOOD
# =========================
@food_bp.route("/update/<food_id>", methods=["PUT"])
@jwt_required()
@role_required(["donor"])
def update_food(food_id):
    donor_id = get_jwt_identity()
    data = request.json

    food = foods_collection.find_one({
        "_id": ObjectId(food_id),
        "donorId": donor_id
    })

    if not food:
        return jsonify({"message": "Food not found"}), 404

    if food["status"] in ["picked", "delivered"]:
        return jsonify({"message": "Cannot edit picked or delivered food"}), 400

    update_fields = {}

    if "foodName" in data:
        update_fields["foodName"] = data["foodName"]

    if "quantity" in data:
        update_fields["quantity"] = data["quantity"]

    if "expiryTime" in data:
        update_fields["expiryTime"] = datetime.fromisoformat(data["expiryTime"])

    if "address" in data:
        update_fields["address"] = data["address"]

    if not update_fields:
        return jsonify({"message": "No fields to update"}), 400

    foods_collection.update_one(
        {"_id": ObjectId(food_id)},
        {"$set": update_fields}
    )

    return jsonify({"message": "Food updated successfully"}), 200


# =========================
# DELETE FOOD
# =========================
@food_bp.route("/delete/<food_id>", methods=["DELETE"])
@jwt_required()
@role_required(["donor"])
def delete_food(food_id):
    donor_id = get_jwt_identity()

    food = foods_collection.find_one({
        "_id": ObjectId(food_id),
        "donorId": donor_id
    })

    if not food:
        return jsonify({"message": "Food not found"}), 404

    if food["status"] in ["picked", "delivered"]:
        return jsonify({"message": "Cannot delete picked or delivered food"}), 400

    foods_collection.delete_one({"_id": ObjectId(food_id)})

    return jsonify({"message": "Food deleted successfully"}), 200


# =========================
# DONOR DASHBOARD STATS
# =========================
@food_bp.route("/donor-stats", methods=["GET"])
@jwt_required()
@role_required(["donor"])
def donor_food_stats():
    donor_id = get_jwt_identity()

    total = foods_collection.count_documents({"donorId": donor_id})
    delivered = foods_collection.count_documents({
        "donorId": donor_id,
        "status": "delivered"
    })
    expired = foods_collection.count_documents({
        "donorId": donor_id,
        "status": "expired"
    })

    return jsonify({
        "total": total,
        "delivered": delivered,
        "expired": expired
    }), 200

@food_bp.route("/available", methods=["GET"])
@jwt_required()
@role_required(["volunteer", "donor"])
def get_available_food():
    foods = list(
        foods_collection.find(
            {"status": "available"},
            {
                "_id": 1,
                "foodName": 1,
                "quantity": 1,
                "foodType": 1,
                "itemCategory": 1,
                "expiryTime": 1,
                "address": 1,
                "location": 1,
                "image": 1
            }
        ).sort("expiryTime", 1)
    )

    for food in foods:
        food["_id"] = str(food["_id"])

    return jsonify(foods), 200

@food_bp.route("/reserve/<food_id>", methods=["POST"])
@jwt_required()
@role_required(["volunteer"])
def reserve_food(food_id):
    volunteer_id = get_jwt_identity()

    result = foods_collection.update_one(
        {
            "_id": ObjectId(food_id),
            "status": "available"
        },
        {
            "$set": {
                "status": "reserved",
                "reservedBy": volunteer_id,
                "reservedAt": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        return jsonify({"message": "Food already reserved or unavailable"}), 400

    return jsonify({"message": "Food reserved successfully"}), 200


@food_bp.route("/my-cart", methods=["GET"])
@jwt_required()
@role_required(["volunteer"])
def get_my_cart():
    volunteer_id = get_jwt_identity()

    foods = list(
        foods_collection.find(
            {
                "reservedBy": volunteer_id,
                "status": {"$in": ["reserved", "picked"]}
            }
        ).sort("reservedAt", -1)
    )

    for food in foods:
        food["_id"] = str(food["_id"])

    return jsonify(foods), 200


@food_bp.route("/pick/<food_id>", methods=["POST"])
@jwt_required()
@role_required(["volunteer"])
def pick_food(food_id):
    volunteer_id = get_jwt_identity()

    result = foods_collection.update_one(
        {
            "_id": ObjectId(food_id),
            "reservedBy": volunteer_id,
            "status": "reserved"
        },
        {
            "$set": {
                "status": "picked",
                "pickedAt": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        return jsonify({"message": "Pick failed"}), 400

    return jsonify({"message": "Picked successfully"}), 200


@food_bp.route("/unreserve/<food_id>", methods=["POST"])
@jwt_required()
@role_required(["volunteer"])
def unreserve_food(food_id):
    volunteer_id = get_jwt_identity()

    result = foods_collection.update_one(
        {
            "_id": ObjectId(food_id),
            "reservedBy": volunteer_id,
            "status": "reserved"
        },
        {
            "$set": {
                "status": "available"
            },
            "$unset": {
                "reservedBy": "",
                "reservedAt": ""
            }
        }
    )

    if result.matched_count == 0:
        return jsonify({"message": "Unable to remove from cart"}), 400

    return jsonify({"message": "Removed from cart"}), 200


@food_bp.route("/deliver/<food_id>", methods=["POST"])
@jwt_required()
@role_required(["volunteer"])
def deliver_food(food_id):
    data = request.json
    volunteer_id = get_jwt_identity()

    required = ["deliveryAddress", "deliveryImage"]
    for field in required:
        if not data.get(field):
            return jsonify({"message": f"{field} is required"}), 400

    result = foods_collection.update_one(
        {
            "_id": ObjectId(food_id),
            "reservedBy": volunteer_id,
            "status": "picked"
        },
        {
            "$set": {
                "status": "delivered",
                "deliveryAddress": data["deliveryAddress"],
                "deliveryImage": data["deliveryImage"],
                "deliveryNotes": data.get("deliveryNotes", ""),
                "deliveredAt": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        return jsonify({"message": "Delivery failed"}), 400

    # ⭐ KARMA POINTS
    users_collection.update_one(
        {"_id": ObjectId(volunteer_id)},
        {
            "$inc": {
                "karmaPoints": 10,
                "deliveriesCompleted": 1
            }
        }
    )

    return jsonify({"message": "Delivered successfully. +10 Karma!"}), 200

@food_bp.route("/volunteer/profile", methods=["GET"])
@jwt_required()
@role_required(["volunteer"])
def volunteer_profile():
    volunteer_id = get_jwt_identity()

    user = users_collection.find_one(
        {"_id": ObjectId(volunteer_id)},
        {"password": 0}
    )

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Volunteer deliveries
    delivered_count = foods_collection.count_documents({
        "reservedBy": volunteer_id,
        "status": "delivered"
    })

    return jsonify({
        "name": user["name"],
        "email": user["email"],
        "karmaPoints": user.get("karmaPoints", 0),
        "deliveriesCompleted": user.get("deliveriesCompleted", delivered_count),
        "createdAt": user["createdAt"]
    }), 200

@food_bp.route("/volunteer/deliveries", methods=["GET"])
@jwt_required()
@role_required(["volunteer"])
def volunteer_deliveries():
    volunteer_id = get_jwt_identity()

    foods = list(
        foods_collection.find(
            {
                "reservedBy": volunteer_id,
                "status": "delivered"
            },
            {
                "_id": 1,
                "foodName": 1,
                "quantity": 1,
                "itemCategory": 1,
                "deliveryAddress": 1,
                "deliveryImage": 1,
                "deliveredAt": 1
            }
        ).sort("deliveredAt", -1)
    )

    for food in foods:
        food["_id"] = str(food["_id"])

    return jsonify(foods), 200

#platform stats
@food_bp.route("/platform/stats", methods=["GET"])
@jwt_required()
def platform_stats():
    total = foods_collection.count_documents({})
    delivered = foods_collection.count_documents({"status": "delivered"})
    expired = foods_collection.count_documents({"status": "expired"})

    return jsonify({
        "totalPosted": total,
        "totalDelivered": delivered,
        "totalExpired": expired
    }), 200

@food_bp.route("/donor/profile", methods=["GET"])
@jwt_required()
@role_required(["donor"])
def donor_profile():
    donor_id = get_jwt_identity()

    donor = users_collection.find_one(
        {"_id": ObjectId(donor_id)},
        {"password": 0}
    )

    if not donor:
        return jsonify({"message": "Donor not found"}), 404

    return jsonify({
        "name": donor.get("name", ""),
        "email": donor.get("email", ""),
        "phone": donor.get("phone", ""),   # ✅ SAFE ACCESS
        "karmaPoints": donor.get("karmaPoints", 0),
        "deliveriesCompleted": donor.get("deliveriesCompleted", 0),
        "createdAt": donor.get("createdAt")
    }), 200

#Public API' s
@food_bp.route("/public/stats", methods=["GET"])
def public_stats():
    return jsonify({
        "totalPosted": foods_collection.count_documents({}),
        "totalDelivered": foods_collection.count_documents({"status": "delivered"}),
        "totalExpired": foods_collection.count_documents({"status": "expired"}),
        "donors": users_collection.count_documents({"role": "donor"}),
        "volunteers": users_collection.count_documents({"role": "volunteer"})
    }), 200

@food_bp.route("/public/donors", methods=["GET"])
def public_donors():
    donors = list(
        users_collection.find(
            {"role": "donor"},
            {"name": 1, "createdAt": 1}
        ).sort("createdAt", -1).limit(20)
    )

    for d in donors:
        d["_id"] = str(d["_id"])

    return jsonify(donors), 200

@food_bp.route("/public/deliveries", methods=["GET"])
def public_deliveries():
    deliveries = list(
        foods_collection.find(
            {"status": "delivered"},
            {
                "_id": 1,
                "foodName": 1,
                "deliveryImage": 1,
                "deliveredAt": 1,
                "deliveryAddress": 1
            }
        ).sort("deliveredAt", -1).limit(10)
    )

    for d in deliveries:
        d["_id"] = str(d["_id"])

    return jsonify(deliveries), 200

@food_bp.route("/public/volunteers", methods=["GET"])
def public_volunteers():
    volunteers = list(
        users_collection.find(
            {"role": "volunteer"},
            {"_id": 1, "name": 1}
        )
    )

    for v in volunteers:
        v["_id"] = str(v["_id"])

    return jsonify(volunteers), 200
