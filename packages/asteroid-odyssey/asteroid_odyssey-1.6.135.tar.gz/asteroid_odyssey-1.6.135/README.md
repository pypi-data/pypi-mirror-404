# Asteroid Odyssey Python SDK

Python SDK for the Asteroid Agents API.

## Installation

```bash
pip install asteroid-odyssey
```

## Usage

```python
from asteroid_odyssey import ApiClient, Configuration, ExecutionApi

# Configure the client
config = Configuration(
    host="https://odyssey.asteroid.ai/agents/v2",
    api_key={"ApiKeyAuth": "your-api-key"}
)

client = ApiClient(config)
execution_api = ExecutionApi(client)

# Execute an agent
response = execution_api.agent_execute_post(
    agent_id="your-agent-id",
    agents_agent_execute_agent_request={"inputs": {"input": "value"}}
)
print(f"Execution ID: {response.execution_id}")
```

## Documentation

See [docs.asteroid.ai](https://docs.asteroid.ai) for full documentation.
