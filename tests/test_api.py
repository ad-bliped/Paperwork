from fastapi.testclient import TestClient

from app.main import app, store


client = TestClient(app)


def setup_function() -> None:
    store.user_topics.clear()
    store.email_preferences.clear()
    store.writing_projects.clear()
    store.reminder_logs.clear()
    store.email_delivery_logs.clear()


def test_recommendation_and_digest_flow() -> None:
    r = client.post("/users/topics", json={"user_id": "u1", "topics": ["방법론", "추천"]})
    assert r.status_code == 200

    r = client.put(
        "/users/email-preferences",
        json={
            "user_id": "u1",
            "send_time": "07:00",
            "timezone": "Asia/Seoul",
            "frequency": "daily",
            "enabled": True,
        },
    )
    assert r.status_code == 200

    rec = client.get("/papers/recommendations/today", params={"user_id": "u1"})
    assert rec.status_code == 200
    assert len(rec.json()["recommendations"]) == 3

    digest = client.get("/users/daily-digest/preview", params={"user_id": "u1"})
    assert digest.status_code == 200
    assert digest.json()["subject"] == "[Paperwork] 오늘의 추천 논문"

    job = client.post("/jobs/send-daily-paper-email")
    assert job.status_code == 200
    assert job.json()["sent"] == 1


def test_writing_progress_and_reminders_flow() -> None:
    create = client.post(
        "/writing-projects",
        json={"user_id": "u2", "title": "석사논문", "sections": {"방법": 1000, "논의": 800}},
    )
    assert create.status_code == 200
    project = create.json()
    pid = project["id"]

    patch = client.patch(
        f"/writing-projects/{pid}/sections/방법",
        json={"current_words": 100, "target_words": 1000},
    )
    assert patch.status_code == 200

    reminders = client.post("/jobs/generate-reminders")
    assert reminders.status_code == 200
    assert reminders.json()["created"] >= 1

    user_reminders = client.get("/users/reminders/today", params={"user_id": "u2"})
    assert user_reminders.status_code == 200
    assert len(user_reminders.json()["reminders"]) >= 1
