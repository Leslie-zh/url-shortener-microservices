from flask import Flask, jsonify,request
from flask import redirect
import time

from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy
import secrets
from sqlalchemy.exc import IntegrityError, ProgrammingError

import requests
from datetime import datetime, timezone


app = Flask(__name__)

CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "postgresql://shortener:shortener123@localhost:5432/shortener_db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Link(db.Model):
    __tablename__ = 'links'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    long_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())



@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.post("/api/links")
def create_link():
    data = request.get_json()
    long_url = data.get("long_url")
    if not long_url:
        return jsonify({"error": "long_url is required"}), 400
    
    code = secrets.token_urlsafe(4) 
    
    new_link = Link(code=code, long_url=long_url)
    db.session.add(new_link)
    db.session.commit()
    
    return jsonify({"code": code, "long_url": long_url}), 201

@app.get("/r/<code>")
def redirect_link(code):
    link = Link.query.filter_by(code=code).first()
    if not link:
        return jsonify({"error": "Short link not found"}), 404
    
    analytics_url = os.getenv("ANALYTICS_URL", "http://analytics-service:8001")

    # 构造要发送的数据（注意：这里先不存真实 IP，只是模拟）
    event_data = {
        "code": code,
        "clicked_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": request.headers.get("User-Agent", "unknown")
    }

    try:
        # requests.post(f"{analytics_url}/api/analytics/events", json=event_data, timeout=2)
        requests.post(
            f"{analytics_url}/api/analytics/events", 
            json=event_data, 
            headers={"X-Internal-Api-Key": os.getenv("INTERNAL_API_KEY", "my-secret-key")},
            timeout=10
        )
    except Exception as e:
        print(f"Failed to send analytics: {e}")

    return redirect(link.long_url, code=302)

# with app.app_context():
#     max_retries = 10
#     for attempt in range(max_retries):
#         try:
#             db.create_all()
#             print("✅ Successfully connected to the database and created tables!")
#             break 
#         except (IntegrityError, ProgrammingError):
#             break
#         except Exception as e:
#             print(f"⏳ Database not ready...")
#             time.sleep(2)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)