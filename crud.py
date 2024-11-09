from sqlalchemy.orm import Session
import models, schemas
import bcrypt
from sqlalchemy import desc
from dotenv import load_dotenv
from datetime import datetime
import base64
import os

load_dotenv()

base64_salt = os.getenv('SALT')

# Decode the base64 string back to bytes
SALT = base64.b64decode(base64_salt)

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.user_email == email).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(models.User).filter(models.User.user_phone == phone).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def hashPassword(passwd: str):
    bytePwd = passwd.encode('utf-8')
    pwd_hash = bcrypt.hashpw(bytePwd, SALT).decode('utf-8')
    return pwd_hash

def get_products(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_product_by_id(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.product_id == product_id).first()


# ######### user

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hashPassword(user.user_password)
    db_user = models.User(
        username=user.username,
        user_email=user.user_email,
        user_phone=user.user_phone,
        user_address=user.user_address,
        role=user.role,
        user_password=hashed_password,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserBase):
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    
    if not db_user:
        return None

    update_data = user_update.model_dump()
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_password(db: Session, user_id: int, newPassword: str):
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not db_user:
        return None
    
    hashed_password = hashPassword(newPassword)
    db_user.user_password = hashed_password
    db.commit()
    db.refresh(db_user)
    return db_user

# ######### products
def create_product(db: Session, product: schemas.ProductCreate):
    if product.image_url == "":
        product.image_url = "default.jpg"
    db_product = models.Product(
        seller_id = product.seller_id,
        product_name=product.product_name,
        product_description = product.product_description,
        product_price = product.product_price,
        product_condition = product.product_condition,
        created_at = datetime.utcnow(),
        image_url = product.image_url
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: schemas.ProductBase):
    db_product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    
    if not db_product:
        return None

    update_data = product_update.model_dump()
    
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    
    return db_product

def delete_product_by_id(db: Session, product_id: int):
    hasil = db.query(models.Product).filter(models.Product.product_id == product_id).delete()
    db.commit()
    return {"record_dihapus":hasil} 

def update_image_product(db: Session, product_id: int, filename: str):
    db_product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    
    if not db_product:
        return None
    db_product.image_url = filename
    
    db.commit()
    db.refresh(db_product)
    
    return db_product.image_url

# ######### cart
def create_cart(db: Session, cart: schemas.CartCreate):
    db_cart = models.Cart(
        seller_id = cart.seller_id
    )
    db.add(db_cart)
    db.commit()
    db.refresh(db_cart)
    return db_cart

def delete_cart_by_id(db: Session, cart_id: int):
    result = db.query(models.Cart).filter(models.Cart.cart_id == cart_id).delete()
    db.commit()
    return {"record_dihapus":result}

def delete_cart_by_user_id(db: Session, user_id: int):
    result = db.query(models.Cart).filter(models.Cart.user_id == user_id).delete()
    db.commit()
    return {"record_dihapus":result}


# ######### cart_item
def create_cart_item(db: Session, cart_item: schemas.CartItemCreate):
    db_cart_item = models.CartItem(
        user_id = cart_item.user_id,
        product_id = cart_item.product_id,
        quantity = cart_item.quantity,
        added_at = datetime.utcnow(),
    )
    db.add(db_cart_item)
    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def update_cart_item(db: Session, cart_item_id: int, cart_item_update: schemas.CartItemBase):
    db_cart_item = db.query(models.CartItem).filter(models.CartItem.cart_item_id == cart_item_id).first()
    
    if not db_cart_item:
        return None

    update_data = cart_item_update.model_dump()
    
    for key, value in update_data.items():
        setattr(db_cart_item, key, value)
    
    db.commit()
    db.refresh(db_cart_item)
    
    return db_cart_item

def delete_cart_item_by_id(db: Session, cart_item_id: int):
    hasil = db.query(models.CartItem).filter(models.CartItem.cart_item_id == cart_item_id).delete()
    db.commit()
    return {"record_dihapus":hasil} 

# ######### transaction
def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    db_transaction = models.Transaction(
        product_id = transaction.product_id,
        buyer_id = transaction.buyer_id,
        price = transaction.price,
        shipping_status = transaction.shipping_status,
        is_paid = transaction.is_paid,
        transaction_date = datetime.utcnow(),
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def update_transaction(db: Session, transaction_id: int, transaction_update: schemas.TransactionBase):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).first()
    
    if not db_transaction:
        return None

    update_data = transaction_update.model_dump()
    
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction

def delete_transaction_by_id(db: Session, transaction_id: int):
    result = db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).delete()
    db.commit()
    return {"record_dihapus":result}