# 🔐 Authentication System Documentation

> **Complete authentication system documentation for Qeem Backend**

## 🌟 Overview

The Qeem backend implements a comprehensive JWT-based authentication system with user registration, login, profile management, and secure API access. This system follows security best practices and provides a robust foundation for user management.

## 🏗️ Architecture

### **Authentication Components**

```
Authentication System
├── JWT Token Management
│   ├── Access Token Generation
│   ├── Token Validation
│   └── Token Refresh (Future)
├── User Management
│   ├── Registration
│   ├── Login
│   ├── Profile Management
│   └── Password Security
├── API Protection
│   ├── Route Guards
│   ├── Dependency Injection
│   └── Error Handling
└── Security Features
    ├── Password Hashing (bcrypt)
    ├── Input Validation
    └── CORS Configuration
```

## 🔑 JWT Implementation

### **Token Structure**

```python
# JWT Payload Structure
{
    "sub": "user_email",           # Subject (user identifier)
    "exp": 1642248000,            # Expiration timestamp
    "iat": 1642244400,            # Issued at timestamp
    "type": "access_token"        # Token type
}
```

### **Token Configuration**

Tokens are created via `app/core/security.py` using environment-driven settings (see `app/core/config.py`). Access tokens are currently issued on login; refresh tokens and rotation are planned.

## 🛡️ Password Security

### **Password Hashing**

```python
# app/core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

### **Password Requirements**

- Minimum 8 characters
- No maximum length (but reasonable limits in frontend)
- Encrypted using bcrypt with salt

## 📋 API Endpoints

### **Authentication Endpoints**

#### **User Registration**

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:**

```json
{
  "id": 1,
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### **User Login**

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### **Get Current User**

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "id": 1,
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### **Update User Profile**

```http
PUT /api/v1/users/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com"
}
```

### **Protected Endpoints**

All endpoints except registration, login, and health check require authentication:

```python
# Example protected endpoint
@router.post("/calculate")
async def calculate_rate(
    payload: RateRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # current_user contains the user's email
    # Access user data via database queries
    pass
```

## 🔒 Security Features

### **CORS Configuration**

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://qeem.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### **Rate Limiting**

```python
# Basic rate limiting (can be enhanced with Redis)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # Login logic
    pass
```

### **Input Validation**

All inputs are validated using Pydantic schemas:

```python
# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, validator

class UserRegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
```

## 🗄️ Database Schema

### **User Model**

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rate_calculations = relationship("RateCalculation", back_populates="user")
```

## 🔧 Dependencies

### **Authentication Dependency**

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.security import decode_token

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return email

def get_current_active_user(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Get current active user from database."""
    user = db.query(User).filter(User.email == current_user).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
```

## 🚨 Error Handling

### **Authentication Errors**

```python
# Common authentication error responses
{
    "detail": "Invalid authentication credentials"
}

{
    "detail": "Could not validate credentials"
}

{
    "detail": "Inactive user"
}

{
    "detail": "User not found"
}
```

### **HTTP Status Codes**

- `200` - Success
- `201` - Created (registration)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (user not found)
- `422` - Validation Error (invalid input data)

## 🔄 Authentication Flow

### **Registration Flow**

```
1. User submits registration form
   ↓
2. Frontend sends POST /auth/register
   ↓
3. Backend validates input data
   ↓
4. Check if email already exists
   ↓
5. Hash password with bcrypt
   ↓
6. Create user record in database
   ↓
7. Return user data (no token)
   ↓
8. Frontend redirects to login
```

### **Login Flow**

```
1. User submits login form
   ↓
2. Frontend sends POST /auth/login
   ↓
3. Backend validates credentials
   ↓
4. Verify password against hash
   ↓
5. Generate JWT access token
   ↓
6. Return token with expiration
   ↓
7. Frontend stores token
   ↓
8. Redirect to protected route
```

### **Protected Route Access**

```
1. User accesses protected route
   ↓
2. Frontend includes token in Authorization header
   ↓
3. Backend validates JWT token
   ↓
4. Extract user email from token
   ↓
5. Inject current_user dependency
   ↓
6. Execute protected endpoint logic
   ↓
7. Return response with user context
```

## 🧪 Testing

### **Authentication Tests**

```python
# tests/test_auth.py
def test_user_registration():
    response = client.post("/api/v1/auth/register", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "testpassword123"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "john@example.com"

def test_user_login():
    # Register user first
    client.post("/api/v1/auth/register", json=user_data)

    response = client.post("/api/v1/auth/login", json={
        "email": "john@example.com",
        "password": "testpassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_protected_endpoint():
    # Login and get token
    login_response = client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
```

## 🔧 Configuration

### **Environment Variables**

```bash
# .env (key excerpts)
DATABASE_URL=postgresql://user:password@localhost:5432/qeem
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN_DAYS=7
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
MARKET_CACHE_TTL=3600
```

### **Security Configuration**

```python
# app/core/config.py
class Settings(BaseSettings):
    # Database
    database_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]

    # Security
    bcrypt_rounds: int = 12

    class Config:
        env_file = ".env"
```

## 🚀 Future Enhancements

### **Planned Features**

1. **Token Refresh** - Implement refresh token mechanism (rotation + storage)
2. **Email Verification** - Send verification emails and verification state
3. **Password Reset** - Forgot password functionality
4. **OAuth Integration** - Social login (Google, GitHub)
5. **Role-Based Access** - Admin, user roles
6. **Session Management** - Multiple device support
7. **Audit Logging** - Track authentication events

### **Security Improvements**

1. **Rate Limiting** - Redis-based rate limiting
2. **Account Lockout** - Lock accounts after failed attempts
3. **IP Whitelisting** - Restrict access by IP
4. **Two-Factor Authentication** - 2FA support
5. **Security Headers** - Additional security headers

## 📚 Related Documentation

- [API Documentation](API.md)
- [Database Schema](DB_SCHEMA.md)
- [Security Best Practices](../qeem-meta/docs/security/authentication.md)
- [Frontend Integration Guide](../qeem-meta/docs/development/frontend-backend-integration.md)

---

<div align="center">
  <strong>🔐 Secure Authentication for Qeem</strong>
  <br>
  <em>Robust, scalable, and secure user management</em>
</div>
