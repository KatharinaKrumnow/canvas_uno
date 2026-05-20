import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


def _encode_activity_name(name: str) -> str:
    return urllib.parse.quote(name, safe="")


def test_get_activities(client, reset_activities):
    response = client.get("/activities")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert "Chess Club" in body
    assert "Programming Class" in body


def test_signup_success(client, reset_activities):
    email = "new.student@mergington.edu"
    path = f"/activities/{_encode_activity_name('Chess Club')}/signup"
    response = client.post(path, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in client.get("/activities").json()["Chess Club"]["participants"]


def test_signup_duplicate(client, reset_activities):
    email = "michael@mergington.edu"
    path = f"/activities/{_encode_activity_name('Chess Club')}/signup"
    response = client.post(path, params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_unregister_success(client, reset_activities):
    email = "michael@mergington.edu"
    path = f"/activities/{_encode_activity_name('Chess Club')}/participants"
    response = client.delete(path, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert email not in client.get("/activities").json()["Chess Club"]["participants"]


def test_unregister_missing_participant(client, reset_activities):
    email = "unknown.student@mergington.edu"
    path = f"/activities/{_encode_activity_name('Chess Club')}/participants"
    response = client.delete(path, params={"email": email})

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not registered for this activity"


def test_missing_activity_errors(client, reset_activities):
    missing_activity = "Nonexistent Activity"
    signup_path = f"/activities/{_encode_activity_name(missing_activity)}/signup"
    unregister_path = f"/activities/{_encode_activity_name(missing_activity)}/participants"

    signup_response = client.post(signup_path, params={"email": "a@student.edu"})
    assert signup_response.status_code == 404
    assert signup_response.json()["detail"] == "Activity not found"

    unregister_response = client.delete(unregister_path, params={"email": "a@student.edu"})
    assert unregister_response.status_code == 404
    assert unregister_response.json()["detail"] == "Activity not found"
