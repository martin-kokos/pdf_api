from fastapi.testclient import TestClient
import requests

from pdf_api.app import app
import pytest

client = TestClient(app)


@pytest.mark.skip(reason="Broken test. Returns 422 Unprocessable entity. https://github.com/encode/starlette/issues/1059 ")
def test_send_file():
    test_file_path = "tests/files/ZA7505_cdb.pdf"

    f = open(test_file_path, "rb")
    request = requests.Request('POST', "http://localhost/pdf_text_chunks", files={'file.pdf': f}).prepare().body

    response = client.post("/pdf_text_chunks", content=request)

    assert response.status_code == 200
    text_elems = response.json()
    assert text_elems[12670] == {
        "pos": 12672,
        "string": "page 351",
        "font_size": 8,
        "type": "p",
    }
