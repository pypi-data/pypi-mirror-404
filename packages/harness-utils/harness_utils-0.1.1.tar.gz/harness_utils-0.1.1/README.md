# harnessutils

Python library for managing LLM context windows in long-running conversations. Enables indefinite conversation length while staying within token limits.

## Installation

```bash
uv add harness-utils
```

## Features

- **Three-tier context management** - Truncation, pruning, and LLM-powered summarization
- **Turn processing** - Stream event handling with hooks and doom loop detection
- **Pluggable storage** - Filesystem and in-memory backends
- **Zero dependencies** - No external runtime requirements
- **Type-safe** - Full Python 3.12+ type hints

## Quick Start

```python
from harnessutils import ConversationManager, Message, TextPart, generate_id

manager = ConversationManager()
conv = manager.create_conversation()

# Add message
msg = Message(id=generate_id("msg"), role="user")
msg.add_part(TextPart(text="Help me debug"))
manager.add_message(conv.id, msg)

# Prune old outputs
manager.prune_before_turn(conv.id)

# Get messages for LLM
model_messages = manager.to_model_format(conv.id)
```

## Context Management

Three tiers handle context overflow:

**1. Truncation** - Limits tool output size (instant, free)
```python
output = manager.truncate_tool_output(large_output, "tool_name")
```

**2. Pruning** - Removes old tool outputs (fast, ~50ms)
```python
result = manager.prune_before_turn(conv.id)
# Keeps recent 40K tokens, removes older outputs
```

**3. Summarization** - LLM compression when needed (slow, ~3-5s)
```python
if manager.needs_compaction(conv.id, usage):
    manager.compact(conv.id, llm_client, parent_msg_id)
```

## Turn Processing

Process streaming LLM responses with hooks:

```python
from harnessutils import TurnProcessor, TurnHooks

hooks = TurnHooks(
    on_tool_call=execute_tool,
    on_doom_loop=handle_loop,
)

processor = TurnProcessor(message, hooks)
for event in llm_stream:
    processor.process_stream_event(event)
```

Includes:
- Tool state machine
- Doom loop detection (3 identical calls)
- Snapshot tracking

## Configuration

```python
from harnessutils import HarnessConfig

config = HarnessConfig()
config.truncation.max_lines = 2000
config.pruning.prune_protect = 40_000  # Keep recent 40K tokens
config.model_limits.default_context_limit = 200_000
```

## Storage

```python
from harnessutils import FilesystemStorage, MemoryStorage

# Filesystem (production)
storage = FilesystemStorage(config.storage)

# In-memory (testing)
storage = MemoryStorage()

# Custom (implement StorageBackend protocol)
# See examples/custom_storage_example.py
storage = YourCustomStorage()
```

## Examples

- `basic_usage.py` - Simple conversation
- `ollama_example.py` - Ollama integration
- `ollama_with_summarization.py` - Full three-tier demo
- `turn_processing_example.py` - Stream processing
- `custom_storage_example.py` - Custom storage adapter (SQLite)

## Development

```bash
uv sync              # Install deps
uv run pytest        # Run tests
uv run mypy src/     # Type check
```

## License

MIT License - see [LICENSE](LICENSE) for details.
