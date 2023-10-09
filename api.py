from datetime import timedelta
import pathlib
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import crud
from models import User
import schemas
from auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user, verify_password

from fastapi_mail import MessageSchema, FastMail, ConnectionConfig
import jwt
import time

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import FastAPI, Depends, Query
from fastapi import Request

import cloudinary
from cloudinary.uploader import upload
from fastapi import UploadFile, File
from decouple import config

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

SECRET_KEY = config('SECRET_KEY')

conf = ConnectionConfig(
    MAIL_USERNAME= config('MAIL_USERNAME'),
    MAIL_PASSWORD= config('MAIL_PASSWORD'),
    MAIL_FROM= config('MAIL_FROM'),
    MAIL_PORT=465,
    MAIL_SERVER="smtp.meta.ua",
    MAIL_FROM_NAME="Example email",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=pathlib.Path(__file__).parent / 'templates',
)

cloudinary.config( 
  cloud_name = config('CLOUDINARY_CLOUD_NAME'), 
  api_key = config('CLOUDINARY_API_KEY'), 
  api_secret = config('CLOUDINARY_API_SECRET') 
)


fastmail = FastMail(conf)


def create_confirmation_token(email: str):
    """
    Створює токен підтвердження для вказаної електронної пошти.

    Параметри:
        email (str): Електронна пошта, для якої потрібно створити токен підтвердження.

    Повертає:
        str: Токен підтвердження.
    """
    payload = {
        "sub": email,
        "exp": int(time.time()) + 3600 
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


async def send_email_confirmation(email: str, confirmation_token: str, background_tasks: BackgroundTasks):
    """
    Надсилає електронний лист для підтвердження електронної пошти користувача.

    Параметри:
        email (str): Електронна пошта користувача, яка повинна бути підтверджена.
        confirmation_token (str): Токен підтвердження, який користувач повинен підтвердити.
        background_tasks (BackgroundTasks): Об'єкт для виконання фонових завдань.

    Повертає:
        None
    """
    message = MessageSchema(
        subject="Email Confirmation",
        recipients=[email],
        body=f"Click the following link to confirm your email: http://127.0.0.1:8000/confirm?token={confirmation_token}",
        subtype="html"
    )
    await fastmail.send_message(message)

@router.post("/contacts/", response_model=schemas.Contact)
def create_contact(contact: schemas.ContactCreate, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Створює новий контакт для вказаного користувача.

    Параметри:
        contact (schemas.ContactCreate): Дані нового контакту.
        user (schemas.User): Залогінений користувач.
        db (Session): Сесія бази даних.

    Повертає:
        schemas.Contact: Створений контакт.
    """
    user_id = user.id
    new_contact = crud.create_contact(db, contact, user_id)
    contacts = crud.get_contacts(db)
    
    return new_contact



@router.get("/contacts/", response_model=List[schemas.Contact])
@limiter.limit("10 per minute")
def read_contacts(request: Request, skip: int = Query(0, alias="page", ge=0), limit: int = Query(10, le=100), 
                db: Session = Depends(get_db)):
    contacts = crud.get_contacts(db, skip, limit)
    return contacts

@router.get("/contacts/{contact_id}", response_model=schemas.Contact)
def read_contact(contact_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = crud.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    if contact.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return contact

@router.put("/contacts/{contact_id}", response_model=schemas.Contact)
def update_contact(contact_id: int, contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    updated_contact = crud.update_contact(db, contact_id, contact)
    if updated_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated_contact

@router.delete("/contacts/{contact_id}", response_model=schemas.Contact)
def delete_contact(contact_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = crud.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    if contact.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    deleted_contact = crud.delete_contact(db, contact_id)
    if deleted_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return deleted_contact

@router.get("/contacts/search/", response_model=List[schemas.Contact])
def search_contacts(query: str, db: Session = Depends(get_db)):
    contacts = crud.search_contacts(db, query)
    return contacts

@router.get("/contacts/birthdays/", response_model=List[schemas.Contact])
def upcoming_birthdays(db: Session = Depends(get_db)):
    contacts = crud.get_upcoming_birthdays(db)
    return contacts


from fastapi import HTTPException

@router.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Реєструє нового користувача в системі.

    Параметри:
        user (schemas.UserCreate): Дані користувача для реєстрації.
        db (Session): Сесія бази даних.
        background_tasks (BackgroundTasks): Об'єкт для виконання фонових завдань.

    Повертає:
        schemas.User: Зареєстрований користувач.
    """
    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    new_user = crud.create_user(db, user)
    users = crud.get_users(db)
    users.append(new_user)

    confirmation_token = create_confirmation_token(user.email)
    background_tasks.add_task(send_email_confirmation, user.email, confirmation_token, background_tasks)
    
    return new_user


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Аутентифікує користувача та повертає токен доступу.

    Параметри:
        form_data (OAuth2PasswordRequestForm): Дані форми, включаючи електронну пошту та пароль.
        db (Session): Сесія бази даних.

    Повертає:
        dict: Об'єкт з токеном доступу та типом токену.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/", response_model=List[schemas.User])
def get_all_users(skip: int = Query(0), limit: int = Query(100), 
                   db: Session = Depends(get_db)):
    users = crud.get_users(db, skip, limit)
    return users



@router.post("/send-confirmation-email/", response_model=dict)
async def send_confirmation_email(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    confirmation_token = create_confirmation_token(user.email)

    confirm_url = f"http://127.0.0.1:8000/confirm?token={confirmation_token}"

    try:
        message = MessageSchema(
            subject="Email Confirmation",
            recipients=[email],
            body=f"Click the following link to confirm your email: {confirm_url}",
            subtype="html"
        )
        await fastmail.send_message(message)
        return {"message": "Confirmation email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send confirmation email: {str(e)}")
    


@router.get("/confirm")
async def confirm_email(token: str, db: Session = Depends(get_db)):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")

    email = decoded_token.get("sub")

    user = crud.get_user_by_email(db, email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()

    return {"message": "Email successfully confirmed"}


@router.get("/verified-users/", response_model=List[schemas.User])
def get_verified_users(skip: int = Query(0), limit: int = Query(100), 
                       db: Session = Depends(get_db)):
    users = crud.get_verified_users(db, skip, limit)
    return users

@router.post("/update-avatar/")
async def update_avatar(file: UploadFile = File(...), user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not file:
        raise HTTPException(status_code=400, detail="No image uploaded")

    response = cloudinary.uploader.upload(file.file)

    avatar_url = response["secure_url"]

    user.avatar_url = avatar_url
    db.commit()

    return {"message": "Avatar updated successfully", "avatar_url": avatar_url}

