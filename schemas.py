from pydantic import BaseModel
from typing import Optional

class HealthCheckResponse(BaseModel):
    """Schema for health check response"""
    status: str
    message: str
    
    class Config:
        from_attributes = True

class HealthCheckLogBase(BaseModel):
    """Base schema for health check log"""
    status: str
    message: str

class HealthCheckLogCreate(HealthCheckLogBase):
    """Schema for creating a health check log"""
    pass

class HealthCheckLog(HealthCheckLogBase):
    """Schema for health check log response"""
    id: int
    
    class Config:
        from_attributes = True
