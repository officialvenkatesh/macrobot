from mcp.server.mcpserver import MCPServer
from macrobot import fred_client

mcp  = MCPServer("macrobot")

@mcp.tool()
async def search_fred_series(query: str, limit: int = 10) -> str:
    """Search FRED for economic data series by keyword.

    Use this FIRST when you don't have an exact FRED series ID. Series IDs are
    short codes like DGS10 or CPIAUCSL. Guessing an ID will fail - search instead.

    FRED matches literal keywords against series titles and notes. Use official
    economic terminology ("consumer price index", "civilian unemployment rate")
    rather than conversational phrasing ("cost of living", "how many people
    are out of work").

    Results include seasonal adjustment (SA/NSA) and a popularity score. When
    two series have the same title, they usually differ by seasonal adjustment
    or vintage - check which one the question actually needs.

    Args:
        query: Keywords describing the data, e.g. "unemployment rate" or
            "10 year treasury yield".
        limit: How many results to return. Default 10.
    """
    results = await fred_client.search_series(query, limit)
    if not results:
        return f"No series found for '{query}'. Try broader keywords."

    lines = [
        f"{r['id']} | {r['title']} | {r['units']} | {r['frequency']} | "
        f"{r['seasonal_adjustment']} | popularity {r['popularity']} | "
        f"{r['start']} to {r['end']}"
        for r in results
    ]
    return "\n".join(lines)

@mcp.tool()
async def get_fred_series_info(series_id: str) -> str:
    """Get metadata for a FRED series: units, frequency, date range, and notes.

    Use this before fetching observations when you need to know what the numbers
    mean - especially units (percent vs index vs dollars) and whether the series
    is seasonally adjusted.

    Args:
        series_id: Exact FRED series ID, e.g. "DGS10". Case sensitive.
    """
    try:
        info = await fred_client.get_series_info(series_id)
    except fred_client.FredError as e:
        return f"Error: {e}"

    return (
        f"ID: {info['id']}\n"
        f"Title: {info['title']}\n"
        f"Units: {info['units']}\n"
        f"Frequency: {info['frequency']}\n"
        f"Seasonal adjustment: {info['seasonal_adjustment']}\n"
        f"Range: {info['start']} to {info['end']}\n"
        f"Last updated: {info['last_updated']}\n"
        f"Notes: {info['notes']}"
    )

@mcp.tool()
async def get_fred_observations(
    series_id: str,
    start: str | None = None,
    end: str | None = None,
    limit: int = 100,
) -> str:
    """Fetch the actual data points for a FRED series.

    Requires an exact series ID - use search_fred_series first if you don't have one.

    Args:
        series_id: Exact FRED series ID, e.g. "DGS10".
        start: Earliest date, YYYY-MM-DD. Omit for the full history.
        end: Latest date, YYYY-MM-DD. Omit for the most recent data.
        limit: Max observations to return. Default 100. Keep this small for
            daily series over long ranges, or the output will be huge.
    """
    try:
        obs = await fred_client.get_observations(series_id, start, end, limit)
    except fred_client.FredError as e:
        return f"Error: {e}"

    if not obs:
        return f"No observations for {series_id} in that range."

    lines = [f"{o['date']}  {o['value']}" for o in obs]
    return f"{series_id} ({len(obs)} observations)\n" + "\n".join(lines)


if __name__ == "__main__":
    mcp.run()