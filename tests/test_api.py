from fastapi.testclient import TestClient
import requests

from pdf_api.app import app
from pathlib import Path

client = TestClient(app)

test_file = Path("tests/files/ZA7505_cdb.pdf")


def prepare_file(filepath: Path) -> dict:
    """
    Prepare args for sending a file payload

    Workaround for: 422 Unprocessable entity. https://github.com/encode/starlette/issues/1059
    """

    with open(filepath, "rb") as f:
        body, content_type = requests.PreparedRequest()._encode_files(files={"file": f}, data={})

    return {
        "content": body,
        "headers": {"Content-Type": content_type},
    }


def test_status():
    response = client.get("/status")
    assert response.json() == {"status": "OK"}


def test_send_file():
    response = client.post("/pdf_text_chunks", **prepare_file(test_file))

    assert response.status_code == 200
    text_elems = response.json()["chunks"]
    assert text_elems[12670] == {
        "pos": 12672,
        "string": "page 351",
        "font_size": 8,
        "type": "p",
    }


def test_get_users():
    response = client.get("/users")
    assert response.status_code == 200


def test_post_user():
    response = client.post("/user/new", data={"username": "Alice"})
    assert response.status_code == 201

    assert client.cookies.get("jwt_token") is not None


def test_get_user():
    client.post("/user/new", data={"username": "Alice"})

    uid = int(client.cookies["uid"])
    response = client.get(f"/user/{uid}")
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "Alice"


def test_get_user_unauth():
    client.post("/user/new", data={"username": "Alice"})
    uid = int(client.cookies["uid"])

    client.cookies.delete("jwt_token")
    response = client.get(f"/user/{uid}")
    assert response.status_code == 401


def test_get_user_corrupt():
    client.post("/user/new", data={"username": "Alice"})
    uid = int(client.cookies["uid"])

    client.cookies["jwt_token"] = "Corrupt"
    response = client.get(f"/user/{uid}")
    assert response.status_code == 401
    client.cookies.delete("jwt_token")


def test_put_user():
    client.post("/user/new", data={"username": "Alice"})

    uid = int(client.cookies["uid"])
    response = client.put(f"/user/{uid}/update", params={"username": "Elis"})
    assert response.status_code == 200


def test_put_user_malic():
    client.post("/user/new", data={"username": "Alice"})

    uid = int(client.cookies["uid"])
    assert uid != 777, "lucky winner"
    response = client.put("/user/777/update", params={"username": "Malory"})
    assert response.status_code == 401


def test_get_user_documents():
    client.post("/user/new", data={"username": "Alice"})

    uid = int(client.cookies["uid"])
    response = client.get(f"/user/{uid}/documents")
    assert response.status_code == 200


def test_post_document():
    client.post("/user/new", data={"username": "Alice"})

    response = client.post("/document/new", **prepare_file(test_file))
    assert response.status_code == 201


def test_delete_user():
    client.post("/user/new", data={"username": "Alice"})

    uid = int(client.cookies["uid"])
    response = client.delete(f"/user/{uid}")
    assert response.status_code == 200


def test_get_documents():
    response = client.get("/documents")
    assert response.status_code == 200


def test_get_document():
    client.post("/user/new", data={"username": "Alice"})

    uid = int(client.cookies["uid"])
    response = client.get(f"/user/{uid}/documents")
    assert len(response.json()["documents"]) == 0

    response = client.post("/document/new", **prepare_file(test_file))

    response = client.get(f"/user/{uid}/documents")
    assert len(response.json()["documents"]) == 1
    inserted_doc_id = response.json()["documents"][0]["id"]

    response = client.get(f"/document/{inserted_doc_id}")
    assert response.status_code == 200


def test_delete_document():
    client.post("/user/new", data={"username": "Alice"})

    uid = int(client.cookies["uid"])
    response = client.post("/document/new", **prepare_file(test_file))

    response = client.get(f"/user/{uid}/documents")
    inserted_doc_id = response.json()["documents"][0]["id"]

    response = client.delete(f"/document/{inserted_doc_id}")
    assert response.status_code == 200
