from __future__ import annotations
import json
import os
import re
import requests
from typing import List, Union, IO
from PyPDF2 import PdfReader
from werkzeug.datastructures import FileStorage
from helpers.index import appendMessage, callGPTModel, _extract_json_safe


ZENODO_API_BASE = "https://zenodo.org/api"


def _normalize_article(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (s or "").lower())).strip()

def handle_dataset_list_edit(user_text: str, referenced: list, non_referenced: list, messagesToUser: list):
    """
    Edit operations supported:
      - add referenced: <value>
      - add non-referenced: <value>
      - delete referenced: <value>
      - delete non-referenced: <value>
      - update referenced: <old> -> <new>
      - update non-referenced: <old> -> <new>

    Returns updated (referenced, non_referenced) as string[].
    """

    system_prompt = {
        "role": "system",
        "content": (
            "You extract dataset list edit operations.\n"
            "Operations: add, update, delete.\n"
            "Lists: referenced, non-referenced.\n"
            "Return ONLY JSON with keys: operation, list, old_value, new_value.\n"
            "If something is missing, use empty string.\n"
        )
    }

    user_prompt = {
        "role": "user",
        "content": (
            f"User message:\n{user_text}\n\n"
            "Return ONLY JSON:\n"
            "{\n"
            '  "operation": "add|update|delete|unknown",\n'
            '  "list": "referenced|non-referenced|unknown",\n'
            '  "old_value": "string",\n'
            '  "new_value": "string"\n'
            "}"
        )
    }

    raw = callGPTModel([system_prompt, user_prompt])
    parsed = _extract_json_safe(raw) or {}

    op = str(parsed.get("operation") or "unknown").strip().lower()
    target_list = str(parsed.get("list") or "unknown").strip().lower()
    old_value = str(parsed.get("old_value") or "").strip()
    new_value = str(parsed.get("new_value") or "").strip()

    if op not in ("add", "update", "delete") or target_list not in ("referenced", "non-referenced"):
        appendMessage(
            messagesToUser,
            role="assistant",
            contentShort="I couldn't understand the edit request. Use add/update/delete and referenced/non-referenced.",
            content="I couldn't understand the edit request. Use add/update/delete and referenced/non-referenced.",
            stage="DefineNextStepInteraction",
            jsonObject=False
        )
        return referenced, non_referenced

    lst = referenced if target_list == "referenced" else non_referenced

    if op == "add":
        if not new_value:
            appendMessage(
                messagesToUser,
                role="assistant",
                contentShort="Please provide the dataset text to add.",
                content="Please provide the dataset text to add.",
                stage="DefineNextStepInteraction",
                jsonObject=False
            )
            return referenced, non_referenced
        lst.append(new_value)

    elif op == "delete":
        if not old_value:
            appendMessage(
                messagesToUser,
                role="assistant",
                contentShort="Please provide the dataset text to delete.",
                content="Please provide the dataset text to delete.",
                stage="DefineNextStepInteraction",
                jsonObject=False
            )
            return referenced, non_referenced
        target = _normalize_article(old_value)
        lst[:] = [x for x in lst if _normalize_article(str(x)) != target]

    elif op == "update":
        if not old_value or not new_value:
            appendMessage(
                messagesToUser,
                role="assistant",
                contentShort="Please provide both old and new values: update <old> -> <new>.",
                content="Please provide both old and new values: update <old> -> <new>.",
                stage="DefineNextStepInteraction",
                jsonObject=False
            )
            return referenced, non_referenced
        target = _normalize_article(old_value)
        replaced = False
        for i, v in enumerate(lst):
            if _normalize_article(str(v)) == target:
                lst[i] = new_value
                replaced = True
                break
        if not replaced:
            appendMessage(
                messagesToUser,
                role="assistant",
                contentShort=f"I couldn't find '{old_value}' in the {target_list} list to update.",
                content=f"I couldn't find '{old_value}' in the {target_list} list to update.",
                stage="DefineNextStepInteraction",
                jsonObject=False
            )

    return referenced, non_referenced


def _extract_zenodo_identifier(input_str: str):
    import re
    from urllib.parse import urlparse

    input_str = input_str.strip()

    # DOI case
    if input_str.startswith("10."):
        return {"record_id": None, "doi": input_str}

    # URL case
    if input_str.startswith("http://") or input_str.startswith("https://"):
        parsed = urlparse(input_str)
        parts = [p for p in parsed.path.split("/") if p]
        record_id = None
        for i, p in enumerate(parts):
            if p in ("record", "records") and i + 1 < len(parts):
                record_id = parts[i + 1]
                break
        return {"record_id": record_id, "doi": None}

    # Raw record ID (digits)
    if re.fullmatch(r"\d+", input_str):
        return {"record_id": input_str, "doi": None}

    # Fallback: treat as DOI
    return {"record_id": None, "doi": input_str}

def _zenodo_fetch_by_id(record_id: str, token: str | None = None):
    url = f"{ZENODO_API_BASE}/records/{record_id}"
    params = {}
    if token:
        params["access_token"] = token
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def _zenodo_fetch_by_doi(doi: str, token: str | None = None):
    url = f"{ZENODO_API_BASE}/records"
    params = {"q": f'doi:"{doi}"'}
    if token:
        params["access_token"] = token
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    hits = r.json().get("hits", {}).get("hits", [])
    if not hits:
        raise ValueError(f"No Zenodo record found for DOI {doi}")
    return hits[0]

def check_zenodo_metadata(identifier: str, api_token: str | None = None) -> dict:
    """
    Fetch a Zenodo record by DOI / URL / ID and normalize it into the same
    JSON structure that can be used as a deposition payload, i.e.:

        {
          "metadata": { ... }
        }

    This lets you reuse existing records as templates for new uploads.
    """
    parsed = _extract_zenodo_identifier(identifier)

    # If no token passed, try via ENV (needed only for private/drafts)
    if api_token is None:
        api_token = os.getenv("ZENODO_API_TOKEN")

    if parsed["record_id"]:
        record = _zenodo_fetch_by_id(parsed["record_id"], api_token)
    else:
        record = _zenodo_fetch_by_doi(parsed["doi"], api_token)

    metadata = record.get("metadata", {}) or {}

    return metadata

def create_zenodo_deposition_with_files(llm_data: dict, files: List[FileStorage]) -> dict:
    """
    Create a Zenodo deposition using a metadata dict of the form:
    {
      "metadata": {
        "title": "...",
        "upload_type": "dataset",
        ...
      }
    }
    and upload one or more files to that deposition.

    Returns the full deposition JSON returned by Zenodo.
    """

    token = os.getenv("ZENODO_API_TOKEN")
    token ="1PHuwqoCl5CHLBXYxtT1qWRKK17a3tCdHxnqxp0gD72vLiLbXh7wVkgQCrIE"
    if not token:
        raise RuntimeError("ZENODO_API_TOKEN environment variable is not set")

    # 1) Create the deposition with metadata
    create_url = f"{ZENODO_API_BASE}/deposit/depositions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    resp = requests.post(create_url, data="{}", headers=headers)
    resp.raise_for_status()
    deposition = resp.json()

    url = f"https://zenodo.org/api/deposit/depositions/{deposition.get('id')}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    llm_data = {
        "metadata": {
            "title": "The CT Scan Dataset",
            "upload_type": "dataset",
            "publication_date": "2023",
            "description": "The CT Scan Dataset comprises 500 anonymized CT scans with segmentation masks manually segmented by trained radiologists, compiled from a partner clinic in Lisbon for experimental use to validate multimodal deep learning strategies for chest imaging.",
            "creators": [
                {
                    "name": "Dr. Ana Silva",
                    "affiliation": "Department of Biomedical Engineering, University of Porto, Portugal",
                    "orcid": "0000-0002-8745-1132",
                    "email": "ana.silva@up.pt",
                    "role": ""
                },
                {
                    "name": "Miguel Fernandes, MSc",
                    "affiliation": "Research Center for Medical Imaging, Hospital de Braga, Portugal",
                    "orcid": "0000-0003-5120-8871",
                    "email": "miguel.fernandes@hbraga.pt",
                    "role": ""
                },
                {
                    "name": "Dr. Laura Martins",
                    "affiliation": "Faculty of Engineering, Instituto Superior Técnico, Portugal",
                    "orcid": "",
                    "email": "laura.martins@tecnico.ulisboa.pt",
                    "role": ""
                }
            ],
            "contributors": [],
            "keywords": [
                "CT scans",
                "chest imaging",
                "segmentation",
                "deep learning",
                "radiology",
                "dataset"
            ],
            "language": "eng",
            "notes": "",
            "license": "Apache-2.0",
            "access_right": "open",
            "embargo_date": "2023",
            "grants": [{"id": "10.13039/501100000780::283595"}],
            "subjects": [{"term": "Astronomy", "identifier": "http://id.loc.gov/authorities/subjects/sh85009003",
                          "scheme": "url"}],
            "locations": [
                {
                    "place": "Lisbon, Portugal",
                    "description": "Data compiled from a partner clinic in Lisbon.",
                    "lat": "",
                    "lon": ""
                }
            ],
        }
    }


    resp = requests.put(url, data=json.dumps(llm_data), headers=headers)
    resp.raise_for_status()
    deposition = resp.json()



    # llm_data should already have the top-level "metadata" key
    #resp = requests.post(create_url, params=params, json=llm_data, timeout=30)


    # 2) Upload files into the bucket associated with the deposition
    bucket_url = deposition["links"]["bucket"]

    for f in files:
        if not f or not f.filename:
            continue

        upload_url = f"{bucket_url}/{f.filename}"
        # Zenodo requires a PUT to the bucket URL
        put_resp = requests.put(
            upload_url,
            params={"access_token": token},
            data=f.stream
        )
        put_resp.raise_for_status()

    # If you want to publish automatically, you could POST:
    # publish_url = f"{ZENODO_API_BASE}/deposit/depositions/{deposition['id']}/actions/publish"
    # pub_resp = requests.post(publish_url, params=params, timeout=30)
    # pub_resp.raise_for_status()
    # deposition = pub_resp.json()

    return deposition

def _extract_text_from_pdf(pdf_source: Union[str, os.PathLike, IO[bytes]]) -> str:
    close_file = False
    if isinstance(pdf_source, (str, os.PathLike)):
        f = open(pdf_source, "rb")
        close_file = True
    else:
        f = pdf_source

    try:
        reader = PdfReader(f)
        pages_text = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(pages_text)
    finally:
        if close_file:
            f.close()

def _split_body_and_references(full_text: str):
    lower = full_text.lower()
    markers = ["\nreferences", "\nreference", "\nbibliography", "\nrefs"]

    for m in markers:
        pos = lower.find(m)
        if pos != -1:
            return full_text[:pos], full_text[pos:]

    return full_text, ""


def provideDatasetNameAndAction(messagesToUser):
    appendMessage(
        messagesToUser,
        role="assistant",
        contentShort="Please provide the dataset name and choose infer or improve.",
        content="",
        stage="DefineNextStepInteraction",
        jsonObject=False
    )

def respond_define_next_step(
    messagesToUser,
    referencedDatasets,
    nonReferencedDatasets,
    summary_prefix="I analyzed the article and identified datasets used by the authors."
):
    summary = (
        f"{summary_prefix}\n"
        f"Referenced: {len(referencedDatasets)}\n"
        f"Not referenced: {len(nonReferencedDatasets)}"
    )

    instructions = (
        "How would you like to proceed?\n"
        "1) Infer metadata (no reference)\n"
        "2) Improve metadata (referenced dataset)\n"
        "3) Edit dataset lists (add/update/delete)"
    )

    examples = (
        "1) Infer metadata of Social Network Graph Dataset\n"
        "2) Improve metadata of Climate Observations 1990–2020\n"
        "3) Add to referenced: My Dataset | https://doi.org/10.xxxx/yyy\n"
        "3) Delete from non-referenced: the CT scan dataset\n"
        "3) Update referenced: Old Dataset Name -> New Dataset Name | https://doi.org/10.xxxx/zzz"
    )

    appendMessage(
        messagesToUser,
        role="assistant",
        stage="DefineNextStepInteraction",
        jsonObject=True,
        contentShort={
            "summary": summary,
            "referencedDatasets": referencedDatasets,
            "nonReferencedDatasets": nonReferencedDatasets,
            "instructions": instructions
        },
        content={
            "summary": summary,
            "referencedDatasets": referencedDatasets,
            "nonReferencedDatasets": nonReferencedDatasets,
            "instructions": instructions
        },
        examples=examples
    )


