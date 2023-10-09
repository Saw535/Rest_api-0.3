import unittest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAPI(unittest.TestCase):
    
    def setUp(self):
        self.token = "token"
        
    def test_read_root(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, World!"})

    def test_get_contacts(self):
        response = client.get("/contacts/")
        self.assertEqual(response.status_code, 200)

    def test_create_contact(self):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone_number": "123456789",
            "birth_date": "1990-01-01"
        }
        response = client.post("/contacts/", json=payload, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)

    def test_get_contact(self):
        contact_id = 40
        response = client.get(f"/contacts/{contact_id}", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)

    def test_update_contact(self):
        contact_id = 41
        payload = {
            "first_name": "Updated",
            "last_name": "Contact",
            "email": "updated.contact@example.com",
            "phone_number": "987654321",
            "birth_date": "1985-05-05"
        }
        response = client.put(f"/contacts/{contact_id}", json=payload, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)

    def test_delete_contact(self):
        contact_id = 40
        response = client.delete(f"/contacts/{contact_id}", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)

    def test_search_contacts(self):
        query = "John"
        response = client.get(f"/contacts/search/?query={query}", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)

    def test_upcoming_birthdays(self):
        response = client.get("/contacts/birthdays/", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
