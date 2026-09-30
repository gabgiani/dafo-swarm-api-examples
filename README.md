# DAFO Swarm API examples

DAFO Swarm exposes an **OpenAI-compatible API** on every node, so you can call your private
swarm from scripts, services and OpenAI client libraries.

| Endpoint | Purpose |
|---|---|
| `GET /v1/models` | The model the swarm is running now |
| `POST /v1/chat/completions` | Chat Completions API |
| `POST /v1/responses` | Responses API (also runs the MCP tools configured in the swarm) |

## Before you start

1. **Node URL** – in DAFO Swarm open **Settings → API → API Access** and copy the *Node URL*.
   Use the coordinator's address for a stable entry point; a connected member also accepts
   requests and forwards them. The HTTP port must be reachable from where your program runs
   (the room code and the P2P relay do not expose it publicly).
2. **API token** – in the same page create a token and copy it with its copy button.
   Programs that use it act as you, with your agents and knowledge.
3. Export both:

   ```sh
   export SWARM_BASE_URL="http://192.168.0.10:43100"   # your Node URL
   export SWARM_API_TOKEN="paste-your-token"
   ```

Every request sends `Authorization: Bearer $SWARM_API_TOKEN`. The model must be ready (an
approved inference plan) before requests succeed.

## Examples

| Folder | What it shows |
|---|---|
| [`curl/`](curl/) | Chat Completions and Responses from the shell (needs `curl` and `jq`) |
| [`javascript/`](javascript/) | Node.js 18+ with the built-in `fetch`, no dependencies |
| [`python/`](python/) | Python 3.9+ standard library only, including calling a configured **agent** |

## Calling an agent

Add `"agent": "<agent id>"` to a Chat Completions or Responses request to answer with that
agent's instructions, tools and knowledge. `python/invoke_agent.py --list-agents` prints the
agents your token can use.

## Limits

- Non-streaming only (`"stream": false`), one completion per request.
- Images and function tools depend on the model the swarm is running.
- Keep the port on a trusted network or behind HTTPS. Browsers calling from another origin
  need a proxy that sets CORS headers.

## OpenAI client libraries

Point the client at the node URL with `/v1` and use your token as the API key, e.g. in Python:

```python
from openai import OpenAI
client = OpenAI(base_url=f"{SWARM_BASE_URL}/v1", api_key=SWARM_API_TOKEN)
model = client.models.list().data[0].id
print(client.chat.completions.create(model=model, messages=[{"role": "user", "content": "Hello"}]).choices[0].message.content)
```
