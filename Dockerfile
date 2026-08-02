# ── Stage 1: build the React frontend ─────────────────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: build the native C++ simulation extension ───────────────────────
FROM python:3.11-slim AS native-builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	cmake \
	&& rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir "pybind11>=2.12.0"
COPY CMakeLists.txt .
COPY cpp/ ./cpp/
RUN cmake -S . -B build -Dpybind11_DIR="$(python -m pybind11 --cmakedir)" \
	&& cmake --build build --config Release

# ── Stage 3: run the Python backend ───────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project sources
COPY . .

# Default to the native engine in the container; Python remains an explicit rollback.
COPY --from=native-builder /build/build/python/ ./
ENV TERNA_SIMULATION_ENGINE=cpp

# Copy the built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Generate the binary data file from the CSV sources
RUN python convert_csv_into_pnz.py

EXPOSE 8080
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8080"]
