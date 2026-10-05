from fastapi import FastAPI
from database import Base, engine
from routers import health

# Create all database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="GOA Hack API",
    description="A FastAPI project with health check endpoints",
    version="1.0.0"
)

# Include routers
app.include_router(health.router)

@app.get("/", tags=["root"])
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to GOA Hack API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
