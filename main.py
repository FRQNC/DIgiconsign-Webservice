# test lokal uvicorn main:app --host 0.0.0.0 --port 8000 --reload --
import uuid
from fastapi import Depends, Request, FastAPI, HTTPException, UploadFile

from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session

import crud, models, schemas
from database import SessionLocal, engine
models.BaseDB.metadata.create_all(bind=engine)

import jwt
import datetime

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

import os

from PIL import Image
import io

from dotenv import load_dotenv

load_dotenv()

# def list_directory_structure(root_dir, indent=''):
#     items = os.listdir(root_dir)
#     for item in items:
#         path = os.path.join(root_dir, item)
#         if os.path.isdir(path):
#             print(f"{indent}{item}/")
#             list_directory_structure(path, indent + '    ')
#         else:
#             print(f"{indent}{item}")

# root_directory = 'path_to_your_root_directory'
# list_directory_structure(str(os.getcwd()))

app = FastAPI(title="Web service Digiconsign",
    version="0.0.1",)

app.add_middleware(
 CORSMiddleware,
 allow_origins=["*"],
 allow_credentials=True,
 allow_methods=["*"],
 allow_headers=["*"],
)


# Ensure the image directory exists
os.makedirs("image", exist_ok=True)

# Mount the image directory
app.mount("/static", StaticFiles(directory="image"), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

path_img = "image/"

@app.get("/")
async def root():
    return {"message": "Dokumentasi API: [url]/docs"}

# create user 
@app.post("/create_user/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_email = crud.get_user_by_email(db, email=user.user_email)
    db_user_phone = crud.get_user_by_phone(db, phone=user.user_phone)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Error: Email sudah digunakan")
    elif db_user_phone:
        raise HTTPException(status_code=400, detail="Error: No telp sudah digunakan")

    return crud.create_user(db=db, user=user)


# hasil adalah akses token    
@app.post("/login_email") #,response_model=schemas.Token
async def login_email(user: schemas.UserLoginEmail, db: Session = Depends(get_db)):
    if not authenticate_by_email(db,user):
        raise HTTPException(status_code=400, detail="Username atau password tidak cocok")

    # ambil informasi username
    user_login = crud.get_user_by_email(db,user.user_email)
    if user_login:
        access_token  = create_access_token(user.user_email)
        user_id = user_login.user_id
        return {"user_id":user_id,"access_token": access_token}
    else:
        raise HTTPException(status_code=400, detail="User tidak ditemukan, kontak admin")
    
@app.post("/login_phone") #,response_model=schemas.Token
async def login_phone(user: schemas.UserLoginPhone, db: Session = Depends(get_db)):
    if not authenticate_by_phone(db,user):
        raise HTTPException(status_code=400, detail="Username atau password tidak cocok")

    # ambil informasi username
    user_login = crud.get_user_by_phone(db,user.user_phone)
    if user_login:
        access_token  = create_access_token(user.user_phone)
        user_id = user_login.user_id
        return {"user_id":user_id,"access_token": access_token}
    else:
        raise HTTPException(status_code=400, detail="User tidak ditemukan, kontak admin")


# #lihat detil user_id
@app.get("/get_user_by_id/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) 
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# update user
@app.put("/update_user/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserBase, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) 

    db_user_old = crud.get_user(db, user_id)
    db_user_email = crud.get_user_by_email(db, email=user_update.user_email)
    db_user_phone = crud.get_user_by_phone(db, phone=user_update.user_phone)
    if db_user_old.user_email != user_update.user_email:
        if db_user_email:
            raise HTTPException(status_code=400, detail="Error: Email sudah digunakan")
    if db_user_old.user_phone != user_update.user_phone:
        if db_user_phone:
            raise HTTPException(status_code=400, detail="Error: No telp sudah digunakan")

    db_user = crud.update_user(db, user_id, user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.put("/update_password/{user_id}", response_model= schemas.ResponseMSG)
def update_password(user_id: int, passwords: schemas.Password, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    if not match_password(db, passwords.old_password, user_id):
        raise HTTPException(status_code=400, detail="Error: Password tidak sesuai")
    update_user_password =  crud.update_password(db,user_id,passwords.new_password)
    if update_user_password:
        return JSONResponse(status_code=200, content={"message" : "Password updated successfully"})
    
@app.post("/forget_password/", response_model= schemas.ResponseMSG)
def forget_password(user_credential: schemas.UserCredential, db: Session = Depends(get_db)):
    typed_email = user_credential.user_email
    typed_phone = user_credential.user_phone
    db_user_email = crud.get_user_by_email(db, typed_email)
    if not db_user_email:
        raise HTTPException(status_code=404, detail="Email tidak ditemukan")
    else:
        db_user_phone = crud.get_user_by_phone(db, typed_phone)
        if not db_user_phone:
            raise HTTPException(status_code=404, detail="No. Telepon tidak ditemukan")
        else:
            if db_user_email.user_id != db_user_phone.user_id:
                raise HTTPException(status_code=404, detail="Tidak ada user dengan gabungan email dan no. telepon tersebut")
            else:
                if user_credential.new_password is None:
                    return JSONResponse(status_code=200, content={"message" : "Kredensial user benar"})
                else:
                    update_user_password =  crud.update_password(db,db_user_email.user_id,user_credential.new_password)
                    if update_user_password:
                        return JSONResponse(status_code=200, content={"message" : "Password updated successfully"})
                    else:
                        raise HTTPException(status_code=500, detail="Gagal mengubah password") 
 

@app.post("/create_product/", response_model=schemas.Product )
def create_product(
    product: schemas.ProductCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token)
    # print(usr)
    new_product = crud.create_product(db=db, product=product)
    return new_product

@app.put("/update_product/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product_update: schemas.ProductBase, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) 

    db_product = crud.update_product(db, product_id, product_update)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.delete("/delete_product/{product_id}")
def delete_product(product_id:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme) ):
    usr =  verify_token(token)
    return crud.delete_product_by_id(db,product_id)

@app.post("/upload_product_image/{product_id}")
async def create_upload_file(file: UploadFile, product_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr = verify_token(token)
    product = crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="id tidak valid")
    
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, JPG and PNG are allowed.")
    
    try:
        image = Image.open(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file")

    old_image = product.image_url
    
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

    compressed_image = compress_image(image)

    file_location = f"{path_img}products/{unique_filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(compressed_image.getbuffer())

    success = crud.update_image_product(db, product_id, unique_filename)

    if success is not None:
        if old_image:
            old_image_path = os.path.join(path_img, "products", old_image)
            if os.path.exists(old_image_path):
                try:
                    os.remove(old_image_path)
                    print(f'Old image {old_image} deleted')
                except Exception as e:
                    print(f'Failed to delete old image {old_image}: {e}')

        return {"info": f"file '{unique_filename}' saved at '{file_location}'"}
    else:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/product_image/{product_id}")
def read_image(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="id tidak valid")
    nama_image = product.image_url
    image_path = os.path.join(path_img, "products", nama_image)
    if not os.path.exists(image_path):
        detail_str = f"File dengan nama {nama_image} tidak ditemukan"
        raise HTTPException(status_code=404, detail=detail_str)
    
    return FileResponse(image_path)

# ######### cart
@app.post("/create_cart/", response_model=schemas.Cart )
def create_cart(cart: schemas.CartCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token)
    new_cart = crud.create_cart(db=db, cart=cart)
    return new_cart

@app.delete("/delete_cart/{cart_id}")
def delete_cart(cart_id:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme) ):
    usr =  verify_token(token)
    return crud.delete_cart_by_id(db,cart_id)

@app.delete("/delete_cart_by_user_id/{user_id}")
def delete_cart(user_id:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme) ):
    usr =  verify_token(token)
    return crud.delete_cart_by_user_id(db,user_id)

# ######### cart_item
@app.post("/create_cart_item/", response_model=schemas.CartItem )
def create_cart_item(cart_item: schemas.CartItemCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token)
    new_cart_item = crud.create_cart_item(db=db, cart_item=cart_item)
    return new_cart_item

@app.put("/update_cart_item/{cart_item_id}", response_model=schemas.CartItem)
def update_cart_item(cart_item_id: int, cart_item_update: schemas.CartItemBase, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) 

    db_cart_item = crud.update_cart_item(db, cart_item_id, cart_item_update)
    if db_cart_item is None:
        raise HTTPException(status_code=404, detail="Cart_item not found")
    return db_cart_item

@app.delete("/delete_cart_item/{cart_item_id}")
def delete_cart_item(cart_item_id:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme) ):
    usr =  verify_token(token)
    return crud.delete_cart_item_by_id(db,cart_item_id)

# ######### transaction
@app.post("/create_transaction/", response_model=schemas.Transaction )
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token)
    new_transaction = crud.create_transaction(db=db, transaction=transaction)
    return new_transaction

@app.put("/update_transaction/{transaction_id}", response_model=schemas.Transaction)
def update_transaction(transaction_id: int, transaction_update: schemas.TransactionBase, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    usr =  verify_token(token) 

    db_transaction = crud.update_transaction(db, transaction_id, transaction_update)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction

@app.delete("/delete_transaction/{transaction_id}")
def delete_transaction(transaction_id:int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme) ):
    usr =  verify_token(token)
    return crud.delete_transaction_by_id(db,transaction_id)

def compress_image(image: Image.Image, quality: int = 85) -> io.BytesIO:
    img_byte_arr = io.BytesIO()
    
    if image.format == 'JPEG' or image.format == 'JPG':
        image.save(img_byte_arr, format='JPEG', quality=quality)
    elif image.format == 'PNG':
        image.save(img_byte_arr, format='PNG', optimize=True)
    else:
        raise ValueError(f"Unsupported image format: {image.format}")
    
    img_byte_arr.seek(0)
    return img_byte_arr

def authenticate_by_email(db,user: schemas.UserCreate):
    user_cari = crud.get_user_by_email(db=db, email=user.user_email)
    if user_cari:
        return (user_cari.user_password == crud.hashPassword(user.user_password))
    else:
        return False  
      
def authenticate_by_phone(db,user: schemas.UserCreate):
    user_cari = crud.get_user_by_phone(db=db, phone=user.user_phone)
    if user_cari:
        return (user_cari.user_password == crud.hashPassword(user.user_password))
    else:
        return False    
    
def match_password(db,typed_password: schemas.Password, user_id= 0, by_email= False, user_email= ""):
    if not by_email:
        user = crud.get_user(db, user_id)
    else:
        user = crud.get_user_by_email(db, user_email)
    if user:
        return user.user_password == crud.hashPassword(typed_password)
    else:
        return False

SECRET_KEY = os.getenv("SECRET_KEY")

def create_access_token(email):
    # info yang penting adalah berapa lama waktu expire
    expiration_time = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=7)    # .now(datetime.UTC)
    access_token = jwt.encode({"email":email,"exp":expiration_time},SECRET_KEY,algorithm="HS256")
    return access_token    

def verify_token(token: str):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=["HS256"])  # bukan algorithm,  algorithms (set)
        email = payload["email"]  
     
    # exception jika token invalid
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Unauthorize token, expired signature, harap login")
    except jwt.PyJWKError:
        raise HTTPException(status_code=401, detail="Unauthorize token, JWS Error")
    # except jwt.JWTClaimsError:
    #     raise HTTPException(status_code=401, detail="Unauthorize token, JWT Claim Error")
    # except jwt.JWTError:
    #     raise HTTPException(status_code=401, detail="Unauthorize token, JWT Error")   
    except Exception as e:
        raise HTTPException(status_code=401, detail="Unauthorize token, unknown error"+str(e))
    
    return {"email": email}

@app.post("/token", response_model=schemas.Token)
async def token(req: Request, form_data: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):

    f = schemas.UserCreate
    f.user_email = form_data.username
    f.user_password = form_data.password
    if not authenticate_by_email(db,f):
        raise HTTPException(status_code=400, detail="email or password tidak cocok")
 
    user_email  = form_data.username

    #buat access token\
    # def create_access_token(user_name,email,role,nama,status,kode_dosen,unit):
    access_token  = create_access_token(user_email)

    return {"access_token": access_token, "token_type": "bearer"}