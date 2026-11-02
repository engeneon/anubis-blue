/** Thin stdio MCP bridge. Arithmetic and authorization stay in the Anubis API.
 * Protocol baseline: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
 */
import { createInterface } from "node:readline";
import { randomUUID } from "node:crypto";
const base = new URL(process.env.ANUBIS_URL || "http://127.0.0.1:8787");
if (
  !["127.0.0.1", "localhost"].includes(base.hostname) ||
  base.protocol !== "http:"
)
  throw new Error("Only a configured loopback Anubis API is supported");
const token = process.env.ANUBIS_AGENT_TOKEN;
if (!token)
  throw new Error("Set ANUBIS_AGENT_TOKEN to a scoped agent identity");
const idField = { type: "string", pattern: "^[a-z_]+_[a-f0-9]{32}$" };
const definition = (name, description, properties, required) => ({
  name,
  description,
  inputSchema: {
    type: "object",
    properties,
    required,
    additionalProperties: false,
  },
});
const tools = [
  definition(
    "read_copilot_context",
    "Read authorized case architecture context without modifying inputs.",
    { case_id: idField },
    ["case_id"],
  ),
  definition(
    "read_copilot_session",
    "Read accepted inputs and revision for a permitted assistant session.",
    { session_id: idField },
    ["session_id"],
  ),
  definition(
    "read_copilot_facts",
    "Read engine-owned result facts. Never substitute model arithmetic.",
    { result_id: idField },
    ["result_id"],
  ),
  definition(
    "propose_workload_inputs",
    "Propose structured facts using the schema in read_copilot_context. Legacy allowlisted changes remain compatible. Human review and the case proposal budget are mandatory. No acceptance tool is exposed.",
    { session_id: idField, proposal: { type: "object" } },
    ["session_id", "proposal"],
  ),
  definition(
    "get_capabilities",
    "Read declared description, modelling and evidence coverage.",
    {},
    [],
  ),
  definition(
    "read_result",
    "Read an authorized immutable result; includes facts and provenance.",
    { result_id: idField },
    ["result_id"],
  ),
  definition(
    "read_job",
    "Read asynchronous compilation state.",
    { job_id: idField },
    ["job_id"],
  ),
  definition(
    "compile_revision",
    "Compile an existing frozen revision within the case agent budget. Does not change assumptions.",
    { revision_id: idField, activation_id: idField },
    ["revision_id"],
  ),
  definition(
    "propose_observations",
    "Submit unaccepted agent assumptions for human review within the case proposal budget. Does not change the draft.",
    {
      draft_id: idField,
      rows: {
        type: "array",
        minItems: 1,
        maxItems: 100,
        items: {
          type: "object",
          required: ["stage_id", "field", "observation"],
          properties: {
            stage_id: { type: "string" },
            field: { type: "string" },
            observation: { type: "object" },
          },
          additionalProperties: false,
        },
      },
    },
    ["draft_id", "rows"],
  ),
  definition(
    "compare_results",
    "Compare existing immutable results without attributing combined changes to one cause.",
    { left_id: idField, right_id: idField },
    ["left_id", "right_id"],
  ),
];
let initialized = false,
  ready = false;
async function call(name, args) {
  const tool = tools.find((t) => t.name === name);
  if (!tool) throw new Error("Unknown tool");
  if (!args || typeof args !== "object" || Array.isArray(args))
    throw new Error("Arguments must be an object");
  for (const k of Object.keys(args)) {
    if (!(k in tool.inputSchema.properties))
      throw new Error("Unknown argument");
    if (k === "proposal") {
      if (!args[k] || typeof args[k] !== "object" || Array.isArray(args[k]))
        throw new Error("Expected proposal object");
      continue;
    }
    if (k === "rows") {
      if (!Array.isArray(args[k]) || args[k].length > 100)
        throw new Error("Invalid proposal rows");
      continue;
    }
    if (!/^[a-z_]+_[a-f0-9]{32}$/.test(args[k]))
      throw new Error("Invalid record identifier");
  }
  for (const k of tool.inputSchema.required)
    if (!(k in args)) throw new Error("Missing argument " + k);
  let path,
    method = "GET",
    body;
  if (name === "read_copilot_context") path = "copilot-context/" + args.case_id;
  if (name === "read_copilot_session")
    path = "copilot-sessions/" + args.session_id;
  if (name === "read_copilot_facts") path = "copilot-facts/" + args.result_id;
  if (name === "propose_workload_inputs") {
    path = "copilot-sessions/" + args.session_id + "/proposals";
    method = "POST";
    body = args.proposal;
  }
  if (name === "get_capabilities") path = "capabilities";
  if (name === "read_result") path = "results/" + args.result_id;
  if (name === "read_job") path = "jobs/" + args.job_id;
  if (name === "compile_revision") {
    path = "compilations";
    method = "POST";
    body = args;
  }
  if (name === "propose_observations") {
    path = "observation-proposals";
    method = "POST";
    body = args;
  }
  if (name === "compare_results") {
    path = "comparisons";
    method = "POST";
    body = args;
  }
  const response = await fetch(new URL("/api/v1/" + path, base), {
    method,
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      "Idempotency-Key": randomUUID(),
    },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(15000),
  });
  const data = await response.json();
  return {
    content: [{ type: "text", text: JSON.stringify(data) }],
    isError: !response.ok,
  };
}
async function handle(m) {
  if (m.jsonrpc !== "2.0") throw new Error("Expected JSON-RPC 2.0");
  if (m.method === "notifications/initialized") {
    ready = true;
    return;
  }
  if (m.id === undefined) return;
  if (m.method === "initialize") {
    initialized = true;
    return {
      protocolVersion: "2025-06-18",
      capabilities: { tools: { listChanged: false } },
      serverInfo: { name: "anubis", version: "0.1.0" },
    };
  }
  if (m.method === "ping") return {};
  if (!initialized || !ready)
    throw new Error("Initialize before requesting tools");
  if (m.method === "tools/list") return { tools };
  if (m.method === "tools/call")
    return await call(m.params?.name, m.params?.arguments || {});
  throw new Error("Method not found");
}
const lines = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of lines) {
  let message;
  try {
    if (line.length > 1024 * 1024) throw new Error("Message too large");
    message = JSON.parse(line);
    const result = await handle(message);
    if (message.id !== undefined)
      process.stdout.write(
        JSON.stringify({ jsonrpc: "2.0", id: message.id, result }) + "\n",
      );
  } catch (e) {
    process.stdout.write(
      JSON.stringify({
        jsonrpc: "2.0",
        id: message?.id ?? null,
        error: { code: -32602, message: e.message },
      }) + "\n",
    );
  }
}
