FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml README.md alembic.ini /app/
COPY intentbid /app/intentbid

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD ["uvicorn", "intentbid.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
