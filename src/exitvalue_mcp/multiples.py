"""Lookup logic over the public ExitValue.ai multiples dataset (no MCP imports here).

Data (CC-BY 4.0), aggregate medians and quartiles of disclosed M&A multiples:
  * https://exitvalue.ai/data/multiples.json          sub-vertical x enterprise-value bracket
  * https://exitvalue.ai/data/multiples-by-year.json  sub-vertical x deal year
Only cells with n >= the file's own threshold (``min_cell_n`` / ``min_n_per_cell``) are
shown; missing cells are reported as gaps, never interpolated or estimated.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import threading
import time
import urllib.request
from typing import Callable

from . import __version__
from .taxonomy import (
    ALIAS_NOTES,
    ALIASES,
    INDUSTRY_DISPLAY_NAMES,
    INDUSTRY_TAXONOMY,
    PARENT_CATEGORY,
    display_name,
)

SITE = "https://exitvalue.ai"
DATA_URL = os.environ.get("EXITVALUE_DATA_URL", f"{SITE}/data/multiples.json")
TREND_URL = os.environ.get("EXITVALUE_TREND_URL", f"{SITE}/data/multiples-by-year.json")
CONNECTOR_URL = f"{SITE}/ai-connector"
HOSTED_MCP_URL = f"{SITE}/api/mcp"
SOURCE_PHRASE = "a licensed historical M&A database, SEC EDGAR filings and verified press releases"
CACHE_TTL_SECONDS = 3600

BRACKETS = {  # multiples.json key -> label
    "under_5m_ev": "under $5M",
    "5m_25m_ev": "$5M-$25M",
    "25m_100m_ev": "$25M-$100M",
    "100m_500m_ev": "$100M-$500M",
    "over_500m_ev": "$500M and up",
}
METRICS = (("ev_ebitda", "EV/EBITDA"), ("ev_revenue", "EV/Revenue"))
MAX_COMPARE = 6
_SUFFIXES = ("-business", "-company", "-companies", "-firm", "-firms", "-shop", "-practice",
             "-practices", "-agency", "-agencies", "-services", "-contractor", "-contractors",
             "-businesses", "s")


# ── data loading (in-memory cache, ~1h) ─────────────────────────────────────

def _fetch_url(url: str = DATA_URL) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": f"exitvalue-mcp/{__version__}",
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 - fixed https URL
        return json.load(r)


class Dataset:
    """Fetches multiples.json at most once per TTL; serves a stale copy if a refresh fails."""

    def __init__(self, fetch: Callable[[], dict] = _fetch_url, ttl: float = CACHE_TTL_SECONDS):
        """``fetch`` defaults to multiples.json; pass ``lambda: _fetch_url(TREND_URL)`` for the per-year file."""
        self._fetch, self._ttl = fetch, ttl
        self._data: dict | None = None
        self._at = 0.0
        self._lock = threading.Lock()

    def get(self) -> dict:
        with self._lock:
            if self._data is None or time.monotonic() - self._at > self._ttl:
                try:
                    self._data = self._fetch()
                    self._at = time.monotonic()
                except Exception:
                    if self._data is None:
                        raise
            return self._data


# ── helpers ────────────────────────────────────────────────────────────────

def calculator_url(sv: str | None = None) -> str:
    return f"{SITE}/valuate?src=mcp-oss" + (f"&industry={sv}" if sv else "")


def cta(sv: str | None = None) -> str:
    return ("Get a free, business-specific valuation range (adjusted for your margins, growth and "
            f"owner dependence) in about 2 minutes: {calculator_url(sv)}")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _sv_parent() -> dict[str, str]:
    out: dict[str, str] = {}
    for ind, svs in INDUSTRY_TAXONOMY.items():
        for sv in svs:
            out.setdefault(sv, ind)
    return out


def _x(v: float, kind: str) -> str:
    return f"{v:.1f}x" if kind == "ev_ebitda" else f"{v:.2f}x"


def _fmt_q(q: dict, kind: str) -> str:
    s = f"median {_x(q['p50'], kind)}"
    if q.get("p25") is not None and q.get("p75") is not None:
        s += f" (middle 50%: {_x(q['p25'], kind)}-{_x(q['p75'], kind)})"
    return s + f", n={q.get('n')}"


def norm_bracket(b: str | None) -> str | None:
    if not b:
        return None
    s = _slug(b).replace("-", "_")
    s = s if s.endswith("_ev") else s + "_ev"
    aliases = {"under_5_ev": "under_5m_ev", "5_25_ev": "5m_25m_ev", "25_100_ev": "25m_100m_ev",
               "100_500_ev": "100m_500m_ev", "over_500_ev": "over_500m_ev", "500m_ev": "over_500m_ev"}
    s = aliases.get(s, s)
    return s if s in BRACKETS else None


def resolve(query: str) -> tuple[str, str] | tuple[None, list[str]]:
    """Plain-English name -> ("sv", sub_vertical_id) | ("industry", id) | (None, suggestions)."""
    parents = _sv_parent()
    names = {sv: display_name(sv) for sv in parents}
    q = _slug(query or "")
    if not q:
        return None, []
    cands = [q] + [q[: -len(s)] for s in _SUFFIXES if q.endswith(s) and len(q) > len(s) + 1]
    for c in cands:
        if c in parents:
            return "sv", c
        if c in ALIASES:
            return "sv", ALIASES[c]
        if c in ALIAS_NOTES:
            return "sv", ALIAS_NOTES[c][0]
        if c in INDUSTRY_DISPLAY_NAMES:
            return "industry", c
    for sv, name in names.items():
        if _slug(name) == q:
            return "sv", sv
    for ind, name in INDUSTRY_DISPLAY_NAMES.items():
        if _slug(name) == q:
            return "industry", ind
    toks = [t for t in q.split("-") if t]
    hits = [sv for sv, name in names.items()
            if all(t in sv.split("-") or t in _slug(name).split("-") for t in toks)]
    hits.sort(key=lambda s: (s.startswith("other"), len(s)))
    if hits:
        return "sv", hits[0]
    pool = list(parents) + list(ALIASES)
    sugg: list[str] = []
    for m in difflib.get_close_matches(q, pool, n=5, cutoff=0.6):
        sv = ALIASES.get(m, m)
        if sv not in sugg:
            sugg.append(sv)
    if sugg and difflib.SequenceMatcher(None, q, sugg[0]).ratio() >= 0.8:
        return "sv", sugg[0]
    return None, sugg


def published_cells(ds: dict, sv: str) -> dict[str, dict]:
    """{bracket: {metric: {p25,p50,p75,n}}} for cells meeting the dataset's min_cell_n."""
    min_n = int(ds.get("min_cell_n", 10))
    out: dict[str, dict] = {}
    for b, cell in ((ds.get("data") or {}).get(sv) or {}).items():
        if b not in BRACKETS or not isinstance(cell, dict):
            continue
        row = {k: q for k, q in cell.items()
               if k in dict(METRICS) and isinstance(q, dict) and q.get("p50") is not None
               and (q.get("n") or 0) >= min_n}
        if row:
            out[b] = row
    return {b: out[b] for b in BRACKETS if b in out}


def _source_line(ds: dict, url: str = DATA_URL) -> str:
    window = ds.get("source_window") or "-".join(str(y) for y in (ds.get("year_range") or [2018, 2026]))
    return (f"Source: ExitValue.ai analysis of disclosed M&A transactions ({window}) "
            f"from {SOURCE_PHRASE}. Data CC-BY 4.0: {url}")


def norm_metric(m: object) -> str | None:
    """'ev_ebitda' / 'EBITDA' / 'EV/Revenue' -> metric key; None if absent/unknown."""
    if not m:
        return None
    s = _slug(str(m)).replace("-", "_")
    s = s if s.startswith("ev_") else "ev_" + s
    return s if s in dict(METRICS) else None


def _alias_note(query: str, sv: str) -> str | None:
    qs = _slug(query)
    for key, (target, note) in ALIAS_NOTES.items():
        if target == sv and (qs == key or qs.startswith(key + "-")):
            return note
    return None


# ── tools ──────────────────────────────────────────────────────────────────

def list_industries(ds: dict) -> str:
    data = ds.get("data") or {}
    lines = ["Industries covered by ExitValue.ai. Sub-verticals marked * have published multiples in the "
             "open dataset; pass the id in [brackets] to get_valuation_multiples, compare_industries or "
             "get_multiples_trend.", ""]
    for ind, svs in INDUSTRY_TAXONOMY.items():
        subs = [f"{display_name(sv)} [{sv}]" + ("*" if sv in data and published_cells(ds, sv) else "")
                for sv in svs]
        lines.append(f"{INDUSTRY_DISPLAY_NAMES.get(ind, ind)} ({ind}): " + ", ".join(subs))
    lines += ["", cta()]
    return "\n".join(lines)


def _not_published(ds: dict, sv: str) -> list[str]:
    min_n = int(ds.get("min_cell_n", 10))
    ind = _sv_parent().get(sv)
    covered = [s for s in INDUSTRY_TAXONOMY.get(ind, []) if published_cells(ds, s)]
    lines = [f"The open dataset has no {display_name(sv)} cell with at least n={min_n} disclosed deals in any "
             "deal-size bracket, so no median is published here (we do not extrapolate)."]
    if covered:
        lines.append(f"Covered {INDUSTRY_DISPLAY_NAMES.get(ind, ind)} sub-verticals: "
                     + ", ".join(f"{display_name(s)} [{s}]" for s in covered) + ".")
    lines.append(f"The hosted ExitValue.ai connector ({HOSTED_MCP_URL}) also publishes all-deal-size medians "
                 "for more categories, and the free calculator still values these businesses using the closest "
                 "comparable categories.")
    return lines


def get_valuation_multiples(ds: dict, industry: str, size_bracket: str | None = None) -> str:
    query = str(industry or "").strip()[:100]
    bracket = norm_bracket(size_bracket)
    kind, val = resolve(query)
    if kind is None:
        sugg = val or []
        msg = f"No industry matched '{query}'."
        if sugg:
            msg += " Did you mean: " + ", ".join(f"{display_name(s)} [{s}]" for s in sugg) + "?"
        return msg + " Call list_industries for all ids.\n\n" + cta()

    if kind == "industry":
        ind = val
        lines = [f"{INDUSTRY_DISPLAY_NAMES[ind]} - M&A valuation multiples by sub-vertical and deal size "
                 "(median, n = disclosed deals; pass a sub-vertical id for quartiles):"]
        any_rows = False
        for sv in INDUSTRY_TAXONOMY[ind]:
            cells = published_cells(ds, sv)
            if bracket:
                cells = {b: c for b, c in cells.items() if b == bracket}
            if not cells:
                continue
            any_rows = True
            parts = []
            for b, c in cells.items():
                m = "ev_ebitda" if "ev_ebitda" in c else "ev_revenue"
                lab = dict(METRICS)[m]
                parts.append(f"{BRACKETS[b]} EV: {lab} {_x(c[m]['p50'], m)} (n={c[m]['n']})")
            lines.append(f"- {display_name(sv)} [{sv}]: " + "; ".join(parts))
        if not any_rows:
            lines.append(f"No cell in this industry meets the n>={ds.get('min_cell_n', 10)} threshold"
                         + (" for that bracket." if bracket else "."))
        lines += ["", _source_line(ds), "", cta()]
        return "\n".join(lines)

    sv = val
    name = display_name(sv)
    lines = [f"{name} - M&A valuation multiples (ExitValue.ai)"]
    qs = _slug(query)
    for key, (target, note) in ALIAS_NOTES.items():
        if target == sv and (qs == key or qs.startswith(key + "-")):
            lines.append(note)
            break
    data_sv = sv
    cells = published_cells(ds, sv)
    if not cells and sv in PARENT_CATEGORY:
        data_sv, note = PARENT_CATEGORY[sv]
        cells = published_cells(ds, data_sv)
        if cells:
            lines.append(f"Too few deals are tagged {name} on their own; figures below are for {note}.")
    if not cells:
        lines += _not_published(ds, sv)
        lines += ["", cta(sv)]
        return "\n".join(lines)

    want = list(cells)
    if bracket and bracket in cells:
        want = [bracket]
    elif bracket:
        lines.append(f"No published cell for the {BRACKETS[bracket]} enterprise-value bracket "
                     f"(needs n>={ds.get('min_cell_n', 10)} disclosed deals); showing what is published.")
    lines.append(f"By deal size (enterprise value), disclosed deals {ds.get('source_window', '2018-2026')}:")
    for b in want:
        parts = [f"{lab} {_fmt_q(cells[b][k], k)}" for k, lab in METRICS if k in cells[b]]
        lines.append(f"- {BRACKETS[b]} EV: " + "; ".join(parts))
    lines.append("These are population medians; a specific business's multiple depends on its margins, "
                 "growth, customer concentration and owner dependence.")
    lines += [_source_line(ds), "", cta(sv)]
    return "\n".join(lines)


def compare_industries(ds: dict, industries: list[str] | str, size_bracket: str | None = None,
                       metric: str | None = None) -> str:
    """2-6 industries side by side: median/IQR/n of one metric per EV bracket (or one bracket)."""
    raw = industries.split(",") if isinstance(industries, str) else list(industries or [])
    queries = [str(q).strip()[:100] for q in raw if str(q).strip()]
    bracket = norm_bracket(size_bracket)
    m = norm_metric(metric) or "ev_ebitda"
    lab = dict(METRICS)[m]
    min_n = int(ds.get("min_cell_n", 10))
    if not 2 <= len(queries) <= MAX_COMPARE:
        return (f"compare_industries needs between 2 and {MAX_COMPARE} industries (got {len(queries)}). "
                "For a single industry use get_valuation_multiples.\n\n" + cta())
    scope = f"{BRACKETS[bracket]} enterprise value" if bracket else "by enterprise-value bracket"
    lines = [f"{lab} multiples compared ({scope}, disclosed deals {ds.get('source_window', '2018-2026')}) "
             "- ExitValue.ai"]
    if metric and norm_metric(metric) is None:
        lines.append(f"Unknown metric '{str(metric)[:30]}'; showing EV/EBITDA (use ev_ebitda or ev_revenue).")
    seen: set[str] = set()
    any_data = other_hint = False
    alt = "ev_revenue" if m == "ev_ebitda" else "ev_ebitda"
    for q in queries:
        kind, val = resolve(q)
        if kind is None:
            sugg = val or []
            lines.append(f"- '{q}': no industry matched" + (
                " (did you mean " + ", ".join(f"{display_name(s)} [{s}]" for s in sugg) + "?)" if sugg else ""))
            continue
        if kind == "industry":
            lines.append(f"- {INDUSTRY_DISPLAY_NAMES[val]} ({val}): this is an industry group, not a "
                         "sub-vertical; pass a sub-vertical id (see list_industries or get_valuation_multiples).")
            continue
        sv = val
        if sv in seen:
            lines.append(f"- '{q}': same category as {display_name(sv)} [{sv}] above")
            continue
        seen.add(sv)
        name = display_name(sv)
        note = _alias_note(q, sv)
        cells = published_cells(ds, sv)
        if not cells and sv in PARENT_CATEGORY:
            p_sv, p_note = PARENT_CATEGORY[sv]
            if published_cells(ds, p_sv):
                cells = published_cells(ds, p_sv)
                note = f"too few deals tagged {name} on their own; figures are for {p_note}"
        if bracket:
            cells = {b: c for b, c in cells.items() if b == bracket}
        suffix = f" [{note.replace('figures below are', 'figures are').rstrip('.')}]" if note else ""
        parts = [f"{BRACKETS[b]} EV: {_fmt_q(c[m], m)}" for b, c in cells.items() if m in c]
        if not parts:
            if any(alt in c for c in cells.values()):
                other_hint = True
            where = f"in the {BRACKETS[bracket]} bracket" if bracket else "in any deal-size bracket"
            lines.append(f"- {name} [{sv}]: INSUFFICIENT DATA - fewer than {min_n} disclosed deals with {lab} "
                         f"{where}, so no median is published{suffix}")
            continue
        any_data = True
        lines.append(f"- {name} [{sv}]: " + "; ".join(parts) + suffix)
    if other_hint:
        lines.append(f"Some rows have no {lab} median but do have {dict(METRICS)[alt]}; call again with "
                     f"metric={alt}.")
    if any_data:
        lines.append("These are population medians; a specific business's multiple depends on its margins, "
                     "growth, customer concentration and owner dependence.")
        lines.append(_source_line(ds))
    lines += ["", cta()]
    return "\n".join(lines)


def _trend_cells(ty: dict, sv: str, metrics: list[str]) -> dict[str, dict]:
    min_n = int(ty.get("min_n_per_cell", 10))
    out: dict[str, dict] = {}
    for yr, cell in sorted(((ty.get("data") or {}).get(sv) or {}).items()):
        if not isinstance(cell, dict):
            continue
        row = {k: cell[k] for k in metrics
               if isinstance(cell.get(k), dict) and cell[k].get("p50") is not None and (cell[k].get("n") or 0) >= min_n}
        if row:
            if cell.get("median_deal_value_m") is not None:
                row["median_deal_value_m"] = cell["median_deal_value_m"]
            out[str(yr)] = row
    return out


def get_multiples_trend(ty: dict, industry: str, metric: str | None = None) -> str:
    """Year-by-year medians for one sub-vertical from multiples-by-year.json; gaps reported, never filled."""
    query = str(industry or "").strip()[:100]
    m = norm_metric(metric)
    metrics = [m] if m else [k for k, _ in METRICS]
    labels = dict(METRICS)
    min_n = int(ty.get("min_n_per_cell", 10))
    y0, y1 = (ty.get("year_range") or [2018, 2026])[:2]
    kind, val = resolve(query)
    if kind is None:
        sugg = val or []
        msg = f"No industry matched '{query}'."
        if sugg:
            msg += " Did you mean: " + ", ".join(f"{display_name(s)} [{s}]" for s in sugg) + "?"
        return msg + " Call list_industries for all ids.\n\n" + cta()
    if kind == "industry":
        have = [sv for sv in INDUSTRY_TAXONOMY[val] if _trend_cells(ty, sv, metrics)]
        return "\n".join([
            f"{INDUSTRY_DISPLAY_NAMES[val]} is an industry group; year-by-year trends are published per "
            "sub-vertical. Pass one of these ids:",
            ", ".join(f"{display_name(s)} [{s}]" for s in have) if have else
            f"(no sub-vertical in this industry has a year with n>={min_n} disclosed deals)",
            "", cta()])
    sv = val
    name = display_name(sv)
    lines = [f"{name} - M&A valuation multiples by deal year (ExitValue.ai)"]
    note = _alias_note(query, sv)
    if note:
        lines.append(note)
    cells = _trend_cells(ty, sv, metrics)
    if not cells and sv in PARENT_CATEGORY:
        p_sv, p_note = PARENT_CATEGORY[sv]
        if _trend_cells(ty, p_sv, metrics):
            cells = _trend_cells(ty, p_sv, metrics)
            lines.append(f"Too few deals are tagged {name} on their own; figures below are for {p_note}.")
    mlabel = labels[m] if m else "EV/EBITDA or EV/Revenue"
    if not cells:
        lines.append(f"The open dataset has no {name} year with at least n={min_n} disclosed deals ({y0}-{y1}), "
                     f"so no year-by-year {mlabel} median is published (we do not extrapolate). "
                     "get_valuation_multiples may still have pooled multi-year figures.")
        return "\n".join(lines + ["", cta(sv)])
    lines.append(f"Median by year the deal was announced (only years with n>={min_n} disclosed deals for a metric):")
    years = [str(y) for y in range(int(y0), int(y1) + 1)]
    for yr in years:
        if yr not in cells:
            continue
        c = cells[yr]
        dv = f" (median deal value ${c['median_deal_value_m']:,.0f}M)" if c.get("median_deal_value_m") else ""
        lines.append(f"- {yr}{dv}: " + "; ".join(f"{labels[k]} {_fmt_q(c[k], k)}" for k in metrics if k in c))
    for k in metrics:
        missing = [y for y in years if k not in cells.get(y, {})]
        if len(missing) == len(years):
            lines.append(f"No year has {min_n}+ disclosed deals with {labels[k]}, so no {labels[k]} trend is "
                         "published.")
        elif missing:
            lines.append(f"No published {labels[k]} median for {', '.join(missing)} (fewer than {min_n} disclosed "
                         "deals that year); gaps are left empty, not estimated.")
    lines.append("Year-to-year moves partly reflect which deals (and deal sizes) were disclosed each year, not "
                 "only market pricing.")
    lines += [_source_line(ty, TREND_URL), "", cta(sv)]
    return "\n".join(lines)


__all__ = ["Dataset", "list_industries", "get_valuation_multiples", "compare_industries",
           "get_multiples_trend", "resolve", "published_cells", "calculator_url", "BRACKETS", "METRICS",
           "DATA_URL", "TREND_URL"]

