// Test-only structured extraction fixture. It is not an interpretation quality test.
import { createServer } from "node:http";
export function fixtureProvider() {
  return createServer(async (req, res) => {
    let raw = "";
    for await (const chunk of req) raw += chunk;
    try {
      const b = JSON.parse(raw);
      if (
        !b.messages.every(
          (m) => !Array.isArray(m) && typeof m.content === "string",
        )
      )
        throw Error("message");
      const ctx = JSON.parse(b.messages.at(-1).content);
      let output = { question: "Ready", changes: [] };
      if (ctx.fact_contract) {
        await new Promise(resolve=>setTimeout(resolve,1200));
        const facts = [];
        const first = ctx.sources.find(s=>s.data.text.includes("typically invokes")) || ctx.sources[0],
          last = ctx.sources.find(s=>s.data.text.includes("30 requests per minute")) || first;
        const detailed = last.data.text.includes("30 requests per minute");
        const add = (
          concept,
          value,
          unit = "",
          period_value = "",
          period_unit = "",
          source = first,
          status = "reported",
        ) =>
          facts.push({
            activity: "Disruption case agent",
            concept,
            value,
            unit,
            period_value,
            period_unit,
            status,
            source_id: source.id,
            quote: source.data.text,
          });
        add("actions", "yes");
        add("calls_typical", "4", "call");
        add("calls_upper", "12", "call");
        if (detailed) {
          for (const [key, value] of [
            ["compute_location", "local"],
            ["search", "no"],
            ["model", "dense8b"],
            ["demand_basis", "measured_peak"],
            ["call_envelope", "upper"],
          ])
            add(key, value, "", "", "", last, "assumed");
          add("requests", "30", "request", "1", "min", last);
          add("input_tokens", "2000", "token", "", "", last, "assumed");
          add("output_tokens", "500", "token", "", "", last, "assumed");
        }
        output = { facts };
      }
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          id: "local-test",
          usage: { prompt_tokens: 100, completion_tokens: 200 },
          choices: [
            {
              finish_reason: "stop",
              message: { content: JSON.stringify(output) },
            },
          ],
        }),
      );
    } catch {
      res.writeHead(400);
      res.end("{}");
    }
  });
}
