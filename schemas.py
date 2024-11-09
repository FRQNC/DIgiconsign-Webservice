from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Union
from enum import Enum

# Enums for product condition and shipping status
class ProductCondition(str, Enum):
    new = 'new'
    very_good = 'very good'
    good = 'good'
    judge_by_pict = 'judge by pict'

class ShippingStatus(str, Enum):
    waiting = 'waiting'
    preparing = 'preparing'
    shipping = 'shipping'
    arrived = 'arrived'

# Base response message
class ResponseMSG(BaseModel):
    msg: str

# User Models
class UserBase(BaseModel):
    username: str
    user_email: str
    user_phone: str
    user_address: str
    created_at: datetime
    role: str

class UserCreate(UserBase):
    user_password: str

class User(UserBase):
    user_id: int

    class Config:
        orm_mode = True

class UserLoginEmail(BaseModel):
    user_email: str
    user_password: str

class UserLoginPhone(BaseModel):
    user_phone: str
    user_password: str

class Password(BaseModel):
    old_password: str
    new_password: str

class UserCredential(BaseModel):
    user_email: str
    user_phone: str
    new_password: Union[str, None] = Field(default=None)

# Product Models
class ProductBase(BaseModel):
    seller_id: int
    product_name: str
    product_description: str
    product_price: float
    product_condition: ProductCondition
    created_at: datetime
    image_url: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    product_id: int

    class Config:
        orm_mode = True

# Cart Models
class CartBase(BaseModel):
    user_id: int

class CartCreate(CartBase):
    pass

class Cart(CartBase):
    cart_id: int

    class Config:
        orm_mode = True

# Cart Items Models
class CartItemBase(BaseModel):
    cart_id: int
    user_id: int
    product_id: int
    quantity: int
    added_at: datetime

class CartItemCreate(CartItemBase):
    pass

class CartItem(CartItemBase):
    cart_item_id: int

    class Config:
        orm_mode = True

# Transaction Models
class TransactionBase(BaseModel):
    product_id: int
    buyer_id: int
    price: float
    shipping_status: ShippingStatus
    is_paid: bool
    transaction_date: datetime
    shipping_address: str

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    transaction_id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str