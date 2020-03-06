########################
# BEL FUNCTION IMPORTS #
########################

# Standard Library
import logging

# Local Imports
import bel.db
import bel.edge
import bel.lang
import bel.lang.bel_specification as bel_specification
import bel.nanopub
import bel.resources
from bel.lang.belobj import BEL

logging.getLogger(__name__).addHandler(logging.NullHandler())
