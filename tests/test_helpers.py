TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "StrongPass123",
}

HEADERS_TEMPLATE = lambda token: {"Authorization": f"Bearer {token}"}

CONTACT_EXAMPLE = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "phone_number": "1234567890",
    "birthday": "2000-01-01",
    "additional_info": "Friend from school",
}
