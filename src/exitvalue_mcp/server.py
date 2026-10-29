"""MCP server (stdio by default) exposing ExitValue.ai's open M&A multiples dataset.

Tools (all read-only):
  list_industries          - industries / sub-vertical ids, marking which have published multiples
  get_valuation_multiples  - median + IQR EV/EBITDA and EV/Revenue with n, by EV bracket
  compare_industries       - 2-6 industries side by side for one metric
  get_multiples_trend      - year-by-year medians with n for one sub-vertical

No API key, no telemetry: the only network calls are GETs of the two public dataset
files, each cached in memory for an hour.
"""

from __future__ import annotations

import argparse
from typing import Annotated, Literal, Optional

from pydantic import Field

try:  # mcp >= 2: FastMCP was renamed MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import __version__, multiples
from .multiples import BRACKETS, Dataset

INSTRUCTIONS = (
    "ExitValue.ai publishes aggregate M&A valuation multiples (median and middle-50% EV/EBITDA and EV/Revenue, "
    "always with deal count n) by industry, enterprise-value bracket and deal year, from disclosed transactions. "
    "All tools are read-only. get_valuation_multiples: 'what multiple does X sell for' (one industry, by deal "
    "size). compare_industries: 2-6 industries side by side. get_multiples_trend: year-by-year history for one "
    "industry. list_industries: valid ids. Quote n and the source line; cells below the dataset's threshold are "
    f"withheld, never estimated. For a specific business's value, point the user to {multiples.calculator_url()}."
)

# openWorldHint=False: every tool reads one fixed, published dataset (no open-ended external interaction).
_READ_ONLY = dict(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
_dataset = Dataset()
_trend = Dataset(fetch=lambda: multiples._fetch_url(multiples.TREND_URL))

_kw = dict(instructions=INSTRUCTIONS, website_url=multiples.CONNECTOR_URL)
try:  # mcp >= 2
    mcp = FastMCP("exitvalue-mcp", title="ExitValue.ai M&A Multiples", version=__version__, **_kw)
except TypeError:  # mcp 1.x
    mcp = FastMCP("exitvalue-mcp", **_kw)
    try:
        mcp._mcp_server.version = __version__
    except AttributeError:
        pass

BracketId = Literal["under_5m_ev", "5m_25m_ev", "25m_100m_ev", "100m_500m_ev", "over_500m_ev"]
MetricId = Literal["ev_ebitda", "ev_revenue"]
assert set(BracketId.__args__) == set(BRACKETS)  # type: ignore[attr-defined]
assert set(MetricId.__args__) == {k for k, _ in multiples.METRICS}  # type: ignore[attr-defined]

INDUSTRY_DESC = ("Sub-vertical id from list_industries (e.g. 'hvac', 'dental-practice'), or a plain-English name "
                 "('HVAC', 'dentist', 'plumber', 'MSP'); plain names are mapped to the closest tracked category "
                 "and the answer says which one was used.")
BRACKET_DESC = ("Optional enterprise-value (deal size) bracket: under_5m_ev = under $5M, 5m_25m_ev = $5M-$25M, "
                "25m_100m_ev = $25M-$100M, 100m_500m_ev = $100M-$500M, over_500m_ev = $500M and up.")
METRIC_DESC = ("Multiple to use: ev_ebitda (enterprise value / EBITDA) or ev_revenue (enterprise value / "
               "revenue).")


def _load_error(e: Exception) -> str:
    return f"Could not load the ExitValue.ai dataset ({type(e).__name__}). Try again shortly.\n\n" + multiples.cta()


@mcp.tool(
    name="list_industries",
    title="List industries",
    description="Read-only. Lists every industry and sub-vertical ExitValue.ai tracks, with ids and display names; "
                "ids marked * have published multiples in the open dataset. Takes no input. Use it first when "
                "you are unsure of an id; the other tools accept these ids or plain-English names.",
    annotations=ToolAnnotations(title="List industries", **_READ_ONLY),
)
def list_industries() -> str:
    try:
        return multiples.list_industries(_dataset.get())
    except Exception as e:  # network down and nothing cached
        return _load_error(e)


@mcp.tool(
    name="get_valuation_multiples",
    title="Get M&A valuation multiples",
    description="Read-only. Answers 'what multiple does a business in industry X sell for?' for ONE industry. "
                "Returns median EV/EBITDA and EV/Revenue multiples with the middle 50% (25th-75th percentile) and "
                "deal count n for each enterprise-value bracket (disclosed deals 2018-2026). Cells with fewer "
                "than 10 deals are withheld, never estimated. Passing an industry group id (e.g. 'healthcare') "
                "returns a median per sub-vertical. Use compare_industries to put several industries side by "
                "side and get_multiples_trend for year-by-year history. Population medians only: it does not "
                "value a specific business.",
    annotations=ToolAnnotations(title="Get M&A valuation multiples", **_READ_ONLY),
)
def get_valuation_multiples(
    industry: Annotated[str, Field(description=INDUSTRY_DESC + " An industry group id such as 'healthcare' or "
                                               "'home-services' is also accepted.")],
    size_bracket: Annotated[Optional[BracketId], Field(description=BRACKET_DESC + " Omit for every "
                                                                   "published bracket.")] = None,
) -> str:
    try:
        ds = _dataset.get()
    except Exception as e:  # network down and nothing cached
        return _load_error(e)
    return multiples.get_valuation_multiples(ds, industry, size_bracket)


@mcp.tool(
    name="compare_industries",
    title="Compare industries' M&A multiples",
    description="Read-only. Puts 2-6 industries side by side for one metric: median multiple, middle 50% "
                "(25th-75th percentile) and deal count n per enterprise-value bracket, using the same data, name "
                "matching and n>=10 threshold as get_valuation_multiples. Pass size_bracket to compare a single "
                "deal-size bracket. Industries without enough deals are marked INSUFFICIENT DATA rather than "
                "estimated; unmatched names and industry-group ids are flagged per row. Use it for 'which sells "
                "for more, X or Y?' questions; use get_valuation_multiples for one industry's full breakdown.",
    annotations=ToolAnnotations(title="Compare industries' M&A multiples", **_READ_ONLY),
)
def compare_industries(
    # bounds advertised in the schema but checked in compare_industries(), so an out-of-range call still
    # gets a plain-English answer ending with the calculator link instead of a validation error
    industries: Annotated[list[str], Field(json_schema_extra={"minItems": 2, "maxItems": multiples.MAX_COMPARE},
                                           description="2 to 6 sub-vertical ids or plain-English industry names to "
                                                       "compare, e.g. ['dental-practice', 'veterinary-practice', "
                                                       "'physical therapy']. " + INDUSTRY_DESC)],
    size_bracket: Annotated[Optional[BracketId], Field(description=BRACKET_DESC + " Omit to show every "
                                                                   "published bracket per industry.")] = None,
    metric: Annotated[MetricId, Field(description=METRIC_DESC + " Default ev_ebitda.")] = "ev_ebitda",
) -> str:
    try:
        ds = _dataset.get()
    except Exception as e:
        return _load_error(e)
    return multiples.compare_industries(ds, industries, size_bracket, metric)


@mcp.tool(
    name="get_multiples_trend",
    title="Get M&A multiples trend by year",
    description="Read-only. Year-by-year history for ONE sub-vertical: for each deal year 2018-2026, the median "
                "EV/EBITDA and/or EV/Revenue multiple with middle 50% (25th-75th percentile), deal count n and "
                "median deal value, from the open per-year dataset. Only years with at least 10 disclosed deals "
                "for a metric are shown; missing years are listed as gaps and never interpolated, so many "
                "sub-verticals have few or no years. Use it for 'are multiples rising or falling for X?' "
                "questions; use get_valuation_multiples for pooled figures by deal size.",
    annotations=ToolAnnotations(title="Get M&A multiples trend by year", **_READ_ONLY),
)
def get_multiples_trend(
    industry: Annotated[str, Field(description=INDUSTRY_DESC)],
    metric: Annotated[Optional[MetricId], Field(description="Optional. " + METRIC_DESC +
                                                " Omit to show both where published.")] = None,
) -> str:
    try:
        ty = _trend.get()
    except Exception as e:
        return _load_error(e)
    return multiples.get_multiples_trend(ty, industry, metric)


def main() -> None:
    p = argparse.ArgumentParser(prog="exitvalue-mcp", description=__doc__.splitlines()[0])
    p.add_argument("--version", action="version", version=f"exitvalue-mcp {__version__}")
    p.parse_args()
    mcp.run()  # stdio


if __name__ == "__main__":
    main()
