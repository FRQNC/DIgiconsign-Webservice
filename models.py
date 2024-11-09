from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Enum, Boolean
from sqlalchemy.orm import relationship
from database import BaseDB
from enum import Enum as PyEnum

# Enum for product condition and shipping status
class ProductConditionEnum(PyEnum):
    new = "new"
    very_good = "very good"
    good = "good"
    judge_by_pict = "judge by pict"

class ShippingStatusEnum(PyEnum):
    waiting = "waiting"
    preparing = "preparing"
    shipping = "shipping"
    arrived = "arrived"

class RoleEnum(PyEnum):
    admin = "admin"
    user = "user"

# User model
class User(BaseDB):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), nullable=False)
    user_password = Column(String(256), nullable=False)
    user_email = Column(String(128), nullable=False)
    user_phone = Column(String(15), nullable=False)
    user_address = Column(String(256), nullable=False)
    created_at = Column(DateTime, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)

    carts = relationship("Cart", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")
    products = relationship("Product", back_populates="seller")
    transactions = relationship("Transaction", back_populates="buyer")

# Cart model
class Cart(BaseDB):
    __tablename__ = 'cart'
    
    cart_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    user = relationship("User", back_populates="carts")
    cart_items = relationship("CartItem", back_populates="cart")

# CartItem model
class CartItem(BaseDB):
    __tablename__ = 'cart_items'
    
    cart_item_id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey('cart.cart_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    added_at = Column(DateTime, nullable=False)
    
    cart = relationship("Cart", back_populates="cart_items")
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

# Product model
class Product(BaseDB):
    __tablename__ = 'products'
    
    product_id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    product_name = Column(String(255), nullable=False)
    product_description = Column(String(2048), nullable=False)
    product_price = Column(Float, nullable=False)
    product_condition = Column(Enum(ProductConditionEnum), nullable=False)
    created_at = Column(DateTime, nullable=False)
    image_url = Column(String(512), nullable=False)
    
    seller = relationship("User", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    transactions = relationship("Transaction", back_populates="product")

# Transaction model
class Transaction(BaseDB):
    __tablename__ = 'transactions'
    
    transaction_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    buyer_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    price = Column(Float, nullable=False)
    shipping_status = Column(Enum(ShippingStatusEnum), nullable=False)
    is_paid = Column(Boolean, nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    shipping_address = Column(String(255), nullable=False)
    
    product = relationship("Product", back_populates="transactions")
    buyer = relationship("User", back_populates="transactions")
