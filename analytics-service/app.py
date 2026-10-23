import os
from datetime import datetime, timezone
import time

from flask import Flask, jsonify,request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy import func  

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "my-secret-key")

db = SQLAlchemy(app)

class Click(db.Model):
    __tablename__ = "clicks"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    clicked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_agent = db.Column(db.Text)

@app.before_request
def check_internal_key():
    if request.path.startswith("/api/analytics/events"):
        if request.headers.get("X-Internal-Api-Key") != INTERNAL_API_KEY:
            return jsonify({"error": "Unauthorized"}), 403

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/api/analytics/stats/<code>")
def get_stats(code):

    total_clicks = Click.query.filter_by(code=code).count()

    daily_stats = db.session.query(
        func.date(Click.clicked_at).label("date"),
        func.count(Click.id).label("count")
    ).filter(Click.code == code).group_by(func.date(Click.clicked_at)).all()

    stats_list = [{"date": str(row.date), "count": row.count} for row in daily_stats]

    return jsonify({
        "code": code,
        "total_clicks": total_clicks,
        "clicks_by_day": stats_list
    }), 200


@app.post("/api/analytics/events")
def record_event():
    data = request.get_json()
    if not data or "code" not in data:
        return jsonify({"error": "code is required"}), 400

    code = data.get("code")
    user_agent = data.get("user_agent", "")

    new_click = Click(code=code, user_agent=user_agent)
    db.session.add(new_click)
    db.session.commit()

    return jsonify({"status": "recorded"}), 201

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
    app.run(host="0.0.0.0", port=8001)