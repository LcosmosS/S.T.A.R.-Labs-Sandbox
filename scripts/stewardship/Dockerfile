FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080 STEWARDSHIP_DELIVERY_DB=/data/stewardship-deliveries.sqlite3
WORKDIR /app
COPY scripts/stewardship/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data
COPY scripts/stewardship/ ./
USER 10001:10001
EXPOSE 8080
CMD ["python", "app.py"]
