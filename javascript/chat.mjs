// Chat Completions and Responses from Node.js 18+ (built-in fetch, no dependencies).
// Usage: SWARM_BASE_URL=... SWARM_API_TOKEN=... node chat.mjs "Your question" [--responses] [--agent <id>]
const baseURL = process.env.SWARM_BASE_URL;
const token = process.env.SWARM_API_TOKEN;
if (!baseURL || !token) throw new Error("Set SWARM_BASE_URL and SWARM_API_TOKEN (see the README).");

const args = process.argv.slice(2);
const useResponses = args.includes("--responses");
const agentIndex = args.indexOf("--agent");
const agent = agentIndex >= 0 ? args[agentIndex + 1] : process.env.SWARM_AGENT;
const prompt = args.find((arg, index) => !arg.startsWith("--") && index !== agentIndex + 1) || "Explain distributed inference briefly.";

async function json(path, options = {}) {
  const response = await fetch(baseURL.replace(/\/$/, "") + path, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  return response.json();
}

const models = await json("/v1/models");
if (!models.data.length) throw new Error("The swarm has no model ready yet.");
const model = models.data[0].id;
const extra = agent ? { agent } : {};

if (useResponses) {
  const result = await json("/v1/responses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, input: prompt, max_output_tokens: 256, stream: false, ...extra }),
  });
  const text = (result.output || [])
    .filter((item) => item.type === "message")
    .flatMap((item) => item.content || [])
    .map((part) => part.text || "")
    .join("");
  console.log(text);
} else {
  const result = await json("/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages: [{ role: "user", content: prompt }], max_tokens: 256, stream: false, ...extra }),
  });
  console.log(result.choices[0].message.content);
}
