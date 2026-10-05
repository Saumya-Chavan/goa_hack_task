from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from schemas import HealthCheckResponse, HealthCheckLog as HealthCheckLogSchema
import models
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", response_model=HealthCheckResponse)
def health_check():
    """
    Health check endpoint - returns the status of the application
    """
    return {
        "status": "healthy",
        "message": "Application is running successfully"
    }

@router.get("/detailed", response_model=HealthCheckResponse)
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check endpoint - checks application and database status
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "message": "Application and database are running successfully"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }

@router.post("/log", response_model=HealthCheckLogSchema)
def log_health_check(db: Session = Depends(get_db)):
    """
    Log a health check status to the database
    """
    log_entry = models.HealthCheckLog(
        status="healthy",
        message=f"Health check performed at {datetime.now()}"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

@router.get("/logs", response_model=list[HealthCheckLogSchema])
def get_health_logs(db: Session = Depends(get_db)):
    """
    Retrieve all health check logs from the database
    """
    logs = db.query(models.HealthCheckLog).all()
    return logs
