from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from fastapi.staticfiles import StaticFiles
from app.groups.routes import router as tools_router
import logging
import os

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MCP Gateway", docs_url="/docs", redoc_url="/redoc")

# Register routers
def register_tools(app: FastAPI):
    app.include_router(tools_router, prefix="/tools")

register_tools(app)

# Middleware de logging detalhado
def setup_middlewares(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request, call_next):
        logging.info(f"Requisição: {request.method} {request.url}")
        response = await call_next(request)
        logging.info(f"Resposta: {response.status_code} para {request.method} {request.url}")
        return response

setup_middlewares(app)

# MCP exposure
doc_mcp = FastApiMCP(app)

# Serve frontend build (React/Vite) como estático
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

@app.get("/")
def root():
    return {"message": "MCP Gateway em execução"}
