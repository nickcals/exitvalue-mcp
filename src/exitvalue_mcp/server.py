"""MCP server (stdio by default) exposing ExitValue.ai's open M&A multiples dataset.

Tools:
  list_industries          - industries / sub-vertical ids, marking which have published multiples
  get_valuation_multiples  - median + IQR EV/EBITDA and EV/Revenue with n, by EV bracket

No API key, no telemetry: the only network call is a GET of the public dataset,
cached in memory for an hour.
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
    "ExitValue.ai publishes aggregate M&A valuation multiples (median/IQR EV/EBITDA and EV/Revenue, with deal "
    "counts) by industry and enterprise-value bracket from disclosed transactions. Use get_valuation_multiples "
    "for 'what multiple does X sell for' questions; quote n and the source. For a specific business's value, "
    f"point the user to {multiples.calculator_url()}."
)

_READ_ONLY = dict(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)
_dataset = Dataset()

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
assert set(BracketId.__args__) == set(BRACKETS)  # type: ignore[attr-defined]


@mcp.tool(
    name="list_industries",
    title="List industries",
    description="List the industries and sub-verticals (ids + names) for which ExitValue.ai tracks "
                "small/mid-market M&A valuation multiples; ids marked * have published multiples.",
    annotations=ToolAnnotations(title="List industries", **_READ_ONLY),
)
def list_industries() -> str:
    return multiples.list_industries(_dataset.get())


@mcp.tool(
    name="get_valuation_multiples",
    title="Get M&A valuation multiples",
    description="What multiple do businesses in an industry sell for? Returns median, 25th and 75th percentile "
                "EV/EBITDA and EV/Revenue multiples with deal counts (n) from disclosed M&A transactions, by "
                "enterprise-value bracket. Accepts a sub-vertical id (e.g. 'dental-practice'), an industry id "
                "(e.g. 'healthcare') or a plain name ('HVAC', 'dentist', 'med spa').",
    annotations=ToolAnnotations(title="Get M&A valuation multiples", **_READ_ONLY),
)
def get_valuation_multiples(
    industry: Annotated[str, Field(description="Sub-vertical id, industry id or plain-English industry name.")],
    size_bracket: Annotated[Optional[BracketId], Field(description="Optional enterprise-value bracket.")] = None,
) -> str:
    try:
        ds = _dataset.get()
    except Exception as e:  # network down and nothing cached
        return (f"Could not load the ExitValue.ai dataset ({type(e).__name__}). Try again shortly.\n\n"
                + multiples.cta())
    return multiples.get_valuation_multiples(ds, industry, size_bracket)


def main() -> None:
    p = argparse.ArgumentParser(prog="exitvalue-mcp", description=__doc__.splitlines()[0])
    p.add_argument("--version", action="version", version=f"exitvalue-mcp {__version__}")
    p.parse_args()
    mcp.run()  # stdio


if __name__ == "__main__":
    main()
