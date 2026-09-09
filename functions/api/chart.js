function jsonError(message, status) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    },
  });
}

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const symbol = url.searchParams.get("symbol") || "";
  const range = url.searchParams.get("range") || "1y";
  const interval = url.searchParams.get("interval") || "1d";

  if (!/^[A-Za-z0-9^=./-]{1,20}$/.test(symbol)) {
    return jsonError("Symbole invalide", 400);
  }

  const target = new URL(
    `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}`,
  );
  target.searchParams.set("range", range);
  target.searchParams.set("interval", interval);
  target.searchParams.set("events", "history");

  try {
    const response = await fetch(target, {
      headers: { "User-Agent": "TDSequentialMonitor/1.0" },
    });
    const body = await response.text();
    if (!response.ok) {
      return jsonError(`Yahoo Finance: ${response.status}`, 502);
    }
    return new Response(body, {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return jsonError(`Yahoo Finance: ${error.message}`, 502);
  }
}
