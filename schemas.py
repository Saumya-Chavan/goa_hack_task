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

from pydantic import Field, field_validator

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1)
    category: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    data: list[Product]
    page: int
    limit: int
    total: int

import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")

class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        if not isinstance(v, str) or not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int

    class Config:
        from_attributes = True

from datetime import datetime
from pydantic import model_validator, computed_field

class OrderItemCreate(BaseModel):
    product_id: Optional[int] = None
    id: Optional[int] = None
    quantity: int = Field(default=1, gt=0)

    @model_validator(mode="after")
    def validate_product_id(self):
        if self.product_id is None and self.id is not None:
            self.product_id = self.id
        if self.product_id is None:
            raise ValueError("product_id is required")
        return self

class OrderCreate(BaseModel):
    customer_id: int
    items: Optional[list[OrderItemCreate]] = None
    products: Optional[list[OrderItemCreate]] = None

    @model_validator(mode="after")
    def validate_items(self):
        item_list = self.items or self.products
        if not item_list:
            raise ValueError("Order must contain at least one item")
        self.items = item_list
        return self

class OrderItem(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True

class Order(BaseModel):
    id: int
    customer_id: int
    created_at: datetime
    status: str
    items: list[OrderItem] = Field(default_factory=list)

    @computed_field
    def atoms(self) -> list[OrderItem]:
        return self.items

    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    data: list[Order]
    page: int
    limit: int
    total: int

class ProductSalesAnalytics(BaseModel):
    product_id: int
    product_name: str
    units_sold: int
    total_revenue: float

    @computed_field
    def name(self) -> str:
        return self.product_name

    @computed_field
    def revenue(self) -> float:
        return self.total_revenue

    class Config:
        from_attributes = True

class TopCustomerAnalytics(BaseModel):
    customer_id: int
    customer_name: str
    email: str
    total_spend: float

    @computed_field
    def id(self) -> int:
        return self.customer_id

    @computed_field
    def name(self) -> str:
        return self.customer_name

    class Config:
        from_attributes = True



