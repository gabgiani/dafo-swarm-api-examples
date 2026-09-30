# Python

`invoke_agent.py` calls a configured agent through `/v1/chat/completions`, using only the
standard library (Python 3.9+).

```sh
export SWARM_BASE_URL="http://192.168.0.10:43100"
export SWARM_API_KEY="paste-your-token"        # API token from Settings → API → API Access
python3 invoke_agent.py --list-agents          # agents your token can use
python3 invoke_agent.py --agent "Plant assistant" "What stopped line 3 yesterday?"
```

If `SWARM_API_KEY` is not set and you run it in a terminal, it asks for the token without
showing it.
