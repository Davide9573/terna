# ── Stage 1: build the React frontend ─────────────────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: run the Python backend ───────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project sources
COPY . .

# Copy the built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Generate the binary data file from the CSV sources
RUN python convert_csv_into_pnz.py

EXPOSE 8080
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8080"]
