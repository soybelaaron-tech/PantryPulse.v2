FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile
COPY frontend/ ./
ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
RUN yarn build

FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy frontend build
COPY --from=frontend-build /app/frontend/build ./static

# Serve frontend from FastAPI
RUN echo '\nfrom fastapi.staticfiles import StaticFiles\nfrom fastapi.responses import FileResponse\nimport os\nif os.path.isdir("/app/static"):\n    app.mount("/static", StaticFiles(directory="/app/static/static"), name="static")\n    @app.get("/{path:path}")\n    async def serve_frontend(path: str):\n        file = f"/app/static/{path}"\n        if os.path.isfile(file):\n            return FileResponse(file)\n        return FileResponse("/app/static/index.html")\n' >> server.py

EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
