"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"].copy()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root redirects to the static index page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        assert "Soccer Team" in data
        assert "Basketball Team" in data
        assert "Drama Club" in data
        assert len(data) == len(activities)  # Total number of activities should match the source
    
    def test_activity_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        soccer = data["Soccer Team"]
        assert "description" in soccer
        assert "schedule" in soccer
        assert "max_participants" in soccer
        assert "participants" in soccer
        assert isinstance(soccer["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Soccer Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Soccer Team"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_registration(self, client):
        """Test that duplicate registrations are prevented"""
        email = "alex@mergington.edu"  # Already registered in Soccer Team
        
        response = client.post(
            f"/activities/Soccer Team/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_students(self, client):
        """Test signing up multiple students"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(f"/activities/Chess Club/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all students were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        chess_participants = activities_data["Chess Club"]["participants"]
        
        for email in emails:
            assert email in chess_participants
    
    def test_signup_when_activity_is_full(self, client):
        """Test that signup is prevented when activity reaches max_participants limit"""
        # Chess Club has max_participants: 12 and already has 2 participants
        # So we can add 10 more before it's full
        max_capacity = activities["Chess Club"]["max_participants"]
        current_count = len(activities["Chess Club"]["participants"])
        spots_available = max_capacity - current_count
        
        # Fill up to capacity
        for i in range(spots_available):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/Chess Club/signup?email={email}")
            assert response.status_code == 200
        
        # Verify activity is now full
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert len(activities_data["Chess Club"]["participants"]) == max_capacity
        
        # Try to add one more student - should fail
        response = client.post("/activities/Chess Club/signup?email=overflow@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "Activity is full" in data["detail"]
    
    def test_signup_at_exact_capacity(self, client):
        """Test edge case when activity is exactly at capacity"""
        # Basketball Team has max_participants: 15 and 1 participant
        # Fill it to exactly max capacity
        max_capacity = activities["Basketball Team"]["max_participants"]
        current_count = len(activities["Basketball Team"]["participants"])
        spots_available = max_capacity - current_count
        
        # Fill to exact capacity
        for i in range(spots_available):
            email = f"player{i}@mergington.edu"
            response = client.post(f"/activities/Basketball Team/signup?email={email}")
            assert response.status_code == 200
        
        # Verify we're at exact capacity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert len(activities_data["Basketball Team"]["participants"]) == max_capacity
        
        # Try to add one more - should fail
        response = client.post("/activities/Basketball Team/signup?email=extraplayer@mergington.edu")
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "alex@mergington.edu"  # Already registered in Soccer Team
        
        response = client.delete(
            f"/activities/Soccer Team/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Soccer Team"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_not_registered(self, client):
        """Test unregistering a student who is not registered"""
        email = "notregistered@mergington.edu"
        
        response = client.delete(
            f"/activities/Soccer Team/unregister?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_signup_and_unregister_workflow(self, client):
        """Test the full workflow of signing up and then unregistering"""
        email = "workflow@mergington.edu"
        activity = "Art Studio"
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify registered
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""
    
    def test_activity_name_with_spaces(self, client):
        """Test that activity names with spaces are handled correctly"""
        response = client.post(
            "/activities/Soccer Team/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
    
    def test_email_with_special_characters(self, client):
        """Test emails with special characters"""
        from urllib.parse import quote
        email = "test+tag@mergington.edu"
        response = client.post(
            f"/activities/Drama Club/signup?email={quote(email)}"
        )
        assert response.status_code == 200
        
        # Verify it was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Drama Club"]["participants"]
