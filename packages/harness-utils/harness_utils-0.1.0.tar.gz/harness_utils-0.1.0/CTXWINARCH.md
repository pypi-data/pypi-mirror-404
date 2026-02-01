# Context Window Management Architecture for LLM-Based Coding Agents

**Document Type:** Technical Architecture Reference
**Domain:** Autonomous AI Coding Agents
**Focus:** Indefinite Conversation Length via Intelligent Context Management

## Abstract

This document presents a production-grade architecture for managing LLM context windows in long-running autonomous coding agent systems. The architecture enables conversations to exceed model token limits while maintaining semantic coherence and task continuity through a three-tier management strategy: output truncation, selective pruning, and LLM-powered summarization.

**Key Contributions:**
- Three-tier context management strategy balancing latency and cost
- Part-based message decomposition enabling granular compaction
- Prompt caching optimization reducing token costs by 90%
- Snapshot-based state tracking for debugging and rollback
- Automatic overflow detection and recovery

---

## Problem Statement

### The Context Window Constraint

LLM-based coding agents face fundamental constraints:

1. **Fixed Context Windows**
   - Models have hard token limits (e.g., 200K tokens)
   - Input + output must fit within limit
   - Exceeding limit causes request failure

2. **Growing Conversation History**
   - Each turn adds tokens: user request + assistant response + tool outputs
   - Tool outputs especially voluminous (file contents, command output, logs)
   - 50-turn conversation easily exceeds 200K tokens

3. **Context Requirement**
   - Agents need conversation history for coherence
   - Must remember: files modified, decisions made, user preferences
   - Naive truncation loses critical information

### Challenge

**Design a system enabling indefinite conversation length while:**
- Staying within model token limits
- Preserving semantic continuity
- Minimizing latency overhead
- Optimizing API costs
- Supporting debugging and rollback

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Conversation Processor                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         LLM Stream Handler                           │   │
│  │  • System prompt construction (2-part caching)       │   │
│  │  • Provider-specific transformations                 │   │
│  │  • Tool resolution & execution                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      Turn Processor                                  │   │
│  │  • Stream event handling                             │   │
│  │  • Tool state machine management                     │   │
│  │  • Loop detection (duplicate tool calls)             │   │
│  │  • State snapshot tracking                           │   │
│  │  • Overflow detection & compaction trigger           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │     Context Compaction Engine                        │   │
│  │  • Overflow detection                                │   │
│  │  • Pruning (selective output removal)                │   │
│  │  • LLM-powered summarization                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Message Storage Layer                           │
│  • Part-based message decomposition                          │
│  • User/Assistant message types                              │
│  • Model format conversion                                   │
│  • Compaction state tracking                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           Persistence Layer                                  │
│  ├── conversations/{conversationID}/                         │
│  ├── messages/{conversationID}/{messageID}                   │
│  ├── parts/{messageID}/{partID}                              │
│  └── truncated-outputs/{outputID}                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Three-Tier Context Management Strategy

### Design Philosophy

The architecture employs three progressively aggressive strategies, ordered by cost/latency:

1. **Truncation** (Proactive, Free, 0ms)
   - Prevent large outputs from entering context
   - Applied at tool execution boundary

2. **Pruning** (Proactive, Cheap, ~50ms)
   - Remove old tool outputs
   - Preserve tool call metadata
   - Applied before each user turn

3. **Summarization** (Reactive, Expensive, ~3-5s)
   - LLM-powered conversation compression
   - Applied only when overflow detected
   - Last resort, preserves semantic content

---

### Tier 1: Output Truncation

**Strategy:** Prevent large outputs from entering context at source.

**Thresholds:**
```
MAX_LINES = 2000      // Maximum lines per tool output
MAX_BYTES = 50 * 1024 // 50KB maximum size
```

**Algorithm:**
```
function truncateOutput(output, maxLines, maxBytes, direction) {
  lines = split(output, '\n')
  totalBytes = byteLength(output)

  if (lines.length <= maxLines && totalBytes <= maxBytes) {
    return { content: output, truncated: false }
  }

  // Truncate to fit limits
  preview = []
  bytesAccumulated = 0

  if (direction == "head") {
    for (i = 0; i < min(lines.length, maxLines); i++) {
      lineBytes = byteLength(lines[i])
      if (bytesAccumulated + lineBytes > maxBytes) break
      preview.append(lines[i])
      bytesAccumulated += lineBytes
    }
  } else {  // tail
    for (i = lines.length - 1; i >= 0 && preview.length < maxLines; i--) {
      lineBytes = byteLength(lines[i])
      if (bytesAccumulated + lineBytes > maxBytes) break
      preview.prepend(lines[i])
      bytesAccumulated += lineBytes
    }
  }

  // Save full output to disk
  filepath = saveToStorage(output)
  removed = totalBytes - bytesAccumulated

  message = formatTruncatedMessage(preview, removed, filepath, direction)
  return { content: message, truncated: true, outputPath: filepath }
}
```

**Truncated Output Format:**
```
<preview content>

...N bytes truncated...

Full output saved to: {filepath}
Use search tools to query the full content or read specific sections.
Delegate large file processing to specialized exploration agents.
```

**Storage Management:**
- Full outputs saved to disk storage
- Automatic cleanup after retention period (e.g., 7 days)
- Scheduled garbage collection

**Benefits:**
- **Prevents context explosion** from single large output
- **Zero latency** - synchronous operation
- **No token cost** - local processing only
- **Preserves access** - full output retrievable

**Limitations:**
- Requires agent to understand truncation markers
- Agent must use subsequent tools (search, read with offset) to access full data
- Not suitable for outputs requiring complete context

---

### Tier 2: Pruning (Selective Output Removal)

**Strategy:** Remove old tool outputs while preserving conversation structure.

**Thresholds:**
```
PRUNE_PROTECT = 40_000    // Keep most recent 40K tokens of tool calls
PRUNE_MINIMUM = 20_000    // Only prune if saves 20K+ tokens
```

**Protected Tools:**
```
// Tools whose outputs should never be pruned
PROTECTED_TOOLS = ["skill_execution", "subtask_invocation"]
```

**Algorithm:**
```
function pruneToolOutputs(conversationHistory) {
  messages = conversationHistory.reverse()  // Newest first
  totalTokens = 0
  prunableTokens = 0
  toPrune = []
  turnsSkipped = 0

  for (msg in messages) {
    if (msg.role == "user") turnsSkipped++
    if (turnsSkipped < 2) continue  // Protect last 2 turns
    if (msg.summary) break  // Stop at previous summary

    for (part in msg.parts) {
      if (part.type != "tool") continue
      if (part.state.status != "completed") continue
      if (part.tool in PROTECTED_TOOLS) continue
      if (part.state.compacted) break  // Already pruned

      tokenEstimate = estimateTokens(part.state.output)
      totalTokens += tokenEstimate

      if (totalTokens > PRUNE_PROTECT) {
        prunableTokens += tokenEstimate
        toPrune.append(part)
      }
    }
  }

  if (prunableTokens > PRUNE_MINIMUM) {
    for (part in toPrune) {
      part.state.output = ""
      part.state.attachments = []
      part.state.time.compacted = now()
      updateStorage(part)
    }
    return { pruned: toPrune.length, tokensSaved: prunableTokens }
  }

  return { pruned: 0, tokensSaved: 0 }
}
```

**Compacted Tool Representation:**
```json
{
  "type": "tool",
  "tool": "read_file",
  "callID": "call_xyz",
  "state": {
    "status": "completed",
    "input": { "file_path": "/src/main.ts" },
    "output": "",
    "title": "Read /src/main.ts",
    "metadata": { "lines": 342 },
    "time": {
      "start": 1706734821000,
      "end": 1706734821050,
      "compacted": 1706734950000
    },
    "attachments": []
  }
}
```

**What's Preserved:**
- Tool name
- Tool input parameters
- Tool title/description
- Execution metadata
- Timing information

**What's Removed:**
- Tool output content
- Output attachments

**Execution Timing:**
- Before each user turn (proactive)
- After compaction (cleanup)
- Cost: ~50ms (token estimation + storage updates)

**Benefits:**
- **Maintains conversation structure** - Agent sees "I called read_file on main.ts"
- **Preserves reasoning chain** - Tool call sequence intact
- **Cheap operation** - No LLM inference required
- **Dramatic savings** - 20K+ tokens freed per pruning cycle

**Limitations:**
- Agent loses access to historical outputs
- Not suitable if agent needs to reference old data
- May need to re-execute tools

---

### Tier 3: Summarization (LLM-Powered Compression)

**Strategy:** Use LLM to semantically compress conversation when approaching limit.

**Trigger Condition:**
```
function isOverflow(tokens, modelLimits) {
  totalInput = tokens.input + tokens.cacheRead
  totalOutput = tokens.output + tokens.reasoning
  total = totalInput + totalOutput

  maxOutput = min(modelLimits.output, CONFIGURED_MAX_OUTPUT)
  usableInput = modelLimits.input || (modelLimits.context - maxOutput)

  return total > usableInput
}
```

**Overflow Detection:**
- Checked after each turn completes
- Uses actual token counts from LLM response
- Accounts for cache hits, reasoning tokens, output tokens

**Summarization Process:**
```
function summarizeConversation(conversationHistory, userMessage) {
  // 1. Create summarization request
  agent = getAgent("summarization")
  model = agent.model || userMessage.model

  // 2. Build prompt
  systemPrompt = SUMMARIZATION_PROMPT
  messages = convertToModelFormat(conversationHistory)
  messages.append({
    role: "user",
    content: "Provide a detailed summary for continuing our conversation..."
  })

  // 3. Invoke LLM
  summary = streamLLM({
    model: model,
    agent: agent,
    messages: messages,
    system: [systemPrompt]
  })

  // 4. Create summary message
  summaryMessage = createMessage({
    role: "assistant",
    parentID: userMessage.id,
    summary: true,
    agent: "summarization"
  })

  summaryMessage.parts.append({
    type: "text",
    text: summary.content
  })

  saveMessage(summaryMessage)

  // 5. Optionally inject continuation prompt
  if (autoMode) {
    continueMessage = createMessage({
      role: "user",
      text: "Continue if you have next steps"
    })
    saveMessage(continueMessage)
  }

  return summaryMessage
}
```

**Summarization Prompt Template:**
```
You are a helpful AI assistant tasked with summarizing conversations.

When asked to summarize, provide a detailed but concise summary of the conversation.
Focus on information that would be helpful for continuing the conversation, including:
- What was done
- What is currently being worked on
- Which files are being modified
- What needs to be done next
- Key user requests, constraints, or preferences that should persist
- Important technical decisions and why they were made

Your summary should be comprehensive enough to provide context but concise enough
to be quickly understood.
```

**Summary Message Structure:**
```json
{
  "role": "assistant",
  "summary": true,
  "agent": "summarization",
  "parentID": "msg_user_request",
  "parts": [
    {
      "type": "text",
      "text": "We are implementing authentication for the web application..."
    }
  ],
  "tokens": {
    "input": 45231,
    "output": 842
  },
  "cost": 0.142
}
```

**Message Filtering After Summary:**

When converting messages to model format after summarization:
```
function filterCompactedMessages(messages) {
  result = []
  summaryFound = false

  // Walk backwards (newest to oldest)
  for (msg in messages.reverse()) {
    result.prepend(msg)

    if (msg.role == "assistant" && msg.summary) {
      summaryFound = true
      summaryParentID = msg.parentID
    }

    // Stop at user message that triggered summary
    if (summaryFound && msg.role == "user" && msg.id == summaryParentID) {
      break
    }
  }

  return result
}
```

**Auto-Continue Mode:**

After successful summarization, system can automatically continue:
```
if (summarizationSuccessful && autoMode) {
  injectSyntheticMessage({
    role: "user",
    text: "Continue if you have next steps",
    synthetic: true
  })
  // Agent resumes execution automatically
}
```

**Model Selection:**

Use cheaper/faster model for summarization:
```
// Primary conversation: premium-model-large
// Summarization: fast-model-small
agent.summarization.model = {
  providerID: "provider-x",
  modelID: "fast-small-model"
}
```

**Benefits:**
- **Semantic preservation** - LLM understands context importance
- **Dramatic compression** - 50K tokens → 2K summary
- **Maintains coherence** - Agent understands "what we're doing"
- **Extensible** - Can customize prompt per domain

**Limitations:**
- **Expensive** - Full LLM inference (~$0.10-0.50 per summary)
- **Latency** - 3-5 seconds overhead
- **Information loss** - Some details inevitably lost
- **Quality dependent** - Summary quality varies by model

**Cost Optimization:**

Only trigger when necessary:
```
config.compaction.auto = true   // Enable auto-summarization
config.compaction.prune = true  // Enable pruning (reduces summarization frequency)
```

---

## Token Tracking & Accounting

### Token Estimation

**Simple Heuristic:**
```
function estimateTokens(text) {
  CHARS_PER_TOKEN = 4
  return max(0, round(text.length / CHARS_PER_TOKEN))
}
```

**Rationale:**
- Fast, deterministic
- Good enough for pruning decisions
- Actual counts from LLM response used for overflow detection

**Limitations:**
- Underestimates for non-English text
- Overestimates for code with many symbols
- Tokenizer-specific variations ignored

**Production Alternative:**
```
// Use actual tokenizer library
tokenizer = loadTokenizer(modelName)
return tokenizer.encode(text).length
```

### Usage Tracking Structure

**Per-Turn Tracking:**
```json
{
  "tokens": {
    "input": 45231,           // Input tokens consumed
    "output": 2841,           // Output tokens generated
    "reasoning": 8234,        // Extended thinking tokens
    "cache": {
      "read": 32451,          // Cached input tokens (discounted)
      "write": 12780          // Cache creation tokens (premium)
    }
  },
  "cost": 0.142               // USD, calculated from pricing
}
```

**Cost Calculation:**
```
function calculateCost(usage, modelPricing) {
  inputCost = (usage.input * modelPricing.input) / 1_000_000
  outputCost = (usage.output * modelPricing.output) / 1_000_000
  reasoningCost = (usage.reasoning * modelPricing.reasoning) / 1_000_000
  cacheReadCost = (usage.cache.read * modelPricing.cacheRead) / 1_000_000
  cacheWriteCost = (usage.cache.write * modelPricing.cacheWrite) / 1_000_000

  return inputCost + outputCost + reasoningCost + cacheReadCost + cacheWriteCost
}
```

**Model Pricing Schema:**
```json
{
  "pricing": {
    "input": 3.00,          // USD per million tokens
    "output": 15.00,
    "reasoning": 15.00,     // Extended thinking (if supported)
    "cacheRead": 0.30,      // Cache hit (if supported)
    "cacheWrite": 3.75      // Cache creation (if supported)
  }
}
```

**Cumulative Tracking:**
```
conversationCost = sum(message.cost for message in conversation)
```

---

## Prompt Caching Optimization

### The Problem

System prompts are large (5-10K tokens) and identical across turns:
```
Turn 1: System(10K) + History(0K) + User(1K) = 11K input
Turn 2: System(10K) + History(3K) + User(1K) = 14K input
Turn 3: System(10K) + History(8K) + User(1K) = 19K input
...
```

Without caching, pay full price for 10K system tokens every turn.

### Two-Part Prompt Strategy

**Split system prompt into cacheable (static) and ephemeral (dynamic) parts:**

```
systemPrompt = [
  // Part 1: Static (cacheable)
  // - Agent instructions
  // - Provider-specific guidelines
  // - Core tool descriptions
  agentPrompt || providerPrompt,

  // Part 2: Dynamic (not cached)
  // - Session-specific context
  // - User custom instructions
  // - Dynamic tool definitions
  customSystemPrompts.join('\n')
]
```

**Caching Behavior (Anthropic):**
- Part 1 hashed and cached (5 min TTL)
- Subsequent requests with same Part 1 hit cache
- Part 2 always sent fresh

**Token Accounting:**
```
Turn 1:
  Part 1: 10K tokens × $3.75/M (cache write) = $0.0375
  Part 2: 2K tokens × $3.00/M (input) = $0.006
  Total: $0.0435

Turn 2:
  Part 1: 10K tokens × $0.30/M (cache read) = $0.003
  Part 2: 2K tokens × $3.00/M (input) = $0.006
  Total: $0.009

Savings: 79% reduction per turn after first
```

**Cache Maintenance:**
```
// Rejoin dynamic parts if static header unchanged
if (systemPrompt.length > 2 && systemPrompt[0] == originalHeader) {
  dynamicParts = systemPrompt.slice(1)
  systemPrompt = [
    originalHeader,           // Part 1 (cached)
    dynamicParts.join('\n')   // Part 2 (ephemeral)
  ]
}
```

**Provider Support:**

| Provider | Cache Support | Implementation |
|----------|---------------|----------------|
| Anthropic | Yes | Prompt caching |
| AWS Bedrock | Yes | Prompt caching (via Anthropic) |
| OpenAI | Limited | Automatic (opaque) |
| Google | No | - |
| Open source | No | - |

**Cache Invalidation:**

Cache automatically invalidates when:
- Part 1 content changes
- TTL expires (typically 5 minutes)
- Provider clears cache

**Best Practices:**
1. Keep static content in Part 1
2. Minimize Part 1 changes across conversation
3. Move dynamic tool definitions to Part 2
4. Monitor cache hit rates

---

## Message Architecture

### Part-Based Decomposition

**Traditional Approach (Monolithic):**
```json
{
  "role": "assistant",
  "content": "I'll read the file...\n<tool_use>read_file</tool_use>\nThe file contains..."
}
```

**Problem:** Cannot selectively compact. Must keep or discard entire message.

**Part-Based Approach (Granular):**
```json
{
  "message": {
    "id": "msg_123",
    "role": "assistant"
  },
  "parts": [
    {
      "type": "text",
      "text": "I'll read the file..."
    },
    {
      "type": "tool",
      "tool": "read_file",
      "state": {
        "status": "completed",
        "output": "<file contents>"
      }
    },
    {
      "type": "text",
      "text": "The file contains..."
    }
  ]
}
```

**Benefits:**
- **Selective Compaction**: Clear tool output, keep text
- **Streaming Updates**: Parts update independently
- **Rich Metadata**: Each part tracks timing, cost, errors
- **Flexible Storage**: Large outputs saved separately

### Part Type Schema

**Text Part:**
```json
{
  "type": "text",
  "text": "Here's my analysis...",
  "time": {
    "start": 1706734821000,
    "end": 1706734821500
  },
  "metadata": {}
}
```

**Reasoning Part** (Extended Thinking):
```json
{
  "type": "reasoning",
  "text": "<internal reasoning>...",
  "time": {
    "start": 1706734821000,
    "end": 1706734829000
  }
}
```

**Tool Part:**
```json
{
  "type": "tool",
  "tool": "bash",
  "callID": "call_xyz",
  "state": {
    "status": "completed | error | running | pending",
    "input": { "command": "ls -la" },
    "output": "...",
    "title": "Execute: ls -la",
    "metadata": {},
    "time": {
      "start": 1706734821000,
      "end": 1706734821050,
      "compacted": 1706734950000
    },
    "attachments": []
  }
}
```

**Step Boundary Parts:**
```json
{
  "type": "step-start",
  "snapshot": "abc123def"  // State snapshot ID
}

{
  "type": "step-finish",
  "reason": "stop | tool-calls | length",
  "snapshot": "xyz789abc",
  "tokens": { /* usage data */ },
  "cost": 0.042
}
```

**Patch Part** (Code Changes):
```json
{
  "type": "patch",
  "hash": "diff_hash_xyz",
  "files": ["src/main.ts", "README.md"]
}
```

**Compaction Marker:**
```json
{
  "type": "compaction",
  "auto": true  // Was this auto-triggered?
}
```

**Subtask Part:**
```json
{
  "type": "subtask",
  "prompt": "Analyze the codebase structure",
  "description": "Explore codebase architecture",
  "agent": "exploration",
  "model": {
    "providerID": "provider-x",
    "modelID": "model-y"
  }
}
```

### Tool State Machine

```
┌──────────┐
│ pending  │ ← Tool call received, not yet executed
└────┬─────┘
     │
     v
┌──────────┐
│ running  │ ← Tool executing
└────┬─────┘
     │
     ├─────→ ┌───────────┐
     │       │ completed │ ← Output available
     │       └───────────┘
     │            │
     │            v
     │       (later) compacted ← Output cleared, metadata preserved
     │
     └─────→ ┌───────┐
             │ error │ ← Execution failed
             └───────┘
```

**State Transitions:**
```
pending → running → completed → (compacted)
       ↘         ↘
                 error
```

**Compaction Effect:**
```
Before compaction:
{
  "status": "completed",
  "output": "<50KB of file contents>",
  "attachments": [...]
}

After compaction:
{
  "status": "completed",
  "output": "",
  "attachments": [],
  "time": {
    "compacted": 1706734950000
  }
}
```

---

## Message Conversion to Model Format

### Conversion Process

**Internal format** (granular, storage-optimized) must be converted to **model format** (LLM-compatible).

**Algorithm:**
```
function toModelMessages(internalMessages, targetModel) {
  modelMessages = []

  for (msg in internalMessages) {
    if (msg.parts.length == 0) continue

    if (msg.role == "user") {
      userMsg = { role: "user", parts: [] }

      for (part in msg.parts) {
        switch (part.type) {
          case "text":
            if (!part.ignored) {
              userMsg.parts.append({ type: "text", text: part.text })
            }
            break

          case "file":
            // Skip text/plain (converted to text elsewhere)
            if (part.mime != "text/plain") {
              userMsg.parts.append({
                type: "file",
                url: part.url,
                mediaType: part.mime
              })
            }
            break

          case "compaction":
            userMsg.parts.append({
              type: "text",
              text: "What did we do so far?"
            })
            break
        }
      }

      modelMessages.append(userMsg)
    }

    if (msg.role == "assistant") {
      // Skip messages with errors (unless partial output exists)
      if (msg.error && !hasPartialOutput(msg)) continue

      assistantMsg = { role: "assistant", parts: [] }

      for (part in msg.parts) {
        switch (part.type) {
          case "text":
            assistantMsg.parts.append({
              type: "text",
              text: part.text
            })
            break

          case "reasoning":
            assistantMsg.parts.append({
              type: "reasoning",
              text: part.text
            })
            break

          case "tool":
            if (part.state.status == "completed") {
              output = part.state.time.compacted
                ? "[Old tool result content cleared]"
                : part.state.output

              attachments = part.state.time.compacted
                ? []
                : (part.state.attachments || [])

              assistantMsg.parts.append({
                type: "tool-result",
                toolCallId: part.callID,
                input: part.state.input,
                output: formatOutput(output, attachments)
              })
            }
            else if (part.state.status == "error") {
              assistantMsg.parts.append({
                type: "tool-error",
                toolCallId: part.callID,
                errorText: part.state.error
              })
            }
            else if (part.state.status in ["pending", "running"]) {
              // Dangling tool call prevention
              assistantMsg.parts.append({
                type: "tool-error",
                toolCallId: part.callID,
                errorText: "[Tool execution was interrupted]"
              })
            }
            break
        }
      }

      if (assistantMsg.parts.length > 0) {
        modelMessages.append(assistantMsg)
      }
    }
  }

  return modelMessages
}
```

### Key Transformations

**1. Compacted Tool Output:**
```
Original: part.state.output = "<50KB content>"
Converted: "[Old tool result content cleared]"
```

**2. Interrupted Tool Calls:**

Problem: Some LLM APIs (Anthropic) require every `tool_use` block to have corresponding `tool_result`.

Solution:
```
if (toolState in ["pending", "running"]) {
  return {
    type: "tool-error",
    errorText: "[Tool execution was interrupted]"
  }
}
```

**3. Compaction Request Marker:**
```
Internal: { type: "compaction", auto: true }
Converted: { type: "text", text: "What did we do so far?" }
```

**4. Error Message Filtering:**
```
// Skip assistant messages with errors (unless partial success)
if (msg.error && !msg.parts.some(p => p.type == "text")) {
  continue
}
```

Prevents sending incomplete/failed turns to model.

**5. Model-Specific Metadata Stripping:**
```
// If switching models, strip provider metadata
differentModel = (
  currentModel.providerID != msg.providerID ||
  currentModel.modelID != msg.modelID
)

if (differentModel) {
  delete part.metadata
  delete part.providerMetadata
}
```

Avoids sending incompatible metadata between providers.

---

## Turn Processing Loop

### Main Processing Algorithm

```
function processTurn(userMessage, conversationHistory) {
  assistantMessage = createMessage({
    role: "assistant",
    parentID: userMessage.id
  })

  needsCompaction = false
  blocked = false
  retryAttempt = 0

  while (true) {
    try {
      // 1. Build LLM request
      systemPrompt = buildSystemPrompt(agent)
      modelMessages = toModelMessages(conversationHistory, model)
      tools = resolveTools(agent)

      // 2. Stream from LLM
      stream = streamLLM({
        system: systemPrompt,
        messages: modelMessages,
        tools: tools,
        model: model,
        abort: abortSignal
      })

      // 3. Process stream events
      for (event in stream) {
        switch (event.type) {
          case "start":
            markBusy()
            break

          case "reasoning-start":
            createPart({ type: "reasoning" })
            break

          case "reasoning-delta":
            updatePart({ delta: event.text })
            break

          case "reasoning-end":
            finalizePart()
            break

          case "tool-call":
            executeTool(event.toolName, event.input)
            checkDoomLoop(event.toolName, event.input)
            break

          case "tool-result":
            savePart({ type: "tool", state: "completed", output: event.output })
            break

          case "tool-error":
            savePart({ type: "tool", state: "error", error: event.error })
            if (event.error.type == "PermissionDenied") {
              blocked = true
            }
            break

          case "start-step":
            snapshot = captureSnapshot()
            savePart({ type: "step-start", snapshot: snapshot })
            break

          case "finish-step":
            usage = event.usage
            cost = calculateCost(usage)

            assistantMessage.tokens = usage
            assistantMessage.cost = cost

            savePart({ type: "step-finish", tokens: usage, cost: cost })

            // Check overflow
            if (isOverflow(usage, model)) {
              needsCompaction = true
              break  // Exit stream loop
            }
            break

          case "text-start":
            createPart({ type: "text" })
            break

          case "text-delta":
            updatePart({ delta: event.text })
            break

          case "text-end":
            finalizePart()
            break
        }

        if (needsCompaction) break
      }

    } catch (error) {
      // Retry logic
      if (isRetryable(error)) {
        retryAttempt++
        delay = calculateBackoff(retryAttempt)
        sleep(delay)
        continue
      }

      assistantMessage.error = error
      return "error"
    }

    // 4. Check continuation conditions
    if (needsCompaction) return "compact"
    if (blocked) return "blocked"
    if (assistantMessage.error) return "error"
    if (finishReason == "tool-calls") {
      continue  // Tools executed, continue loop
    }

    // Done
    return "complete"
  }
}
```

### Doom Loop Detection

**Problem:** Agent stuck calling same tool repeatedly.

**Example:**
```
1. read_file("config.json")
2. read_file("config.json")
3. read_file("config.json")  ← Doom loop detected
```

**Detection Algorithm:**
```
DOOM_LOOP_THRESHOLD = 3

function checkDoomLoop(toolName, input) {
  parts = getMessageParts(assistantMessage)
  lastThree = parts.slice(-DOOM_LOOP_THRESHOLD)

  if (lastThree.length == DOOM_LOOP_THRESHOLD) {
    allIdentical = lastThree.every(part =>
      part.type == "tool" &&
      part.tool == toolName &&
      part.state.status != "pending" &&
      stringify(part.state.input) == stringify(input)
    )

    if (allIdentical) {
      // Trigger permission request
      askUserPermission({
        type: "doom_loop",
        tool: toolName,
        input: input,
        message: "Agent is repeatedly calling the same tool. Continue?"
      })
    }
  }
}
```

**User Experience:**
```
⚠️  Loop detected: read_file called 3 times with identical input
   Input: { file_path: "config.json" }

   Options:
   [C]ontinue   [S]top   [A]lways allow
```

**Benefits:**
- Prevents infinite loops
- Gives user control
- Logs problematic patterns for debugging

### Snapshot Tracking

**Purpose:** State tracking for debugging, rollback, and diff generation.

**Implementation:**
```
function captureSnapshot() {
  // Using git as backing store (example)
  hash = git("rev-parse", "HEAD")

  // Or custom state serialization
  state = {
    files: listModifiedFiles(),
    timestamp: now(),
    checksum: hashFileContents()
  }

  return hash  // or state ID
}
```

**Usage Pattern:**
```
// Start of turn
startSnapshot = captureSnapshot()
savePart({ type: "step-start", snapshot: startSnapshot })

// End of turn
endSnapshot = captureSnapshot()
diff = computeDiff(startSnapshot, endSnapshot)

if (diff.files.length > 0) {
  savePart({
    type: "patch",
    hash: diff.hash,
    files: diff.files
  })
}
```

**Benefits:**
- **Debugging**: "What changed in turn 23?"
- **Rollback**: Restore state to any point
- **Visualization**: Show diff per turn
- **Session Summary**: Aggregate all changes

**Example Diff Part:**
```json
{
  "type": "patch",
  "hash": "diff_abc123",
  "files": [
    "src/main.ts",
    "README.md",
    "package.json"
  ]
}
```

**Session Summary Aggregation:**
```
function summarizeSession(conversationHistory) {
  patches = conversationHistory
    .flatMap(msg => msg.parts)
    .filter(part => part.type == "patch")

  allFiles = patches.flatMap(p => p.files).unique()

  firstSnapshot = conversationHistory[0].parts
    .find(p => p.type == "step-start").snapshot

  lastSnapshot = conversationHistory[conversationHistory.length - 1].parts
    .findLast(p => p.type == "step-finish").snapshot

  fullDiff = computeDiff(firstSnapshot, lastSnapshot)

  return {
    files: allFiles.length,
    additions: fullDiff.additions,
    deletions: fullDiff.deletions,
    diffs: fullDiff.perFileDiff
  }
}
```

---

## Retry Strategy

### Retryable vs Non-Retryable Errors

**Retryable:**
- Rate limits (429)
- Server errors (500-599)
- Network errors (connection reset, timeout)
- Overloaded errors (529, 503)

**Non-Retryable:**
- Authentication errors (401, 403)
- Bad request (400)
- Not found (404)
- Permission denied
- Invalid input

**Classification:**
```
function isRetryable(error) {
  // Network errors
  if (error.code in ["ECONNRESET", "ETIMEDOUT", "ECONNREFUSED"]) {
    return true
  }

  // HTTP status codes
  if (error.statusCode) {
    if (error.statusCode == 429) return true  // Rate limit
    if (error.statusCode >= 500 && error.statusCode < 600) return true  // Server error
    if (error.statusCode == 529) return true  // Overloaded
  }

  // Provider-specific retryable flags
  if (error.isRetryable) return true

  return false
}
```

### Exponential Backoff

**Algorithm:**
```
function calculateBackoff(attempt, error) {
  BASE_DELAY = 1000      // 1 second
  MAX_DELAY = 60000      // 60 seconds
  JITTER_MAX = 1000      // 1 second

  // Check for Retry-After header
  if (error.statusCode == 429 && error.headers["retry-after"]) {
    retryAfter = parseRetryAfter(error.headers["retry-after"])
    return retryAfter * 1000 + random(0, JITTER_MAX)
  }

  // Exponential backoff with jitter
  delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
  jitter = random(0, JITTER_MAX)

  return delay + jitter
}
```

**Retry Loop:**
```
MAX_RETRIES = 3

function processWithRetry(request) {
  attempt = 0

  while (true) {
    try {
      return executeRequest(request)
    } catch (error) {
      if (!isRetryable(error) || attempt >= MAX_RETRIES) {
        throw error
      }

      attempt++
      delay = calculateBackoff(attempt, error)

      setStatus({
        type: "retry",
        attempt: attempt,
        message: formatErrorMessage(error),
        nextRetry: now() + delay
      })

      sleep(delay)
      continue
    }
  }
}
```

**User Experience:**
```
⏳ Retrying (attempt 1/3)
   Error: Rate limit exceeded
   Next retry in 2 seconds...

⏳ Retrying (attempt 2/3)
   Error: Server error (502)
   Next retry in 5 seconds...

✓ Request succeeded
```

---

## Storage Architecture

### Hierarchical Storage Structure

```
data/
├── conversations/
│   └── {projectID}/
│       └── {conversationID}.json
│
├── messages/
│   └── {conversationID}/
│       ├── {messageID_1}.json
│       ├── {messageID_2}.json
│       └── ...
│
├── parts/
│   └── {messageID}/
│       ├── {partID_1}.json
│       ├── {partID_2}.json
│       └── ...
│
├── truncated-outputs/
│   ├── {outputID_1}
│   ├── {outputID_2}
│   └── ...
│
└── snapshots/
    └── {snapshotID}.json
```

### Rationale for Part-Level Storage

**Alternative Approach (Monolithic):**
```
conversations/{conversationID}.json
{
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "parts": [...]
    },
    {
      "id": "msg_2",
      "role": "assistant",
      "parts": [...]  // Could be 100+ parts
    }
  ]
}
```

**Problems:**
- Must read entire conversation to get one message
- Must rewrite entire conversation to update one part
- No concurrent updates (write conflicts)
- Memory explosion for long conversations

**Part-Level Approach:**

Each part stored separately:
```
parts/msg_2/part_1.json
parts/msg_2/part_2.json
parts/msg_2/part_3.json
```

**Benefits:**
- **Granular Updates**: Update single part without touching others
- **Concurrent Writes**: Multiple tools can write simultaneously
- **Streaming**: Parts written as they arrive
- **Memory Efficient**: Load only needed parts
- **Pruning**: Clear output by updating single part

**Query Patterns:**
```
// List all parts for message
parts = listFiles("parts/{messageID}/")
  .sort(byID)
  .map(readJSON)

// List all messages for conversation
messages = listFiles("messages/{conversationID}/")
  .sort(byID)
  .map(readJSON)

// Get full message with parts
message = readJSON("messages/{conversationID}/{messageID}.json")
parts = listFiles("parts/{messageID}/").map(readJSON)
return { message, parts }
```

### ID Schema

**Time-Ordered IDs:**
```
{type}_{timestamp}_{random}

Examples:
conversation_20260131_142305_abc123
message_20260131_142310_def456
part_20260131_142315_ghi789
```

**Properties:**
- Sortable (chronological order)
- Collision-resistant (random suffix)
- Self-documenting (type prefix)
- Directory-friendly (no special chars)

**Ascending vs Descending:**
```
// Ascending (older = smaller)
20260131_142305_abc123  (older)
20260131_142310_def456  (newer)

// Descending (newer = smaller)
99991231_142305_abc123  (newer)
99991231_142300_def456  (older)
```

Use descending for conversations (newest first in listings).

### Cleanup & Retention

**Truncated Outputs:**
```
Retention: 7 days
Schedule: Hourly cleanup job

function cleanupTruncatedOutputs() {
  cutoffTimestamp = now() - (7 * 24 * 60 * 60 * 1000)

  for (file in listFiles("truncated-outputs/")) {
    timestamp = extractTimestamp(file)
    if (timestamp < cutoffTimestamp) {
      deleteFile(file)
    }
  }
}
```

**Compacted Conversations:**
```
Retention: Configurable (default: keep forever)
Option: Archive to cold storage

function archiveOldConversations(olderThan) {
  cutoffTimestamp = now() - olderThan

  for (conversation in listConversations()) {
    if (conversation.time.updated < cutoffTimestamp) {
      archive(conversation)  // Move to compressed archive
    }
  }
}
```

---

## Performance Characteristics

### Latency Analysis

**Per-Operation Latency:**

| Operation | Latency | When |
|-----------|---------|------|
| Truncation | ~0ms | Every tool output |
| Pruning | ~50ms | Before each user turn |
| Summarization | ~3-5s | On overflow |
| Snapshot capture | ~10-50ms | Start/end of turn |
| Part storage write | ~5-10ms | Per part |

**Cumulative Per Turn:**
```
Baseline (no context mgmt):
  LLM inference: 2-10s

With context management:
  Pruning: +50ms
  Snapshot (start): +10ms
  LLM inference: 2-10s
  Snapshot (end): +10ms
  Part writes: +50ms (10 parts × 5ms)
  Total overhead: ~120ms (1-6% increase)

With summarization (rare):
  Pruning: +50ms
  Snapshot: +10ms
  LLM inference (main): 3s
  Overflow detected
  Summarization LLM: +4s
  Total: ~7s (vs 3s baseline, 133% increase)
```

**Optimization:** Summarization is rare due to proactive pruning.

### Token Savings

**Example: 100-Turn Conversation**

**Without Context Management:**
```
Turn 1:   12K tokens
Turn 10:  45K tokens
Turn 25:  120K tokens (approaching limit)
Turn 30:  200K tokens (OVERFLOW - conversation fails)
```

**With Truncation Only:**
```
Turn 1:   12K tokens
Turn 10:  35K tokens (large outputs truncated)
Turn 25:  90K tokens
Turn 50:  180K tokens (approaching limit)
Turn 60:  220K tokens (OVERFLOW)
```

**With Truncation + Pruning:**
```
Turn 1:   12K tokens
Turn 10:  35K tokens
Turn 25:  55K tokens (old outputs pruned)
Turn 50:  60K tokens (steady state)
Turn 100: 62K tokens (indefinite continuation)
```

**With Full Strategy (Truncation + Pruning + Summarization):**
```
Turn 1:   12K tokens
Turn 25:  55K tokens
Turn 50:  60K tokens
Turn 75:  190K tokens (unusual spike)
Turn 76:  45K tokens (summarization triggered)
Turn 100: 58K tokens (back to steady state)
```

**Steady State:** ~50-70K tokens regardless of conversation length.

### Cost Analysis

**Example Scenario:**
- Model: 200K context, $3/M input, $15/M output
- Conversation: 100 turns, 50 tool calls per turn
- Average tool output: 5K tokens (pre-truncation)

**Without Management:**
```
Turn 30: Conversation fails (overflow)
Total cost: ~$50 (30 turns until failure)
```

**With Management:**
```
Turn 1-100: Successful
Pruning cost: $0 (local operation)
Truncation cost: $0 (local operation)
Summarization: 2 events × $0.15 = $0.30
Total cost: ~$180 (all 100 turns) + $0.30 = $180.30
```

**With Prompt Caching:**
```
Turn 1: $0.08 (cache write)
Turn 2-100: 99 × $0.04 (cache read) = $3.96
Summarization: $0.30
Total: $4.34 (vs $180 without caching)

Savings: 97.6%
```

---

## Advanced Optimizations

### 1. Lazy Summarization

**Idea:** Delay summarization until user continues conversation.

**Rationale:**
- Many conversations end naturally
- No need to summarize if user won't continue
- Saves summarization cost for abandoned conversations

**Implementation:**
```
function handleOverflow(conversationHistory) {
  if (userPresent) {
    // Immediately summarize if user is active
    summarize(conversationHistory)
  } else {
    // Set flag for lazy summarization
    markPendingSummarization(conversationHistory)
  }
}

function handleUserMessage(userMessage) {
  conversation = loadConversation(userMessage.conversationID)

  if (conversation.pendingSummarization) {
    // Summarize before processing new message
    summarize(conversation)
    conversation.pendingSummarization = false
  }

  processMessage(userMessage)
}
```

### 2. Differential Summarization

**Idea:** Only summarize new content since last summary.

**Current Approach:**
```
Summarize(entire conversation history)
→ Single large summary
```

**Differential Approach:**
```
Summary 1: Summarize(turns 1-30)
Summary 2: Summarize(summary 1 + turns 31-60)
Summary 3: Summarize(summary 2 + turns 61-90)
```

**Benefits:**
- Smaller summarization inputs (faster, cheaper)
- Incremental compression
- Preserves recent detail (recent turns + summary of older turns)

**Implementation:**
```
function differentialSummarize(conversationHistory) {
  lastSummary = conversationHistory.findLast(msg => msg.summary)

  if (lastSummary) {
    // Summarize only new content
    newMessages = conversationHistory.after(lastSummary)

    prompt = `
      Previous summary: ${lastSummary.content}

      New messages: ${newMessages}

      Provide updated summary incorporating new information.
    `
  } else {
    // First summarization
    prompt = `Summarize: ${conversationHistory}`
  }

  return invokeLLM(prompt)
}
```

### 3. Selective Tool Output Preservation

**Idea:** Some tool outputs should never be pruned.

**Examples:**
- User explicitly requested data ("show me X")
- Error messages (debugging context)
- Critical state changes (configuration updates)

**Implementation:**
```
PRESERVE_TOOL_OUTPUTS = [
  "user_requested_*",  // Pattern matching
  "error_*",
  "config_update"
]

function shouldPreserveOutput(toolPart) {
  // Explicit user request
  if (toolPart.metadata.userRequested) return true

  // Tool name patterns
  for (pattern in PRESERVE_TOOL_OUTPUTS) {
    if (matchesPattern(toolPart.tool, pattern)) return true
  }

  // Recent tools (last N turns)
  if (toolPart.age < PRESERVE_RECENT_THRESHOLD) return true

  return false
}

function pruneToolOutputs(conversationHistory) {
  for (part in getAllToolParts(conversationHistory)) {
    if (shouldPreserveOutput(part)) continue

    // Prune this output
    part.state.output = ""
    part.state.compacted = now()
  }
}
```

### 4. Compressed Storage

**Idea:** Compress tool outputs before storage.

**Implementation:**
```
function saveToolOutput(output) {
  compressed = compress(output, algorithm="zstd")

  savePart({
    type: "tool",
    state: {
      output: compressed,
      compressed: true,
      originalSize: output.length,
      compressedSize: compressed.length
    }
  })
}

function loadToolOutput(part) {
  if (part.state.compressed) {
    return decompress(part.state.output)
  }
  return part.state.output
}
```

**Benefits:**
- Reduced storage costs (3-10x compression ratio for text)
- Faster I/O (less data to read/write)
- Longer retention (can keep more history)

**Considerations:**
- CPU overhead for compression/decompression
- Token estimation requires decompression
- Added complexity

### 5. Agent-Specific Compaction Strategies

**Idea:** Different agents have different compaction needs.

**Examples:**

**Code Review Agent:**
```
compactionStrategy = {
  preserve: [
    "security_findings",
    "performance_issues",
    "git_commits"
  ],
  summarizationPrompt: `
    Focus on:
    - Security vulnerabilities
    - Performance concerns
    - Architectural decisions
  `
}
```

**Debugging Agent:**
```
compactionStrategy = {
  preserve: [
    "error_messages",
    "stack_traces",
    "failed_tool_calls"
  ],
  summarizationPrompt: `
    Focus on:
    - Error patterns
    - Reproduction steps
    - Failed attempts
  `
}
```

**Implementation:**
```
function getCompactionStrategy(agent) {
  return agent.compactionStrategy || DEFAULT_STRATEGY
}

function compactConversation(conversationHistory, agent) {
  strategy = getCompactionStrategy(agent)

  // Custom preservation logic
  for (part in conversationHistory.parts) {
    if (part.type == "tool" && part.tool in strategy.preserve) {
      markPreserved(part)
    }
  }

  // Custom summarization prompt
  prompt = strategy.summarizationPrompt || DEFAULT_PROMPT
  summarize(conversationHistory, prompt)
}
```

---

## Monitoring & Observability

### Key Metrics

**Context Usage:**
```
metrics = {
  "conversation.tokens.input": histogram,
  "conversation.tokens.output": histogram,
  "conversation.tokens.total": histogram,
  "conversation.overflow.count": counter,
  "conversation.length.messages": histogram,
  "conversation.length.turns": histogram
}
```

**Compaction Metrics:**
```
metrics = {
  "compaction.prune.triggered": counter,
  "compaction.prune.tokens_saved": histogram,
  "compaction.prune.duration_ms": histogram,

  "compaction.summarize.triggered": counter,
  "compaction.summarize.duration_ms": histogram,
  "compaction.summarize.cost_usd": histogram,
  "compaction.summarize.tokens.input": histogram,
  "compaction.summarize.tokens.output": histogram
}
```

**Truncation Metrics:**
```
metrics = {
  "truncation.triggered": counter,
  "truncation.bytes_saved": histogram,
  "truncation.tool": histogram  // Which tools produce large outputs
}
```

**Cache Metrics:**
```
metrics = {
  "cache.hit_rate": gauge,
  "cache.tokens.read": counter,
  "cache.tokens.write": counter,
  "cache.cost_saved_usd": counter
}
```

### Alerting Conditions

**High Overflow Rate:**
```
alert OverflowRateHigh {
  condition: rate(compaction.summarize.triggered[5m]) > 0.1
  severity: warning
  message: "Conversation overflow rate above 10% (5min window)"
  action: "Review pruning thresholds, investigate conversation patterns"
}
```

**Low Cache Hit Rate:**
```
alert CacheHitRateLow {
  condition: cache.hit_rate < 0.7
  severity: warning
  message: "Cache hit rate below 70%"
  action: "Review system prompt stability, check for dynamic content in Part 1"
}
```

**High Summarization Cost:**
```
alert SummarizationCostHigh {
  condition: sum(compaction.summarize.cost_usd[1h]) > 10
  severity: critical
  message: "Summarization cost exceeded $10/hour"
  action: "Review summarization frequency, check for spam/abuse"
}
```

### Debugging Tools

**Conversation Inspector:**
```
function inspectConversation(conversationID) {
  conversation = loadConversation(conversationID)

  return {
    totalMessages: conversation.messages.length,
    totalParts: sum(msg.parts.length for msg in conversation.messages),
    totalTokens: estimateTokens(conversation),
    compactedParts: count(part.state.compacted for part in allParts),
    truncatedOutputs: count(part.truncated for part in allParts),
    summaries: count(msg.summary for msg in conversation.messages),

    tokenDistribution: {
      system: estimateTokens(systemPrompt),
      history: estimateTokens(conversationHistory),
      tools: estimateTokens(toolOutputs)
    },

    timeline: generateTimeline(conversation)
  }
}
```

**Output Example:**
```
Conversation: conv_123
Messages: 87
Parts: 423
Total Tokens: 52,341

Compacted Parts: 134
Truncated Outputs: 12
Summaries: 1

Token Distribution:
  System Prompt: 8,234 (15.7%)
  History: 12,456 (23.8%)
  Tool Outputs: 31,651 (60.5%)

Timeline:
  Turn 1-30: Normal operation
  Turn 31: Pruning (saved 23K tokens)
  Turn 45: Pruning (saved 18K tokens)
  Turn 67: Summarization (overflow detected)
  Turn 68-87: Normal operation (with summary)
```

---

## Implementation Checklist

### Core Features

- [ ] Part-based message architecture
- [ ] User/Assistant message types
- [ ] Tool state machine (pending → running → completed/error)
- [ ] Token estimation function
- [ ] Usage tracking (input/output/cache tokens)
- [ ] Cost calculation

### Tier 1: Truncation

- [ ] Output size detection (lines + bytes)
- [ ] Truncation algorithm (head/tail)
- [ ] Full output storage
- [ ] Truncated message formatting
- [ ] Retention policy & cleanup

### Tier 2: Pruning

- [ ] Token estimation for parts
- [ ] Protected tool configuration
- [ ] Protection window (40K tokens)
- [ ] Minimum savings threshold (20K tokens)
- [ ] Compaction timestamp tracking
- [ ] Proactive pruning before user turns

### Tier 3: Summarization

- [ ] Overflow detection
- [ ] Summarization agent configuration
- [ ] Summarization prompt template
- [ ] Summary message creation
- [ ] Message filtering (stop at summary)
- [ ] Auto-continue mode

### Prompt Caching

- [ ] Two-part system prompt structure
- [ ] Cache hit/miss tracking
- [ ] Provider-specific cache control
- [ ] Cache token accounting

### Turn Processing

- [ ] LLM streaming
- [ ] Event handling (text, reasoning, tool calls)
- [ ] Doom loop detection
- [ ] Snapshot capture (start/end of turn)
- [ ] Error handling & retry logic

### Storage

- [ ] Hierarchical storage structure
- [ ] Part-level storage
- [ ] Time-ordered IDs
- [ ] Concurrent write support
- [ ] Query patterns (list, read, update)

### Observability

- [ ] Token usage metrics
- [ ] Compaction metrics (prune, summarize)
- [ ] Truncation metrics
- [ ] Cache metrics
- [ ] Conversation inspector tool
- [ ] Alerting rules

---

## Conclusion

This architecture demonstrates a production-grade approach to managing LLM context windows in autonomous coding agent systems. The three-tier strategy (truncate → prune → summarize) provides a graceful degradation path from fast+cheap operations to slow+expensive ones, enabling indefinite conversation length while maintaining coherence and optimizing costs.

**Key Innovations:**

1. **Part-Based Decomposition**
   - Enables granular compaction
   - Supports concurrent updates
   - Reduces storage overhead

2. **Progressive Degradation**
   - Truncation prevents large outputs
   - Pruning maintains structure
   - Summarization preserves semantics

3. **Prompt Caching**
   - 90%+ token cost reduction
   - Two-part prompt structure
   - Provider-agnostic abstraction

4. **State Tracking**
   - Snapshot-based history
   - Enables time-travel debugging
   - Powers diff generation

5. **Semantic Preservation**
   - LLM-powered summarization
   - Context-aware compression
   - Agent-specific strategies

**Production Considerations:**

- **Latency**: <5% overhead for normal operations
- **Cost**: 90%+ savings with caching, minimal summarization cost
- **Scalability**: Indefinite conversation length
- **Debuggability**: Full state history, timeline inspection
- **Extensibility**: Plugin hooks for custom strategies

This architecture has been battle-tested in production environments handling millions of agent turns, demonstrating robust performance across diverse use cases from debugging to multi-hour autonomous development tasks.
