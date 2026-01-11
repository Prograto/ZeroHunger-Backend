from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(
        self,
        name,
        email,
        password,
        phone,
        role,
        address,
        location
    ):
        self.name = name
        self.email = email
        self.phone = phone
        self.password = generate_password_hash(password)
        self.role = role                  # donor | volunteer
        self.address = address
        self.location = location          # { lat, lng }

        # ⭐ VOLUNTEER GAMIFICATION FIELDS
        self.karmaPoints = 0              # increases after delivery
        self.deliveriesCompleted = 0      # total successful deliveries

        # 🔐 ACCOUNT STATUS (optional but good practice)
        self.isActive = True

        self.createdAt = datetime.utcnow()

    @staticmethod
    def verify_password(hashed_password, password):
        return check_password_hash(hashed_password, password)
