# Stage 1: Build React UI
FROM node:22-slim AS ui-build
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ .
RUN npm run build

# Stage 2: Python API + static UI
FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY data/ data/
RUN pip install --no-cache-dir .

# Copy React build into static dir served by FastAPI
COPY --from=ui-build /app/ui/dist /app/static

EXPOSE 8000

HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
