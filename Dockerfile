FROM python:3.11-slim

WORKDIR /backend

COPY ./backend .

RUN pip install poetry && \
  poetry config virtualenvs.create false && \
  poetry install --no-interaction --no-ansi --only main

COPY ./frontend/dist ./ui

CMD exec uvicorn app.server:app --host 0.0.0.0 --port $PORT
