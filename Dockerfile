FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY assets ./assets

RUN pip install --no-cache-dir .
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "huarun_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
