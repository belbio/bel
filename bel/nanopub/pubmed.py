#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pubmed related utilities

Given PMID - collect Pubmed data and Pubtator Bioconcepts used for the BELMgr
or enhancing BEL Nanopubs
"""

# Standard Library
import asyncio
import copy
import datetime
import re
from typing import Any, Mapping, MutableMapping

# Third Party
import cachetools
import httpx
from loguru import logger
from lxml import etree

# Local
import bel.core.settings as settings
import bel.terms.terms
from bel.core.utils import http_client, url_path_param_quoting

# Replace PMID
PUBMED_TMPL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id="

# https://www.ncbi.nlm.nih.gov/research/pubtator-api/publications/export/biocjson?pmids=28483577,28483578,28483579

PUBTATOR_URL = (
    "https://www.ncbi.nlm.nih.gov/research/pubtator-api/publications/export/biocjson?pmids="
)

pubtator_ns_convert = {
    "CHEBI": "CHEBI",
    "Species": "TAX",
    "Gene": "EG",
    "Chemical": "MESH",
    "Disease": "MESH",
}

pubtator_entity_convert = {"Chemical": "Abundance", "Gene": "Gene", "Disease": "Pathology"}
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


@cachetools.cached(cachetools.TTLCache(maxsize=200, ttl=3600))
def get_pubtator_url(pmid):
    """Get pubtator content from url"""

    pubtator = None

    url = f"{PUBTATOR_URL}{pmid}"

    r = http_client.get(url, timeout=10)

    if r and r.status_code == 200:
        pubtator = r.json()

    else:
        logger.error(f"Cannot access Pubtator, status: {r.status_code} url: {url}")

    return pubtator


def pubtator_convert_to_key(annotation: dict) -> str:
    """Convert pubtator annotation info to key (NS:ID)"""

    ns = pubtator_ns_convert.get(annotation["infons"]["type"], None)
    id_ = annotation["infons"]["identifier"]
    id_ = id_.replace("MESH:", "")

    if ns is None:
        logger.warning("")
    return f"{ns}:{id_}"


def get_pubtator(pmid):
    """Get Pubtator Bioconcepts from Pubmed Abstract

    Re-configure the denotations into an annotation dictionary format
    and collapse duplicate terms so that their spans are in a list.
    """

    annotations = []

    pubtator = get_pubtator_url(pmid)
    if pubtator is None:
        return annotations

    known_types = ["CHEBI", "Chemical", "Disease", "Gene", "Species"]

    for passage in pubtator["passages"]:
        for annotation in passage["annotations"]:
            if annotation["infons"]["type"] not in known_types:
                continue

            key = pubtator_convert_to_key(annotation)

            annotations.append(
                {
                    "key": key,
                    "text": annotation["text"],
                    "locations": copy.copy(annotation["locations"]),
                }
            )

    return annotations


def process_pub_date(year, mon, day, medline_date):
    """Create pub_date from what Pubmed provides in Journal PubDate entry"""

    # TODO - check to see if following would work better
    # import dateparser
    # pub_date = dateparser.parse(medline_date, settings={"PREFER_DAY_OF_MONTH": "first"})
    # pub_date = pub_date.strftime("%Y-%m-%d")

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
        doc["compounds"].append({"key": f"MESH:{chem_id}", "label": chem.text})

    compounds = [cmpd["key"] for cmpd in doc["compounds"]]
    doc["mesh"] = []
    for mesh in root.xpath("//MeshHeading/DescriptorName"):
        mesh_id = f"MESH:{mesh.get('UI')}"
        if mesh_id in compounds:
            continue
        doc["mesh"].append({"key": mesh_id, "label": mesh.text})

    return doc


@cachetools.cached(cachetools.TTLCache(maxsize=200, ttl=3600))
def get_pubmed_url(pmid):
    """Get pubmed url"""

    root = None

    try:
        pubmed_url = f"{PUBMED_TMPL}{str(pmid)}"

        r = http_client.get(pubmed_url)

        logger.info(f"Status {r.status_code}  URL: {pubmed_url}")

        if r.status_code == 200:
            content = r.content
            root = etree.fromstring(content)
        else:
            logger.warning(f"Could not download pubmed url: {pubmed_url}")

    except Exception as e:
        logger.warning(
            f"Bad Pubmed request, error: {str(e)}",
            url=f'{PUBMED_TMPL.replace("PMID", pmid)}',
        )

    return root


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

    root = get_pubmed_url(pmid)

    if root is None:
        return None

    try:
        doc["pmid"] = root.xpath("//PMID/text()")[0]
    except Exception as e:
        return None

    if doc["pmid"] != pmid:
        logger.error(f"Requested PMID {doc['pmid']}doesn't match record PMID {pmid}")

    if root.find("PubmedArticle") is not None:
        doc = parse_journal_article_record(doc, root)
    elif root.find("PubmedBookArticle") is not None:
        doc = parse_book_record(doc, root)

    return doc


async def async_get_normalized_terms_for_annotations(term_keys):
    """Async collection of normalized terms for annotations"""

    normalized = asyncio.gather(
        *[bel.terms.terms.async_get_normalized_terms(term_key) for term_key in term_keys]
    )

    return normalized


def get_normalized_terms_for_annotations(term_keys):

    return [bel.terms.terms.get_normalized_terms(term_key) for term_key in term_keys]


def add_annotations(pubmed):
    """Add nanopub annotations to pubmed doc

    Enhance MESH terms etc as full-fledged nanopub annotations for use by the BEL Nanopub editor
    """

    term_keys = (
        [entry["key"] for entry in pubmed.get("compounds", [])]
        + [entry["key"] for entry in pubmed.get("mesh", [])]
        + [entry["key"] for entry in pubmed.get("pubtator", [])]
    )
    term_keys = list(set(term_keys))

    terms = {}

    for entry in pubmed.get("pubtator", []):
        terms[entry["key"]] = {"key": entry["key"], "label": entry["text"]}

    for entry in pubmed.get("compounds", []):
        terms[entry["key"]] = {"key": entry["key"], "label": entry["label"]}

    for entry in pubmed.get("mesh", []):
        terms[entry["key"]] = {"key": entry["key"], "label": entry["label"]}

    # loop = asyncio.get_event_loop()
    # normalized = loop.run_until_complete(async_get_normalized_terms_for_annotations(term_keys))

    normalized = get_normalized_terms_for_annotations(terms.keys())

    normalized = sorted(normalized, key=lambda x: x["annotation_types"], reverse=True)

    pubmed["annotations"] = []

    for annotation in normalized:

        # HACK - only show first annotation type
        if len(annotation["annotation_types"]) > 0:
            annotation_type = annotation["annotation_types"][0]
        else:
            annotation_type = ""

        if annotation.get("label", False):
            terms[annotation["original"]]["key"] = annotation["decanonical"]
            terms[annotation["original"]]["label"] = annotation["label"]
            terms[annotation["original"]]["annotation_types"] = [annotation_type]

    pubmed["annotations"] = copy.deepcopy(
        sorted(terms.values(), key=lambda x: x.get("annotation_types", []), reverse=True)
    )

    # Add missing
    for idx, annotation in enumerate(pubmed["annotations"]):
        if annotation["label"] == "":
            pubmed["annotations"][idx]["label"] = annotation["key"]

    return pubmed


def get_pubmed_for_beleditor(pmid: str, pubmed_only: bool = False) -> Mapping[str, Any]:
    """Get fully annotated pubmed doc with Pubtator and full entity/annotation_types

    Args:
        pmid: Pubmed PMID

    Returns:
        Mapping[str, Any]: pubmed dictionary
    """

    pubmed = get_pubmed(pmid)

    if pubmed is None:
        return pubmed

    if not pubmed_only:
        pubmed["pubtator"] = get_pubtator(pmid)

    # Add entity types and annotation types to annotations
    pubmed = add_annotations(pubmed)

    return pubmed


def main():

    pmid = "19894120"

    pubmed = get_pubmed_for_beleditor(pmid)


if __name__ == "__main__":
    main()
