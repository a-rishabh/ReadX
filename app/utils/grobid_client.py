# app/utils/grobid_client.py
import os
import requests
from lxml import etree

# Base URL for GROBID service
GROBID_URL = os.getenv("GROBID_URL", "http://localhost:8070")

def parse_pdf_with_grobid(pdf_path: str, service: str = "processFulltextDocument") -> str:
    """
    Send a PDF to GROBID and get structured TEI XML.
    Services:
        - processHeaderDocument
        - processFulltextDocument
        - processReferences
    """
    url = f"{GROBID_URL}/api/{service}"
    with open(pdf_path, "rb") as f:
        response = requests.post(
            url,
            files={"input": f},
            data={"consolidateHeader": 1, "consolidateCitations": 1},
            timeout=60,
        )
    response.raise_for_status()
    return response.text  # TEI XML string


# ----------------------------------------------------------------------
# Author extraction
# ----------------------------------------------------------------------

def extract_authors_from_tei(tei_xml: str) -> list[str]:
    """
    Extract author names from TEI XML returned by GROBID.
    Returns a list of strings like "Firstname Lastname".
    """
    authors = []
    root = etree.fromstring(tei_xml.encode("utf-8"))
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}

    for author in root.xpath(".//tei:author", namespaces=ns):
        forename = author.find(".//tei:forename", namespaces=ns)
        surname = author.find(".//tei:surname", namespaces=ns)
        if forename is not None and surname is not None:
            authors.append(f"{forename.text.strip()} {surname.text.strip()}")

    return authors


# ----------------------------------------------------------------------
# Body sections extraction
# ----------------------------------------------------------------------

def extract_body_sections_from_tei(tei_xml: str) -> dict[str, str]:
    """
    Extract structured sections from TEI XML body.
    Returns a dict {section_title: section_text}.
    """
    root = etree.fromstring(tei_xml.encode("utf-8"))
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    sections = {}

    for div in root.xpath(".//tei:div", namespaces=ns):
        # Try to get section title
        head = div.find("tei:head", namespaces=ns)
        sec_title = head.text.strip().lower() if head is not None and head.text else "unnamed_section"

        # Extract paragraphs
        paragraphs = []
        for p in div.findall(".//tei:p", namespaces=ns):
            if p.text:
                paragraphs.append(p.text.strip())
        if paragraphs:
            sections[sec_title] = "\n".join(paragraphs)

    return sections


# ----------------------------------------------------------------------
# Utility wrapper
# ----------------------------------------------------------------------

def parse_with_grobid(pdf_path: str) -> dict:
    """
    Full pipeline:
    - Call GROBID
    - Extract authors
    - Extract sections
    """
    tei_xml = parse_pdf_with_grobid(pdf_path, service="processFulltextDocument")
    authors = extract_authors_from_tei(tei_xml)
    sections = extract_body_sections_from_tei(tei_xml)

    # Optional: get abstract if available
    abstract = sections.get("abstract")

    return {
        "authors": authors,
        "sections": sections,
        "abstract": abstract,
        "tei": tei_xml,  # keep raw for debugging if needed
    }
