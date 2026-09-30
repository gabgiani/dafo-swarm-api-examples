#!/usr/bin/env python3
"""Invoke a configured DAFO Swarm agent through its OpenAI-compatible API."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:43100"


def request_json(base_url: str, path: str, api_key: str, payload: dict[str, Any] | None = None) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        method="GET" if data is None else "POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{error.code} {error.reason}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach {base_url}: {error.reason}") from error


def active_model_id(base_url: str, api_key: str) -> str:
    models = request_json(base_url, "/v1/models", api_key)
    available_models = models.get("data", [])
    if not available_models:
        raise RuntimeError("The coordinator has no active model.")
    return available_models[0]["id"]


def configured_agents(base_url: str, api_key: str) -> list[dict[str, str]]:
    state = request_json(base_url, "/api/state", api_key)
    agents = state.get("agents", {})
    agent_records = agents.values() if isinstance(agents, dict) else agents
    return [
        {"id": agent["id"], "name": agent.get("name", agent["id"])}
        for agent in agent_records
        if "id" in agent
    ]


def select_agent(agents: list[dict[str, str]], requested_agent: str | None) -> dict[str, str]:
    if requested_agent:
        matching_agents = [
            agent
            for agent in agents
            if requested_agent in (agent["id"], agent["name"])
        ]
        if len(matching_agents) == 1:
            return matching_agents[0]
        if not matching_agents:
            raise RuntimeError(f"No configured agent matches {requested_agent!r}.")
        raise RuntimeError(f"More than one configured agent matches {requested_agent!r}.")
    if len(agents) == 1:
        return agents[0]
    if not agents:
        raise RuntimeError("The coordinator has no configured agents.")
    choices = ", ".join(f'{agent["name"]} ({agent["id"]})' for agent in agents)
    raise RuntimeError(f"Choose an agent with --agent. Available agents: {choices}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?", help="User message for the selected agent.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SWARM_BASE_URL", DEFAULT_BASE_URL),
        help=f"Coordinator URL (default: {DEFAULT_BASE_URL}).",
    )
    parser.add_argument("--agent", help="Configured agent ID or exact name.")
    parser.add_argument("--api-key", default=os.environ.get("SWARM_API_KEY"), help="API token (default: SWARM_API_KEY).")
    parser.add_argument("--max-tokens", type=int, default=300, help="Maximum completion tokens.")
    parser.add_argument("--temperature", type=float, default=0, help="Sampling temperature.")
    parser.add_argument("--list-agents", action="store_true", help="Print configured agents and exit.")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if not arguments.api_key:
            if not sys.stdin.isatty():
                raise RuntimeError("Set SWARM_API_KEY to an API token from Settings > API > API Access.")
            print("Create a token in DAFO Swarm: Settings > API > API Access.")
            arguments.api_key = getpass.getpass("Paste your API token (hidden), then press Enter: ").strip()
            if not arguments.api_key:
                raise RuntimeError("No token entered. Run the example again and paste your API token.")
        agents = configured_agents(arguments.base_url, arguments.api_key)
        if arguments.list_agents:
            print(json.dumps(agents, indent=2))
            return 0
        if not arguments.prompt:
            raise RuntimeError("Provide a prompt or use --list-agents.")
        agent = select_agent(agents, arguments.agent)
        print(f"Agent {agent['name']} - question: {arguments.prompt}", flush=True)
        response = request_json(
            arguments.base_url,
            "/v1/chat/completions",
            arguments.api_key,
            {
                "model": active_model_id(arguments.base_url, arguments.api_key),
                "agent": agent["id"],
                "messages": [{"role": "user", "content": arguments.prompt}],
                "max_tokens": arguments.max_tokens,
                "temperature": arguments.temperature,
            },
        )
        choice = response["choices"][0]
        print(f"Agent {agent['name']} - answer: {choice['message']['content']}")
        print(f"[{response.get('usage', {}).get('completion_tokens', '?')} tokens; finish: {choice['finish_reason']}]")
        if choice["finish_reason"] == "length":
            print("The answer reached the token limit. Run again with --max-tokens 512 if the model context allows it.", file=sys.stderr)
        return 0
    except (KeyError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
