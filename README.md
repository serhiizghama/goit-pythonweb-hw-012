# 📞 FastAPI Contacts API

A complete **Contacts Management RESTful API** built with **FastAPI**, supporting:

- 🔐 User registration, login, JWT authentication
- ✅ Email confirmation with token verification
- 📇 Contact CRUD operations
- 🔍 Contact search and upcoming birthday queries
- 📤 Avatar uploads to Cloudinary
- 🐳 Dockerized setup

---

### **Set up Environment Variables**

Create a `.env`  in the root of the project:

```ini
DATABASE_URL=postgresql+asyncpg://admin:admin@db:5432/contacts
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_TIME=3600
CORS_ORIGINS=http://localhost,http://127.0.0.1:8000

MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_FROM=your_email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_FROM_NAME=FastAPI Contacts

CLOUDINARY_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 🐳 **Build & Run using Docker**

```ini
docker-compose up --build
```

💡 On container startup, the API will:
- Apply Alembic migrations
- Start on http://localhost:8000

🧪 Poetry Development Mode
For local development outside Docker:
```bash
poetry install

alembic revision --autogenerate -m "your_migration_message"

alembic upgrade head

poetry run uvicorn src.main:app --reload
```


### 🚀 **API Access**
🔑 Auth

|Method|Endpoint|Description|
|---|---|---|
|POST|/auth/register|Register user|
|POST|/auth/login|Login and get JWT|
|GET|/auth/confirm_email/{token}|Email verification|
|POST|/auth/request_email|Re-send confirmation email|

🙋‍♂️ Users

|Method|Endpoint|Description|
|---|---|---|
|GET|/users/me|Get current user info|
|PATCH|/users/avatar|Upload avatar (Cloudinary)|

📇 Contacts

|Method|Endpoint|Description|
|---|---|---|
|POST|/contacts/|Create a new contact|
|GET|/contacts/|List contacts with filtering|
|GET|/contacts/{id}|Get a specific contact|
|PATCH|/contacts/{id}|Update a contact|
|DELETE|/contacts/{id}|Delete a contact|
|GET|/contacts/search/|Search contacts by name/email|
|GET|/contacts/birthdays/|Upcoming birthdays within a given number of days|

### 📜 **API Docs**
- Swagger UI: http://localhost:8000/docs
- ReDoc UI: http://localhost:8000/redoc

🧪 Health Check
```bash
GET /healthcheck
```

✨ Technologies Used
- FastAPI
- PostgreSQL
- SQLAlchemy (Async)
- Alembic
- JWT Auth
- Cloudinary (avatar uploads)
- FastMail (email verification)
- Docker + Docker Compose


