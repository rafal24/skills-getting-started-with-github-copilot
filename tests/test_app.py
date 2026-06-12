"""
Tests for the Mergington High School Activities API

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and conditions
- Act: Execute the code being tested
- Assert: Verify the results
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture to reset activities state before each test"""
    from src.app import activities
    
    # Arrange: Store original state
    original_state = {
        k: {
            "description": v["description"],
            "schedule": v["schedule"],
            "max_participants": v["max_participants"],
            "participants": v["participants"].copy()
        }
        for k, v in activities.items()
    }
    
    yield
    
    # Cleanup: Restore original state after test
    for activity_name in list(activities.keys()):
        activities[activity_name]["participants"] = original_state[activity_name]["participants"].copy()


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, reset_activities):
        """Test that GET /activities returns all activities"""
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert len(data) >= 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_structure(self, reset_activities):
        """Test that each activity has required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing {field} in {activity_name}"
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
    
    def test_activities_have_participants(self, reset_activities):
        """Test that activities have initial participants"""
        # Arrange
        activity_to_check = "Chess Club"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data.get(activity_to_check)
        
        # Assert
        assert activity is not None, f"{activity_to_check} not found"
        assert len(activity["participants"]) > 0, f"{activity_to_check} has no participants"


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_existing_activity(self, reset_activities):
        """Test successful signup for an existing activity"""
        # Arrange
        activity_name = "Science Club"
        test_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert test_email in data["message"]
        assert activity_name in data["message"]
    
    def test_signup_adds_participant_to_list(self, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        # Arrange
        activity_name = "Science Club"
        test_email = "testuser@mergington.edu"
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity_name]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        
        # Assert
        response_after = client.get("/activities")
        final_count = len(response_after.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert test_email in response_after.json()[activity_name]["participants"]
    
    def test_signup_for_nonexistent_activity_fails(self, reset_activities):
        """Test signup for a non-existent activity returns 404"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        test_email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{nonexistent_activity}/signup?email={test_email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_email_fails(self, reset_activities):
        """Test that signing up twice with same email returns error"""
        # Arrange
        activity_name = "Art Club"
        test_email = "duplicate@mergington.edu"
        
        # Act - First signup
        response1 = client.post(f"/activities/{activity_name}/signup?email={test_email}")
        assert response1.status_code == 200
        
        # Act - Second signup with same email
        response2 = client.post(f"/activities/{activity_name}/signup?email={test_email}")
        data2 = response2.json()
        
        # Assert
        assert response2.status_code == 400
        assert "already signed up" in data2["detail"]
    
    def test_signup_response_includes_details(self, reset_activities):
        """Test that signup returns appropriate message with all details"""
        # Arrange
        activity_name = "Drama Club"
        test_email = "success@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in data["message"]
        assert test_email in data["message"]
        assert activity_name in data["message"]


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""
    
    def test_remove_existing_participant_succeeds(self, reset_activities):
        """Test removing an existing participant from an activity"""
        # Arrange
        activity_name = "Science Club"
        test_email = "toremove@mergington.edu"
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        
        # Act
        response = client.delete(f"/activities/{activity_name}/participants?email={test_email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in data["message"]
        assert test_email in data["message"]
    
    def test_remove_participant_removes_from_list(self, reset_activities):
        """Test that removing participant actually removes them from the list"""
        # Arrange
        activity_name = "Science Club"
        test_email = "testremove@mergington.edu"
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        
        # Act - Verify added
        response_before = client.get("/activities")
        assert test_email in response_before.json()[activity_name]["participants"]
        
        # Act - Remove
        client.delete(f"/activities/{activity_name}/participants?email={test_email}")
        
        # Assert - Verify removed
        response_after = client.get("/activities")
        assert test_email not in response_after.json()[activity_name]["participants"]
    
    def test_remove_from_nonexistent_activity_fails(self, reset_activities):
        """Test removing from a non-existent activity returns 404"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        test_email = "student@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{nonexistent_activity}/participants?email={test_email}")
        
        # Assert
        assert response.status_code == 404
    
    def test_remove_nonexistent_participant_fails(self, reset_activities):
        """Test removing a participant who isn't in the activity returns 404"""
        # Arrange
        activity_name = "Science Club"
        test_email = "notinlist@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/participants?email={test_email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in data["detail"]
    
    def test_remove_increases_available_spots(self, reset_activities):
        """Test that removing a participant increases available spots"""
        # Arrange
        activity_name = "Science Club"
        test_email = "testspot@mergington.edu"
        response_initial = client.get("/activities")
        initial_max = response_initial.json()[activity_name]["max_participants"]
        initial_participants = len(response_initial.json()[activity_name]["participants"])
        initial_spots = initial_max - initial_participants
        
        # Act - Add participant
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        response_after_add = client.get("/activities")
        spots_after_add = response_after_add.json()[activity_name]["max_participants"] - len(response_after_add.json()[activity_name]["participants"])
        
        # Act - Remove participant
        client.delete(f"/activities/{activity_name}/participants?email={test_email}")
        response_after_remove = client.get("/activities")
        spots_after_remove = response_after_remove.json()[activity_name]["max_participants"] - len(response_after_remove.json()[activity_name]["participants"])
        
        # Assert
        assert spots_after_add == initial_spots - 1, "Spots should decrease after signup"
        assert spots_after_remove == initial_spots, "Spots should be restored after removal"


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static(self, reset_activities):
        """Test that root endpoint redirects to static files"""
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivityAvailability:
    """Tests for activity availability logic"""
    
    def test_availability_is_valid(self, reset_activities):
        """Test that availability is correctly calculated"""
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            max_participants = activity_data["max_participants"]
            current_participants = len(activity_data["participants"])
            assert current_participants <= max_participants, \
                f"{activity_name} has {current_participants} participants but max is {max_participants}"
    
    def test_capacity_constraint_respected(self, reset_activities):
        """Test that participant count respects capacity"""
        # Arrange
        activity_name = "Chess Club"
        response_before = client.get("/activities")
        chess_data = response_before.json()[activity_name]
        max_capacity = chess_data["max_participants"]
        current_count = len(chess_data["participants"])
        available_slots = max_capacity - current_count
        
        # Act - Fill available slots
        for i in range(available_slots):
            email = f"capacity_test_{i}@mergington.edu"
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Assert - Verify capacity reached
        response_final = client.get("/activities")
        final_count = len(response_final.json()[activity_name]["participants"])
        assert final_count == max_capacity


class TestActivityNames:
    """Tests for all activity names"""
    
    def test_all_required_activities_exist(self, reset_activities):
        """Test that all required activities exist by category"""
        # Arrange
        sports_keywords = ["soccer", "basketball", "gym"]
        artistic_keywords = ["art", "drama"]
        intellectual_keywords = ["chess", "programming", "debate", "science"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        activity_names = [name.lower() for name in data.keys()]
        
        # Assert - Sports activities
        sports_found = [name for name in activity_names if any(
            keyword in name for keyword in sports_keywords
        )]
        assert len(sports_found) >= 2, \
            f"Expected at least 2 sports activities, found: {sports_found}"
        
        # Assert - Artistic activities
        artistic_found = [name for name in activity_names if any(
            keyword in name for keyword in artistic_keywords
        )]
        assert len(artistic_found) >= 2, \
            f"Expected at least 2 artistic activities, found: {artistic_found}"
        
        # Assert - Intellectual activities
        intellectual_found = [name for name in activity_names if any(
            keyword in name for keyword in intellectual_keywords
        )]
        assert len(intellectual_found) >= 2, \
            f"Expected at least 2 intellectual activities, found: {intellectual_found}"
