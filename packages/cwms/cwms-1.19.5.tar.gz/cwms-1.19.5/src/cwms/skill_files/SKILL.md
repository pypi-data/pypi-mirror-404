---
name: cwms
description: "Extended context memory through intelligent swap-to-disk. Automatically manages long conversations by storing older context in searchable format. This skill activates automatically when conversations exceed 20,000 tokens, when user references something from earlier in a long conversation, or on /cwms commands."
allowed-tools: Read, Bash, Glob, Grep, Write
---

# Context Window Management - Operational Instructions

This skill provides extended context memory for Claude Code by swapping older conversation context to disk and retrieving it when needed.

## Automatic Activation

This skill should activate in these situations:

1. **Long conversations** - When you estimate the conversation exceeds ~20,000 tokens
2. **Past context requests** - When user asks about something discussed earlier
3. **Session start** - Check for existing context from previous sessions
4. **Explicit commands** - `/cwms status`, `/cwms search <query>`, etc.

## Token Estimation

Estimate tokens mentally: **~4 characters = 1 token**

- Short message (100 chars) = ~25 tokens
- Medium message (500 chars) = ~125 tokens
- Long message (2000 chars) = ~500 tokens
- Code blocks tend to have higher token density

## Commands Reference

All commands output JSON. Parse the output to get results.

### Check Status

```bash
cwms status --project "PROJECT_NAME"
```

Returns: `{"success": true, "total_chunks": N, "total_tokens": N, ...}`

### Swap Context to Disk

```bash
cwms swap --project "PROJECT_NAME" --messages-file /tmp/ctx_swap.json
```

Input file format:

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Returns: `{"success": true, "chunks_stored": N, "tokens_stored": N, "summary": "..."}`

### Search Past Context

```bash
cwms search --project "PROJECT_NAME" --query "search terms" --top-k 5
```

Returns: `{"success": true, "results": [{"summary": "...", "score": 0.85, ...}]}`

### Retrieve Formatted Context

```bash
cwms retrieve --project "PROJECT_NAME" --query "topic" --top-k 5
```

Returns: `{"success": true, "context": "formatted text for injection"}`

### List Summaries

```bash
cwms summaries --project "PROJECT_NAME"
```

Returns: `{"success": true, "summaries": [{"timestamp": "...", "summary": "..."}]}`

### Estimate Tokens

```bash
cwms estimate --messages-file /tmp/ctx.json --threshold 32000
```

Returns: `{"success": true, "token_count": N, "should_swap": true/false}`

### Clear Project Context

```bash
cwms clear --project "PROJECT_NAME" --confirm
```

### Show Configuration

```bash
cwms config
```

## Workflow: Session Start

When starting a new session or when this skill first activates:

1. Get the project name:

   ```bash
   basename "$PWD"
   ```

2. Check for existing context:

   ```bash
   cwms status --project "$(basename $PWD)"
   ```

3. If `total_chunks > 0`, inform user:
   > "Previous context available: N chunks (M tokens) from DATE"

## Workflow: Automatic Swap and Clear (CRITICAL)

Context management is **automated** via hooks. When context exceeds the threshold (~32k tokens):

1. **Stop hook detects** - The auto-swap hook monitors context size
2. **Swap executes** - Older context is swapped to disk automatically
3. **You receive instruction** - A blocked stop with "EXECUTE `/clear` NOW"
4. **You execute `/clear`** - This resets your context window
5. **Bridge summary injected** - SessionStart hook provides context continuity

### When You See the Clear Instruction

When your stop is blocked with a message like:

```
🔄 **CONTEXT SWAP COMPLETE - ACTION REQUIRED**
```

**YOU MUST:**

1. Execute `/clear` immediately
2. The bridge summary will be automatically injected
3. Continue the conversation normally

### Why This Matters

- **[Research](https://arxiv.org/abs/2512.24601)** shows LLM performance degrades significantly after ~33k tokens
- The swap preserves conversation history to searchable disk storage
- The clear resets your active context for optimal performance
- The bridge summary maintains continuity of understanding

### DO NOT Skip the /clear

This is essential for maintaining optimal performance. The system handles:

- Preserving recent context (last ~8,000 tokens)
- Saving older context to disk (searchable)
- Providing a bridge summary after clear

## Workflow: Manual Swap (Optional)

If you need to manually swap context:

1. **Write messages to temp file**:

   ```json
   {
     "messages": [
       {"role": "user", "content": "earlier user message"},
       {"role": "assistant", "content": "earlier assistant response"}
     ]
   }
   ```

2. **Run swap command**:

   ```bash
   cwms swap --project "$(basename $PWD)" --messages-file /tmp/ctx_swap.json
   ```

3. **Inform user and execute /clear**:
   > "Swapped N chunks (M tokens) to disk. Executing /clear for optimal performance."

4. **Clean up temp file**:

   ```bash
   rm /tmp/ctx_swap.json
   ```

## Workflow: Context Retrieval

When user asks about something from earlier in a long conversation:

1. **Detect the need** - User says things like:
   - "What did we discuss about X earlier?"
   - "Remember when we worked on Y?"
   - "Go back to what you said about Z"

2. **Search for relevant context**:

   ```bash
   cwms retrieve --project "$(basename $PWD)" --query "relevant topic"
   ```

3. **Parse the result** and incorporate the `context` field into your response

4. **Cite the source**:
   > "From earlier in our conversation: [relevant information]"

## Workflow: Explicit Commands

### `/cwms status`

```bash
cwms status --project "$(basename $PWD)"
```

Format and display the results to the user.

### `/cwms search <query>`

```bash
cwms search --project "$(basename $PWD)" --query "<query>"
```

Display search results with scores and summaries.

### `/cwms summary`

```bash
cwms summaries --project "$(basename $PWD)"
```

Display all chunk summaries chronologically.

### `/cwms clear`

```bash
cwms clear --project "$(basename $PWD)" --confirm
```

Confirm with user before clearing.

### `/cwms config`

```bash
cwms config
```

Display current configuration settings.

## Configuration

Default configuration values:

- **Threshold**: 32,000 tokens (swap at 80% = 25,600 tokens)
- **Preserve recent**: 8,000 tokens always kept
- **Chunk size**: 2,000 tokens per chunk
- **Retrieval top_k**: 5 chunks

Users can customize by creating `~/.claude/cwms/config.yaml`:

```yaml
context:
  threshold_tokens: 32000
  swap_trigger_percent: 0.80
  preserve_recent_tokens: 8000

storage:
  directory: ~/.claude/cwms
  max_age_days: 30

embeddings:
  provider: none  # none | local

retrieval:
  top_k: 5
  min_similarity: 0.7
```

## Best Practices

1. **Don't swap too aggressively** - Only swap when approaching the threshold
2. **Preserve recent context** - Always keep the most recent ~8,000 tokens
3. **Use descriptive queries** - When retrieving, use specific topic keywords
4. **Inform the user** - Always tell users when you swap or retrieve context
5. **Check on session start** - Users appreciate knowing their history is available

## Troubleshooting

### CLI not found

Ensure the package is installed:

```bash
pip install cwms
# or
poetry install
```

### Embedding errors

If embeddings fail, the system falls back to keyword search. Options for semantic search:

**Option 1: Local embeddings**

```bash
pip install 'cwms[local]'  # Requires torch
```

Note: Local embeddings may have installation issues on some Mac systems.

**Option 2: Keyword search only (no dependencies)**
Set `embeddings.provider: none` in config - uses BM25 keyword matching (default).

### Permission errors

Check storage directory permissions:

```bash
ls -la ~/.claude/cwms/
```
