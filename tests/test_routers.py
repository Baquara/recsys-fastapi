import pytest
from unittest.mock import patch


# ── Items ─────────────────────────────────────────────────────────────────────

def test_list_items_empty(client):
    r = client.get("/items")
    assert r.status_code == 200
    assert r.json() == []


def test_create_and_list_items(client):
    payload = {"items": [
        {"itemId": 1, "title": "Alpha", "description": "Desc A", "tag": ["a"]},
        {"itemId": 2, "title": "Beta",  "description": "Desc B", "tag": ["b"]},
    ]}
    r = client.post("/items", json=payload)
    assert r.status_code == 201
    items = client.get("/items").json()
    assert len(items) == 2


def test_get_item_found(client):
    client.post("/items", json={"items": [{"itemId": 7, "title": "G", "description": "D", "tag": []}]})
    r = client.get("/items/7")
    assert r.status_code == 200
    assert r.json()["title"] == "G"


def test_get_item_not_found(client):
    assert client.get("/items/999").status_code == 404


def test_update_item_found(client):
    client.post("/items", json={"items": [{"itemId": 1, "title": "Old", "description": "D", "tag": []}]})
    r = client.put("/items/1", json={"title": "New", "description": "D2", "tag": ["x"]})
    assert r.status_code == 200
    assert r.json()["title"] == "New"


def test_update_item_not_found(client):
    r = client.put("/items/999", json={"title": "X", "description": "D", "tag": []})
    assert r.status_code == 404


def test_delete_item_found(client):
    client.post("/items", json={"items": [{"itemId": 1, "title": "X", "description": "D", "tag": []}]})
    assert client.delete("/items/1").status_code == 200
    assert client.get("/items/1").status_code == 404


def test_delete_item_not_found(client):
    assert client.delete("/items/999").status_code == 404


# ── Users ─────────────────────────────────────────────────────────────────────

def test_list_ratings_empty(client):
    assert client.get("/users").json() == []


def test_create_and_list_ratings(client):
    payload = {"items": [
        {"userId": 1, "itemId": 1, "rating": 5.0, "timestamp": 1000},
        {"userId": 1, "itemId": 2, "rating": 4.0, "timestamp": 1001},
    ]}
    r = client.post("/users", json=payload)
    assert r.status_code == 201
    assert len(client.get("/users").json()) == 2


def test_get_user_ratings_found(client):
    client.post("/users", json={"items": [{"userId": 3, "itemId": 1, "rating": 3.0, "timestamp": 1000}]})
    r = client.get("/users/3")
    assert r.status_code == 200
    assert r.json()[0]["userId"] == 3


def test_get_user_ratings_not_found(client):
    assert client.get("/users/999").status_code == 404


def test_update_user_ratings_found(client):
    client.post("/users", json={"items": [{"userId": 1, "itemId": 1, "rating": 3.0, "timestamp": 1000}]})
    r = client.put("/users/1", json={"items": [{"itemId": 1, "rating": 5.0, "timestamp": 2000}]})
    assert r.status_code == 200


def test_update_user_ratings_not_found(client):
    r = client.put("/users/999", json={"items": [{"itemId": 1, "rating": 5.0, "timestamp": 2000}]})
    assert r.status_code == 404


def test_delete_user_found(client):
    client.post("/users", json={"items": [{"userId": 5, "itemId": 1, "rating": 4.0, "timestamp": 1000}]})
    assert client.delete("/users/5").status_code == 200
    assert client.get("/users/5").status_code == 404


def test_delete_user_not_found(client):
    assert client.delete("/users/999").status_code == 404


# ── Events ────────────────────────────────────────────────────────────────────

def test_list_events_empty(client):
    assert client.get("/events").json() == []


def test_create_and_list_events(client):
    r = client.post("/events", json={"userId": 1, "itemId": 1, "rating": 1.0, "timestamp": 1000})
    assert r.status_code == 200
    assert len(client.get("/events").json()) == 1


def test_list_events_filter_by_user(client):
    client.post("/events", json={"userId": 1, "itemId": 1, "rating": 1.0, "timestamp": 1000})
    client.post("/events", json={"userId": 2, "itemId": 1, "rating": 1.0, "timestamp": 1001})
    r = client.get("/events?user_id=1")
    assert r.status_code == 200
    assert all(e["userId"] == 1 for e in r.json())


def test_list_events_filter_by_item(client):
    client.post("/events", json={"userId": 1, "itemId": 10, "rating": 1.0, "timestamp": 1000})
    client.post("/events", json={"userId": 1, "itemId": 20, "rating": 1.0, "timestamp": 1001})
    r = client.get("/events?item_id=10")
    assert r.status_code == 200
    assert all(e["itemId"] == 10 for e in r.json())


# ── Recommendations ───────────────────────────────────────────────────────────

def test_collaborative_success(client):
    with patch("app.routers.recommendations.recommendation_service.get_collaborative") as m:
        m.return_value = {"recommendations": [], "execution_time": {}}
        r = client.get("/recommendations/collaborative?sel_item=Alpha&nrec=3")
    assert r.status_code == 200


def test_collaborative_not_found(client):
    with patch("app.routers.recommendations.recommendation_service.get_collaborative",
               side_effect=ValueError("no match")):
        r = client.get("/recommendations/collaborative?sel_item=zzz&nrec=3")
    assert r.status_code == 404


def test_content_based_success(client):
    with patch("app.routers.recommendations.recommendation_service.get_content_based") as m:
        m.return_value = [{"target": {}}, {"position": 1}]
        r = client.get("/recommendations/content-based?item_index=0&n=2")
    assert r.status_code == 200


def test_content_based_not_found(client):
    with patch("app.routers.recommendations.recommendation_service.get_content_based",
               side_effect=IndexError("out of range")):
        r = client.get("/recommendations/content-based?item_index=999&n=2")
    assert r.status_code == 404


def test_hybrid_success(client):
    with patch("app.routers.recommendations.recommendation_service.get_hybrid") as m:
        m.return_value = {"alpha": 0.5, "recommendations": []}
        r = client.get("/recommendations/hybrid?sel_item=Alpha&nrec=3&alpha=0.5")
    assert r.status_code == 200


def test_hybrid_not_found(client):
    with patch("app.routers.recommendations.recommendation_service.get_hybrid",
               side_effect=ValueError("no match")):
        r = client.get("/recommendations/hybrid?sel_item=zzz&nrec=3")
    assert r.status_code == 404


def test_auto_success(client):
    with patch("app.routers.recommendations.recommendation_service.get_auto") as m:
        m.return_value = {"method": "content_based", "ratings_count": 0, "items": []}
        r = client.get("/recommendations/auto?sel_item=Alpha&nrec=3")
    assert r.status_code == 200
    assert r.json()["method"] == "content_based"


def test_auto_not_found(client):
    with patch("app.routers.recommendations.recommendation_service.get_auto",
               side_effect=ValueError("no match")):
        r = client.get("/recommendations/auto?sel_item=zzz&nrec=3")
    assert r.status_code == 404


# ── Admin ─────────────────────────────────────────────────────────────────────

def test_clear_database(client):
    client.post("/items", json={"items": [{"itemId": 1, "title": "X", "description": "D", "tag": []}]})
    r = client.delete("/admin/database")
    assert r.status_code == 200
    assert client.get("/items").json() == []


def test_system_info(client):
    with patch("app.routers.admin.system_service.get_system_info") as m:
        m.return_value = type("SI", (), {
            "uptime": "1d", "total_ram_mb": "8192", "available_ram_mb": "4096",
            "cpu_model": "Intel", "cpu_clock_mhz": "3600", "database_size": "1M",
        })()
        r = client.get("/admin/system")
    assert r.status_code == 200
    assert r.json()["uptime"] == "1d"
