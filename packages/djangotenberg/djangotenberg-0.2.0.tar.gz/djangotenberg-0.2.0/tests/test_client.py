from djangotenberg.client import APIClient
from djangotenberg.properties import PageSize, Property

def test_api_client_get_health():
    client = APIClient()
    res = client.health()
    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/json; charset=utf-8"
    assert res.json().get("status") == "up"


def test_api_client_html_to_pdf():
    client = APIClient()
    res = client.html_to_pdf("<html><body><h1>Hello World</h1></body></html>")
    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/pdf"

def test_api_client_html_to_pdf_with_properties():
    client = APIClient()
    
    props = Property()
    props = props.page_size(PageSize.A4_PAGE_SIZE)
    properties = props.build()
    
    res = client.html_to_pdf("<html><body><h1>Hello World</h1></body></html>", properties)
    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/pdf"


def test_api_client_read_pdf_metadata():
    client = APIClient()
    res = client.read_pdf_metadata([{"file": "test.pdf", "data": b"test"}])
    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/json"

def test_api_client_write_pdf_metadata():
    mock_metadata = {
        "Author": "Mr. Python Developer",
        "Title": "Test PDF",
        "Subject": "Test PDF",
        "Keywords": "Test PDF",
        "Creator": "Mr. Python Developer",
        "Producer": "Mr. Python Developer",
    }

    with open("tests/test_data/html_result.pdf", "rb") as f:
        data = f.read()
    
    client = APIClient()
    res = client.write_pdf_metadata([{"file": "html_result.pdf", "data": data}], mock_metadata)
    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/pdf"


def test_api_client_merge_pdf():
    client = APIClient()
    with open("tests/test_data/html_result.pdf", "rb") as f:
        data = f.read()
    
    with open("tests/test_data/html_result2.pdf", "rb") as f:
        data2 = f.read()

    res = client.merge_pdf([
        {"file": "html_result.pdf", "data": data},
        {"file": "html_result2.pdf", "data": data2}
    ])

    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/pdf"
