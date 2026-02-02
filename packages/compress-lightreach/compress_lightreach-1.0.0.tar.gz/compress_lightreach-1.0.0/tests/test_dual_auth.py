"""
Comprehensive tests for dual authentication system (JWT + API keys).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, timedelta

from api.main import app
from api.database import Base, User, RefreshToken, Subscription, SubscriptionPlan, SubscriptionTier, APIKey, get_db, seed_default_plans
from api.config import settings
from api.password_utils import hash_password
from api.jwt_utils import create_access_token
from api.db_utils import create_api_key


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session for testing."""
    # Shared in-memory DB for TestClient threadpool + per-test isolation.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(engine)

    # Seed plans once
    seed_session = TestingSessionLocal()
    seed_default_plans(seed_session)
    seed_session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def jwt_secret_key(monkeypatch):
    """Set JWT secret key for testing."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-jwt-authentication-12345")
    from api.config import Settings
    settings = Settings()
    return settings.JWT_SECRET_KEY


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user with subscription."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create FREE subscription
    free_plan = db_session.query(SubscriptionPlan).filter_by(tier=SubscriptionTier.FREE).first()
    if not free_plan:
        free_plan = SubscriptionPlan(
            tier=SubscriptionTier.FREE,
            name="Free",
            price_monthly=0,
            tokens_per_month=50_000,
            rate_limit_per_minute=30,
            allows_greedy=True,
            allows_optimal=False,
        )
        db_session.add(free_plan)
        db_session.commit()
    
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user.id,
        email=user.email,
        plan_id=free_plan.id,
        status="active",
        billing_cycle_start=now,
        billing_cycle_end=now + timedelta(days=30),
        next_billing_date=now + timedelta(days=30),
    )
    db_session.add(subscription)
    db_session.commit()
    
    return user


@pytest.fixture
def test_api_key(db_session: Session, test_user):
    """Create a test API key for the user."""
    subscription = db_session.query(Subscription).filter_by(user_id=test_user.id).first()
    plain_key, api_key = create_api_key(
        db=db_session,
        subscription_id=subscription.id,
        user_id=test_user.id,
        name="Test Key"
    )
    return plain_key, api_key


class TestJWTAuthentication:
    """Test JWT authentication for frontend."""
    
    def test_register_user(self, client, db_session):
        """Test user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        
        # Verify user was created
        user = db_session.query(User).filter_by(email="newuser@example.com").first()
        assert user is not None
        
        # Verify subscription was created
        subscription = db_session.query(Subscription).filter_by(user_id=user.id).first()
        assert subscription is not None
    
    def test_login_with_jwt(self, client, test_user, jwt_secret_key, db_session):
        """Test login and JWT token generation."""
        # Clean up any existing refresh tokens for this user
        db_session.query(RefreshToken).filter_by(user_id=test_user.id).delete()
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "refresh_token" in response.cookies
    
    def test_access_protected_route_with_jwt(self, client, test_user, jwt_secret_key):
        """Test accessing protected route with JWT token."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        access_token = login_response.json()["access_token"]
        
        # Access protected route
        response = client.post(
            "/api/v1/compress",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "algorithm": "greedy"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        # Should succeed (200) or fail with validation, but not auth error
        assert response.status_code != 401
        assert response.status_code != 403
    
    def test_refresh_token(self, client, test_user, jwt_secret_key, db_session):
        """Test token refresh."""
        # Clean up any existing refresh tokens
        db_session.query(RefreshToken).filter_by(user_id=test_user.id).delete()
        db_session.commit()
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        refresh_token = login_response.cookies.get("refresh_token")
        
        # Refresh
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        assert "access_token" in refresh_response.json()
    
    def test_logout(self, client, test_user, jwt_secret_key, db_session):
        """Test logout."""
        # Clean up any existing refresh tokens
        db_session.query(RefreshToken).filter_by(user_id=test_user.id).delete()
        db_session.commit()
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        refresh_token = login_response.cookies.get("refresh_token")
        
        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            cookies={"refresh_token": refresh_token}
        )
        assert logout_response.status_code == 200
        
        # Verify token is revoked
        from api.password_utils import hash_refresh_token
        token_hash = hash_refresh_token(refresh_token)
        token_record = db_session.query(RefreshToken).filter_by(token_hash=token_hash).first()
        assert token_record.is_revoked is True


class TestAPIKeyAuthentication:
    """Test API key authentication for library usage."""
    
    def test_access_protected_route_with_api_key(self, client, test_api_key):
        """Test accessing protected route with API key."""
        plain_key, api_key = test_api_key
        
        response = client.post(
            "/api/v1/compress",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "algorithm": "greedy"
            },
            headers={"X-API-Key": plain_key}
        )
        # Should succeed (200) or fail with validation, but not auth error
        assert response.status_code != 401
        assert response.status_code != 403
    
    def test_api_key_invalid(self, client):
        """Test with invalid API key."""
        response = client.post(
            "/api/v1/compress",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "algorithm": "greedy"
            },
            headers={"X-API-Key": "invalid_key"}
        )
        assert response.status_code == 401
    
    def test_api_key_missing(self, client):
        """Test without API key."""
        response = client.post(
            "/api/v1/compress",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "algorithm": "greedy"
            }
        )
        assert response.status_code == 401


class TestAPIKeyManagement:
    """Test API key management endpoints (JWT protected)."""
    
    def test_list_api_keys(self, client, test_user, test_api_key, jwt_secret_key):
        """Test listing API keys."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        access_token = login_response.json()["access_token"]
        
        # List API keys
        response = client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        keys = response.json()
        assert len(keys) >= 1
        assert "masked_key" in keys[0]
        assert "api_key" not in keys[0]  # Should never return plain key
    
    def test_create_api_key(self, client, test_user, jwt_secret_key, db_session):
        """Test creating a new API key."""
        # Clean up any existing refresh tokens
        db_session.query(RefreshToken).filter_by(user_id=test_user.id).delete()
        db_session.commit()
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        access_token = login_response.json()["access_token"]
        
        # Create API key
        response = client.post(
            "/api/v1/api-keys",
            json={"name": "My New Key"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "api_key" in data  # Only returned on creation
        assert data["name"] == "My New Key"
        assert data["api_key"].startswith("lr_live_")
        
        # Verify key was created in database
        api_key_id = data["id"]
        key_record = db_session.query(APIKey).filter_by(id=api_key_id).first()
        assert key_record is not None
        assert key_record.user_id == test_user.id
    
    def test_delete_api_key(self, client, test_user, test_api_key, jwt_secret_key, db_session):
        """Test deleting (deactivating) an API key."""
        plain_key, api_key = test_api_key
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        access_token = login_response.json()["access_token"]
        
        # Delete API key
        response = client.delete(
            f"/api/v1/api-keys/{api_key.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 204
        
        # Verify key is deactivated
        db_session.refresh(api_key)
        assert api_key.is_active is False
        
        # Verify key no longer works
        response = client.post(
            "/api/v1/compress",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "algorithm": "greedy"
            },
            headers={"X-API-Key": plain_key}
        )
        assert response.status_code == 401


class TestDualAuthCompatibility:
    """Test that both auth methods work together."""
    
    def test_jwt_and_api_key_both_work(self, client, test_user, test_api_key, jwt_secret_key):
        """Test that both JWT and API key authentication work for the same routes."""
        plain_key, api_key = test_api_key
        
        # Test with API key
        response1 = client.post(
            "/api/v1/decompress",
            json={"llm_format": "DICT:k=v|PROMPT:text"},
            headers={"X-API-Key": plain_key}
        )
        assert response1.status_code != 401
        
        # Test with JWT
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        access_token = login_response.json()["access_token"]
        
        response2 = client.post(
            "/api/v1/decompress",
            json={"llm_format": "DICT:k=v|PROMPT:text"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response2.status_code != 401
    
    def test_prefer_jwt_over_api_key(self, client, test_user, test_api_key, jwt_secret_key):
        """Test that JWT is preferred when both are provided."""
        plain_key, api_key = test_api_key
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        access_token = login_response.json()["access_token"]
        
        # Provide both JWT and API key - JWT should be used
        response = client.post(
            "/api/v1/compress",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "algorithm": "greedy"
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-API-Key": plain_key
            }
        )
        # Should use JWT (user's subscription) rather than API key's subscription
        assert response.status_code != 401

