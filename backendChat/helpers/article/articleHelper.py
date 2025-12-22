from __future__ import annotations
import json
import os
import re
from typing import Tuple
import requests
from typing import List, Union, IO
from PyPDF2 import PdfReader
from werkzeug.datastructures import FileStorage
from helpers.index import appendMessage, callGPTModel, _extract_json_safe

ZENODO_API_BASE = "https://zenodo.org/api"
BASE = "https://www.f-uji.net"

def _normalize_article(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (s or "").lower())).strip()

ZENODO_REF_PATTERN = re.compile(
    r"(10\.5281\/zenodo\.\d+|https?:\/\/(?:www\.)?zenodo\.org\/records\/\d+|https?:\/\/doi\.org\/10\.5281\/zenodo\.\d+)",
    re.IGNORECASE
)

def _parse_referenced_entry(entry: str) -> Tuple[str, str]:
    entry = (entry or "").strip()

    if "|" in entry:
        name, ref = entry.split("|", 1)
        return name.strip(), ref.strip()

    m = ZENODO_REF_PATTERN.search(entry)
    if not m:
        return entry, ""
    ref = m.group(0).strip()
    name = (entry[:m.start()] + entry[m.end():]).strip()
    return name, ref

def _parse_referenced_entry_with_gpt_fallback(
    entry: str
) -> Tuple[str, str]:
    """
    Try regex-based parsing first.
    If no Zenodo ref found, ask GPT to extract dataset_name + zenodo_ref.
    """

    # 1) Try deterministic parsing
    name, ref = _parse_referenced_entry(entry)
    if ref and _has_zenodo_ref(ref):
        return name, ref

    # 2) GPT fallback
    system_prompt = {
        "role": "system",
        "content": (
            "Extract dataset name and Zenodo reference from text.\n"
            "Return ONLY valid JSON.\n"
            "Do NOT invent references.\n"
            "If no Zenodo DOI or URL is present, return empty string for zenodo_ref."
        )
    }

    user_prompt = {
        "role": "user",
        "content": (
            f"Text:\n{entry}\n\n"
            "Return JSON:\n"
            "{\n"
            '  "dataset_name": "",\n'
            '  "zenodo_ref": ""\n'
            "}"
        )
    }

    raw = callGPTModel([system_prompt, user_prompt])
    parsed = _extract_json_safe(raw) or {}

    gpt_name = str(parsed.get("dataset_name") or "").strip()
    gpt_ref = str(parsed.get("zenodo_ref") or "").strip()

    # 3) Validate GPT output (NO hallucinations)
    if gpt_ref and not _has_zenodo_ref(gpt_ref):
        gpt_ref = ""

    # 4) Prefer GPT name only if it improves things
    final_name = gpt_name if gpt_name else name
    final_ref = gpt_ref if gpt_ref else ref

    return final_name, final_ref

def _has_zenodo_ref(s: str) -> bool:
    return bool(ZENODO_REF_PATTERN.search(s or ""))

def handle_dataset_list_edit(user_text: str, referenced: list, non_referenced: list, messagesToUser: list):
    """
    Improved dataset list editor.

    Key behavior:
    - User may provide FULL dataset name or ONLY A FUZZY/PARTIAL PART of it.
    - For referenced list entries, we try to match datasets by:
        1) exact normalized name match
        2) regex-based token containment (fuzzy)
        3) if still not found: ONE GPT fallback to resolve which referenced entry is intended
    - For referenced ADD/UPDATE, user can provide the Zenodo ref anywhere in the text:
        "<dataset name part> <zenodo doi/url>"
        Also supports legacy: "<name> | <ref>"

    Requires helpers available in your module:
      - _normalize_article
      - ZENODO_REF_PATTERN / _has_zenodo_ref
      - _parse_referenced_entry (internal entry parse)
      - _parse_referenced_entry_with_gpt_fallback (internal entry parse with GPT fallback)
      - callGPTModel, _extract_json_safe, appendMessage
    """

    # -------------------------
    # 0) Helpers (local)
    # -------------------------
    def _parse_user_name_and_ref(text: str) -> Tuple[str, str]:
        """
        Accepts:
          - "name | ref"
          - "name ref"
          - "ref" (edge)
        Returns (name, ref)
        """
        text = (text or "").strip()
        if "|" in text:
            a, b = text.split("|", 1)
            return a.strip(), b.strip()

        m = ZENODO_REF_PATTERN.search(text)
        if not m:
            return text.strip(), ""
        ref = m.group(0).strip()
        name = (text[:m.start()] + text[m.end():]).strip()
        return name, ref

    def _build_fuzzy_regex(query: str) -> re.Pattern | None:
        """
        Build a regex that checks whether ALL query tokens appear (in any order) in a candidate string.
        """
        tokens = [t for t in _normalize_article(query).split(" ") if t]
        if not tokens:
            return None
        # Require all tokens as word boundaries (approx)
        lookaheads = "".join([rf"(?=.*\b{re.escape(t)}\b)" for t in tokens])
        return re.compile(lookaheads, re.IGNORECASE)

    def _match_referenced_index_by_regex(old_name_part: str, lst: list[str]) -> Tuple[int | None, list[int]]:
        """
        Return (best_idx_or_None, candidate_idxs)

        We treat:
          - exact normalized match as best
          - else regex fuzzy (all tokens present)
        If multiple candidates, return None + candidates.
        """
        old_norm = _normalize_article(old_name_part)
        if not old_norm:
            return None, []

        # 1) exact match on internal name
        exact_hits = []
        for i, entry in enumerate(lst):
            name, _ = _parse_referenced_entry(entry)
            if _normalize_article(name) == old_norm:
                exact_hits.append(i)
        if len(exact_hits) == 1:
            return exact_hits[0], exact_hits
        if len(exact_hits) > 1:
            return None, exact_hits

        # 2) fuzzy: all tokens of query appear in candidate name
        rx = _build_fuzzy_regex(old_name_part)
        if rx is None:
            return None, []

        fuzzy_hits = []
        for i, entry in enumerate(lst):
            name, _ = _parse_referenced_entry(entry)
            if rx.search(_normalize_article(name)):
                fuzzy_hits.append(i)

        if len(fuzzy_hits) == 1:
            return fuzzy_hits[0], fuzzy_hits
        return None, fuzzy_hits

    def _gpt_choose_referenced_index(old_value: str, lst: list[str]) -> int | None:
        """
        One GPT interaction: user typed something, and our regex matching didn't find a single target.
        Ask GPT to choose the best dataset from the referenced list.
        Returns index or None.
        """
        # Keep list compact to reduce token usage
        options = []
        for i, entry in enumerate(lst):
            name, ref = _parse_referenced_entry(entry)
            options.append({"index": i, "dataset_name": name, "zenodo_ref": ref})

        system_prompt_local = {
            "role": "system",
            "content": (
                "You are helping map a user's partial dataset name to one item from a list.\n"
                "Return ONLY JSON.\n"
                "If none match, return index = -1.\n"
                "Do NOT invent options.\n"
            )
        }
        user_prompt_local = {
            "role": "user",
            "content": (
                f"User wants to edit this referenced dataset (partial name):\n{old_value}\n\n"
                f"Referenced list options:\n{json.dumps(options, ensure_ascii=False)}\n\n"
                "Return ONLY JSON:\n"
                '{ "index": 0 }'
            )
        }

        raw_local = callGPTModel([system_prompt_local, user_prompt_local])
        parsed_local = _extract_json_safe(raw_local) or {}
        try:
            idx = int(parsed_local.get("index", -1))
        except Exception:
            idx = -1

        if 0 <= idx < len(lst):
            return idx
        return None

    def _respond_ambiguous(old_value: str, lst: list[str], candidate_idxs: list[int], action_word: str):
        top = candidate_idxs[:5]
        suggestions = []
        for i in top:
            nm, rf = _parse_referenced_entry(lst[i])
            suggestions.append(f"- {nm} | {rf}".strip())
        appendMessage(
            messagesToUser,
            role="assistant",
            contentShort=f"I found multiple referenced datasets matching '{old_value}'. Please be more specific.",
            content=(
                f"I found multiple referenced datasets matching '{old_value}' for {action_word}.\n\n"
                "Candidates:\n" + "\n".join(suggestions)
            ),
            stage="DefineNextStepInteraction",
            jsonObject=False
        )

    # -------------------------
    # 1) Extract edit op via GPT (you already do this)
    # -------------------------
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

    # -----------------------
    # ADD
    # -----------------------
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

        if target_list == "referenced":
            # user does NOT need pipe; accept "name ref" or "name | ref"
            name, ref = _parse_user_name_and_ref(new_value)

            if not name or not ref or not _has_zenodo_ref(ref):
                appendMessage(
                    messagesToUser,
                    role="assistant",
                    contentShort="To add a referenced dataset, include a Zenodo DOI/URL after the dataset name.",
                    content=(
                        "Referenced datasets MUST include a Zenodo reference.\n\n"
                        "Examples:\n"
                        "- add referenced: My Dataset https://doi.org/10.5281/zenodo.1234567\n"
                        "- add referenced: My Dataset https://zenodo.org/records/1234567\n"
                        "- add referenced: My Dataset 10.5281/zenodo.1234567"
                    ),
                    stage="DefineNextStepInteraction",
                    jsonObject=False
                )
                return referenced, non_referenced

            lst.append(f"{name} | {ref}")
        else:
            lst.append(new_value)

        return referenced, non_referenced

    # -----------------------
    # DELETE
    # -----------------------
    if op == "delete":
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

        if target_list == "referenced":
            # match by exact or fuzzy via regex; if none -> GPT choose; if ambiguous -> ask user
            idx, candidates = _match_referenced_index_by_regex(old_value, lst)
            if idx is None:
                if not candidates:
                    idx = _gpt_choose_referenced_index(old_value, lst)
                    if idx is None:
                        appendMessage(
                            messagesToUser,
                            role="assistant",
                            contentShort=f"I couldn't find '{old_value}' in the referenced list to delete.",
                            content=f"I couldn't find '{old_value}' in the referenced list to delete.",
                            stage="DefineNextStepInteraction",
                            jsonObject=False
                        )
                        return referenced, non_referenced
                else:
                    _respond_ambiguous(old_value, lst, candidates, "delete")
                    return referenced, non_referenced

            del lst[idx]
            return referenced, non_referenced

        # non-referenced delete: keep simple exact match
        target = _normalize_article(old_value)
        lst[:] = [x for x in lst if _normalize_article(str(x)) != target]
        return referenced, non_referenced

    # -----------------------
    # UPDATE
    # -----------------------
    if op == "update":
        if not old_value or not new_value:
            appendMessage(
                messagesToUser,
                role="assistant",
                contentShort="Please provide both old and new values: update <old> -> <new>.",
                content=(
                    "Examples:\n"
                    "- update referenced: Old Name -> New Name\n"
                    "- update referenced: Old Name -> https://doi.org/10.5281/zenodo.1234567\n"
                    "- update referenced: part of name -> New Name https://zenodo.org/records/1234567\n"
                    "- update non-referenced: Old Name -> New Name"
                ),
                stage="DefineNextStepInteraction",
                jsonObject=False
            )
            return referenced, non_referenced

        if target_list == "referenced":
            # 1) Find which entry to update (exact or fuzzy). If none -> GPT; if ambiguous -> ask user
            idx, candidates = _match_referenced_index_by_regex(old_value, lst)
            if idx is None:
                if not candidates:
                    idx = _gpt_choose_referenced_index(old_value, lst)
                    if idx is None:
                        appendMessage(
                            messagesToUser,
                            role="assistant",
                            contentShort=f"I couldn't find '{old_value}' in the referenced list to update.",
                            content=(
                                f"I couldn't find '{old_value}' in the referenced list to update.\n"
                                "Tip: you can type a partial name, but it must uniquely identify one dataset."
                            ),
                            stage="DefineNextStepInteraction",
                            jsonObject=False
                        )
                        return referenced, non_referenced
                else:
                    _respond_ambiguous(old_value, lst, candidates, "update")
                    return referenced, non_referenced

            cur_name, cur_ref = _parse_referenced_entry_with_gpt_fallback(str(lst[idx]))

            # 2) Parse the user's new_value (supports: name ref, name only, ref only, name|ref)
            new_name, new_ref = _parse_user_name_and_ref(new_value)

            final_name = new_name.strip() if new_name.strip() else cur_name
            final_ref = new_ref.strip() if new_ref.strip() else cur_ref

            if not final_ref or not _has_zenodo_ref(final_ref):
                appendMessage(
                    messagesToUser,
                    role="assistant",
                    contentShort="Referenced datasets must keep a valid Zenodo DOI/URL.",
                    content="Please provide a valid Zenodo DOI/URL in the update message.",
                    stage="DefineNextStepInteraction",
                    jsonObject=False
                )
                return referenced, non_referenced

            lst[idx] = f"{final_name} | {final_ref}"
            return referenced, non_referenced

        # non-referenced update (exact match)
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

    return referenced, non_referenced

def _extract_zenodo_identifier(input_str: str):
    import re
    from urllib.parse import urlparse

    if not input_str:
        return {"record_id": None, "doi": None}

    s = input_str.strip()

    # 1) DOI anywhere in the string (highest priority)
    doi_match = re.search(r"(10\.5281\/zenodo\.\d+)", s, re.IGNORECASE)
    if doi_match:
        return {"record_id": None, "doi": doi_match.group(1)}

    # 2) Zenodo record URL (records or record)
    if s.startswith("http://") or s.startswith("https://"):
        parsed = urlparse(s)
        parts = [p for p in parsed.path.split("/") if p]

        for i, p in enumerate(parts):
            if p in ("record", "records") and i + 1 < len(parts):
                rid = parts[i + 1]
                if rid.isdigit():
                    return {"record_id": rid, "doi": None}

    # 3) Raw numeric record ID
    if re.fullmatch(r"\d+", s):
        return {"record_id": s, "doi": None}

    # 4) Raw DOI (without URL)
    if s.startswith("10.5281/zenodo."):
        return {"record_id": None, "doi": s}

    # 5) Nothing usable found
    return {"record_id": None, "doi": None}

import os
import json
import requests
from typing import Any, Dict


def run_fuji_fair_assessment(article_uuid: str, doi: str) -> dict:
    """
    Run a F-UJI FAIR assessment for a given DOI, save full JSON, and also
    compute + save a compact summary with:
      - maturity.FAIR
      - score_percent.FAIR
      - score_earned.FAIR, score_total.FAIR, diff

    Saves:
      articles/<uuid>/fuji_result.json
      articles/<uuid>/fuji_summary.json

    Returns:
      {
        "doi": ...,
        "fuji_summary": {...},
        "fuji_result": {...}
      }
    """

    BASE = "https://www.f-uji.net"
    session = requests.Session()

    # Stable session cookie (F-UJI is session-based)
    session.cookies.set(
        "PHPSESSID",
        article_uuid,
        domain="www.f-uji.net",
        path="/"
    )

    headers = {
        "accept": "*/*",
        "accept-language": "pt-PT,pt;q=0.9,en;q=0.8",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest",
        "referer": f"{BASE}/index.php",
    }

    data = {
        "pid": doi,
        "service_url": "",
        "service_type": "oai_pmh",
        "use_datacite": "true",
        "enable_cache": "false",
        "metric_id": "metrics_v0.8",
    }

    # 1) Start assessment
    r1 = session.post(f"{BASE}/inc_result.php", headers=headers, data=data, timeout=60)
    if r1.status_code != 200:
        raise RuntimeError(f"F-UJI assessment start failed (status={r1.status_code})")

    # 2) Export JSON
    r2 = session.get(f"{BASE}/export.php", headers={"referer": f"{BASE}/index.php"}, timeout=60)
    if r2.status_code != 200:
        raise RuntimeError(f"F-UJI export failed (status={r2.status_code})")

    content_type = r2.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise RuntimeError(f"F-UJI export did not return JSON (content-type={content_type})")

    fuji_result: Dict[str, Any] = r2.json()

    # ---------- Save full result ----------
    base_dir = os.path.join("articles", article_uuid)
    os.makedirs(base_dir, exist_ok=True)

    full_path = os.path.join(base_dir, "fuji_result.json")
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(fuji_result, f, indent=2, ensure_ascii=False)

    # ---------- Extract requested fields ----------
    summary = fuji_result.get("summary", {}) or {}

    score_earned = summary.get("score_earned", {}) or {}
    score_total = summary.get("score_total", {}) or {}
    score_percent = summary.get("score_percent", {}) or {}
    maturity = summary.get("maturity", {}) or {}

    def _num(x, default=0.0) -> float:
        try:
            if x is None:
                return float(default)
            return float(x)
        except Exception:
            return float(default)

    # -------- PER-ELEMENT SCORES --------
    score_by_element = {}

    # Union of all keys that appear anywhere
    all_keys = set(score_earned) | set(score_total) | set(score_percent)

    for key in sorted(all_keys):
        earned = _num(score_earned.get(key))
        total = _num(score_total.get(key))
        percent = _num(score_percent.get(key))

        if percent== 100:
            score_by_element[key] = {
                "percent": percent
            }
        else:
            score_by_element[key] = {
                "earned": earned,
                "total": total,
                "missing": max(total - earned, 0),
                "percent": percent
            }

    # -------- FINAL SUMMARY --------
    fuji_summary = {
        # High-level FAIR indicators
        "maturity_fair": _num(maturity.get("FAIR")),
        "score_percent_fair": _num(score_percent.get("FAIR")),

        # Full per-element breakdown (THIS is what you asked for)
        "score_by_element": score_by_element
    }

    # ---------- Save summary ----------
    summary_path = os.path.join(base_dir, "fuji_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(fuji_summary, f, indent=2, ensure_ascii=False)

    # Return both (you can choose to return only summary if you prefer)
    return {
        "doi": doi,
        "fuji_summary": fuji_summary,
        #"fuji_result": fuji_result
    }


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

    resp = requests.put(url, data=json.dumps(llm_data), headers=headers)
    resp.raise_for_status()
    deposition = resp.json()

    # llm_data should already have the top-level "metadata" key
    # resp = requests.post(create_url, params=params, json=llm_data, timeout=30)

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
        "How would you like to proceed?\n\n"
        "A) Infer metadata (datasets WITHOUT a reference)\n"
        "   - Use when the dataset has no DOI/URL/citation.\n"
        "   - Format: infer <dataset name>\n\n"
        "B) Improve metadata (datasets WITH a Zenodo reference)\n"
        "   - Use when the dataset is in the Referenced list (has Zenodo DOI/URL).\n"
        "   - Format: improve <dataset name>\n\n"
        "C) Edit dataset lists (add / update / delete)\n"
        "   - Referenced entries MUST include a Zenodo DOI/URL.\n"
        "   - Referenced format: <dataset name> | <Zenodo DOI/URL>\n"
        "   - Non-referenced format: <dataset name>\n\n"
        "Zenodo reference accepted formats:\n"
        "  - 10.5281/zenodo.1234567\n"
        "  - https://doi.org/10.5281/zenodo.1234567\n"
        "  - https://zenodo.org/records/1234567"
    )

    examples = (
        "Infer examples:\n"
        "- infer Social Network Graph Dataset\n\n"
        "Improve examples (must exist in Referenced list):\n"
        "- improve Climate Observations 1990–2020\n\n"
        "Edit examples:\n"
        "- add referenced: My Dataset | https://doi.org/10.5281/zenodo.1234567\n"
        "- add non-referenced: the CT scan dataset\n"
        "- delete referenced: My Dataset\n"
        "- delete non-referenced: the CT scan dataset\n"
        "- update referenced: Old Dataset Name -> New Dataset Name\n"
        "- update referenced: Old Dataset Name -> New Dataset Name | https://doi.org/10.5281/zenodo.7654321\n"
        "- update referenced: Old Dataset Name -> | https://zenodo.org/records/7654321\n"
        "- update non-referenced: Old Dataset Name -> New Dataset Name"
    )

    appendMessage(messagesToUser,
                  role="assistant",
                  stage="DefineNextStepInteraction",
                  jsonObject=True,
                  contentShort={"summary": summary,
                                "referencedDatasets": referencedDatasets,
                                "nonReferencedDatasets": nonReferencedDatasets,
                                "instructions": instructions},
                  content={"summary": summary,
                           "referencedDatasets": referencedDatasets,
                           "nonReferencedDatasets": nonReferencedDatasets,
                           "instructions": instructions},
                  examples=examples
                  )
