from app.firebase_config import db

docs = (db.collection("detection_logs").order_by("timestamp", direction= "DESCENDING").limit(5).stream()
)
for doc in docs:
    print(doc.to_dict())