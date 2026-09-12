# macrobot

An MCP server that gives Claude access to FRED (Federal Reserve Economic Data) —
roughly 800,000 US economic time series including Treasury yields, CPI,
unemployment, and home prices.

With this running, you can ask Claude questions like *"what's the Case-Shiller
index done over the last two years?"* and it fetches and reasons over the real
numbers instead of answering from memory.

## Tools

| Tool | What it does |
|---|---|
| `search_fred_series` | Find series by keyword. Returns ID, title, units, frequency, seasonal adjustment, popularity, and date range. |
| `get_fred_series_info` | Metadata for one series — units, frequency, seasonal adjustment, last updated, notes. |
| `get_fred_observations` | The actual data points for a series over a date range. |

## Setup

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and a free
[FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html).

```bash
git clone https://github.com/officialvenkatesh/macrobot.git
cd macrobot
uv sync
```

Create a `.env` file in the project root:

```
FRED_API_KEY=your_key_here
```

## Running

Test the tools interactively with the MCP Inspector:

```bash
uv run mcp dev src/macrobot/server.py
```

To use it in Claude Desktop, add this to `claude_desktop_config.json`
(Settings → Developer → Edit Config), then fully restart the app:

```json
{
  "mcpServers": {
    "macrobot": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/macrobot",
        "run",
        "python",
        "src/macrobot/server.py"
      ]
    }
  }
}
```

## Layout

```
src/macrobot/
├── fred_client.py   # HTTP layer — talks to the FRED API
└── server.py        # MCP layer — declares tools and their descriptions
```

The split is deliberate: `fred_client.py` can be tested standalone without the
MCP machinery running, which makes debugging much easier.

## Design notes

**Tool descriptions are the interface.** The model sees only each tool's
docstring and type hints — nothing else. Two descriptions here earn their place:

- `search_fred_series` explicitly says to search before fetching, because
  models will otherwise invent plausible-looking series IDs (`US10YR`) that
  don't exist and fail with an unhelpful 400.
- Search results include seasonal adjustment (SA/NSA) because FRED has many
  pairs of series with *identical* titles that differ only in adjustment —
  `CSUSHPISA` and `CSUSHPINSA`, for example. Without that field the model
  can't tell them apart.

**Errors return as strings, not exceptions.** A raised exception gives the model
a generic failure. Returning `"Error: No series found with ID 'US10YR'"` lets it
read what went wrong and recover by searching instead.

**Responses are trimmed.** FRED returns verbose JSON; each function keeps only
the fields that matter. Every returned field becomes tokens in the model's
context, so passing raw API responses through is expensive and noisy.

## Known limitations

- Search ranks by popularity, which buries niche series. Searching
  "house price index" returns general CPI first.
- FRED's search is literal keyword matching, not semantic — conversational
  phrasing ("cost of living") matches poorly.