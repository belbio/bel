#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pubmed related utilities

Given PMID - collect Pubmed data and Pubtator Bioconcepts used for the BELMgr
or enhancing BEL Nanopubs
"""

# Standard Library
import copy
import datetime
import re
from typing import Any, Mapping, MutableMapping

# Third Party Imports
from loguru import logger

# Local Imports
import bel.core.settings as settings
from bel.core.utils import http_client, url_path_param_quoting
from lxml import etree
import bel.terms.terms


# Replace PMID
PUBMED_TMPL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id=PMID"
)

PUBTATOR_TMPL = (
    "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/BioConcept/PMID/JSON"
)

pubtator_ns_convert = {
    "CHEBI": "CHEBI",
    "Species": "TAX",
    "Gene": "EG",
    "Chemical": "MESH",
    "Disease": "MESH",
}
pubtator_entity_convert = {
    "Chemical": "Abundance",
    "Gene": "Gene",
    "Disease": "Pathology",
}
pubtator_annotation_convert = {"Disease": "Pathology"}
pubtator_known_types = [key for key in pubtator_ns_convert.keys()]


def node_text(node):
    """Needed for things like abstracts which have internal tags (see PMID:27822475)"""

    if node.text:
        result = node.text
    else:
        result = ""
    for child in node:
        if child.tail is not None:
            result += child.tail
    return result


def get_pubtator(pmid):
    """Get Pubtator Bioconcepts from Pubmed Abstract

    Re-configure the denotations into an annotation dictionary format
    and collapse duplicate terms so that their spans are in a list.
    """
    r = http_client.get(PUBTATOR_TMPL.replace("PMID", pmid), timeout=10)
    if r and r.status_code == 200:
        pubtator = r.json()[0]
    else:
        logger.error(
            f"Cannot access Pubtator, status: {r.status_code} url: {PUBTATOR_TMPL.replace('PMID', pmid)}"
        )
        return None

    known_types = ["CHEBI", "Chemical", "Disease", "Gene", "Species"]

    for idx, anno in enumerate(pubtator["denotations"]):
        s_match = re.match(r"(\w+):(\w+)", anno["obj"])
        c_match = re.match(r"(\w+):(\w+):(\w+)", anno["obj"])
        if c_match:
            (ctype, namespace, cid) = (
                c_match.group(1),
                c_match.group(2),
                c_match.group(3),
            )

            if ctype not in known_types:
                logger.debug(f"{ctype} not in known_types for Pubtator")
            if namespace not in known_types:
                logger.debug(f"{namespace} not in known_types for Pubtator")

            pubtator["denotations"][idx][
                "obj"
            ] = f'{pubtator_ns_convert.get(namespace, "UNKNOWN")}:{cid}'
            pubtator["denotations"][idx]["entity_type"] = pubtator_entity_convert.get(ctype, None)
            pubtator["denotations"][idx]["annotation_type"] = pubtator_annotation_convert.get(
                ctype, None
            )
        elif s_match:
            (ctype, cid) = (s_match.group(1), s_match.group(2))

            if ctype not in known_types:
                logger.debug(f"{ctype} not in known_types for Pubtator")

            pubtator["denotations"][idx][
                "obj"
            ] = f'{pubtator_ns_convert.get(ctype, "UNKNOWN")}:{cid}'
            pubtator["denotations"][idx]["entity_type"] = pubtator_entity_convert.get(ctype, None)
            pubtator["denotations"][idx]["annotation_type"] = pubtator_annotation_convert.get(
                ctype, None
            )

    annotations = {}
    for anno in pubtator["denotations"]:
        logger.debug(anno)
        if anno["obj"] not in annotations:
            annotations[anno["obj"]] = {"spans": [anno["span"]]}
            annotations[anno["obj"]]["entity_types"] = [anno.get("entity_type", [])]
            annotations[anno["obj"]]["annotation_types"] = [anno.get("annotation_type", [])]

        else:
            annotations[anno["obj"]]["spans"].append(anno["span"])

    del pubtator["denotations"]
    pubtator["annotations"] = copy.deepcopy(annotations)

    return pubtator


def process_pub_date(year, mon, day, medline_date):
    """Create pub_date from what Pubmed provides in Journal PubDate entry
    """

    if medline_date:
        year = "0000"
        match = re.search(r"\d{4,4}", medline_date)
        if match:
            year = match.group(0)

        if year and re.match("[a-zA-Z]+", mon):
            pub_date = datetime.datetime.strptime(f"{year}-{mon}-{day}", "%Y-%b-%d").strftime(
                "%Y-%m-%d"
            )
        elif year:
            pub_date = f"{year}-{mon}-{day}"

    else:
        pub_date = None
        if year and re.match("[a-zA-Z]+", mon):
            pub_date = datetime.datetime.strptime(f"{year}-{mon}-{day}", "%Y-%b-%d").strftime(
                "%Y-%m-%d"
            )
        elif year:
            pub_date = f"{year}-{mon}-{day}"

    return pub_date


def parse_book_record(doc: dict, root) -> dict:
    """Parse Pubmed Book entry"""

    doc["title"] = next(iter(root.xpath("//BookTitle/text()")))

    doc["authors"] = []
    for author in root.xpath("//Author"):
        last_name = next(iter(author.xpath("LastName/text()")), "")
        first_name = next(iter(author.xpath("ForeName/text()")), "")
        initials = next(iter(author.xpath("Initials/text()")), "")
        if not first_name and initials:
            first_name = initials
        doc["authors"].append(f"{last_name}, {first_name}")

    pub_year = next(iter(root.xpath("//Book/PubDate/Year/text()")), None)
    pub_mon = next(iter(root.xpath("//Book/PubDate/Month/text()")), "Jan")
    pub_day = next(iter(root.xpath("//Book/PubDate/Day/text()")), "01")
    medline_date = next(iter(root.xpath("//Journal/JournalIssue/PubDate/MedlineDate/text()")), None)

    pub_date = process_pub_date(pub_year, pub_mon, pub_day, medline_date)

    doc["pub_date"] = pub_date

    for abstracttext in root.xpath("//Abstract/AbstractText"):
        abstext = node_text(abstracttext)

        label = abstracttext.get("Label", None)
        if label:
            doc["abstract"] += f"{label}: {abstext}\n"
        else:
            doc["abstract"] += f"{abstext}\n"

    doc["abstract"] = doc["abstract"].rstrip()

    return doc


def parse_journal_article_record(doc: dict, root) -> dict:
    """Parse Pubmed Journal Article record"""

    doc["title"] = next(iter(root.xpath("//ArticleTitle/text()")), "")

    # TODO https://stackoverflow.com/questions/4770191/lxml-etree-element-text-doesnt-return-the-entire-text-from-an-element
    atext = next(iter(root.xpath("//Abstract/AbstractText/text()")), "")

    for abstracttext in root.xpath("//Abstract/AbstractText"):
        abstext = node_text(abstracttext)

        label = abstracttext.get("Label", None)
        if label:
            doc["abstract"] += f"{label}: {abstext}\n"
        else:
            doc["abstract"] += f"{abstext}\n"

    doc["abstract"] = doc["abstract"].rstrip()

    doc["authors"] = []
    for author in root.xpath("//Author"):
        last_name = next(iter(author.xpath("LastName/text()")), "")
        first_name = next(iter(author.xpath("ForeName/text()")), "")
        initials = next(iter(author.xpath("Initials/text()")), "")
        if not first_name and initials:
            first_name = initials
        doc["authors"].append(f"{last_name}, {first_name}")

    pub_year = next(iter(root.xpath("//Journal/JournalIssue/PubDate/Year/text()")), None)
    pub_mon = next(iter(root.xpath("//Journal/JournalIssue/PubDate/Month/text()")), "Jan")
    pub_day = next(iter(root.xpath("//Journal/JournalIssue/PubDate/Day/text()")), "01")
    medline_date = next(iter(root.xpath("//Journal/JournalIssue/PubDate/MedlineDate/text()")), None)

    pub_date = process_pub_date(pub_year, pub_mon, pub_day, medline_date)

    doc["pub_date"] = pub_date
    doc["journal_title"] = next(iter(root.xpath("//Journal/Title/text()")), "")
    doc["joural_iso_title"] = next(iter(root.xpath("//Journal/ISOAbbreviation/text()")), "")
    doc["doi"] = next(iter(root.xpath('//ArticleId[@IdType="doi"]/text()')), None)

    doc["compounds"] = []
    for chem in root.xpath("//ChemicalList/Chemical/NameOfSubstance"):
        chem_id = chem.get("UI")
        doc["compounds"].append({"id": f"MESH:{chem_id}", "name": chem.text})

    compounds = [cmpd["id"] for cmpd in doc["compounds"]]
    doc["mesh"] = []
    for mesh in root.xpath("//MeshHeading/DescriptorName"):
        mesh_id = f"MESH:{mesh.get('UI')}"
        if mesh_id in compounds:
            continue
        doc["mesh"].append({"id": mesh_id, "name": mesh.text})

    return doc


def get_pubmed(pmid: str) -> Mapping[str, Any]:
    """Get pubmed xml for pmid and convert to JSON

    Remove MESH terms if they are duplicated in the compound term set

    ArticleDate vs PubDate gets complicated: https://www.nlm.nih.gov/bsd/licensee/elements_descriptions.html see <ArticleDate> and <PubDate>
    Only getting pub_year at this point from the <PubDate> element.

    Args:
        pmid: pubmed id number as a string

    Returns:
        pubmed json
    """

    doc = {
        "abstract": "",
        "pmid": pmid,
        "title": "",
        "authors": [],
        "pub_date": "",
        "journal_iso_title": "",
        "journal_title": "",
        "doi": "",
        "compounds": [],
        "mesh": [],
    }

    r = None
    try:
        pubmed_url = PUBMED_TMPL.replace("PMID", str(pmid))
        r = http_client.get(pubmed_url)
        content = r.content
        logger.info(f"Getting Pubmed URL {pubmed_url}")
        root = etree.fromstring(content)

    except Exception as e:
        status_code = None
        if r:
            status_code = r.status_code

        logger.exception(
            f"Bad Pubmed request, status: {status_code} error: {str(e)}",
            url=f'{PUBMED_TMPL.replace("PMID", pmid)}',
        )
        return {"doc": {}, "message": f"Cannot get PMID: {pubmed_url}"}

    doc["pmid"] = root.xpath("//PMID/text()")[0]

    if doc["pmid"] != pmid:
        logger.error("Requested PMID doesn't match record PMID", url=pubmed_url)

    if root.find("PubmedArticle") is not None:
        doc = parse_journal_article_record(doc, root)
    elif root.find("PubmedBookArticle") is not None:
        doc = parse_book_record(doc, root)

    return doc


def enhance_pubmed_annotations(pubmed: MutableMapping[str, Any]) -> Mapping[str, Any]:
    """Enhance Pubmed object

    Add additional entity and annotation types to annotations
    Use preferred id for namespaces as needed
    Add strings from Title, Abstract matching Pubtator BioConcept spans

    NOTE - basically duplicated code with bel:bel.nanopub.pubmed - just uses
            internal function calls instead of bel_api calls

    Args:
        pubmed

    Returns:
        pubmed object
    """

    text = pubmed["title"] + pubmed["abstract"]

    annotations = {}

    for nsarg in pubmed["annotations"]:
        terms = bel.terms.terms.get_terms(nsarg)

        if terms:
            term = terms[0]
            new_nsarg = bel.terms.terms.get_normalized_terms(term["id"])["decanonical"]
            pubmed["annotations"][nsarg]["name"] = term["name"]
            pubmed["annotations"][nsarg]["label"] = term["label"]
            pubmed["annotations"][nsarg]["entity_types"] = list(
                set(pubmed["annotations"][nsarg]["entity_types"] + term.get("entity_types", []))
            )
            pubmed["annotations"][nsarg]["annotation_types"] = list(
                set(
                    pubmed["annotations"][nsarg]["annotation_types"]
                    + term.get("annotation_types", [])
                )
            )

            if new_nsarg != nsarg:
                annotations[new_nsarg] = copy.deepcopy(pubmed["annotations"][nsarg])
            else:
                annotations[nsarg] = copy.deepcopy(pubmed["annotations"][nsarg])

    for nsarg in annotations:
        for idx, span in enumerate(annotations[nsarg]["spans"]):
            string = text[span["begin"] - 1 : span["end"] - 1]
            annotations[nsarg]["spans"][idx]["text"] = string

    pubmed["annotations"] = copy.deepcopy(annotations)

    return pubmed


def get_pubmed_for_beleditor(pmid: str, pubmed_only: bool = False) -> Mapping[str, Any]:
    """Get fully annotated pubmed doc with Pubtator and full entity/annotation_types

    Args:
        pmid: Pubmed PMID

    Returns:
        Mapping[str, Any]: pubmed dictionary
    """

    pubmed = get_pubmed(pmid)

    if not pubmed_only:
        pubtator = get_pubtator(pmid)
        pubmed["annotations"] = copy.deepcopy(pubtator["annotations"])

    # Add entity types and annotation types to annotations
    pubmed = enhance_pubmed_annotations(pubmed)

    return pubmed


def main():

    pmid = "19894120"

    pubmed = get_pubmed_for_beleditor(pmid)


if __name__ == "__main__":
    main()
