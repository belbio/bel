# Standard Library
import copy
import enum
import json
import re
from typing import Any, List, Mapping, Optional, Tuple, Union

# Third Party
# Third Party Imports
from pydantic import BaseModel, Field, root_validator


class Configuration(BaseModel):
    """BEL Configuration object

    stored in Arangodb bel.bel_config.configuration
    """

    pass
