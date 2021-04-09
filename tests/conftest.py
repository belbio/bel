# Standard Library
import os
import sys

# Third Party
import dotenv
import pytest
from starlette.testclient import TestClient

root_dir_path = os.path.dirname(os.path.realpath(__file__))

# Setup environment
files = [f"{root_dir_path}/pytest.env"]


for fn in files:
    print("FN", fn)
    dotenv.load_dotenv(fn, override=False)

# Load System Path before importing bel modules
import bel.db.arangodb  # isort:skip
import bel.db.elasticsearch  # isort:skip
import bel.db.redis  # isort:skip


@pytest.fixture(scope="session")
def client():

    try:
        # Local
        from api.app.main import app

        client = TestClient(app)
        print("##################### App", app, "Client", client)
        return client

    except Exception:
        return None


# @pytest.fixture
# def clean_databases():
#     """Clean up test arangodb database and elasticsearch index"""

#     bel.db.arangodb.reset_databases()
#     bel.db.elasticsearch.reset_indexes()

#     return True
