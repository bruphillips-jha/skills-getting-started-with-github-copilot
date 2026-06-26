from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities_state():
    snapshot = deepcopy(activities)

    yield

    activities.clear()
    activities.update(snapshot)


def test_get_activities_returns_200_and_payload(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_activity in payload
    assert isinstance(payload[expected_activity]["participants"], list)


def test_signup_adds_participant_successfully(client):
    # Arrange
    activity_name = "RoboticsLab"
    email = "newstudent@mergington.edu"
    activities[activity_name] = {
        "description": "Build and program robots",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 5,
        "participants": [],
    }

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "UnknownActivity"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_duplicate_participant(client):
    # Arrange
    activity_name = "CreativeWriting"
    email = "writer@mergington.edu"
    activities[activity_name] = {
        "description": "Practice storytelling and writing",
        "schedule": "Mondays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": [email],
    }

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_400_when_activity_is_full(client):
    # Arrange
    activity_name = "FullClass"
    email = "waiting@mergington.edu"
    activities[activity_name] = {
        "description": "Already at capacity",
        "schedule": "Tuesdays, 3:00 PM - 4:00 PM",
        "max_participants": 1,
        "participants": ["enrolled@mergington.edu"],
    }

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert email not in activities[activity_name]["participants"]


def test_unregister_removes_participant_successfully(client):
    # Arrange
    activity_name = "VolunteerClub"
    email = "helper@mergington.edu"
    activities[activity_name] = {
        "description": "Community volunteering",
        "schedule": "Wednesdays, 4:00 PM - 5:00 PM",
        "max_participants": 8,
        "participants": [email],
    }

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "MissingActivity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_missing_participant(client):
    # Arrange
    activity_name = "MathCircle"
    email = "absent@mergington.edu"
    activities[activity_name] = {
        "description": "Advanced math practice",
        "schedule": "Thursdays, 4:00 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["present@mergington.edu"],
    }

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found in this activity"
