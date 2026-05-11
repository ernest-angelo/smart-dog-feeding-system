from app.firebase_config import db
from datetime import datetime

data = {
    "timestamp": str(datetime.now()),
    "confidence": 0.91,
    "trigger_status": True,
    "cooldown_remaining": 36000
}

db.collection("detection_logs").add(data)

print("Detection saved")