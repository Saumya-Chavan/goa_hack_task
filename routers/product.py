from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
import models
import schemas

router = APIRouter(prefix="/products", tags=["products"])

@router.get("", response_model=schemas.ProductListResponse)
@router.get("/", response_model=schemas.ProductListResponse, include_in_schema=False)
def get_products(
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    page_limit: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db)
):
    actual_limit = page_limit if page_limit is not None else limit
    query = db.query(models.Product)
    
    if category is not None and category.strip() != "":
        query = query.filter(models.Product.category == category)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
        
    total = query.count()
    
    offset = (page - 1) * actual_limit
    products = query.offset(offset).limit(actual_limit).all()
    
    return schemas.ProductListResponse(
        data=products,
        page=page,
        limit=actual_limit,
        total=total
    )

@router.post("", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product_update: schemas.ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    update_data = product_update.model_dump()
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    return db_product

@router.patch("/{product_id}", response_model=schemas.Product)
def patch_product(product_id: int, product_update: schemas.ProductUpdate, db: Session = Depends(get_db)):
    return update_product(product_id=product_id, product_update=product_update, db=db)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    db.delete(db_product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
