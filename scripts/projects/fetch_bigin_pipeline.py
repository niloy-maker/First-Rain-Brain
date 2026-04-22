"""
fetch_bigin_pipeline.py
========================
Pulls 84-deal pipeline from Bigin via COQL, resolves Account_Name join,
attempts to pull Region (Pipelines) and Industry (Accounts) picklist values.

Graceful degradation: if Region/Industry fields don't exist yet (Niloy
hasn't done admin work), retry without them. classify_pipeline.py then
applies regex fallback.

Output: data/projects/bigin_pipeline_raw.json

Usage:
    python fetch_bigin_pipeline.py
    # or from orchestrator:
    from fetch_bigin_pipeline import fetch_pipeline
    deals = fetch_pipeline()

Author: First Rain CFO Intelligence System v3.0
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Claude Code runs this via its own Bigin MCP client.
# In standalone testing, import the shim below.
try:
    from claude_bigin_client import coql_query
except ImportError:
    # Standalone test mode — assume a shim you wire up in Claude Code
    def coql_query(select_query):
        raise NotImplementedError("Wire up coql_query() to your Bigin MCP client")


PIPELINE_NAME = "Sales Pipeline 26-27"
OUTPUT_PATH = Path("data/projects/bigin_pipeline_raw.json")


# ---------- COQL queries ----------

COQL_PIPELINE_FULL = f"""
SELECT
  id,
  Deal_Name,
  Account_Name.id,
  Account_Name.Account_Name,
  Amount,
  Closing_Date,
  Stage,
  Pipeline,
  Probability,
  Created_Time,
  Modified_Time,
  Region,
  Owner.id,
  Owner.name
FROM Pipelines
WHERE Pipeline = '{PIPELINE_NAME}'
""".strip()

COQL_PIPELINE_FALLBACK = f"""
SELECT
  id,
  Deal_Name,
  Account_Name.id,
  Account_Name.Account_Name,
  Amount,
  Closing_Date,
  Stage,
  Pipeline,
  Probability,
  Created_Time,
  Modified_Time,
  Owner.id,
  Owner.name
FROM Pipelines
WHERE Pipeline = '{PIPELINE_NAME}'
""".strip()


def _coql_accounts_industry(account_ids):
    """Build COQL for Accounts lookup, chunked if needed."""
    # Bigin COQL IN clause has practical limits; chunk to 50
    chunks = [account_ids[i:i+50] for i in range(0, len(account_ids), 50)]
    return [
        f"SELECT id, Account_Name, Industry FROM Accounts WHERE id IN ({','.join(repr(a) for a in chunk)})"
        for chunk in chunks
    ]


def _coql_accounts_fallback(account_ids):
    """Same as above but without Industry — used if Industry field absent."""
    chunks = [account_ids[i:i+50] for i in range(0, len(account_ids), 50)]
    return [
        f"SELECT id, Account_Name FROM Accounts WHERE id IN ({','.join(repr(a) for a in chunk)})"
        for chunk in chunks
    ]


# ---------- Core fetch ----------

def _fetch_pipeline_deals():
    """Try the full query first, fall back if Region field is missing."""
    try:
        result = coql_query(COQL_PIPELINE_FULL)
        region_available = True
    except Exception as e:
        err = str(e).lower()
        if "region" in err and ("invalid" in err or "not found" in err or "column" in err):
            print("[fetch_bigin_pipeline] Region field not yet configured — using fallback COQL", file=sys.stderr)
            result = coql_query(COQL_PIPELINE_FALLBACK)
            region_available = False
        else:
            raise

    deals = result.get("data", []) if isinstance(result, dict) else result
    return deals, region_available


def _fetch_accounts(account_ids):
    """Pull Industry for the set of account IDs referenced by the deals."""
    if not account_ids:
        return {}, False

    industry_available = True
    rows = []

    try:
        for query in _coql_accounts_industry(account_ids):
            result = coql_query(query)
            rows.extend(result.get("data", []) if isinstance(result, dict) else result)
    except Exception as e:
        err = str(e).lower()
        if "industry" in err and ("invalid" in err or "not found" in err or "column" in err):
            print("[fetch_bigin_pipeline] Industry field not yet configured — using fallback COQL", file=sys.stderr)
            rows = []
            for query in _coql_accounts_fallback(account_ids):
                result = coql_query(query)
                rows.extend(result.get("data", []) if isinstance(result, dict) else result)
            industry_available = False
        else:
            raise

    index = {row["id"]: row for row in rows}
    return index, industry_available


# ---------- Normalization ----------

def _normalize_deal(deal_row, account_index, region_available, industry_available):
    """Shape raw COQL row into the v11 renderer's expected format."""
    account_id = (deal_row.get("Account_Name") or {}).get("id") if isinstance(deal_row.get("Account_Name"), dict) else deal_row.get("Account_Name.id")
    account_name = (deal_row.get("Account_Name") or {}).get("Account_Name") if isinstance(deal_row.get("Account_Name"), dict) else deal_row.get("Account_Name.Account_Name")

    industry = None
    if account_id and account_id in account_index:
        industry = account_index[account_id].get("Industry") if industry_available else None

    return {
        "id": deal_row.get("id"),
        "deal": deal_row.get("Deal_Name", ""),
        "account": account_id,
        "account_name": account_name,
        "amount": float(deal_row.get("Amount") or 0),
        "prob": float(deal_row.get("Probability") or 0),
        "stage": deal_row.get("Stage", ""),
        "close": deal_row.get("Closing_Date"),
        "created": deal_row.get("Created_Time"),
        "modified": deal_row.get("Modified_Time"),
        "industry": industry,  # None if field absent — classify_pipeline.py will regex-fallback
        "region": deal_row.get("Region") if region_available else None,
        "exec": _map_owner_to_exec_code(deal_row.get("Owner.name") or (deal_row.get("Owner") or {}).get("name")),
    }


def _map_owner_to_exec_code(owner_name):
    """Map Bigin owner full name to exec code (CK/SP/DS/ND)."""
    if not owner_name:
        return None
    mapping = {
        "chinmay": "CK",
        "shilpa": "SP",
        "dhruv": "DS",
        "niloy": "ND",
    }
    lower = owner_name.lower()
    for key, code in mapping.items():
        if key in lower:
            return code
    return None


# ---------- Entrypoint ----------

def fetch_pipeline():
    """
    Main entrypoint. Returns dict with:
      - deals: list of normalized deal rows
      - meta: {region_available, industry_available, fetched_at, count}
    """
    deals_raw, region_available = _fetch_pipeline_deals()

    account_ids = set()
    for d in deals_raw:
        acct = d.get("Account_Name")
        if isinstance(acct, dict):
            account_ids.add(acct.get("id"))
        else:
            account_ids.add(d.get("Account_Name.id"))
    account_ids.discard(None)

    account_index, industry_available = _fetch_accounts(sorted(account_ids))

    normalized = [
        _normalize_deal(d, account_index, region_available, industry_available)
        for d in deals_raw
    ]

    result = {
        "deals": normalized,
        "meta": {
            "region_available": region_available,
            "industry_available": industry_available,
            "fetched_at": datetime.now().astimezone().isoformat(),
            "count": len(normalized),
        }
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"[fetch_bigin_pipeline] {len(normalized)} deals · Region={region_available} · Industry={industry_available}")
    return result


if __name__ == "__main__":
    fetch_pipeline()
