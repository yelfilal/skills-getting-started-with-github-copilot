import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore in-memory state before each test to ensure isolation."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture()
def client():
    return TestClient(app)


# ── GET /activities ────────────────────────────────────────────────────────────

def test_get_activities_returns_200(client):
    # Arrange – no setup needed, default data is sufficient

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200


def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_count = len(activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert len(response.json()) == expected_count


def test_get_activities_structure(client):
    # Arrange
    required_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    for name, details in response.json().items():
        assert required_fields.issubset(details.keys()), (
            f"Activity '{name}' is missing one of {required_fields}"
        )


# ── POST /activities/{activity_name}/signup ────────────────────────────────────

def test_signup_new_student_succeeds(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    assert email in activities[activity_name]["participants"]


def test_signup_unknown_activity_returns_404(client):
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_returns_400(client):
    # Arrange – michael is already in Chess Club
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_duplicate_does_not_add_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    count_before = len(activities[activity_name]["participants"])

    # Act
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert len(activities[activity_name]["participants"]) == count_before


# ── GET / (redirect) ──────────────────────────────────────────────────────────

def test_root_redirects_to_static_index(client):
    # Arrange – no setup needed

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")
