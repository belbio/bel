# Standard Library
import copy
import gzip
import json
from typing import List

# Third Party
# Third Party Imports
from loguru import logger

# Local
import bel.core.mail

# Local Imports
import bel.core.settings as settings
import bel.core.utils
import bel.db.arangodb as arangodb
import bel.db.elasticsearch as elasticsearch
import bel.resources.namespace
import bel.resources.ortholog


def create_email_body_for_update_resources(results):
    """Create email message body for update_resources"""

    failures = [url for url in results if results[url]["state"] == "Failed"]
    warnings = [url for url in results if results[url]["state"] == "Warning"]
    successes = [url for url in results if results[url]["state"] == "Succeeded"]

    body, html_content = "", ""

    # Failed
    if failures:
        body += f"Failed [{len(failures)}]\n\n"
        html_content += f"<h2>Failed [{len(failures)}]</h2>\n\n"

        for url in failures:
            result = results[url]

            body += f"Resource: {url}\n"
            html_content += f'<h3 style="color: red;">Resource: {url}</h3>\n'

            html_content += "<ul>\n"
            for message in result["messages"]:
                body += f"   {message}\n"
                html_content += f"<li>{message}</li>\n"
            html_content += "</ul>\n"
            body += "\n\n"

    # Warnings
    if warnings:
        body += f"Warnings [{len(warnings)}]\n\n"
        html_content += f"<h2>Failed [{len(warnings)}]</h2>\n\n"

        for url in warnings:
            result = results[url]

            body += f"Resource: {url}\n"
            html_content += f'<h3 style="color: orange;">Resource: {url}</h3>\n'

            html_content += "<ul>\n"
            for message in result["messages"]:
                body += f"   {message}\n"
                html_content += f"<li>{message}</li>\n"
            html_content += "</ul>\n"
            body += "\n\n"

    # Succeeded
    if successes:
        body += f"Succeeded [{len(successes)}]\n\n"
        html_content += f"<h2>Succeeded [{len(successes)}]</h2>\n"

        for url in successes:
            result = results[url]

            body += f"Resource: {url}\n"
            html_content += f'<h3 style="color: green;">Resource: {url}</h3>\n'

            html_content += "<ul>\n"
            for message in result["messages"]:
                body += f"   {message}\n"
                html_content += f"<li>{message}</li>\n"
            html_content += "</ul>\n"
            body += "\n\n"

    body_html = f"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Updated BEL Resources for {settings.HOST_NAME}</title>
  </head>
  <body>
    <div id="content">{html_content}</div>
  </body>
</html>
    """

    return (body, body_html)


def update_resources(urls: List[str] = None, force: bool = False, email: str = None):
    """Update bel resources

    Reads the arangodb resources_metadata objects to figure out what bel resource urls to process
    unless a url is provided to download (at which point it will be added to resources_metadata on
    successful load)

    Args:
        url: url to bel resource file as *.jsonl.gz
    """

    if urls is None:
        urls = []

    results = {}

    # Load provided url if available
    if urls:
        for url in urls:
            try:
                results[url] = load_resource(resource_url=url, force=force)
            except Exception as e:
                results[url]["state"] = "Failed"
                results[url]["messages"].append(f"ERROR: Problem loading resource: {url} {str(e)}")
                logger.exception(f"Problem loading resource: {url} {str(e)}")

    # Load using Resource URLs from bel resource metadata
    else:

        for resource in arangodb.resources_metadata_coll:
            if "resource_download_url" not in resource:
                logger.info("Continuing")
                continue
            logger.info(f"Resource {resource}")
            url = resource["resource_download_url"]
            try:
                results[url] = load_resource(resource_url=url, force=force)
            except Exception as e:
                results[url]["state"] = "Failed"
                results[url]["messages"].append(f"ERROR: Problem loading resource: {url} {str(e)}")
                logger.exception(f"Problem loading resource: {url} {str(e)}")

    if email is not None:
        subject = f"BEL Resources Update for {settings.HOST_NAME}"
        (body, body_html) = create_email_body_for_update_resources(results)
        bel.core.mail.send_simple_email(email, subject, body, body_html=body_html)

    logger.info("Finished updating BEL Resources")

    return results


def load_resource(resource_url: str = None, force: bool = False):
    """Load BEL Resource file

    Forceupdate will create a new index in Elasticsearch regardless of whether
    an index with the resource version already exists.

    Args:
        resource_url: URL from which to download the resource to load into the BEL API
        force: force full update - e.g. don't leave Elasticsearch indexes alone if their version ID matches
    """

    try:
        if resource_url:
            logger.info(f"Loading resource url: {resource_url}")

        # Download resource from url
        if resource_url:
            fp = bel.core.utils.download_file(resource_url)
            fp.seek(0)
            f = gzip.open(fp, "rt")

        if not f:
            return {
                "state": "Failed",
                "messages": [f"Error: Failed to read resource file for {resource_url}"],
            }

        metadata = json.loads(f.__next__())

    except Exception:
        return {
            "state": "Failed",
            "messages": [f"Error: Failed download and parse resource file for {resource_url}"],
        }

    metadata = metadata.get("metadata", None)
    if metadata is None:
        return {
            "state": "Failed",
            "messages": [
                f"Error: Failed to process resource file for {resource_url} - missing metadata"
            ],
            "resource_type": None,
        }

    # Load resource files
    if metadata["resource_type"] == "namespace":
        result = bel.resources.namespace.load_terms(
            f, metadata, force=force, resource_download_url=resource_url
        )

    elif metadata["resource_type"] == "orthologs":
        result = bel.resources.ortholog.load_orthologs(
            f, metadata, force=force, resource_download_url=resource_url
        )

    else:
        logger.info(f"Unrecognized resource type: {metadata['metadata']['type']}")
        result = {
            "state": "Failed",
            "messages": [f"Error: Unrecognized resource type: {metadata['metadata']['type']}"],
        }

    f.close

    result["resource_type"] = metadata["resource_type"]

    return result


def delete_resource(source: str, resource_type: str = "namespace"):

    if resource_type == "namespace":
        bel.resources.namespace.delete_namespace(source)
    elif resource_type == "ortholog":
        bel.resources.ortholog.delete_source(source)
