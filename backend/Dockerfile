FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY parameters.py simulator.py utility.py convert_csv_into_pnz.py ./
COPY backend ./backend
COPY power_generation_2025.csv power_imp_exp_2025.csv power_consumption_2025.csv ./

# Build the binary dataset at image build time so startup is fast.
RUN python convert_csv_into_pnz.py

RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
