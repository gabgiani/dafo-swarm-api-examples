#!/usr/bin/env bash
# Chat Completions with cURL. Needs SWARM_BASE_URL and SWARM_API_TOKEN (see the README).
# Optional: SWARM_AGENT=<agent id> to answer with a configured agent.
set -euo pipefail
: "${SWARM_BASE_URL:?set SWARM_BASE_URL to your Node URL}"
: "${SWARM_API_TOKEN:?set SWARM_API_TOKEN to an API token}"
PROMPT="${1:-Explain distributed inference briefly.}"
AUTH="Authorization: Bearer $SWARM_API_TOKEN"

MODEL=$(curl --fail --silent --show-error -H "$AUTH" "$SWARM_BASE_URL/v1/models" | jq -er '.data[0].id')

jq -n --arg model "$MODEL" --arg prompt "$PROMPT" --arg agent "${SWARM_AGENT:-}" '
  {model: $model, messages: [{role: "user", content: $prompt}], max_tokens: 256, stream: false}
  + (if $agent == "" then {} else {agent: $agent} end)' |
  curl --fail --silent --show-error "$SWARM_BASE_URL/v1/chat/completions" \
    -H "$AUTH" -H 'Content-Type: application/json' --data-binary @- |
  jq -r '.choices[0].message.content'
