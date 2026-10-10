from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from database import get_db
import models
import schemas

router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("", response_model=schemas.Customer, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=schemas.Customer, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """
    Create a new customer.
    Returns 409 Conflict if a customer with the given email already exists.
    """
    existing_customer = db.query(models.Customer).filter(models.Customer.email == customer.email).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this email already exists"
        )
    
    db_customer = models.Customer(**customer.model_dump())
    try:
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this email already exists"
        )
        
    return db_customer

@router.get("", response_model=list[schemas.Customer])
@router.get("/", response_model=list[schemas.Customer], include_in_schema=False)
def get_customers(
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db)
):
    """
    Retrieve list of customers.
    """
    query = db.query(models.Customer)
    if limit is not None:
        return query.offset(skip).limit(limit).all()
    return query.offset(skip).all()

@router.get("/{customer_id}", response_model=schemas.Customer)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a customer by ID.
    """
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return db_customer
