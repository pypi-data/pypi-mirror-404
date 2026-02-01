from djangotenberg.retry import retry
from djangotenberg.client import APIClient


client = APIClient()

def test_retry_with_callable():
    res = retry(client.health, delay=1)
    assert res.status_code == 200