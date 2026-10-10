from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional
from database import get_db
import models
import schemas

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    """
    Create an order in a single transaction:
    - Verifies customer exists.
    - Verifies all products exist and have sufficient stock.
    - Deducts stock.
    - Saves order and order items (atoms) using current product prices.
    - If stock is insufficient or items/customer not found, rolls back and returns 404.
    """
    try:
        # 1. Verify customer exists
        customer = db.query(models.Customer).filter(models.Customer.id == order_in.customer_id).first()
        if not customer:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {order_in.customer_id} not found"
            )

        items = order_in.items or []
        if not items:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must contain at least one item"
            )

        # 2. Check total requested quantities per product against current stock
        product_quantities: dict[int, int] = {}
        for item in items:
            product_quantities[item.product_id] = product_quantities.get(item.product_id, 0) + item.quantity

        products_map: dict[int, models.Product] = {}
        for pid, requested_qty in product_quantities.items():
            product = db.query(models.Product).filter(models.Product.id == pid).first()
            if not product:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {pid} not found"
                )
            if product.stock < requested_qty:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Insufficient stock for product '{product.name}' (ID: {product.id}). Available: {product.stock}, requested: {requested_qty}"
                )
            products_map[pid] = product

        # 3. Create the order
        new_order = models.Order(
            customer_id=order_in.customer_id,
            created_at=datetime.utcnow(),
            status="pending"
        )
        db.add(new_order)
        db.flush()  # Generate new_order.id

        # 4. Deduct stock and save order atoms (items)
        for item in items:
            product = products_map[item.product_id]
            product.stock -= item.quantity

            order_item = models.OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price
            )
            db.add(order_item)

        # 5. Commit transaction
        db.commit()
        db.refresh(new_order)
        return new_order

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )

@router.get("/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """
    Get one order with its atoms.
    """
    order = (
        db.query(models.Order)
        .options(joinedload(models.Order.items))
        .filter(models.Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order

@router.get("", response_model=schemas.OrderListResponse)
@router.get("/", response_model=schemas.OrderListResponse, include_in_schema=False)
def get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    page_limit: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db)
):
    """
    List orders with paging.
    """
    actual_limit = page_limit if page_limit is not None else limit
    query = db.query(models.Order).options(joinedload(models.Order.items))
    total = query.count()

    offset = (page - 1) * actual_limit
    orders = query.offset(offset).limit(actual_limit).all()

    return schemas.OrderListResponse(
        data=orders,
        page=page,
        limit=actual_limit,
        total=total
    )
