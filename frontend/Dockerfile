# Multi-stage build for combined backend and frontend

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend
FROM python:3.12-slim AS backend
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend
COPY --from=frontend-build /app/frontend/.next ./frontend/.next
COPY --from=frontend-build /app/frontend/package.json ./frontend/
COPY --from=frontend-build /app/frontend/public ./frontend/public

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Start command
CMD ["./start.sh"]
