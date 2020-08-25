# Standard Library
import re
from dataclasses import dataclass
from typing import List, Mapping, Optional

# Third Party Imports
import arango
import arango.client
import arango.database
import arango.exceptions
import boltons.iterutils
from loguru import logger

# Local Imports
import bel.core.settings as settings
from bel.core.utils import _create_hash


edgestore_db_name = settings.EDGESTORE_DB  # Edgestore
resources_db_name = settings.RESOURCES_DB  # BEL Resources (Namespaces, etc)
bel_db_name = settings.BEL_DB  # Misc BEL

# Collection names
edgestore_nodes_name = "nodes"  # edgestore node collection name
edgestore_edges_name = "edges"  # edgestore edge collection name
edgestore_pipeline_name = "pipeline"  # edgestore pipeline state collection name

# BEL Resources
equiv_nodes_name = "equivalence_nodes"  # equivalence node collection name
equiv_edges_name = "equivalence_edges"  # equivalence edge collection name
ortholog_nodes_name = "ortholog_nodes"  # ortholog node collection name
ortholog_edges_name = "ortholog_edges"  # ortholog edge collection name
resources_metadata_name = "resources_metadata"  # BEL Resources metadata
terms_coll_name = "terms"  # BEL Namespaces/Terms collection name

# BEL database collections
bel_config_name = "bel_config"  # BEL settings and configuration
bel_namespaces_name = "bel_namespaces"  # BEL namespaces
bel_validations_name = "validations"  # BEL Assertion/Annotation validations


# TODO - update get db and get collections using same pattern as in userstore/common/db.py
#        I made the mistake below of edgestore_db = sys_db.create_database()
#        instead of
#           sys_db.create_database('edgestore')
#           edgestore_db = client.db('edgestore')
#           if edgestore_db.has_collection('xxx'):
#               xxx_coll = edgestore_db.collection('xxx')
#           else:
#               xxx_coll = edgestore_db.create_collection('xxx')


def get_user_credentials(username, password):
    """Get username/password

    Use provided username and password OR in config OR blank in that order
    """
    username = boltons.iterutils.first([username, settings.ARANGO_USER], default="")
    password = boltons.iterutils.first([password, settings.ARANGO_PASSWORD], default="",)

    return username, password


def get_client(url=None, port=None, username=None, password=None):
    """Get arango client and edgestore db handle"""

    url = boltons.iterutils.first([url, settings.ARANGO_URL, "http://localhost:8529"])
    (username, password) = get_user_credentials(username, password)

    try:
        client = arango.ArangoClient(hosts=url)
        client.db(verify=True)
        return client

    except Exception:
        logger.error(f"Cannot access arangodb at {url}")
        return None


# Index mgmt #################################################################################
@dataclass
class IndexDefinition:
    """Class for defining collection indexes"""

    fields: List[str]  # ordered list of fields to be indexed
    id: Optional[str] = None  # ID is provided by arangodb
    type: str = "hash"  # primary or edge indexes are ignored
    unique: bool = False
    sparse: Optional[bool] = None
    deduplicate: Optional[bool] = None
    name: str = None
    in_background: bool = True


def add_index(collection, index: IndexDefinition):
    """Add index"""

    # add_hash_index(fields, unique=None, sparse=None, deduplicate=None, name=None, in_background=None)
    if index.type == "hash":
        collection.add_hash_index(
            index.fields,
            unique=index.unique,
            sparse=index.sparse,
            deduplicate=index.deduplicate,
            name=index.name,
            in_background=index.in_background,
        )
    elif index.type == "persistent":
        collection.add_persistent_index(
            index.fields,
            unique=index.unique,
            sparse=index.sparse,
            name=index.name,
            in_background=index.in_background,
        )
    else:
        logger.error(f"Cannot add index type: {index.type}")


def remove_old_indexes(
    collection,
    current_indexes: Mapping[str, IndexDefinition],
    desired_indexes: Mapping[str, IndexDefinition],
):
    """Remove out of date indexes"""

    for key in current_indexes:
        if key not in desired_indexes:
            print(f"Removing index {key} id: {current_indexes[key].id} from {collection}")
            collection.delete_index(current_indexes[key].id)


def update_index_state(collection, desired_indexes: List[IndexDefinition]):
    """Update index state

    desired_indexes keys = f"{index_type}_{'_'.join(sorted(fields))}", e.g. hash_firstname_lastname

    Remove indices that are not specified and add indices that are missing
    """

    new = {}
    for index in desired_indexes:
        index_key = f"{index.type}_{'_'.join(sorted(index.fields))}"
        new[index_key] = index

    desired_indexes = new

    current_indexes_list = collection.indexes()
    current_indexes: dict = {}
    for idx in current_indexes_list:
        if idx["type"] in ["primary", "edge"]:
            continue  # skip primary indices

        idx.pop("selectivity", None)
        index = IndexDefinition(**idx)
        index_key = f"{index.type}_{'_'.join(sorted(index.fields))}"
        current_indexes[index_key] = index

    remove_old_indexes(collection, current_indexes, desired_indexes)

    # Add missing desired indexes
    for key in desired_indexes:
        if key not in current_indexes:
            add_index(collection, desired_indexes[key])


# Index mgmt ##################################################################################


def get_edgestore_handles(
    client: arango.client.ArangoClient, username=None, password=None,
) -> dict:
    """Get Edgestore arangodb database handles

    Args:
        client (arango.client.ArangoClient): Description
        username (None, optional): Description
        password (None, optional): Description
    """

    (username, password) = get_user_credentials(username, password)

    # client is created when module is first imported
    sys_db = client.db("_system", username=username, password=password)

    # Create a new database for Edgestore
    if sys_db.has_database(edgestore_db_name):
        if username and password:
            edgestore_db = client.db(edgestore_db_name, username=username, password=password)
        else:
            edgestore_db = client.db(edgestore_db_name)
    else:
        if username and password:
            sys_db.create_database(
                name=edgestore_db_name,
                users=[{"username": username, "password": password, "active": True}],
            )
        else:
            sys_db.create_database(name=edgestore_db_name)
        edgestore_db = client.db(edgestore_db_name)

    # Add edges collection
    if edgestore_db.has_collection(edgestore_edges_name):
        edges_coll = edgestore_db.collection(edgestore_edges_name)
    else:
        edges_coll = edgestore_db.create_collection(
            edgestore_edges_name, edge=True, index_bucket_count=64
        )

    # Add nodes collection
    if edgestore_db.has_collection(edgestore_nodes_name):
        nodes_coll = edgestore_db.collection(edgestore_nodes_name)
    else:
        nodes_coll = edgestore_db.create_collection(edgestore_nodes_name, index_bucket_count=64)

    # Add pipeline_info collection
    if edgestore_db.has_collection(edgestore_pipeline_name):
        pipeline_coll = edgestore_db.collection(edgestore_pipeline_name)
    else:
        pipeline_coll = edgestore_db.create_collection(
            edgestore_pipeline_name, index_bucket_count=64
        )

    # Update indexes
    update_index_state(
        edges_coll,
        [
            IndexDefinition(type="hash", fields=["relation"], unique=False),
            IndexDefinition(type="hash", fields=["edge_types"], unique=False),
            IndexDefinition(type="hash", fields=["nanopub_id"], unique=False),
            IndexDefinition(type="hash", fields=["metadata.project"], unique=False),
            IndexDefinition(type="hash", fields=["annotations[*].id"], unique=False),
        ],
    )
    update_index_state(
        nodes_coll,
        [
            IndexDefinition(type="hash", fields=["names"], unique=False),
            IndexDefinition(type="hash", fields=["components"], unique=False),
        ],
    )
    update_index_state(
        pipeline_coll, [IndexDefinition(type="persistent", fields=["processed_ts"], unique=False),],
    )

    return {
        "edgestore_db": edgestore_db,
        "nodes_coll": nodes_coll,
        "edges_coll": edges_coll,
        "pipeline_coll": pipeline_coll,
    }


def get_resources_handles(client, username=None, password=None):
    """Get BEL Resources arangodb handle"""

    (username, password) = get_user_credentials(username, password)

    sys_db = client.db("_system", username=username, password=password)

    # Create a new database named "bel_resources"
    if sys_db.has_database(resources_db_name):
        if username and password:
            resources_db = client.db(resources_db_name, username=username, password=password)
        else:
            resources_db = client.db(resources_db_name)
    else:
        if username and password:
            resources_db = sys_db.create_database(
                name=resources_db_name,
                users=[{"username": username, "password": password, "active": True}],
            )
        else:
            resources_db = sys_db.create_database(name=resources_db_name)

    if resources_db.has_collection(resources_metadata_name):
        resources_metadata_coll = resources_db.collection(resources_metadata_name)
    else:
        resources_metadata_coll = resources_db.create_collection(resources_metadata_name)

    if resources_db.has_collection(equiv_nodes_name):
        equiv_nodes_coll = resources_db.collection(equiv_nodes_name)
    else:
        equiv_nodes_coll = resources_db.create_collection(equiv_nodes_name)

    if resources_db.has_collection(equiv_edges_name):
        equiv_edges_coll = resources_db.collection(equiv_edges_name)
    else:
        equiv_edges_coll = resources_db.create_collection(equiv_edges_name, edge=True)

    if resources_db.has_collection(ortholog_nodes_name):
        ortholog_nodes_coll = resources_db.collection(ortholog_nodes_name)
    else:
        ortholog_nodes_coll = resources_db.create_collection(ortholog_nodes_name)

    if resources_db.has_collection(ortholog_edges_name):
        ortholog_edges_coll = resources_db.collection(ortholog_edges_name)
    else:
        ortholog_edges_coll = resources_db.create_collection(ortholog_edges_name, edge=True)

    if resources_db.has_collection(terms_coll_name):
        terms_coll = resources_db.collection(terms_coll_name)
    else:
        terms_coll = resources_db.create_collection(terms_coll_name)

    # Update indexes
    update_index_state(
        equiv_nodes_coll, [IndexDefinition(type="hash", fields=["key"], unique=True)]
    )
    update_index_state(
        terms_coll,
        [
            IndexDefinition(type="hash", fields=["key"], unique=True),
            IndexDefinition(type="persistent", fields=["alt_keys[*]"], unique=False, sparse=True),
            IndexDefinition(
                type="persistent", fields=["equivalence_keys[*]"], unique=False, sparse=True
            ),
            IndexDefinition(
                type="persistent", fields=["obsolete_keys[*]"], unique=False, sparse=True
            ),
        ],
    )
    update_index_state(
        ortholog_nodes_coll, [IndexDefinition(type="hash", fields=["key"], unique=True)]
    )

    return {
        "resources_db": resources_db,
        "resources_metadata_coll": resources_metadata_coll,
        "equiv_nodes_coll": equiv_nodes_coll,
        "equiv_edges_coll": equiv_edges_coll,
        "ortholog_nodes_coll": ortholog_nodes_coll,
        "ortholog_edges_coll": ortholog_edges_coll,
        "terms_coll": terms_coll,
    }


def get_bel_handles(client, username=None, password=None):
    """Get BEL API arango db handle"""

    (username, password) = get_user_credentials(username, password)

    sys_db = client.db("_system", username=username, password=password)

    # Create a new database named "bel"
    if sys_db.has_database(bel_db_name):
        if username and password:
            bel_db = client.db(bel_db_name, username=username, password=password)
        else:
            bel_db = client.db(bel_db_name)
    else:
        if username and password:
            sys_db.create_database(
                name=bel_db_name,
                users=[{"username": username, "password": password, "active": True}],
            )
        else:
            sys_db.create_database(name=bel_db_name)

        bel_db = client.db(bel_db_name)

    if bel_db.has_collection(bel_config_name):
        bel_config_coll = bel_db.collection(bel_config_name)
    else:
        bel_config_coll = bel_db.create_collection(bel_config_name, index_bucket_count=64)

    if bel_db.has_collection(bel_validations_name):
        bel_validations_coll = bel_db.collection(bel_validations_name)
    else:
        bel_validations_coll = bel_db.create_collection(bel_validations_name, index_bucket_count=64)

    return {
        "bel_db": bel_db,
        "bel_config_coll": bel_config_coll,
        "bel_validations_coll": bel_validations_coll,
    }


# #############################################################################
# Initialize arango_client !!!!!!!!!!!!!!!!!!!
#     and provide db and collection handles
# #############################################################################
client = get_client()

# Edgestore db
edgestore_handles = get_edgestore_handles(client)
edgestore_db = edgestore_handles["edgestore_db"]
nodes_coll = edgestore_handles["nodes_coll"]
edges_coll = edgestore_handles["edges_coll"]
pipeline_coll = edgestore_handles["pipeline_coll"]

# Resources db
resources_handles = get_resources_handles(client)
resources_db = resources_handles["resources_db"]
resources_metadata_coll = resources_handles["resources_metadata_coll"]
equiv_nodes_coll = resources_handles["equiv_nodes_coll"]
equiv_edges_coll = resources_handles["equiv_edges_coll"]
ortholog_nodes_coll = resources_handles["ortholog_nodes_coll"]
ortholog_edges_coll = resources_handles["ortholog_edges_coll"]
terms_coll = resources_handles["terms_coll"]

# BEL db
bel_handles = get_bel_handles(client)
bel_db = bel_handles["bel_db"]
bel_config_coll = bel_handles["bel_config_coll"]
bel_validations_coll = bel_handles["bel_validations_coll"]


def delete_database(client, db_name, username=None, password=None):
    """Delete Arangodb database

    """

    (username, password) = get_user_credentials(username, password)

    sys_db = client.db("_system", username=username, password=password)

    try:
        return sys_db.delete_database(db_name)
    except Exception:
        logger.warn("No arango database {db_name} to delete, does not exist")


def batch_load_docs(db, doc_iterator, on_duplicate: str = "replace"):
    """Batch load documents

    Args:
        db: ArangoDB client database handle
        doc_iterator:  function that yields (collection_name, doc_key, doc)
        on_duplicate: defaults to replace, but can be error, update, replace or ignore

        https://python-driver-for-arangodb.readthedocs.io/en/master/specs.html?highlight=import_bulk#arango.collection.StandardCollection.import_bulk
    """

    batch_size = 500

    counter = 0
    collections = {}
    docs = {}

    if on_duplicate not in ["error", "update", "replace", "ignore"]:
        logger.error(f"Bad parameter for on_duplicate: {on_duplicate}")
        return

    for (collection_name, doc) in doc_iterator:
        if collection_name not in collections:
            collections[collection_name] = db.collection(collection_name)
            docs[collection_name] = []

        counter += 1

        docs[collection_name].append(doc)

        if counter % batch_size == 0:
            # logger.debug(f"Bulk import arangodb: {counter}")
            for collection_name in docs:
                collections[collection_name].import_bulk(
                    docs[collection_name], on_duplicate=on_duplicate, halt_on_error=False
                )
                docs[collection_name] = []

    # logger.debug(f"Bulk import arangodb: {counter}")
    for collection_name in docs:
        try:
            collections[collection_name].import_bulk(
                docs[collection_name], details=True, on_duplicate=on_duplicate, halt_on_error=False
            )

            docs[collection_name] = []
        except arango.exceptions.DocumentInsertError as e:
            logger.error(f"Problem with arango bulk import: {str(e)}")


def arango_id_to_key(_id):
    """Remove illegal chars from potential arangodb _key (id) or return hashed key if > 60 chars

    Arango _key cannot be longer than 254 chars but we convert to hash if over 60 chars

    Args:
        _id (str): id to be used as arangodb _key

    Returns:
        (str): _key value with illegal chars removed
    """

    if len(_id) > 60:
        key = _create_hash(_id)
    elif len(_id) < 1:
        logger.error(f"Arango _key cannot be an empty string: Len={len(_id)}  Key: {_id}")
    else:
        key = re.sub(r"[^a-zA-Z0-9\_\-\:\.\@\(\)\+\,\=\;\$\!\*\%]+", r"_", _id)

    return key


def aql_query(db, query, batch_size=20, ttl=300):
    """Run AQL query
    
    Default batch_size = 20
    Default time to live for the query is 300

    Returns:
        result_cursor
    """

    result = db.aql.execute(query, batch_size=batch_size, ttl=ttl)

    return result
