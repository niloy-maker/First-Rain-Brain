"""
classify_pipeline.py
====================
Applies region + industry classification to Bigin pipeline deals.

Priority order (per deal):
  1. Bigin field value (if populated) — authoritative
  2. Regex pattern match on Deal_Name — fallback
  3. "Unknown" — last resort, logged for investigation

Output: data/projects/bigin_pipeline_classified.json

The regex dictionaries below are derived from observed deal-name patterns
in the 84-deal Apr 21 payload. Update as new patterns surface.

Usage:
    python classify_pipeline.py
    # or from orchestrator:
    from classify_pipeline import classify
    classified = classify(bigin_pipeline_raw)
"""

import json
import re
from pathlib import Path

INPUT_PATH = Path("data/projects/bigin_pipeline_raw.json")
OUTPUT_PATH = Path("data/projects/bigin_pipeline_classified.json")


# ---------- Region regex (Appendix B of merge spec) ----------

REGION_PATTERNS = [
    # Europe
    (r'\b(Germany|Berlin|Munich|Frankfurt|Hamburg|D[üu]sseldorf|Cologne|Geneva|Switzerland|Zurich|Basel|Milan|Rome|Italy|Paris|France|Nuremberg|Hannover|Essen|Stuttgart|Amsterdam|Netherlands|Brussels|Belgium|Vienna|Austria|Madrid|Barcelona|Spain|Lisbon|Portugal|Vitafood|Vitafoods)\b', 'Europe'),
    # UK
    (r'\b(UK|United Kingdom|London|Manchester|Birmingham|Glasgow|Edinburgh|Leeds|Bristol|Liverpool|NEC|Olympia|ExCeL|ExCel|Utility Week|In-Cosmetics)\b', 'UK'),
    # Americas
    (r'\b(USA|US|America|New York|NYC|Chicago|LA|Los Angeles|SF|San Francisco|Boston|Miami|Vegas|Las Vegas|Anaheim|Orlando|Dallas|Houston|Atlanta|CES|NAB|Canada|Toronto|Mexico|Brazil|Sao Paulo|Argentina|Buenos Aires)\b', 'Americas'),
    # Middle East
    (r'\b(Dubai|UAE|Abu Dhabi|Saudi|Riyadh|KSA|Qatar|Doha|Oman|Kuwait|Bahrain|Jordan|Egypt|Cairo|Israel|Tel Aviv|ADIPEC|Arab)\b', 'Middle East'),
    # South East Asia
    (r'\b(Singapore|Bangkok|Thailand|Malaysia|Kuala Lumpur|KL|Vietnam|Hanoi|Ho Chi Minh|Jakarta|Indonesia|Manila|Philippines|Hong Kong|Shanghai|Beijing|China|Taipei|Taiwan|Tokyo|Osaka|Japan|Seoul|South Korea|Korea)\b', 'SEA'),
    # Rest of World
    (r'\b(Australia|Sydney|Melbourne|Brisbane|NZ|New Zealand|Auckland|Russia|Moscow|South Africa|Cape Town|Johannesburg|Nigeria|Lagos|Kenya|Nairobi)\b', 'RoW'),
    # India (must be last — catches everything else referencing Indian cities)
    (r'\b(India|Mumbai|Delhi|NCR|Noida|Gurgaon|Bangalore|B.?Glore|Blr|Chennai|Kolkata|Pune|Hyderabad|Ahmedabad|Jaipur|Lucknow|Kochi|Coimbatore|Nagpur|Indore|Bhopal|BIEC|JWCC|Pragati|NESCO|YBN|Bombay)\b', 'India'),
]


INDUSTRY_PATTERNS = [
    # Electrical / Energy / Smart Metering
    (r'\b(Renew|Elecrama|RenewX|Secure|electrical|energy|power|smart meter|metering|solar|wind|Elecoma)\b', 'Electrical / Energy / Smart Metering'),
    # Architecture / Interior / Building Materials
    (r'\b(Acetech|Index|Archi|interior|design week|Cosmohome|ceramic|tile|flooring|DJGF|Home expo|Smart home)\b', 'Architecture / Interior / Building Materials'),
    # Construction Machinery
    (r'\b(BCMT|IMME|Bauma|Excon|construction equipment|earthmoving|JCB|concrete|Excon)\b', 'Construction Machinery'),
    # Pharma / APIs / Devices
    (r'\b(CPhI|PharmaTech|pharma|API|formulation|Medical|medical device|Medicall|DIA)\b', 'Pharma / APIs / Devices'),
    # Specialty Chemicals
    (r'\b(Chem|chemical|Lube|lubricant|Mosil|Bechem|petrochem|PaintIndia|Coatings|Iberchem|specialty)\b', 'Specialty Chemicals'),
    # HVAC & Building Automation
    (r'\b(HVAC|ACREX|Climatizacao|air condition|cooling|refrigerat|IAQ)\b', 'HVAC & Building Automation'),
    # AV & Tech
    (r'\b(InfoComm|ISE|AV|audio video|NAB|Christie|broadcast|ProSound|display tech)\b', 'AV & Tech'),
    # Nutraceuticals
    (r'\b(Vitafood|Vitafoods|HiE|HPCI|Food Ingredients|SupplySide|FI|nutraceutical|Amaara|ayurveda)\b', 'Nutraceuticals'),
    # Beauty / Fragrance
    (r'\b(Cosmoprof|In-Cosmetics|beauty|fragrance|cosmetic|HPCI|personal care)\b', 'Beauty / Fragrance'),
    # Rail
    (r'\b(InnoTrans|rail|railway|metro|wagon|Trainmet)\b', 'Rail'),
    # Textile Machinery
    (r'\b(ITMA|ITME|Textile|Truetzschler|spinning|weaving|BharatTex)\b', 'Textile Machinery'),
    # Industrial Mfg (catchall — must be late)
    (r'\b(Automation India|IMTEX|MACH|EMO|industrial|manufacturing|Messung|Labguard|Klenzaids|Elliott|Ebara|Turbomachinery|Nordex|GIC|Spectrum|Filtration|Filtech)\b', 'Industrial Mfg'),
    # Stones (niche — explicit names)
    (r'\b(Stona|Indian Stone|marble|granite|Swarnshilp|Jewel)\b', 'Stones'),
]


def _match_region(text):
    if not text:
        return "Unknown"
    for pattern, region in REGION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return region
    return "Unknown"


def _match_industry(text):
    if not text:
        return "Unknown"
    for pattern, industry in INDUSTRY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return industry
    return "Unknown"


def _bucket_stage(stage):
    """Map Bigin stage to dashboard bucket (matches v11 renderer)."""
    if not stage:
        return "active"
    stage_lower = stage.lower()
    if "closed won" in stage_lower:
        return "won"
    if "closed lost" in stage_lower:
        return "lost"
    if "not qualified" in stage_lower or "junk" in stage_lower:
        return "junk"
    # Hot stages — late funnel
    if any(s in stage_lower for s in ["design", "price quote", "existing confirmed", "qualified"]):
        return "hot"
    # Everything else = active
    return "active"


def _compute_weighted(amount, prob):
    return float(amount or 0) * (float(prob or 0) / 100.0)


def classify(raw_payload):
    """
    Main entrypoint. Takes the dict produced by fetch_bigin_pipeline.py.
    Returns dict with deals classified + bucket tags + weighted amounts.
    """
    deals = raw_payload["deals"]
    region_available = raw_payload["meta"]["region_available"]
    industry_available = raw_payload["meta"]["industry_available"]

    unknown_region = []
    unknown_industry = []

    for deal in deals:
        deal_name = deal.get("deal", "") or ""

        # Region: prefer Bigin field; fallback to regex on deal name
        if not deal.get("region"):
            deal["region"] = _match_region(deal_name)
            deal["region_source"] = "regex"
        else:
            deal["region_source"] = "bigin"
        if deal["region"] == "Unknown":
            unknown_region.append(deal.get("id"))

        # Industry: prefer Bigin field; fallback to regex on deal name
        if not deal.get("industry"):
            deal["industry"] = _match_industry(deal_name)
            deal["industry_source"] = "regex"
        else:
            deal["industry_source"] = "bigin"
        if deal["industry"] == "Unknown":
            unknown_industry.append(deal.get("id"))

        # Bucket + weighted
        deal["bucket"] = _bucket_stage(deal.get("stage"))
        deal["weighted"] = _compute_weighted(deal.get("amount"), deal.get("prob"))

    result = {
        "deals": deals,
        "meta": {
            **raw_payload["meta"],
            "classified_at": raw_payload["meta"]["fetched_at"],
            "unknown_region_ids": unknown_region,
            "unknown_industry_ids": unknown_industry,
            "regex_fallback_used_region": not region_available,
            "regex_fallback_used_industry": not industry_available,
        }
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"[classify_pipeline] {len(deals)} deals classified · "
          f"unknown region={len(unknown_region)} · unknown industry={len(unknown_industry)}")
    return result


if __name__ == "__main__":
    with open(INPUT_PATH) as f:
        raw = json.load(f)
    classify(raw)
