from enum import StrEnum

class CitationFormat(StrEnum):
    CochraneRecord = "CochraneRecord"
    CochraneCrdRecord = "CochraneCrdRecord"
    Ris = "Ris"
    Enw = "Enw"
    PubmedNbib = "PubmedNbib"
    PubmedAbstract = "PubmedAbstract"
    Refworks = "Refworks"
    OvidTagged = "OvidTagged"
    OvidReference = "OvidReference"

def parse_ris_file_raw(content: str) -> list[dict[str, list[str]]]:
    """Parse RIS file content and return list of raw records."""
    ...

def parse_enw_file_raw(content: str) -> list[dict[str, list[str]]]:
    """Parse ENW (EndNote) file content and return list of raw records."""
    ...

def parse_pubmed_nbib_file_raw(content: str) -> list[dict[str, list[str]]]:
    """Parse PubMed NBIB file content and return list of raw records."""
    ...

def parse_pubmed_abstract_file_raw(content: str) -> list[dict[str, list[str]]]:
    """Parse PubMed Abstract file content and return list of raw records."""
    ...

def parse_refworks_file_raw(content: str) -> list[dict[str, list[str]]]:
    """Parse RefWorks file content and return list of raw records."""
    ...

def parse_cochrane_record_file_raw(content: str) -> list[dict[str, list[str]]]:
    """Parse Cochrane record export content and return list of raw records."""
    ...

def parse_ovid_tagged_file_raw(content: str) -> list[dict[str, list[str]]]:
    """Parse Ovid tagged file content and return list of raw records."""
    ...

def parse_ovid_reference_file_raw(content: str) -> list[dict[str, list[str]]]:
    """Parse Ovid reference export content and return list of raw records."""
    ...

def parse_citation_file_raw(content: str) -> tuple[CitationFormat, list[dict[str, list[str]]]]:
    """Detect file format and parse raw records, returning the format."""
    ...
