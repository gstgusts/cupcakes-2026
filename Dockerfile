# syntax=docker/dockerfile:1

# --- CSS: compile Tailwind from the classes used in the templates
FROM node:22-alpine AS css
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY app ./app
RUN npm run build:css

# --- Runtime
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd -m appuser
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=css /build/app/static/css/app.css app/static/css/app.css

USER appuser
EXPOSE 5000

# Apply migrations, then start the web app
CMD ["sh", "-c", "flask --app run db upgrade && gunicorn -b 0.0.0.0:5000 -w 2 run:app"]
