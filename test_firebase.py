from app.firebase_config import db

data = {
    "message": "Firebase connected"
}

db.collection("test").add(data)

print("SUCCESS")