def test_room1_check_answer_success(client):
    payload = {
        "selected_images": ["image2.jpg", "image3.jpg", "image5.jpg", "image6.jpg"]
    }
    response = client.post("/check_room1_answer", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"


def test_room1_check_answer_fail(client):
    payload = {"selected_images": ["image4.jpg"]}
    response = client.post("/check_room1_answer", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "fail"


def test_room2_submit_rejects_invalid_image(client):
    response = client.post("/room2/submit", json={"image": "nope.jpg", "label": 1})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "error"


def test_room3_anomaly_endpoints(client):
    trajectory = [[0, 0, 0.0], [1, 1, 1.0], [2, 1, 2.0]]

    response = client.post("/api/anomaly/score", json={"trajectory": trajectory})
    assert response.status_code == 200
    data = response.get_json()
    assert 0.0 <= data["score"] <= 1.0

    response = client.post("/api/anomaly/save", json={"trajectory": trajectory})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["saved_count"] == 1

    response = client.post("/api/anomaly/classify", json={"trajectory": trajectory})
    assert response.status_code == 200
    data = response.get_json()
    assert data["label"] == "hostile"
    assert data["reason"] == "similarity"
    assert data["bank_size"] == 1


def test_room4_rsa_flow_without_cpp(client):
    response = client.post("/api/room4/lidar_scan", json={"objects": ["obj1"]})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert isinstance(data["cipher"], list)
    assert {k["id"] for k in data["key_options"]} == {"K1", "K2", "K3"}

    response = client.post("/api/room4/rsa_try", json={"key_id": "K3"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert ("STOP" in data["decoded_text"]) or ("ENTITY" in data["decoded_text"])


def test_room4_rsa_try_requires_scan(client):
    response = client.post("/api/room4/rsa_try", json={"key_id": "K3"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"


def test_room4_rsa_try_rejects_unknown_key(client):
    response = client.post("/api/room4/lidar_scan", json={"objects": ["obj1"]})
    assert response.status_code == 200

    response = client.post("/api/room4/rsa_try", json={"key_id": "NOPE"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
