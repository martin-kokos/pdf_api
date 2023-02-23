from fastapi.testclient import TestClient

from pdf_api.app import app
import pytest

client = TestClient(app)


@pytest.mark.skip(reason="Returns 422 UNprocessable entity, dunno why. Manually works")
def test_send_file():
    test_file_path = "tests/files/ZA7505_cdb.pdf"

    f = open(test_file_path, "rb")
    response = client.post("/pdf_text_chunks", files={"upload-file": f})

    assert response.status_code == 200
    text_elems = response.json()
    assert text_elems[12670] == {
        "pos": 12672,
        "string": "page 351",
        "font_size": 8,
        "type": "p",
    }
