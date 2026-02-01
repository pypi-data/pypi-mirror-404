# Construct Labs CRM Agent Environment

Python SDK for the Construct Labs CRM Agent Environment - a reinforcement learning environment for training AI agents to interact with CRM systems.

## License

This software requires a commercial license from Construct Labs GmbH. 
Contact hello@construct-labs.com for licensing inquiries.

## Installation

```bash
pip install construct-labs-crm-env
```

## Quick Start

```python
from construct_labs_crm_env import CrmAgentEnv, CrmAgentAction, CRMActionType

# Connect to the CRM environment
with CrmAgentEnv(
    base_url="https://api.construct-labs.com",
    api_key="your-api-key"  # Issued by Construct Labs
) as env:
    # Reset the environment
    result = env.reset()
    
    # List companies
    result = env.step(CrmAgentAction(
        action_type=CRMActionType.LIST_COMPANIES,
        limit=10
    ))
    print(result.observation.data)
```

## Environment Variables

You can set your API key via environment variable:

```bash
export CRM_AGENT_API_KEY=your-api-key
```

```python
# API key is read from environment
env = CrmAgentEnv(base_url="https://api.construct-labs.com")
```

## LLM Integration Example

The SDK is designed to work with LLM-based agents. Here's how to parse LLM tool calls:

```python
from construct_labs_crm_env import CrmAgentEnv

with CrmAgentEnv(
    base_url="https://api.construct-labs.com",
    api_key="your-api-key"
) as env:
    result = env.reset()
    
    # Simulate an LLM generating a tool call
    llm_tool_call = {
        "name": "list_companies",
        "arguments": {"limit": 5}
    }
    
    # Parse the tool call into a CrmAgentAction
    parsed = env.parse_tool_call(llm_tool_call)
    
    if parsed.is_valid:
        result = env.step(parsed.action)
        print(result.observation.model_dump_json(indent=2))
    else:
        print(f"Invalid tool call: {parsed.error_message}")
```

## Customization

Subclass `CrmAgentEnv` to customize agent behavior:

### Custom System Prompt

```python
class SalesAgent(CrmAgentEnv):
    @property
    def system_prompt(self) -> str:
        return """You are a sales assistant AI.
        
Your goal is to help close deals by:
1. Finding relevant companies and contacts
2. Creating opportunities with accurate values
3. Adding follow-up tasks

Be concise. Focus on high-value opportunities."""
```

### Restricted Tool Set

```python
class ReadOnlyAgent(CrmAgentEnv):
    """Agent that can only read data, not modify."""
    
    @property
    def tools(self) -> list[dict]:
        read_only = {'list_companies', 'get_company', 'list_people', 
                     'get_person', 'list_opportunities', 'submit_answer'}
        return [t for t in self._default_tools() 
                if t['function']['name'] in read_only]
```

### Custom Observation Formatting

```python
class VerboseAgent(CrmAgentEnv):
    def format_observation(self, observation):
        base = super().format_observation(observation)
        return f"=== CRM Response ===\n{base}\n=== End ==="
```

## Available Actions

### Company Operations
- `LIST_COMPANIES` - List all companies
- `GET_COMPANY` - Get a specific company by ID
- `CREATE_COMPANY` - Create a new company
- `UPDATE_COMPANY` - Update an existing company
- `DELETE_COMPANY` - Delete a company

### Contact Operations
- `LIST_PEOPLE` - List all contacts
- `GET_PERSON` - Get a specific contact by ID
- `CREATE_PERSON` - Create a new contact
- `UPDATE_PERSON` - Update an existing contact
- `DELETE_PERSON` - Delete a contact

### Opportunity Operations
- `LIST_OPPORTUNITIES` - List all opportunities
- `GET_OPPORTUNITY` - Get a specific opportunity by ID
- `CREATE_OPPORTUNITY` - Create a new opportunity
- `UPDATE_OPPORTUNITY` - Update an existing opportunity
- `DELETE_OPPORTUNITY` - Delete an opportunity

### Note Operations
- `LIST_NOTES` - List all notes
- `CREATE_NOTE` - Create a note attached to a record

### Task Operations
- `LIST_TASKS` - List all tasks
- `CREATE_TASK` - Create a new task
- `UPDATE_TASK` - Update an existing task
- `COMPLETE_TASK` - Mark a task as complete

### Submit Answer
- `SUBMIT_ANSWER` - Submit the final answer and end the session

## Integration with Training Frameworks

### Collecting Rollouts for RL Training

The SDK is designed for reinforcement learning. Here's how to collect rollouts with rewards:

```python
from dataclasses import dataclass, field
from construct_labs_crm_env import CrmAgentEnv, CrmAgentObservation

@dataclass
class Rollout:
    """A single episode rollout for training."""
    observations: list[CrmAgentObservation] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)  # Raw tool calls
    rewards: list[float] = field(default_factory=list)
    done: bool = False
    total_reward: float = 0.0

def collect_rollout(env: CrmAgentEnv, agent, seed: int | None = None) -> Rollout:
    """Collect a single rollout from the environment."""
    rollout = Rollout()
    
    # Reset environment
    result = env.reset(seed=seed)
    rollout.observations.append(result.observation)
    
    while not result.done:
        # Get action from agent (returns tool call dict)
        tool_call = agent.get_action(
            system_prompt=env.system_prompt,
            tools=env.tools,
            observation=result.observation,
        )
        
        # Parse and execute
        parsed = env.parse_tool_call(tool_call)
        
        if parsed.is_valid:
            result = env.step(parsed.action)
            reward = result.reward if result.reward is not None else 0.0
        else:
            # Invalid action penalty
            reward = -1.0
            result.done = True
        
        # Store transition
        rollout.actions.append(tool_call)
        rollout.rewards.append(reward)
        rollout.observations.append(result.observation)
    
    rollout.done = True
    rollout.total_reward = sum(rollout.rewards)
    return rollout

# Collect multiple rollouts for training
def collect_rollouts(
    env: CrmAgentEnv,
    agent,
    num_rollouts: int,
    seed_offset: int = 0,
) -> list[Rollout]:
    """Collect multiple rollouts for batch training."""
    rollouts = []
    for i in range(num_rollouts):
        rollout = collect_rollout(env, agent, seed=seed_offset + i)
        rollouts.append(rollout)
    return rollouts

# Example usage
with CrmAgentEnv(
    base_url="https://api.construct-labs.com",
    api_key="your-api-key"
) as env:
    # Collect 10 rollouts
    rollouts = collect_rollouts(env, your_agent, num_rollouts=10)
    
    # Compute statistics
    avg_reward = sum(r.total_reward for r in rollouts) / len(rollouts)
    avg_length = sum(len(r.actions) for r in rollouts) / len(rollouts)
    
    print(f"Average reward: {avg_reward:.2f}")
    print(f"Average episode length: {avg_length:.1f}")
```

### GRPO Training Integration

For Group Relative Policy Optimization (GRPO) training:

```python
from construct_labs_crm_env import CrmAgentEnv

def collect_grpo_group(
    env: CrmAgentEnv,
    agent,
    group_size: int = 8,
    seed: int = 0,
) -> list[Rollout]:
    """Collect a group of rollouts with the same seed for GRPO."""
    group = []
    for _ in range(group_size):
        # Same seed = same initial state, different agent samples
        rollout = collect_rollout(env, agent, seed=seed)
        group.append(rollout)
    return group

def compute_grpo_advantages(group: list[Rollout]) -> list[float]:
    """Compute relative advantages within a group."""
    rewards = [r.total_reward for r in group]
    mean_reward = sum(rewards) / len(rewards)
    std_reward = (sum((r - mean_reward) ** 2 for r in rewards) / len(rewards)) ** 0.5
    
    if std_reward < 1e-8:
        return [0.0] * len(rewards)
    
    return [(r - mean_reward) / std_reward for r in rewards]

# Training loop
with CrmAgentEnv(
    base_url="https://api.construct-labs.com",
    api_key="your-api-key"
) as env:
    for step in range(num_training_steps):
        # Collect group of rollouts
        group = collect_grpo_group(env, agent, group_size=8, seed=step)
        
        # Compute advantages
        advantages = compute_grpo_advantages(group)
        
        # Update policy using advantages
        agent.update(group, advantages)
```

### Basic Training Loop

```python
from construct_labs_crm_env import CrmAgentEnv

env = CrmAgentEnv(
    base_url="https://api.construct-labs.com",
    api_key="your-api-key"
)

with env:
    result = env.reset(seed=42)
    
    while not result.done:
        # Get action from your agent/LLM
        tool_call = your_agent.get_action(
            env.system_prompt,
            env.tools,
            result.observation
        )
        
        # Parse and execute
        parsed = env.parse_tool_call(tool_call)
        if parsed.is_valid:
            result = env.step(parsed.action)
        else:
            # Handle invalid action
            print(f"Invalid action: {parsed.error_message}")
            break
```

## API Reference

### CrmAgentEnv

Main client class for interacting with the CRM environment.

**Constructor:**
- `base_url` (str): Base URL of the CRM environment server
- `api_key` (str, optional): API key for authentication
- `connect_timeout_s` (float): Connection timeout in seconds (default: 10)
- `message_timeout_s` (float): Message timeout in seconds (default: 60)

**Methods:**
- `reset(seed=None)` - Reset the environment
- `step(action)` - Execute an action
- `state()` - Get current environment state
- `close()` - Close the connection
- `parse_tool_call(tool_call)` - Parse LLM tool call to action
- `format_observation(observation)` - Format observation for LLM

**Properties (overridable):**
- `system_prompt` - System prompt for the agent
- `tools` - Available tool definitions

### CrmAgentAction

Pydantic model for CRM actions.

```python
action = CrmAgentAction(
    action_type=CRMActionType.CREATE_COMPANY,
    company_name="Acme Corp",
    company_domain="acme.com",
    company_employees=100
)
```

### CrmAgentObservation

Pydantic model for CRM observations.

- `success` (bool): Whether the action succeeded
- `error` (str | None): Error message if failed
- `data` (dict): Raw response data
- `done` (bool): Whether episode has ended
- `reward` (float | None): Reward signal

Use `observation.model_dump_json()` to get JSON representation.

## Support

For licensing, technical support, or questions:

**Email:** hello@construct-labs.com

## License

Copyright (c) 2024 Construct Labs GmbH. All rights reserved.

This software is proprietary and requires a commercial license.
See [LICENSE](LICENSE) for details.
