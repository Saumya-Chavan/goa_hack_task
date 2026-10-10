from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
import models
import schemas

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/product-sales", response_model=list[schemas.ProductSalesAnalytics])
@router.get("/products/sales", response_model=list[schemas.ProductSalesAnalytics], include_in_schema=False)
@router.get("/product-revenue", response_model=list[schemas.ProductSalesAnalytics], include_in_schema=False)
@router.get("/revenue-by-product", response_model=list[schemas.ProductSalesAnalytics], include_in_schema=False)
def get_product_sales_analytics(db: Session = Depends(get_db)):
    """
    1. Total revenue and units sold per product using SQLAlchemy joins and aggregation.
    """
    results = (
        db.query(
            models.Product.id.label("product_id"),
            models.Product.name.label("product_name"),
            func.coalesce(func.sum(models.OrderItem.quantity), 0).label("units_sold"),
            func.coalesce(func.sum(models.OrderItem.quantity * models.OrderItem.unit_price), 0.0).label("total_revenue")
        )
        .outerjoin(models.OrderItem, models.Product.id == models.OrderItem.product_id)
        .group_by(models.Product.id, models.Product.name)
        .order_by(func.coalesce(func.sum(models.OrderItem.quantity * models.OrderItem.unit_price), 0.0).desc())
        .all()
    )

    return [
        schemas.ProductSalesAnalytics(
            product_id=r.product_id,
            product_name=r.product_name,
            units_sold=int(r.units_sold),
            total_revenue=round(float(r.total_revenue), 2)
        )
        for r in results
    ]

@router.get("/top-customers", response_model=list[schemas.TopCustomerAnalytics])
@router.get("/top-5-customers", response_model=list[schemas.TopCustomerAnalytics], include_in_schema=False)
@router.get("/customers/top", response_model=list[schemas.TopCustomerAnalytics], include_in_schema=False)
def get_top_customers(
    limit: int = Query(5, ge=1),
    db: Session = Depends(get_db)
):
    """
    2. Top 5 customers by total spend using SQLAlchemy joins and aggregation.
    """
    results = (
        db.query(
            models.Customer.id.label("customer_id"),
            models.Customer.name.label("customer_name"),
            models.Customer.email.label("email"),
            func.coalesce(func.sum(models.OrderItem.quantity * models.OrderItem.unit_price), 0.0).label("total_spend")
        )
        .join(models.Order, models.Customer.id == models.Order.customer_id)
        .join(models.OrderItem, models.Order.id == models.OrderItem.order_id)
        .group_by(models.Customer.id, models.Customer.name, models.Customer.email)
        .order_by(func.sum(models.OrderItem.quantity * models.OrderItem.unit_price).desc())
        .limit(limit)
        .all()
    )

    return [
        schemas.TopCustomerAnalytics(
            customer_id=r.customer_id,
            customer_name=r.customer_name,
            email=r.email,
            total_spend=round(float(r.total_spend), 2)
        )
        for r in results
    ]

@router.get("/low-stock", response_model=list[schemas.Product])
@router.get("/stock-below-threshold", response_model=list[schemas.Product], include_in_schema=False)
@router.get("/products/low-stock", response_model=list[schemas.Product], include_in_schema=False)
def get_products_below_stock_threshold(
    threshold: int = Query(10, ge=0),
    db: Session = Depends(get_db)
):
    """
    3. Products with stock below threshold, passed as a query parameter, defaulting to 10.
    """
    products = (
        db.query(models.Product)
        .filter(models.Product.stock < threshold)
        .order_by(models.Product.stock.asc())
        .all()
    )
    return products
