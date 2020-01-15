#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:  program.py <customer>

"""

import copy
import json
import os
import sys
from typing import Any, List, Mapping, MutableSequence

import bel.db.arangodb as arangodb
import bel.lang.bel_specification
import bel.lang.belobj
import bel.utils as utils
import structlog
from bel.Config import config

log = structlog.getLogger(__name__)

Edges = MutableSequence[Mapping[str, Any]]


def nanopub_to_edges(nanopub: dict = {}, rules: List[str] = [], orthologize_targets: list = []):
    """Process nanopub into edges and load into EdgeStore

    Args:
        nanopub: BEL Nanopub
        rules: list of compute rules to process
        orthologize_targets: list of species in TAX:<int> format

    Returns:
        list: of edges

    Edge object:
        {
            "edge": {
                "subject": {
                    "name": subj_canon,
                    "name_lc": subj_canon.lower(),
                    "label": subj_lbl,
                    "label_lc": subj_lbl.lower(),
                    "components": subj_components,
                },
                "relation": {  # relation _key is based on a hash
                    "relation": edge_ast.bel_relation,
                    "edge_hash": edge_hash,
                    "edge_dt": edge_dt,
                    "nanopub_url": nanopub_url,
                    "nanopub_id": nanopub_id,
                    "nanopub_status": nanopub_status,
                    "citation": citation,
                    "subject_canon": subj_canon,
                    "subject": subj_lbl,
                    "object_canon": obj_canon,
                    "object": obj_lbl,
                    "annotations": nanopub['annotations'],
                    "metadata": nanopub['metadata'],
                    "public_flag": True,  # will be added when groups/permissions feature is finished,
                    "edge_types": edge_types,
                },
                'object': {
                    "name": obj_canon,
                    "name_lc": obj_canon.lower(),
                    "label": obj_lbl,
                    "label_lc": obj_lbl.lower(),
                    "components": obj_components,
                }
            }
        }
    """

    # Collect input values ####################################################
    nanopub_url = nanopub.get("source_url", "")

    edge_dt = utils.dt_utc_formatted()  # don't want this in relation_id

    # Extract BEL Version and make sure we can process this
    if nanopub["nanopub"]["type"]["name"].upper() == "BEL":
        bel_version = nanopub["nanopub"]["type"]["version"]
        versions = bel.lang.bel_specification.get_bel_versions()
        if bel_version not in versions:
            log.error(
                f"Do not know this BEL Version: {bel_version}, these are the ones I can process: {versions.keys()}"
            )
            return []
    else:
        log.error(
            f"Not a BEL Nanopub according to nanopub.type.name: {nanopub['nanopub']['type']['name']}"
        )
        return []

    # Required for BEL parsing/canonicalization/orthologization
    api_url = config["bel_api"]["servers"]["api_url"]

    try:
        citation_string = normalize_nanopub_citation(nanopub)
    except Exception as e:
        log.error(f"Could not create citation string for {nanopub_url}")
        citation_string = ""

    if orthologize_targets == []:
        if config["bel_api"].get("edges", None):
            orthologize_targets = config["bel_api"]["edges"].get("orthologize_targets", [])

    # orig_species_id = [anno['id'] for anno in nanopub['nanopub']['annotations'] if anno['type'] == 'Species']
    # if orig_species_id:
    #     orig_species_id = orig_species_id[0]

    master_annotations = copy.deepcopy(nanopub["nanopub"]["annotations"])
    master_metadata = copy.deepcopy(nanopub["nanopub"]["metadata"])
    master_metadata.pop("gd_abstract", None)

    nanopub_type = nanopub["nanopub"]["metadata"].get("nanopub_type")
    nanopub_status = ""
    if nanopub["nanopub"]["metadata"].get("gd_status", False):
        nanopub_status = nanopub["nanopub"]["metadata"]["gd_status"]
    elif nanopub["nanopub"]["metadata"].get("status", False):
        nanopub_status = nanopub["nanopub"]["metadata"]["status"]

    # Create Edge Assertion Info ##############################################
    # r = generate_assertion_edge_info(nanopub['nanopub']['assertions'], orig_species_id, orthologize_targets, bel_version, api_url, nanopub_type)
    r = generate_assertion_edge_info(
        nanopub["nanopub"]["assertions"], orthologize_targets, bel_version, api_url, nanopub_type
    )
    edge_info_list = r["edge_info_list"]

    # Build Edges #############################################################
    edges = []
    errors = []
    for edge_info in edge_info_list:
        annotations = copy.deepcopy(master_annotations)
        metadata = copy.deepcopy(master_metadata)

        errors.extend(edge_info["errors"])

        if not edge_info.get("canonical"):
            continue

        # TODO - remove this
        # if edge_info.get('species_id', False):
        #     annotations = orthologize_context(edge_info['species_id'], annotations)

        edge_hash = utils._create_hash(
            f'{edge_info["canonical"]["subject"]} {edge_info["canonical"]["relation"]} {edge_info["canonical"]["object"]}'
        )

        edge = {
            "edge": {
                "subject": {
                    "name": edge_info["canonical"]["subject"],
                    "name_lc": edge_info["canonical"]["subject"].lower(),
                    "label": edge_info["decanonical"]["subject"],
                    "label_lc": edge_info["decanonical"]["subject"].lower(),
                    "components": edge_info["subject_comp"],
                },
                "relation": {
                    "relation": edge_info["canonical"]["relation"],
                    "edge_hash": edge_hash,
                    "edge_dt": edge_dt,
                    "nanopub_url": nanopub_url,
                    "nanopub_id": nanopub["nanopub"]["id"],
                    "nanopub_status": nanopub_status,
                    "citation": citation_string,
                    "subject_canon": edge_info["canonical"]["subject"],
                    "subject": edge_info["decanonical"]["subject"],
                    "object_canon": edge_info["canonical"]["object"],
                    "object": edge_info["decanonical"]["object"],
                    "annotations": copy.deepcopy(annotations),
                    "metadata": copy.deepcopy(metadata),
                    "public_flag": True,
                    "edge_types": edge_info["edge_types"],
                    "species_id": edge_info["species_id"],
                    "species_label": edge_info["species_label"],
                },
                "object": {
                    "name": edge_info["canonical"]["object"],
                    "name_lc": edge_info["canonical"]["object"].lower(),
                    "label": edge_info["decanonical"]["object"],
                    "label_lc": edge_info["decanonical"]["object"].lower(),
                    "components": edge_info["object_comp"],
                },
            }
        }

        edges.append(copy.deepcopy(edge))

    return {
        "edges": edges,
        "nanopub_id": nanopub["nanopub"]["id"],
        "nanopub_url": nanopub_url,
        "success": True,
        "errors": errors,
    }


def extract_ast_species(ast):
    """Extract species from ast.species set of tuples (id, label)"""

    species_id = "None"
    species_label = "None"
    species = [
        (species_id, species_label) for (species_id, species_label) in ast.species if species_id
    ]

    if len(species) == 1:
        (species_id, species_label) = species[0]

    if not species_id:
        species_id = "None"
        species_label = "None"

    log.debug(f"AST Species: {ast.species}  Species: {species}  SpeciesID: {species_id}")

    return (species_id, species_label)


# def generate_assertion_edge_info(assertions: List[dict], orig_species_id: str, orthologize_targets: List[str], bel_version: str, api_url: str, nanopub_type: str) -> dict:
def generate_assertion_edge_info(
    assertions: List[dict],
    orthologize_targets: List[str],
    bel_version: str,
    api_url: str,
    nanopub_type: str = "",
) -> dict:
    """Create edges (SRO) for assertions given orthologization targets

    Args:
        assertions: list of BEL statements (SRO object)
        orthologize_targets: list of species in TAX:<int> format
        bel_version: to be used for processing assertions
        api_url: BEL API url endpoint to use for terminologies and orthologies
    """

    bo = bel.lang.belobj.BEL(bel_version, api_url)
    bo_computed = bel.lang.belobj.BEL(bel_version, api_url)

    edge_info_list = []

    with utils.Timer() as t:
        for assertion in assertions:
            # if not assertion.get('relation', False):
            #     continue  # Skip any subject only statements

            start_time = t.elapsed
            bo.parse(assertion)

            if not bo.ast:
                errors = [
                    f"{error[0]} {error[1]}"
                    for error in bo.validation_messages
                    if error[0] == "ERROR"
                ]
                edge_info = {"errors": copy.deepcopy(errors)}
                edge_info_list.append(copy.deepcopy(edge_info))
                continue

            # populate canonical terms and orthologs for assertion
            bo.collect_nsarg_norms()
            bo.collect_orthologs(orthologize_targets)

            log.debug(
                "Timing - time to collect nsargs and orthologs", delta_ms=(t.elapsed - start_time)
            )

            (edge_species_id, edge_species_label) = extract_ast_species(bo.ast)
            orig_species_id = edge_species_id

            canon = bo.canonicalize().to_triple()

            components = get_node_subcomponents(bo.ast)  # needs to be run after canonicalization
            computed_asts = bo.compute_edges(
                ast_result=True
            )  # needs to be run after canonicalization
            decanon = bo.decanonicalize().to_triple()

            if nanopub_type == "backbone":
                edge_types = ["backbone"]
            else:
                edge_types = ["original", "primary"]

            if assertion.get("relation", False):

                causal_edge_type = []
                if "causal" in bo.spec["relations"]["info"][assertion["relation"]]["categories"]:
                    edge_types.append("causal")

                edge_info = {
                    "edge_types": edge_types,
                    "species_id": edge_species_id,
                    "species_label": edge_species_label,
                    "canonical": canon,
                    "decanonical": decanon,
                    "subject_comp": components["subject_comp"],
                    "object_comp": components["object_comp"],
                    "errors": [],
                }
                edge_info_list.append(copy.deepcopy(edge_info))

            # Loop through primary computed asts
            for computed_ast in computed_asts:
                bo_computed.ast = computed_ast
                bo_computed.collect_nsarg_norms()
                canon = bo_computed.canonicalize().to_triple()
                components = get_node_subcomponents(
                    bo_computed.ast
                )  # needs to be run after canonicalization
                decanon = bo_computed.decanonicalize().to_triple()

                (edge_species_id, edge_species_label) = extract_ast_species(bo_computed.ast)

                edge_info = {
                    "edge_types": ["computed"],
                    "species_id": edge_species_id,
                    "species_label": edge_species_label,
                    "canonical": canon,
                    "decanonical": decanon,
                    "subject_comp": components["subject_comp"],
                    "object_comp": components["object_comp"],
                    "errors": [],
                }
                if [edge for edge in edge_info_list if edge.get("canonical", {}) == canon]:
                    continue  # skip if edge is already included (i.e. the primary is same as computed edge)
                edge_info_list.append(copy.deepcopy(edge_info))

            # Skip orthologs if backbone nanopub
            if nanopub_type == "backbone":
                continue

            # only process orthologs if there are species-specific NSArgs
            if len(bo.ast.species) > 0:
                # Loop through orthologs
                for species_id in orthologize_targets:
                    log.debug(f"Orig species: {orig_species_id}  Target species: {species_id}")
                    if species_id == orig_species_id:
                        continue

                    bo.orthologize(species_id)

                    (edge_species_id, edge_species_label) = extract_ast_species(bo.ast)

                    if edge_species_id == "None" or edge_species_id == orig_species_id:
                        log.debug(
                            f'Skipping orthologization- species == "None" or {orig_species_id}  ASTspecies: {bo.ast.species} for {bo}'
                        )
                        continue

                    ortho_decanon = bo.orthologize(
                        species_id
                    ).to_triple()  # defaults to decanonicalized orthologized form
                    ortho_canon = bo.canonicalize().to_triple()
                    computed_asts = bo.compute_edges(
                        ast_result=True
                    )  # needs to be run after canonicalization
                    components = get_node_subcomponents(
                        bo.ast
                    )  # needs to be run after canonicalization

                    if assertion.get("relation", False):
                        edge_info = {
                            "edge_types": ["orthologized", "primary"] + causal_edge_type,
                            "species_id": edge_species_id,
                            "species_label": edge_species_label,
                            "canonical": ortho_canon,
                            "decanonical": ortho_decanon,
                            "subject_comp": components["subject_comp"],
                            "object_comp": components["object_comp"],
                            "errors": [],
                        }

                        edge_info_list.append(copy.deepcopy(edge_info))

                    # Loop through orthologized computed asts
                    for computed_ast in computed_asts:
                        bo_computed.ast = computed_ast
                        bo_computed.collect_nsarg_norms()
                        canon = bo_computed.canonicalize().to_triple()
                        components = get_node_subcomponents(
                            bo_computed.ast
                        )  # needs to be run after canonicalization
                        decanon = bo_computed.decanonicalize().to_triple()

                        (edge_species_id, edge_species_label) = extract_ast_species(bo_computed.ast)

                        edge_info = {
                            "edge_types": ["computed", "orthologized"],
                            "species_id": edge_species_id,
                            "species_label": edge_species_label,
                            "canonical": canon,
                            "decanonical": decanon,
                            "subject_comp": components["subject_comp"],
                            "object_comp": components["object_comp"],
                            "errors": [],
                        }
                        if [edge for edge in edge_info_list if edge.get("canonical", {}) == canon]:
                            continue  # skip if edge is already included (i.e. the primary is same as computed edge)
                        edge_info_list.append(copy.deepcopy(edge_info))

    log.debug("Timing - Generated all edge info for all nanopub assertions", delta_ms=t.elapsed)

    return {"edge_info_list": edge_info_list}


def get_node_subcomponents(ast):

    sub, obj = [], []

    try:
        sub = ast.bel_subject.subcomponents(subcomponents=[])

        # TODO - update handling nested BEL statement - see Natalie's recommendation on how to handle
        obj_components = []
        if ast.bel_object.__class__.__name__ == "BELAst":  # Nested BEL Assertion
            obj_components = ast.bel_object.bel_subject.subcomponents(subcomponents=[])
            obj_components = ast.bel_object.bel_object.subcomponents(subcomponents=obj_components)
        elif hasattr(ast.bel_object, "subcomponents"):  # Normal BEL Assertion
            obj_components = ast.bel_object.subcomponents(subcomponents=[])

        obj = obj_components

    except Exception as e:
        log.warning(f"Problem getting subcomponents for {ast.to_string()}", error=str(e))

    return {"subject_comp": sub, "object_comp": obj}


def orthologize_context(
    orthologize_target: str, annotations: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Orthologize context

    Replace Species context with new orthologize target and add a annotation type of OrthologizedFrom
    """

    url = f'{config["bel_api"]["servers"]["api_url"]}/terms/{orthologize_target}'
    r = utils.get_url(url)
    species_label = r.json().get("label", "unlabeled")

    orthologized_from = {}
    for idx, annotation in enumerate(annotations):
        if annotation["type"] == "Species":
            orthologized_from = {"id": annotation["id"], "label": annotation["label"]}
            annotations[idx] = {"type": "Species", "id": orthologize_target, "label": species_label}

    if "id" in orthologized_from:
        annotations.append(
            {
                "type": "OrigSpecies",
                "id": f'Orig-{orthologized_from["id"]}',
                "label": f'Orig-{orthologized_from["label"]}',
            }
        )

    return annotations


def normalize_nanopub_citation(nanopub):

    citation_string = ""
    if nanopub["nanopub"]["citation"].get("database", False):
        if nanopub["nanopub"]["citation"]["database"]["name"].lower() == "pubmed":
            citation_string = f"PMID:{nanopub['nanopub']['citation']['database']['id']}"
        else:
            citation_string = f"{nanopub['nanopub']['citation']['database']['name']}:{nanopub['nanopub']['citation']['database']['id']}"
    elif nanopub["nanopub"]["citation"].get("reference", False):
        citation_string = nanopub["nanopub"]["citation"]["reference"]
    elif nanopub["nanopub"]["citation"].get("uri", False):
        citation_string = nanopub["nanopub"]["citation"]["uri"]

    return citation_string


def main():
    pass


if __name__ == "__main__":
    # Setup logging
    import logging.config

    module_fn = os.path.basename(__file__)
    module_fn = module_fn.replace(".py", "")

    if config.get("logging", False):
        logging.config.dictConfig(config.get("logging"))

    log = logging.getLogger(f"{module_fn}")

    main()
