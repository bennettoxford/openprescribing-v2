def test_index(client):
    rsp = client.get("/")
    assert rsp.status_code == 200
