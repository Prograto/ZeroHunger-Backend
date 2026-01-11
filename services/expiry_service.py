from datetime import datetime
from utils.db import foods_collection

def check_expired_food():
    now = datetime.utcnow()

    foods_collection.update_many(
        {
            "expiryTime": {"$lte": now},
            "status": "available"
        },
        {"$set": {"status": "expired"}}
    )
