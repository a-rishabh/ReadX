import os
import requests
from lxml import etree
from typing import Optional

GROBID_URL = os.getenv("GROBID_URL", "http://localhost:8070")

def parse_pdf_with_grobid(pdf_path: str, service: str = "processFulltextDocument") -> str:
    """
    Send a PDF to GROBID and get structured TEI XML (as string).
    Services:
      - processHeaderDocument   → title, authors, abstract, affiliations
      - processFulltextDocument → full text, body sections
      - processReferences       → reference list
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


# 🔧 XML namespace for TEI
NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def extract_authors_from_tei(tei_xml: str) -> list[str]:
    """Extract clean list of author names from TEI XML."""
    authors = []
    root = etree.fromstring(tei_xml.encode("utf-8"))
    for author in root.xpath(".//tei:author", namespaces=NS):
        forename = author.find(".//tei:forename", namespaces=NS)
        surname = author.find(".//tei:surname", namespaces=NS)
        if forename is not None and surname is not None:
            authors.append(f"{forename.text.strip()} {surname.text.strip()}")
    return authors


def extract_affiliations_from_tei(tei_xml: str) -> dict:
    """
    Extract author → affiliation(s) mapping from TEI XML.
    Returns dict {author_name: [affiliation1, affiliation2]}.
    """
    root = etree.fromstring(tei_xml.encode("utf-8"))
    author_aff_map = {}

    for author in root.xpath(".//tei:author", namespaces=NS):
        forename = author.find(".//tei:forename", namespaces=NS)
        surname = author.find(".//tei:surname", namespaces=NS)
        if forename is None or surname is None:
            continue
        author_name = f"{forename.text.strip()} {surname.text.strip()}"

        affs = []
        for aff in author.xpath(".//tei:affiliation/tei:orgName", namespaces=NS):
            if aff.text:
                affs.append(aff.text.strip())

        if affs:
            author_aff_map[author_name] = affs

    return author_aff_map


def extract_abstract_from_tei(tei_xml: str) -> Optional[str]:
    """Extract abstract text from TEI XML."""
    root = etree.fromstring(tei_xml.encode("utf-8"))
    abstract_nodes = root.xpath(".//tei:abstract", namespaces=NS)
    if abstract_nodes:
        return " ".join("".join(n.itertext()).strip() for n in abstract_nodes)
    return None


def extract_title_from_tei(tei_xml: str) -> Optional[str]:
    """Extract paper title from TEI XML."""
    root = etree.fromstring(tei_xml.encode("utf-8"))
    title_node = root.find(".//tei:titleStmt/tei:title", namespaces=NS)
    return title_node.text.strip() if title_node is not None else None



def extract_body_sections_from_tei(tei_xml: str) -> dict[str, str]:
    """
    Parse TEI XML body into {section_name: text}.
    GROBID usually returns <div type="section"><head>Title</head><p>...</p></div>
    """
    sections: dict[str, str] = {}
    root = etree.fromstring(tei_xml.encode("utf-8"))

    for div in root.xpath(".//tei:text//tei:body//tei:div", namespaces=NS):
        # Section title
        head_el = div.find("tei:head", namespaces=NS)
        section_name = head_el.text.strip() if head_el is not None else "unnamed"

        # Section text = concat all <p> paragraphs
        paras = [p.text for p in div.findall(".//tei:p", namespaces=NS) if p.text]
        section_text = "\n".join(paras).strip()

        if section_text:
            sections[section_name] = section_text

    return sections


def chunk_sections(sections: dict[str, str], max_tokens: int = 800) -> list[tuple[str, str]]:
    """
    Convert TEI sections into (section_name, chunk) pairs.
    Similar to pdf_parser.chunk_text but for structured TEI.
    """
    chunk_pairs = []
    for sec_name, text in sections.items():
        words = text.split()
        max_words = int(max_tokens * 1.3)
        for i in range(0, len(words), max_words):
            chunk = " ".join(words[i:i+max_words]).strip()
            if chunk:
                chunk_pairs.append((sec_name, chunk))
    return chunk_pairs
