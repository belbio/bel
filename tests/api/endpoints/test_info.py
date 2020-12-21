# Standard Library
import re


def test_status(client):
    """Status details on API"""

    response = client.get("/status")
    print("Response", response.json())

    assert response.status_code == 200
    assert response.json()["state"] == "OK"


# def test_settings(token):

#     headers = {"Authorization": f"Bearer {token}"}
#     response = client.get("/settings", headers=headers)
#     settings = response.json()

#     print("DumpVar:\n", json.dumps(response.json(), indent=4))

#     assert settings.get("ARANGO_URL", False)
#     assert settings.get("ELASTICSEARCH_URL", False)


def test_version(client):
    """Check that the version is returned"""

    r = client.get("/version")
    result = r.json()

    print("Version", result)
    version = result["version"]

    assert re.match("\d+\.\d+", version)


def test_ping(client):
    """Non-authenticated endpoint to test that the API is running"""

    r = client.get("/ping")
    result = r.json()

    print("Ping", result)

    assert result["running"] == True
