FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
CMD ["sh", "-c", "python -c 'from app import db, app; app.app_context().push(); db.create_all()' && gunicorn -w 4 -b 0.0.0.0:8000 app:app"]