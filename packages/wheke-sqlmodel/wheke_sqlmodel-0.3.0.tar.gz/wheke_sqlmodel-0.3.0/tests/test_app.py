from fastapi import status
from fastapi.testclient import TestClient


def test_list_entries(client: TestClient) -> None:
    response = client.post("/entries", json={"value": "test"})
    assert response.status_code == status.HTTP_201_CREATED

    response = client.get("/entries")
    assert response.status_code == status.HTTP_200_OK

    assert len(response.json()) == 1
