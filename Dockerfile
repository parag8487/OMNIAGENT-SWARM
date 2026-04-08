# Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Final Image
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend to backend static directory
# Based on Flask(static_folder='../static') in backend/app/__init__.py
# backend/run.py is at /app/backend/run.py
# static folder should be at /app/static (which is ../static relative to /app/backend/app)
COPY --from=frontend-builder /app/frontend/dist ./static

# Set environment variables
ENV FLASK_APP=backend/run.py
ENV PYTHONUNBUFFERED=1
ENV PORT=5001

# Expose port
EXPOSE 5001

# Run the application
CMD gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 0 "backend.run:main()"