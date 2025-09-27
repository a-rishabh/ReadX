import os
import requests

GROBID_URL = os.getenv("GROBID_URL", "http://localhost:8070")

def parse_pdf_with_grobid(pdf_path: str, service: str = "processFulltextDocument") -> dict:
    """
    Send a PDF to GROBID and get structured TEI XML.
    Available services: processHeaderDocument, processFulltextDocument, processReferences
    """
    url = f"{GROBID_URL}/api/{service}"
    with open(pdf_path, "rb") as f:
        response = requests.post(
            url,
            files={"input": f},
            data={"consolidateHeader": 1, "consolidateCitations": 1},
            timeout=60
        )
    response.raise_for_status()
    return response.text  # XML string (TEI format)


from lxml import etree

def extract_authors_from_tei(tei_xml: str) -> list[str]:
    """Extract author names from TEI XML returned by GROBID."""
    authors = []
    root = etree.fromstring(tei_xml.encode("utf-8"))
    for author in root.xpath(".//tei:author", namespaces={"tei": "http://www.tei-c.org/ns/1.0"}):
        forename = author.find(".//tei:forename", namespaces={"tei": "http://www.tei-c.org/ns/1.0"})
        surname = author.find(".//tei:surname", namespaces={"tei": "http://www.tei-c.org/ns/1.0"})
        if forename is not None and surname is not None:
            authors.append(f"{forename.text} {surname.text}")
    return authors
