# Standard Library
import os
import sys

# Third Party
# Local Imports
import dotenv
import pytest

root_dir_path = os.path.dirname(os.path.realpath(__file__))


# TODO - why is this removed?
# sys.path.remove("/Users/william/studio/dev/bel/src")

sys.path.append("/Users/william/studio/dev/bel/src")

# Setup environment
files = [f"{root_dir_path}/pytest.env"]


for fn in files:
    print("FN", fn)
    dotenv.load_dotenv(fn, override=False)

import bel.db.arangodb  # isort:skip
import bel.db.elasticsearch  # isort:skip
import bel.db.redis  # isort:skip


@pytest.fixture
def clean_databases():
    """Clean up test arangodb database and elasticsearch index"""

    bel.db.arangodb.reset_databases()
    bel.db.elasticsearch.reset_indexes()

    return True
