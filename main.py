from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import models
from database import Base, engine
from routers import health, product, customer, order, analytics

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="GOA Hack API",
    description="A FastAPI project with health check endpoints",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(health.router)
app.include_router(product.router)
app.include_router(customer.router)
app.include_router(order.router)
app.include_router(analytics.router)


@app.get("/dashboard", include_in_schema=False)
@app.get("/app", include_in_schema=False)
def serve_dashboard():
    """Serve the React + Tailwind frontend dashboard"""
    return FileResponse("static/index.html")


@app.get("/", tags=["root"])
def read_root(request: Request):
    """Root endpoint - serves dashboard in browser, JSON for API clients"""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {
        "message": "Welcome to GOA Hack API",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
