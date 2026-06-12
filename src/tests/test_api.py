"""End-to-end tests for the FastAPI recommendation service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_home():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert "message" in payload
    assert "API" in payload["message"]


def test_users_endpoint_returns_ids():
    with TestClient(app) as client:
        response = client.get("/users", params={"limit": 5})

    assert response.status_code == 200
    payload = response.json()
    assert "available_user_ids" in payload
    assert payload["total_unique_users"] >= 0


def test_recommendations_endpoint_returns_items_for_sample_user():
    with TestClient(app) as client:
        users_response = client.get("/users", params={"limit": 1})
        user_id = users_response.json()["available_user_ids"][0]
        response = client.get(f"/users/{user_id}/recommendations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == user_id
    assert payload["n_recommendations"] > 0
    assert {"rank", "game_title", "score"} <= set(payload["recommendations"][0])


def test_recommendations_endpoint_returns_404_for_unknown_user():
    with TestClient(app) as client:
        response = client.get("/users/-1/recommendations")

    assert response.status_code == 404
