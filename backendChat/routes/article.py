# routes/article.py
from __future__ import annotations

import os
import re
import json
from flask import Blueprint
from flasgger import swag_from
from flask_cors import cross_origin
from auth import require_auth
from helpers.article.articleHelper import check_zenodo_metadata, create_zenodo_deposition_with_files, \
    _extract_text_from_pdf, _split_body_and_references, _normalize_article, \
    handle_dataset_list_edit, respond_define_next_step, _parse_referenced_entry_with_gpt_fallback, \
    run_fuji_fair_assessment
from flask import request
from helpers.index import makeResponse, appendMessage, callGPTModel, _extract_json_safe

ZENODO_API_BASE = "https://zenodo.org/api"

# ----------------------------
# NEW FLASK ROUTE (the one you requested)
# ----------------------------

article_bp = Blueprint("article", __name__)


@article_bp.route("/article/upload-file", methods=['POST'])
@cross_origin()
@require_auth
@swag_from("../swagger/article/upload-article.yml")
def analyze_author_datasets_citation_status_using_gpt():
    messagesToUser = []
    messagesToChat = []

    # ---- CHECK FILE ----
    if 'file' not in request.files:
        appendMessage(messagesToUser, contentShort="I can’t find your file", stage="Start")
        return makeResponse(messagesToUser, 400, True)

    file = request.files["file"]

    if file.filename == '':
        appendMessage(messagesToUser, contentShort="I can’t select your file", stage="Start")
        return makeResponse(messagesToUser, 400, True)

    # ------ FIXED: EXTRACT TEXT FROM THE UPLOADED FILE ------
    full_text = _extract_text_from_pdf(file)
    body_text, refs_text = _split_body_and_references(full_text)

    max_chars = 20000
    body_snippet = body_text[:max_chars]
    refs_snippet = refs_text[:max_chars]

    system_prompt = {
        "role": "system",
        "content": (
            "You are an academic integrity assistant. "
            "Your task is to analyze research papers and identify datasets. "
            "For this task, a dataset is ANY author-created artifact that contains data, "
            "including raw data, processed data, experimental results, logs, tables, "
            "spreadsheets, metrics, reproducibility packages, and experiment bundles."
        )
    }

    user_prompt = {
        "role": "user",
        "content": f"""
    Identify datasets created, collected, curated, released, or newly proposed by the authors.

    IMPORTANT DEFINITION:
    In this task, a "dataset" means ANY author-created artifact that CONTAINS DATA, including:
    - Raw, processed, or derived data
    - Experimental results, outputs, metrics, logs
    - Tables or spreadsheets of results
    - Reproducibility packages, experiment bundles, replication archives
    - Containers, scripts, workflows, or configuration files ONLY IF they include data files or recorded results

    IGNORE well-known public datasets (e.g., MNIST, CIFAR-10, COCO, UCI, ImageNet), unless the authors created a NEW dataset, subset, or derived data.

    --------------------------------
    STRICT CLASSIFICATION RULES
    --------------------------------

    You MUST classify datasets into EXACTLY ONE of the following categories.

    1) author_datasets_with_references

    Include a dataset here ONLY IF at least ONE of the following is TRUE:
    - The dataset has an EXPLICIT and RESOLVABLE URL, DOI, or repository link written in the paper body
    - The dataset is clearly linked to a SPECIFIC bibliographic entry in the REFERENCES section
    - The reference is NOT a placeholder, NOT an example, and NOT a template

    IMPORTANT:
    - If you CANNOT point to a real URL, DOI, repository link, or a concrete REFERENCES entry,
      the dataset MUST NOT be classified as referenced.

    For each referenced dataset, you MUST return:
    - dataset_name
    - reference_or_link (URL, DOI, or full reference entry)

    2) author_datasets_without_references

    Include a dataset here if:
    - The dataset is described or named by the authors
    - BUT there is NO explicit URL, DOI, or repository link
    - AND there is NO concrete matching entry in the REFERENCES section

    --------------------------------
    CRITICAL VALIDATION RULES (DO NOT VIOLATE)
    --------------------------------

    - A dataset name alone does NOT count as a reference
    - Titles that *sound like datasets* (e.g., "X: A Dataset for Y") are NOT references by themselves
    - Phrases like "we introduce a dataset called X" WITHOUT a link or citation are NOT references
    - If you are UNSURE whether a reference is valid, classify the dataset as WITHOUT reference
    - DO NOT infer, assume, or invent references

    --------------------------------
    OUTPUT RULES
    --------------------------------

    - Use the dataset’s explicit name if available; otherwise use the most specific descriptive name
    - Only include datasets attributable to the authors of THIS paper
    - If no valid author-created datasets exist, return empty arrays
    - Return ONLY valid JSON
    - DO NOT add explanations, comments, or extra text

    --------------------------------
    RETURN FORMAT (STRICT)
    --------------------------------

    {{
      "author_datasets_with_references": [
        {{
          "dataset_name": "",
          "reference_or_link": ""
        }}
      ],
      "author_datasets_without_references": [
        {{
          "dataset_name": ""
        }}
      ]
    }}

    --------------------------------
    BODY TEXT:
    {body_snippet}

    --------------------------------
    REFERENCES:
    {refs_snippet}
    """
    }

    # # ---- CALL GPT ----
    # raw_response = callGPTModel([system_prompt, user_prompt])
    #
    # # ---- JSON EXTRACTION ----
    # data = _extract_json_safe(raw_response)
    #
    # # Normalize to always produce arrays
    # raw_with_refs = (data or {}).get("author_datasets_with_references", []) or []
    # raw_without_refs = (data or {}).get("author_datasets_without_references", []) or []
    #
    # referenced = []
    # for item in raw_with_refs:
    #     if isinstance(item, dict):
    #         name = str(item.get("dataset_name", "")).strip()
    #         ref = str(item.get("reference_or_link", "")).strip()
    #         referenced.append(f"{name} | {ref}".strip(" |"))
    #
    # non_referenced = []
    # for item in raw_without_refs:
    #     if isinstance(item, dict):
    #         non_referenced.append(str(item.get("dataset_name", "")).strip())
    #     else:
    #         non_referenced.append(str(item).strip())
    #
    # # If extraction failed, keep empty lists and show an error summary
    # if data is None:
    #     summary_short = "I couldn't extract dataset information from the article. Please try another PDF."
    #     summary_full = summary_short
    # else:
    #     summary_short = (
    #         "I found datasets in the article.\n"
    #         f"Referenced: {len(referenced)}\n"
    #         f"Not referenced: {len(non_referenced)}"
    #     )
    #     summary_full = (
    #         "I found datasets in the article.\n\n"
    #         f"Referenced datasets: {len(referenced)}\n"
    #         f"Datasets without references: {len(non_referenced)}"
    #     )

    # TODO delete
    summary_full= "I found datasets in the article.\nReferenced: 2\nNot referenced: 0"
    summary_short = summary_full
    referenced =  [
                     "Curated dataset of 18 computational experiments (E1-E18) | https://doi.org/10.5281/zenodo.15492423",
                     "Reproducibility package of a curated dataset of 18 computational experiments | https://doi.org/10.5281/zenodo.15166258"
                 ]
    non_referenced= []

    # ---- BUILD CLIENT-COMPATIBLE CHAT RESPONSE (SINGLE MESSAGE) ----
    respond_define_next_step(
        messagesToUser,
        referenced,
        non_referenced,
        summary_prefix="I found datasets in the article."
    )

    return makeResponse(messagesToUser, 200, True)


# result = analyze_author_datasets_citation_status_using_gpt("example1.pdf")

# print("WITH REFERENCES:", result["author_datasets_with_references"])
# print("WITHOUT REFERENCES:", result["author_datasets_without_references"])

# {
#   "author_datasets_with_references": [
#     {
#       "dataset_name": "HospitalX-CXR Collection",
#       "reference_or_link": "Silva et al. Protocols for Chest X-ray Acquisition in Regional Hospitals. 2021."
#     }
#   ],
#   "author_datasets_without_references": [
#     {
#       "dataset_name": "the CT scan dataset"
#     }
#   ]
# }

# artigo rep sem referencia dos 2 zenodos
# {
#     "role": "assistant",
#     "jsonObject": true,
#     "contentShort": {
#         "summary": "I found datasets in the article.\nReferenced: 0\nNot referenced: 1",
#         "referencedDatasets": [],
#         "nonReferencedDatasets": [
#             "CompRep: A Dataset For Computational Reproducibility"
#         ]
#     },
#     "content": {
#         "summary": "I found datasets in the article.\n\nReferenced datasets: 0\nDatasets without references: 1",
#         "referencedDatasets": [],
#         "nonReferencedDatasets": [
#             "CompRep: A Dataset For Computational Reproducibility"
#         ]
#     },
#     "stage": "DefineNextStepInteraction"
# }


# artigo rep com as 2 referencias
# [
#     {
#         "role": "assistant",
#         "jsonObject": true,
#         "contentShort": {
#             "summary": "I found datasets in the article.\nReferenced: 2\nNot referenced: 0",
#             "referencedDatasets": [
#                 "Curated dataset of 18 computational experiments (E1-E18) | https://doi.org/10.5281/zenodo.15492423",
#                 "Reproducibility package of a curated dataset of 18 computational experiments | https://doi.org/10.5281/zenodo.15166258"
#             ],
#             "nonReferencedDatasets": []
#         },
#         "content": {
#             "summary": "I found datasets in the article.\n\nReferenced datasets: 2\nDatasets without references: 0",
#             "referencedDatasets": [
#                 "Curated dataset of 18 computational experiments (E1-E18) | https://doi.org/10.5281/zenodo.15492423",
#                 "Reproducibility package of a curated dataset of 18 computational experiments | https://doi.org/10.5281/zenodo.15166258"
#             ],
#             "nonReferencedDatasets": []
#         },
#         "stage": "DefineNextStepInteraction"
#     }
# ]


@article_bp.route("/article/check-metadata", methods=["POST"])
@cross_origin()
@require_auth
@swag_from("../swagger/article/zenodo-check.yml")
def zenodo_check_metadata_route():
    messagesToUser = []

    data = request.get_json(silent=True) or {}
    identifier = data.get("identifier")

    if not identifier:
        appendMessage(messagesToUser, "Missing 'identifier' field", "Error")
        return makeResponse(messagesToUser, 400, True)

    try:
        summary = check_zenodo_metadata(identifier)
        return makeResponse(summary, 200, True)

    except Exception as e:
        appendMessage(messagesToUser, f"Error: {str(e)}", "Error")
        return makeResponse(messagesToUser, 500, True)


@article_bp.route("/article/choose-next-step", methods=["POST"])
@cross_origin()
@require_auth
def choose_next_step():
    request_data = request.get_json(silent=True) or {}
    messages = request_data.get("messages", [])
    messagesToUser = []

    article_uuid = (request_data.get("article_uuid") or "").strip()
    #TODO

    article_uuid="12345678"

    if not messages:
        respond_define_next_step(
            messagesToUser,
            referencedDatasets=[],
            nonReferencedDatasets=[],
            summary_prefix="No previous conversation found. Please choose a next step."
        )
        return makeResponse(messagesToUser, 200, True)

    # -------- 1) Get dataset lists from previous assistant jsonObject message --------
    referencedDatasets = []     # Option A: list[str] like "name | reference"
    nonReferencedDatasets = []  # list[str]

    for m in reversed(messages):
        c = m.get("content")
        if isinstance(c, dict) and ("referencedDatasets" in c or "nonReferencedDatasets" in c):
            referencedDatasets = c.get("referencedDatasets", []) or []
            nonReferencedDatasets = c.get("nonReferencedDatasets", []) or []
            break

    # -------- 2) Get last user text (fallback if roles are missing) --------
    last_user_msg = next((m for m in reversed(messages) if m.get("role") == "user"), None)
    if last_user_msg is None:
        last_user_msg = messages[-1]

    user_text = (last_user_msg.get("content") or "") if isinstance(last_user_msg, dict) else ""
    if isinstance(user_text, dict):
        user_text = json.dumps(user_text)

    user_text = str(user_text).strip()

    if not user_text:
        respond_define_next_step(
            messagesToUser,
            referencedDatasets=referencedDatasets,
            nonReferencedDatasets=nonReferencedDatasets,
            summary_prefix="I didn't receive a command. Please choose one of the options below."
        )
        return makeResponse(messagesToUser, 200, True)

    # -------- 3) If user wants to edit the lists (add/update/delete), handle it here --------
    EDIT_PATTERN = re.compile(
        r"\b("
        r"add(?:s|ed|ing)?|"
        r"update(?:s|d|ing)?|"
        r"delete(?:s|d|ing)?|"
        r"remove(?:s|d|ing)?|"
        r"edit(?:s|ed|ing)?"
        r")\b",
        re.IGNORECASE
    )

    if EDIT_PATTERN.search(user_text):
        referencedDatasets, nonReferencedDatasets = handle_dataset_list_edit(
            user_text,
            referencedDatasets,
            nonReferencedDatasets,
            messagesToUser
        )

        respond_define_next_step(
            messagesToUser,
            referencedDatasets,
            nonReferencedDatasets,
            summary_prefix="Updated dataset lists."
        )
        return makeResponse(messagesToUser, 200, True)


    # -------- 4) Use GPT ONLY to extract action + dataset_name (infer/improve) --------
    system_prompt = {
        "role": "system",
        "content": (
            "Extract the user's intended action and dataset name.\n"
            "Accepted actions: infer, improve.\n"
            "User may write infer%, improve%, infer metadata, improve metadata.\n"
            "Return ONLY JSON with keys: action, dataset_name.\n"
            'Example: {"action":"improve","dataset_name":"HospitalX-CXR Collection"}'
        )
    }

    user_prompt = {
        "role": "user",
        "content": f'User message:\n{user_text}\n\nReturn ONLY JSON.'
    }

    raw='{"action":"improve","dataset_name":"Reproducibility package of a curated dataset of 18 computational experiments"}'
    #TODO TO BE deleted
    #raw = callGPTModel([system_prompt, user_prompt])

    parsed = _extract_json_safe(raw) or {}

    action = str(parsed.get("action") or "unknown").strip().lower().replace("%", "")
    dataset_name = str(parsed.get("dataset_name") or "").strip()

    if action not in ("infer", "improve") or not dataset_name:
        appendMessage(
            messagesToUser,
            role="assistant",
            contentShort="Please write: infer <dataset name> OR improve <dataset name>.",
            content="Please write: infer <dataset name> OR improve <dataset name>.",
            stage="DefineNextStepInteraction",
            jsonObject=False
        )
        return makeResponse(messagesToUser, 200, True)

    # -------- 5) If improve: fetch reference_or_link + Zenodo metadata + F-UJI --------
    reference_or_link = ""
    zenodo_metadata = None
    fuji_error = ""
    fuji_result = ""

    if action == "improve":
        target = _normalize_article(dataset_name)

        # Find ref
        for s in referencedDatasets:
            if not isinstance(s, str):
                continue
            name, ref = _parse_referenced_entry_with_gpt_fallback(s)
            if _normalize_article(name) == target:
                reference_or_link = ref
                break

        if not reference_or_link:
            appendMessage(
                messagesToUser,
                role="assistant",
                contentShort=f"I couldn't find the reference for '{dataset_name}'. Please select a dataset from the referenced list.",
                content=f"I couldn't find the reference for '{dataset_name}'. Please select a dataset from the referenced list.",
                stage="DefineNextStepInteraction",
                jsonObject=False
            )
            return makeResponse(messagesToUser, 200, True)

        # Fetch Zenodo metadata
        try:
            zenodo_metadata = check_zenodo_metadata(reference_or_link)
        except Exception as e:
            appendMessage(
                messagesToUser,
                role="assistant",
                contentShort=f"I found the reference but couldn't fetch Zenodo metadata: {str(e)}",
                content=f"I found the reference but couldn't fetch Zenodo metadata: {str(e)}",
                stage="DefineNextStepInteraction",
                jsonObject=False
            )
            return makeResponse(messagesToUser, 200, True)


        # We do NOT hard-fail if article_uuid is missing or F-UJI fails.
        if article_uuid:
            try:
                fuji_result = run_fuji_fair_assessment(article_uuid=article_uuid, doi=reference_or_link)
                fuji_path = os.path.join("articles", article_uuid, "fuji_result.json")
            except Exception as e:
                fuji_error = str(e)
                fuji_path = os.path.join("articles", article_uuid, "fuji_result.json")
        else:
            fuji_error = "Missing article_uuid in request body (required to save F-UJI result under articles/<uuid>/)."

    # -------- 6) Return payload --------
    #TODO alterar
    #next_stage = "InferDatasetMetadata" if action == "infer" else "ImproveDatasetMetadata"
    next_stage = "DefineNextStepInteraction"


    payload = {
        "action": action,
        "fuji_result": fuji_result
    }

    if action == "improve":
        payload["reference_or_link"] = reference_or_link
        payload["zenodo_metadata"] = zenodo_metadata

        if fuji_error:
            payload["fuji_error"] = fuji_error

    appendMessage(
        messagesToUser,
        role="assistant",
        stage=next_stage,
        jsonObject=True,
        contentShort=payload,
        content=payload
    )

    return makeResponse(messagesToUser, 200, True)


@article_bp.route("/article/infer-dataset-metadata", methods=['POST'])
@cross_origin()
@require_auth
@swag_from("../swagger/article/infer-dataset-metadata.yml")
def infer_dataset_metadata_from_article():
    messagesToUser = []
    messagesToChat = []

    dataset_name = request.form.get("dataset_name")
    if not dataset_name:
        appendMessage(messagesToUser, contentShort="Missing 'dataset_name' in form data", stage="Start")
        return makeResponse(messagesToUser, 400, True)

    # ---- CHECK FILE ----
    if 'file' not in request.files:
        appendMessage(messagesToUser, contentShort="I can’t find your file", stage="Start")
        return makeResponse(messagesToUser, 400, True)

    file = request.files["file"]

    if file.filename == '':
        appendMessage(messagesToUser, contentShort="I can’t select your file", stage="Start")
        return makeResponse(messagesToUser, 400, True)

    """
    Given an article (PDF path or file-like object) and the name of a dataset
    created/used by the authors, use an LLM to infer Zenodo-style metadata
    for that dataset.

    Returns a JSON object similar in structure to `check_zenodo_metadata`,
    but without record_id/links (because this is not yet a Zenodo record).
    """

    # 1) Extrair texto do PDF
    full_text = _extract_text_from_pdf(file)
    body_text, refs_text = _split_body_and_references(full_text)

    max_chars = 20000
    body_snippet = body_text[:max_chars]
    refs_snippet = refs_text[:max_chars]

    # 2) Prompt para o LLM – focado NO DATASET ESPECÍFICO
    system_prompt = {
        "role": "user",
        "content": f"""
    We are interested in a dataset called:

        "{dataset_name}"

    The dataset is created/collected/curated by the AUTHORS of this article.  
    Therefore, extract ALL possible information about each author and use it to populate the
    "creators" section of the Zenodo metadata structure.

    You MUST do the following:

    1. Extract ALL AUTHOR INFORMATION present in the article, including:
       - Full name
       - Email address
       - Organization / affiliation
       - Department / research group
       - Country (if inferable from affiliation)
       - ORCID (if present)
       - Any explicit tagging such as "corresponding author"
       - Any role labels (e.g., "lead researcher", "principal investigator")

    2. Use ONLY author information explicitly present in the article; if something is missing,
       leave the field empty without hallucinating.

    3. Dataset creators MUST be authors. Each creator should include:
       "name", "affiliation", "orcid" (if any), "email" (if any), "role" (if explicitly mentioned).

    4. Contributors (non-authors) should only be added if they appear in acknowledgments
       or other text (e.g., "data curators", "annotation team"). Leave empty if unclear.

    5. Infer dataset metadata (description, coverage, keywords, rights, funding, relationships)
       ONLY from evidence in the article body, metadata, methods, acknowledgments, or references.

    6. NEVER invent DOIs, links, licenses, or repository locations unless they explicitly appear.

    7. Use dataset_name as the dataset title unless a more precise dataset title is stated.

    8. Funding information must come ONLY from the article's funding/acknowledgement section
       (e.g., FCT, EU H2020, NIH, NSF). Extract:
       - funder name
       - grant id
       - acronym
       - project title (if present)

    9. Coverage fields (dates, locations) should be extracted ONLY if the article describes:
       - data collection period
       - institutions or countries of acquisition
       - any geographical information linked to the dataset.

    10. Return ONLY a single JSON object compatible with Zenodo's deposition API,
        with this exact structure:

    {{
      "metadata": {{
        "title": "",
        "upload_type": "dataset",
        "publication_date": "",
        "version": "",
        "doi": "",
        "description": "",

        "creators": [
          {{
            "name": "",
            "affiliation": "",
            "orcid": "",
            "email": "",
            "role": ""
          }}
        ],

        "contributors": [
          {{
            "name": "",
            "affiliation": "",
            "orcid": "",
            "email": "",
            "role": ""
          }}
        ],

        "keywords": [],
        "language": "",
        "notes": "",

        "related_identifiers": [
          {{
            "identifier": "",
            "relation": "",
            "scheme": ""
          }}
        ],

        "communities": [
          {{
            "identifier": ""
          }}
        ],

        "license": "",
        "access_right": "",
        "embargo_date": "",

        "grants": [
          {{
            "funder": "",
            "grant_id": "",
            "acronym": "",
            "title": ""
          }}
        ],
        "subjects": [
          {{
            "term": "",
            "identifier": "",
            "scheme": ""
          }}
        ],

        "resource_type": {{
          "type": "dataset",
          "title": "Dataset"
        }},

        "dates": [
          {{
            "type": "",
            "start": "",
            "end": "",
            "description": ""
          }}
        ],

        "locations": [
          {{
            "place": "",
            "description": "",
            "lat": null,
            "lon": null
          }}
        ],

        "imprint": {{
          "publisher": "",
          "place": ""
        }}
      }}
    }}

    Do NOT include any explanation, comments, or text outside this JSON.

    ---------------------
    DATASET NAME:
    {dataset_name}

    ---------------------
    BODY TEXT:
    {body_snippet}

    ---------------------
    REFERENCES:
    {refs_snippet}
    """
    }

    # 3) Chamar o LLM
    # use BOTH system + user messages (not system_prompt twice)
    raw_response = callGPTModel([system_prompt, system_prompt])
    llm_data = _extract_json_safe(raw_response)

    # 4) Garantir que o output está no formato Zenodo { "metadata": { ... } }
    # Fallback mínimo se algo correr mal
    if not isinstance(llm_data, dict) or "metadata" not in llm_data:
        llm_data = {
            "metadata": {
                "title": dataset_name,
                "upload_type": "dataset",
                "publication_date": "",
                "version": "",
                "doi": "",
                "description": "",
                "creators": [],
                "contributors": [],
                "keywords": [],
                "language": "",
                "notes": "",
                "related_identifiers": [],
                "communities": [],
                "license": "",
                "access_right": "",
                "embargo_date": "",
                "grants": [],
                "subjects": [],
                "resource_type": {
                    "type": "dataset",
                    "title": "Dataset"
                },
                "dates": [],
                "locations": [],
                "imprint": {
                    "publisher": "",
                    "place": ""
                }
            }
        }

    return makeResponse(llm_data, 200, True)


@article_bp.route("/article/create-dataset-zenodo", methods=["POST"])
@cross_origin()
@require_auth
@swag_from("../swagger/article/create-dataset-zenodo.yml")
def zenodo_create_dataset_route():
    messagesToUser = []

    # ---- CHECK METADATA JSON ----
    metadata_str = request.form.get("metadata")
    if not metadata_str:
        appendMessage(messagesToUser, "Missing 'metadata' field in form data", "Error")
        return makeResponse(messagesToUser, 400, True)

    try:
        llm_data = json.loads(metadata_str)
    except json.JSONDecodeError:
        appendMessage(messagesToUser, "Invalid JSON in 'metadata' field", "Error")
        return makeResponse(messagesToUser, 400, True)

    if not isinstance(llm_data, dict) or "metadata" not in llm_data:
        appendMessage(messagesToUser, "JSON must have top-level 'metadata' key", "Error")
        return makeResponse(messagesToUser, 400, True)

    # ---- CHECK FILES ----
    # Accept multiple files via "files" field (files[] on frontend) or a single "file"
    files = request.files.getlist("files")
    if not files:
        # fallback: maybe frontend sent just "file"
        single_file = request.files.get("file")
        if single_file:
            files = [single_file]

    if not files:
        appendMessage(messagesToUser, "No files provided for upload", "Error")
        return makeResponse(messagesToUser, 400, True)

    # ---- CALL ZENODO API ----
    try:
        deposition = create_zenodo_deposition_with_files(llm_data, files)
    except Exception as e:
        appendMessage(messagesToUser, f"Error creating Zenodo deposition: {str(e)}", "Error")
        return makeResponse(messagesToUser, 500, True)

    # You can wrap it directly; front-end will see Zenodo's JSON.
    return makeResponse(deposition, 200, True)
