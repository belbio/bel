#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pubmed related utilities

Given PMID - collect Pubmed data and Pubtator Bioconcepts used for the BELMgr
or enhancing BEL Nanopubs
"""

from typing import Mapping, Any
from lxml import etree
import re
import copy
import datetime

from bel.Config import config
import bel.lang.bel_utils as bel_utils
from bel.utils import get_url, url_path_param_quoting

import structlog
log = structlog.getLogger(__name__)

# Replace PMID
if config['bel_api']['servers'].get('pubmed_api_key', False):
    PUBMED_TMPL = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&api_key={config["bel_api"]["servers"]["pubmed_api_key"]}&id=PMID'
else:
    PUBMED_TMPL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id=PMID'

PUBTATOR_TMPL = 'https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/BioConcept/PMID/JSON'

pubtator_ns_convert = {'CHEBI': 'CHEBI', 'Species': 'TAX', 'Gene': 'EG', 'Chemical': 'MESH', 'Disease': 'MESH'}
pubtator_entity_convert = {'Chemical': 'Abundance', 'Gene': 'Gene', 'Disease': 'Pathology', }
pubtator_annotation_convert = {'Disease': 'Pathology', }
pubtator_known_types = [key for key in pubtator_ns_convert.keys()]


def get_pubtator(pmid):
    """Get Pubtator Bioconcepts from Pubmed Abstract

    Re-configure the denotations into an annotation dictionary format
    and collapse duplicate terms so that their spans are in a list.
    """
    r = get_url(PUBTATOR_TMPL.replace('PMID', pmid), timeout=10)
    if r and r.status_code == 200:
        pubtator = r.json()
    else:
        log.error(f"Cannot access Pubtator, status: {r.status_code} url: {PUBTATOR_TMPL.replace('PMID', pmid)}")
        return None

    known_types = ['CHEBI', 'Chemical', 'Disease', 'Gene', 'Species', ]

    for idx, anno in enumerate(pubtator["denotations"]):
        s_match = re.match(r'(\w+):(\w+)', anno['obj'])
        c_match = re.match(r'(\w+):(\w+):(\w+)', anno['obj'])
        if c_match:
            (ctype, namespace, cid) = (c_match.group(1), c_match.group(2), c_match.group(3), )

            if ctype not in known_types:
                log.info(f'{ctype} not in known_types for Pubtator')
            if namespace not in known_types:
                log.info(f'{namespace} not in known_types for Pubtator')

            pubtator["denotations"][idx]['obj'] = f'{pubtator_ns_convert.get(namespace, "UNKNOWN")}:{cid}'
            pubtator["denotations"][idx]['entity_type'] = pubtator_entity_convert.get(ctype, None)
            pubtator["denotations"][idx]['annotation_type'] = pubtator_annotation_convert.get(ctype, None)
        elif s_match:
            (ctype, cid) = (s_match.group(1), s_match.group(2), )

            if ctype not in known_types:
                log.info(f'{ctype} not in known_types for Pubtator')

            pubtator["denotations"][idx]['obj'] = f'{pubtator_ns_convert.get(ctype, "UNKNOWN")}:{cid}'
            pubtator["denotations"][idx]['entity_type'] = pubtator_entity_convert.get(ctype, None)
            pubtator["denotations"][idx]['annotation_type'] = pubtator_annotation_convert.get(ctype, None)

    annotations = {}
    for anno in pubtator['denotations']:
        log.info(anno)
        if anno['obj'] not in annotations:
            annotations[anno['obj']] = {'spans': [anno['span']]}
            annotations[anno['obj']]['entity_types'] = [anno.get('entity_type', [])]
            annotations[anno['obj']]['annotation_types'] = [anno.get('annotation_type', [])]

        else:
            annotations[anno['obj']]['spans'].append(anno['span'])

    del pubtator['denotations']
    pubtator['annotations'] = copy.deepcopy(annotations)

    return pubtator


def process_pub_date(year, mon, day):
    """Create pub_date from what Pubmed provides in Journal PubDate entry
    """

    pub_date = None
    if year and re.match('[a-zA-Z]+', mon):
        pub_date = datetime.datetime.strptime(f'{year}-{mon}-{day}', '%Y-%b-%d').strftime('%Y-%m-%d')
    elif year:
        pub_date = f'{year}-{mon}-{day}'

    return pub_date


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
    pubmed_url = PUBMED_TMPL.replace('PMID', str(pmid))
    r = get_url(pubmed_url)
    log.info(f'Getting Pubmed URL {pubmed_url}')

    try:
        root = etree.fromstring(r.content)
        doc = {'abstract': ''}
        doc['pmid'] = root.xpath("//PMID/text()")[0]
        doc['title'] = next(iter(root.xpath("//ArticleTitle/text()")), '')

        for abstracttext in root.xpath('//Abstract/AbstractText'):

            abstext = abstracttext.text

            label = abstracttext.get('Label', None)
            if label:
                doc['abstract'] += f'{label}: {abstext}\n'
            else:
                doc['abstract'] += f'{abstext}\n'

        doc['abstract'] = doc['abstract'].rstrip()

        doc['authors'] = []
        for author in root.xpath('//Author'):
            last_name = next(iter(author.xpath('LastName/text()')), '')
            first_name = next(iter(author.xpath('ForeName/text()')), '')
            initials = next(iter(author.xpath('Initials/text()')), '')
            if not first_name and initials:
                first_name = initials
            doc['authors'].append(f'{last_name}, {first_name}')

        pub_year = next(iter(root.xpath("//Journal/JournalIssue/PubDate/Year/text()")), None)
        pub_mon = next(iter(root.xpath("//Journal/JournalIssue/PubDate/Month/text()")), 'Jan')
        pub_day = next(iter(root.xpath("//Journal/JournalIssue/PubDate/Day/text()")), '01')

        pub_date = process_pub_date(pub_year, pub_mon, pub_day)

        doc['pub_date'] = pub_date
        doc['journal_title'] = next(iter(root.xpath('//Journal/Title/text()')), '')
        doc['joural_iso_title'] = next(iter(root.xpath('//Journal/ISOAbbreviation/text()')), '')
        doc['doi'] = next(iter(root.xpath('//ArticleId[@IdType="doi"]/text()')), None)

        doc['compounds'] = []
        for chem in root.xpath("//ChemicalList/Chemical/NameOfSubstance"):
            chem_id = chem.get('UI')
            doc['compounds'].append({'id': f"MESH:{chem_id}", 'name': chem.text})

        compounds = [cmpd['id'] for cmpd in doc['compounds']]
        doc['mesh'] = []
        for mesh in root.xpath("//MeshHeading/DescriptorName"):
            mesh_id = f"MESH:{mesh.get('UI')}"
            if mesh_id in compounds:
                continue
            doc['mesh'].append({'id': mesh_id, 'name': mesh.text})

        return doc
    except Exception as e:
        log.error(f"Bad Pubmed request, status: {r.status_code} error: {e}", url=f'{PUBMED_TMPL.replace("PMID", pmid)}')
        return {'message': f"Cannot get PMID: {pubmed_url}"}


def enhance_pubmed_annotations(pubmed: Mapping[str, Any]) -> Mapping[str, Any]:
    """Enhance pubmed namespace IDs

    Add additional entity and annotation types to annotations
    Use preferred id for namespaces as needed
    Add strings from Title, Abstract matching Pubtator BioConcept spans

    NOTE - basically duplicated code with bel_api:api.services.pubmed

    Args:
        pubmed

    Returns:
        pubmed object
    """

    text = pubmed['title'] + pubmed['abstract']

    annotations = {}

    for nsarg in pubmed['annotations']:
        url = f'{config["bel_api"]["servers"]["api_url"]}/terms/{url_path_param_quoting(nsarg)}'
        log.info(f'URL: {url}')
        r = get_url(url)
        log.info(f'Result: {r}')
        new_nsarg = ''
        if r and r.status_code == 200:
            term = r.json()
            new_nsarg = bel_utils.convert_nsarg(term['id'], decanonicalize=True)

            pubmed['annotations'][nsarg]['name'] = term['name']
            pubmed['annotations'][nsarg]['label'] = term['label']
            pubmed['annotations'][nsarg]['entity_types'] = list(set(pubmed['annotations'][nsarg]['entity_types'] + term.get('entity_types', [])))
            pubmed['annotations'][nsarg]['annotation_types'] = list(set(pubmed['annotations'][nsarg]['annotation_types'] + term.get('annotation_types', [])))

        if new_nsarg != nsarg:
            annotations[new_nsarg] = copy.deepcopy(pubmed['annotations'][nsarg])
        else:
            annotations[nsarg] = copy.deepcopy(pubmed['annotations'][nsarg])

    for nsarg in annotations:
        for idx, span in enumerate(annotations[nsarg]['spans']):
            string = text[span['begin'] - 1:span['end'] - 1]
            annotations[nsarg]['spans'][idx]['text'] = string

    pubmed['annotations'] = copy.deepcopy(annotations)

    return pubmed


def get_pubmed_for_beleditor(pmid: str) -> Mapping[str, Any]:
    """Get fully annotated pubmed doc with Pubtator and full entity/annotation_types

    Args:
        pmid: Pubmed PMID

    Returns:
        Mapping[str, Any]: pubmed dictionary
    """

    pubmed = get_pubmed(pmid)
    pubtator = get_pubtator(pmid)
    pubmed['annotations'] = copy.deepcopy(pubtator['annotations'])

    # Add entity types and annotation types to annotations
    pubmed = enhance_pubmed_annotations(pubmed)

    return pubmed


def main():

    pmid = '19894120'

    pubmed = get_pubmed_for_beleditor(pmid)

    import json
    print('DumpVar:\n', json.dumps(pubmed, indent=4))


if __name__ == '__main__':
    main()

