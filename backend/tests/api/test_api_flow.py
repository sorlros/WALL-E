# import pytest (removed)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import shutil

# PATCH: Set DATABASE_URL to SQLite before importing db.database
# This prevents SQLAlchemy from trying to load PostgreSQL drivers (psycopg) which might be missing.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Override dependency
from db.database import Base, get_db
from api.auth import get_current_user
from main import app

# Setup In-Memory DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

import uuid

# Mock User
class MockUser:
    id = uuid.UUID("36b8f84d-df4e-4d49-b662-bcde71a8764f")
    email = "test@example.com"

def override_get_current_user():
    return MockUser()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def setup_db():
    print("🛠️ Setting up test database...")
    Base.metadata.create_all(bind=engine)

def teardown_db():
    print("🧹 Tearing down test database...")
    Base.metadata.drop_all(bind=engine)
    # Cleanup storage if any created
    if os.path.exists("storage/images"):
        # careful not to delete real data if running locally
        pass

def test_create_mission():
    try:
        response = client.post(
            "/missions/",
            json={
                "name": "Test Mission",
                "description": "Integration Test",
                "location_name": "Test Lab",
                "gps_lat": 37.5665,
                "gps_lng": 126.9780
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == "Test Mission", f"Expected 'Test Mission', got {data.get('name')}"
        assert data["gps_lat"] == 37.5665
        assert "id" in data
        print(f"✅ test_create_mission passed. Mission ID: {data['id']}")
        return data["id"]
    except Exception as e:
        print(f"❌ test_create_mission failed: {e}")
        raise e

def test_create_detection(mission_id):
    try:
        # Create a dummy image
        file_content = b"fake image bytes"
        
        response = client.post(
            f"/missions/{mission_id}/detections",
            data={
                "label": "crack",
                "confidence": 0.95,
                "bbox": "[0.1, 0.1, 0.5, 0.5]"
            },
            files={"file": ("test.jpg", file_content, "image/jpeg")}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["label"] == "crack"
        assert data["mission_id"] == mission_id
        assert "image_url" in data
        print(f"✅ test_create_detection passed. Detection ID: {data['id']}")
        return data["id"]
    except Exception as e:
        print(f"❌ test_create_detection failed: {e}")
        raise e

def test_update_detection_gps_updates_mission(detection_id, mission_id):
    try:
        # New GPS coordinates
        new_lat = 37.5000
        new_lng = 127.0000
        
        response = client.patch(
            f"/missions/detections/{detection_id}/gps",
            data={
                "gps_lat": new_lat,
                "gps_lng": new_lng
            }
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # KEY CHECK: The response should be the MISSION object, updated
        assert data["id"] == mission_id, "Expected returned object to be Mission"
        assert data["gps_lat"] == new_lat
        assert data["gps_lng"] == new_lng
        
        # Verify by fetching mission again
        response = client.get(f"/missions/{mission_id}")
        mission_data = response.json()
        assert mission_data["gps_lat"] == new_lat
        print("✅ test_update_detection_gps_updates_mission passed (Mission Updated)")
    except Exception as e:
        print(f"❌ test_update_detection_gps_updates_mission failed: {e}")
        raise e

def test_read_missions():
    try:
        response = client.get("/missions/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print("✅ test_read_missions passed")
    except Exception as e:
        print(f"❌ test_read_missions failed: {e}")
        raise e

if __name__ == "__main__":
    setup_db()
    try:
        mission_id = test_create_mission()
        detection_id = test_create_detection(mission_id)
        test_update_detection_gps_updates_mission(detection_id, mission_id)
        test_read_missions()
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print("\n💥 TESTS FAILED")
    finally:
        teardown_db()
