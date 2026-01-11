from datetime import datetime

class Food:
    def __init__(
        self,
        donor_id,
        food_name,
        quantity,
        food_type,
        item_category,
        expiry_time,
        location,
        address,
        is_same_as_location,
        image
    ):
        self.donorId = donor_id
        self.foodName = food_name
        self.quantity = quantity
        self.foodType = food_type
        self.itemCategory = item_category
        self.expiryTime = expiry_time
        self.location = location
        self.address = address
        self.isSameAsLocation = is_same_as_location
        self.image = image  # 🖼 Base64
        self.status = "available"
        self.createdAt = datetime.utcnow()
