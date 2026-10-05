from sqlalchemy import Column, Integer, String
from database import Base

class HealthCheckLog(Base):
    """Model for storing health check logs"""
    __tablename__ = "health_check_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, index=True)
    message = Column(String)
