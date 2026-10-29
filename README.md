# exitvalue-mcp

An MCP (Model Context Protocol) server that answers **"what multiple do businesses in industry X sell for?"** with real M&A data: median, 25th and 75th percentile **EV/EBITDA** and **EV/Revenue** multiples, by industry and deal size, from disclosed transactions (2018-2026).

- Free, open source (MIT), **no API key, no telemetry**.
- Data: the open [ExitValue.ai multiples dataset](https://exitvalue.ai/data/multiples.json) (CC-BY 4.0), fetched once and cached in memory for an hour.
- Honest by design: every figure comes with its deal count (`n`); cells with fewer than the dataset's `min_cell_n` (10) disclosed deals are withheld, never extrapolated.
- Works with Claude Desktop, Claude Code, Cursor, Windsurf, VS Code and any other MCP client (stdio transport).

> Don't want to install anything? Use the **hosted connector**: `https://exitvalue.ai/api/mcp` (Streamable HTTP, no auth). Setup guide: <https://exitvalue.ai/ai-connector>. It is also in the official MCP Registry as `ai.exitvalue/ma-multiples`.

## Tools

| Tool | What it does |
|---|---|
| `list_industries` | Lists industries and sub-vertical ids (dental practice, HVAC, SaaS, trucking, ...), marking which have published multiples. |
| `get_valuation_multiples` | `industry` (id or plain English: "dentist", "med spa", "plumber", "MSP") and optional `size_bracket` (`under_5m_ev`, `5m_25m_ev`, `25m_100m_ev`, `100m_500m_ev`, `over_500m_ev`). Returns medians + interquartile range with `n` per enterprise-value bracket. |

## Example

**Question:** "What multiple do dental practices sell for?"

**`get_valuation_multiples({"industry": "dental practice"})`** (real output, dataset of 2026-10-29):

```text
Dental Practice - M&A valuation multiples (ExitValue.ai)
By deal size (enterprise value), disclosed deals 2018-2026:
- $5M-$25M EV: EV/EBITDA median 7.0x (middle 50%: 6.5x-8.3x), n=10
- $100M-$500M EV: EV/EBITDA median 11.9x (middle 50%: 11.2x-14.3x), n=14
- $500M and up EV: EV/EBITDA median 14.0x (middle 50%: 11.9x-15.8x), n=17; EV/Revenue median 2.65x (middle 50%: 2.11x-6.18x), n=10
These are population medians; a specific business's multiple depends on its margins, growth, customer concentration and owner dependence.
Source: ExitValue.ai analysis of disclosed M&A transactions (2018-2026) from a licensed historical M&A database, SEC EDGAR filings and verified press releases. Data CC-BY 4.0: https://exitvalue.ai/data/multiples.json

Get a free, business-specific valuation range (adjusted for your margins, growth and owner dependence) in about 2 minutes: https://exitvalue.ai/valuate?src=mcp-oss&industry=dental-practice

```

Plain-English names are mapped to the closest category and say so (e.g. "plumber" uses HVAC, "MSP" uses IT services, "med spa" uses other healthcare). When a category has no cell with enough deals, the tool says that rather than guessing.

## Install

### uvx (no install step)

```bash
uvx --from git+https://github.com/nickcals/exitvalue-mcp exitvalue-mcp
```

### pip

```bash
pip install git+https://github.com/nickcals/exitvalue-mcp
exitvalue-mcp
```

Requires Python 3.10+. Works with the `mcp` Python SDK 1.x and 2.x.

## Client configuration

### Claude Desktop

`claude_desktop_config.json` (Settings -> Developer -> Edit Config):

```json
{
  "mcpServers": {
    "exitvalue": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/nickcals/exitvalue-mcp", "exitvalue-mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project):

```json
{
  "mcpServers": {
    "exitvalue": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/nickcals/exitvalue-mcp", "exitvalue-mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add exitvalue -- uvx --from git+https://github.com/nickcals/exitvalue-mcp exitvalue-mcp
```

### Zero-install: hosted server

Any client that supports remote MCP servers can skip the local install and point at the hosted endpoint:

```json
{
  "mcpServers": {
    "exitvalue": { "url": "https://exitvalue.ai/api/mcp" }
  }
}
```

In Claude (web/desktop) add it under Settings -> Connectors -> Add custom connector with the URL `https://exitvalue.ai/api/mcp`. Step-by-step instructions for ChatGPT, Claude, Cursor and others: <https://exitvalue.ai/ai-connector>.

## Development

```bash
git clone https://github.com/nickcals/exitvalue-mcp && cd exitvalue-mcp
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest
npx @modelcontextprotocol/inspector exitvalue-mcp   # optional: poke at it in the MCP Inspector
```

`EXITVALUE_DATA_URL` overrides the dataset URL (e.g. to point at a mirror).

## Data and license

- Code: MIT (see [LICENSE](LICENSE)).
- Data: [exitvalue.ai/data/multiples.json](https://exitvalue.ai/data/multiples.json), **CC-BY 4.0**. Aggregate medians/quartiles of disclosed M&A multiples by sub-vertical and enterprise-value bracket, built from a licensed historical M&A database, SEC EDGAR filings and verified press releases; cells need n >= 10 per metric and outliers are excluded. Please cite <https://exitvalue.ai> if you use it. Also mirrored, with a datapackage and citation file, at [github.com/nickcals/multiples](https://github.com/nickcals/multiples).

These are population medians, not a valuation of any particular business. For a business-specific range (adjusted for margins, growth, customer concentration and owner dependence), try the free calculator at <https://exitvalue.ai/valuate?src=mcp-oss>.
