from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_PORT = os.getenv("MAIL_PORT")
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS")
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS")
USE_CREDENTIALS = os.getenv("USE_CREDENTIALS")
VALIDATE_CERTS = os.getenv("VALIDATE_CERTS")


from fastapi import Depends, FastAPI
import models
import database
import api
from fastapi.responses import FileResponse
from pathlib import Path
from auth import OAuth2PasswordBearer
import crud
import schemas
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


models.Base.metadata.create_all(bind=database.engine)

app.include_router(api.router)

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

@app.get("/favicon.ico")
async def get_favicon():
    favicon_path = Path("path_to_your_favicon.ico")
    if favicon_path.is_file():
        return FileResponse(favicon_path, headers={"Content-Type": "image/x-icon"})
    else:
        return {"message": "Favicon not found"}, 404
    

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)
       

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



