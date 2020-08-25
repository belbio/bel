# Standard Library
import glob
import json
import os
import sys

# Local Imports
import dotenv
import pytest
from starlette.testclient import TestClient

root_dir_path = os.path.dirname(os.path.realpath(__file__))

# Setup environment
files = [f"{root_dir_path}/pytest.env"]


for fn in files:
    print("FN", fn)
    dotenv.load_dotenv(fn, override=False)

import bel.core.settings  # isort:skip
import bel.db.arangodb  # isort:skip
import bel.db.elasticsearch  # isort:skip
import bel.db.redis  # isort:skip


def pytest_sessionfinish(session, exitstatus):
    pass  # TODO - remove elasticsearch index and arangodb database


@pytest.fixture(scope="session")
def client():
    """API client with a user role token embedded"""

    # TODO provide actual token
    try:
        from main import app

        headers = {"Authorization": "Bearer UserToken"}
        client = TestClient(app)
        client.headers = headers
        return client

    except Exception as e:
        return f"Client creation problem {str(e)}"


@pytest.fixture(scope="session")
def admin_client():
    """API client with an admin role token embedded"""

    # TODO provide actual token
    try:
        from main import app

        headers = {"Authorization": "Bearer AdminToken"}
        admin_client = TestClient(app)
        admin_client.headers = headers
        return admin_client

    except Exception as e:
        return f"Client creation problem {str(e)}"


@pytest.fixture
def clean_databases():
    """Clean up test arangodb database and elasticsearch index"""
    db.arangodb.reset_database()

    db.elasticsearch.reset_indexes()

    db.redis.reset_queues()

    return True


# Load network JGF data files for use in tests
@pytest.fixture(scope="session")
def testdata():
    """Data for tests"""

    data = {}
    files = glob.glob(f"{root_dir_path}/data_files/*.json")
    for fp in files:
        basename = os.path.basename(fp).replace(".json", "")
        with open(fp, "r") as f:
            data[basename] = json.load(f)

    return data
