"""
Security & Authentication Module
JWT authentication, API key management, rate limiting
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from passlib.context import CryptContext
import jwt
from loguru import logger
from utils.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT settings
SECRET_KEY = settings.jwt_secret_key if hasattr(settings, 'jwt_secret_key') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class User:
    """User model"""
    def __init__(self, username: str, email: str, is_active: bool = True):
        self.username = username
        self.email = email
        self.is_active = is_active


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time

    Returns:
        JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token data

    Raises:
        HTTPException if token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """
    Get current authenticated user from JWT token

    Usage in FastAPI:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user": user.username}
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    # In production, fetch user from database
    user = User(username=username, email=payload.get("email", ""))

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Verify API key

    Usage:
        @app.get("/api/v1/data")
        async def get_data(authenticated: bool = Depends(verify_api_key)):
            return {"data": "sensitive"}
    """
    if not api_key:
        raise HTTPException(status_code=403, detail="API key required")

    # In production, check against database
    valid_api_keys = {
        settings.dnse_api_key: "DNSE API",
        # Add more API keys here
    }

    if api_key not in valid_api_keys:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(status_code=403, detail="Invalid API key")

    return True


class RateLimiter:
    """
    Simple rate limiter using Redis

    Limits requests per IP/API key to prevent abuse
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limit

        Args:
            identifier: Unique identifier (IP, API key, user ID)

        Returns:
            True if within limit, raises HTTPException otherwise
        """
        from utils.cache import cache_manager

        key = f"rate_limit:{identifier}"
        current = cache_manager.get(key, 0)

        if current >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s"
            )

        # Increment counter
        cache_manager.set(key, current + 1, self.window_seconds)

        return True


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
    """
    Encrypt sensitive data (API keys, secrets)

    Args:
        data: Data to encrypt
        key: Encryption key (uses SECRET_KEY if not provided)

    Returns:
        Encrypted string
    """
    from cryptography.fernet import Fernet
    import base64

    if key is None:
        # Use SECRET_KEY padded/hashed to valid Fernet key
        import hashlib
        key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())

    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return encrypted.decode()


def decrypt_sensitive_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """
    Decrypt sensitive data

    Args:
        encrypted_data: Encrypted string
        key: Decryption key

    Returns:
        Decrypted string
    """
    from cryptography.fernet import Fernet
    import base64

    if key is None:
        import hashlib
        key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())

    f = Fernet(key)
    decrypted = f.decrypt(encrypted_data.encode())
    return decrypted.decode()
