from pydantic import BaseModel
from datetime import date
from pydantic import BaseModel


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birth_date: date

class ContactCreate(ContactBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def model_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "birth_date": self.birth_date
        }

class Contact(ContactBase):
    id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True


