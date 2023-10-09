import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from main import app
from auth import create_access_token

@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module")
def test_user(db):
    from models import User
    from crud import create_user

    user = User(email="test@gmail.com", password="password")
    create_user(db, user)
    return user

@pytest.fixture(scope="module")
def access_token(test_user):
    token = create_access_token(data={"sub": test_user.email})
    return token

def test_create_contact(client, db, access_token):
    new_contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "phone_number": "1234567890",
        "birth_date": "1990-01-01"
    }
    response = client.post(
        "/contacts/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=new_contact_data
    )
    assert response.status_code == 200
    created_contact = response.json()
    assert created_contact["first_name"] == new_contact_data["first_name"]

def test_get_contact(client, db, access_token):
    new_contact_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "janedoe@example.com",
        "phone_number": "9876543210",
        "birth_date": "1990-02-01"
    }
    response = client.post(
        "/contacts/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=new_contact_data
    )
    assert response.status_code == 200
    created_contact = response.json()

    response = client.get(
        f"/contacts/{created_contact['id']}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    retrieved_contact = response.json()
    assert retrieved_contact["first_name"] == created_contact["first_name"]

def test_update_contact(client, db, access_token):
    new_contact_data = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alicesmith@example.com",
        "phone_number": "5555555555",
        "birth_date": "1995-05-05"
    }
    response = client.post(
        "/contacts/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=new_contact_data
    )
    assert response.status_code == 200
    created_contact = response.json()

    updated_data = {
        "first_name": "Alicia",
        "last_name": "Johnson",
        "email": "aliciajohnson@example.com",
        "phone_number": "7777777777",
        "birth_date": "1997-07-07"
    }
    response = client.put(
        f"/contacts/{created_contact['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=updated_data
    )
    assert response.status_code == 200
    updated_contact = response.json()
    assert updated_contact["first_name"] == updated_data["first_name"]

def test_delete_contact(client, db, access_token):
    new_contact_data = {
        "first_name": "Bob",
        "last_name": "Johnson",
        "email": "bobjohnson@example.com",
        "phone_number": "5555555555",
        "birth_date": "1990-05-05"
    }
    response = client.post(
        "/contacts/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=new_contact_data
    )
    assert response.status_code == 200
    created_contact = response.json()

    response = client.delete(
        f"/contacts/{created_contact['id']}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    deleted_contact = response.json()
    assert deleted_contact["id"] == created_contact["id"]

def test_upcoming_birthdays(client, db, access_token):
    upcoming_birthday_contact_data = {
        "first_name": "Upcoming",
        "last_name": "Birthday",
        "email": "upcoming@example.com",
        "phone_number": "9999999999",
        "birth_date": "2000-10-23"
    }
    response = client.post(
        "/contacts/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=upcoming_birthday_contact_data
    )
    assert response.status_code == 200

    response = client.get(
        "/contacts/birthdays/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

def test_search_contacts(client, db, access_token):
    contacts_data = [
        {"first_name": "John", "last_name": "Doe", "email": "john@example.com", "phone_number": "1111111111", "birth_date": "1990-01-01"},
        {"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com", "phone_number": "2222222222", "birth_date": "1991-02-02"},
        {"first_name": "Alice", "last_name": "Johnson", "email": "alice@example.com", "phone_number": "3333333333", "birth_date": "1992-03-03"}
    ]
    for contact_data in contacts_data:
        response = client.post(
            "/contacts/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=contact_data
        )
        assert response.status_code == 200

    search_query = "Jane"
    response = client.get(
        f"/contacts/search/?query={search_query}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

def test_cleanup(db):
    db.close()

