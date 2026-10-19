FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY scripts/stewardship/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt \
    && useradd --create-home --uid 10001 appuser
COPY scripts/stewardship/ ./
USER 10001:10001
EXPOSE 8080
CMD ["python", "-I", "app.py"]
