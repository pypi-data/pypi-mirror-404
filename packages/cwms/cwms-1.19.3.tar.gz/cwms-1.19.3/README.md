# Context Window Management: Transparent Extended Memory for Claude Code

Context Window Management is a Claude Code skill that provides **transparent extended memory** for long coding sessions. When your conversation grows large, it persists older content to disk with summaries and keywords, enabling retrieval when needed. After a context reset (`/clear`), a bridge summary is injected so Claude retains awareness of previous work.

**What it does:**

- **Persists conversation history** — older context saved to disk with searchable summaries
- **Bridge summaries after /clear** — Claude receives context about what was discussed
- **On-demand retrieval** — full conversation history searchable via keyword or semantic search
- **Cross-session memory** — context persists across sessions and is retrievable anytime

**Current limitations:**

- **Manual /clear required** — when threshold is reached, Claude is instructed to execute `/clear`, but this requires the command to be run
- **Default extractive summaries** — summaries use regex extraction by default (LLM-powered summarization available as opt-in, see below)
- **Manual retrieval** — relevant past context must be explicitly searched for (proactive retrieval planned)

## Quick Start

```bash
# Install from PyPI
pip install cwms

# Or install from source
git clone https://github.com/Taderich73/cwms.git
cd cwms
poetry install

# Install the Claude Code skill
cwms install-skill

# Optional: Install with automatic context swapping
cwms install-skill --auto-swap

# Check status
cwms status --project "my-project"

# Search stored context
cwms search --project "my-project" --query "authentication"

# View configuration
cwms config
```

## Why Context Window Management?

**Problem**: Claude Code's context window fills up during long sessions. Performance degrades as context grows ([research shows significant degradation after ~33k tokens](https://arxiv.org/abs/2512.24601)), and eventually you hit the limit, losing earlier conversation history.

**Solution**: Context Window Management provides transparent extended memory by:
1. **Monitoring** token usage and warning when approaching threshold
2. **Persisting** older conversation chunks to disk with summaries and keywords
3. **Injecting** a bridge summary after `/clear` so Claude knows what was discussed
4. **Enabling retrieval** of full conversation history via search

This creates a workflow where context can be reset without losing awareness of previous work.

## Core Workflow: Extended Memory with Bridge Summaries

The key feature is the **bridge summary** that provides continuity across context resets. Here's the workflow:

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. MONITOR: Token usage tracked via status line                    │
│     └─> Writes to /tmp/claude-context-{session}.json               │
├─────────────────────────────────────────────────────────────────────┤
│  2. THRESHOLD: Context reaches 80% of limit (e.g., 25,600/32,000)  │
│     └─> auto-swap hook triggers on Stop event                       │
├─────────────────────────────────────────────────────────────────────┤
│  3. SWAP: Older content saved to disk                               │
│     ├─> Chunks stored at ~/.claude/cwms/{project}/         │
│     ├─> Summary + keywords extracted (regex or LLM-powered)         │
│     ├─> Bridge summary saved to /tmp/                               │
│     └─> Continuation guide with search queries saved                │
├─────────────────────────────────────────────────────────────────────┤
│  4. PROMPT: Hook instructs Claude to execute /clear                 │
│     └─> ⚠️ Claude or user must run /clear (not yet automatic)       │
├─────────────────────────────────────────────────────────────────────┤
│  5. INJECT: After /clear, SessionStart hook fires                   │
│     ├─> Reads bridge summary from /tmp/                             │
│     ├─> Injects as additionalContext automatically                  │
│     └─> Claude receives awareness of swapped content                │
├─────────────────────────────────────────────────────────────────────┤
│  6. CONTINUE: Claude resumes with:                                  │
│     ├─> Summary of what was being worked on                         │
│     ├─> Key topics, files referenced, actions taken                 │
│     └─> Suggested search queries if details needed                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Note:** Step 4 currently requires Claude to execute the `/clear` command when prompted. True automatic clearing is not yet possible due to Claude Code platform limitations.

### What Claude Sees After Auto-Swap

After `/clear`, Claude automatically receives context like this:

```markdown
## Context Bridge (Auto-Swap Recovery)

Your context was automatically swapped to disk and cleared for optimal performance.

### Summary of Swapped Content

**Scope:** 3 conversation segment(s), 18,500 tokens

**Key Topics:** authentication, jwt, middleware, session
**Files Referenced:** src/auth.py, src/middleware.py, config.yaml

**Segment Summaries:**
1. User asked about implementing JWT authentication...
2. Assistant created middleware handler for token validation...
3. Discussion of session management strategies...

### Suggested Context Recovery Queries

Run these to retrieve detailed context if needed:
- `cwms retrieve --project "myapp" --query "jwt authentication"`
```

### What Happens After /clear

The bridge summary is injected automatically after `/clear`, giving Claude awareness of:

- What was being worked on
- Key topics and files referenced
- Actions that were taken
- Suggested search queries for retrieving details

Claude can continue the task with this context. Use `cwms retrieve` when Claude needs the full content of swapped conversations (e.g., exact code that was written, specific error messages).

**Current limitation:** The `/clear` command must be executed by Claude when prompted, or manually by the user. The swap-to-disk happens automatically, but the context reset requires action.

## How It Works

Context Window Management provides transparent extended memory:

1. **Monitors conversation size** - Tracks token usage via status line throughout the session
2. **Smart swapping** - Persists older context to disk at safe points (not mid-code-block, not during tool execution)
3. **Generates summaries** - Extracts key topics, files, and actions (regex by default; optional LLM-powered via API)
4. **Prompts for /clear** - When threshold reached, instructs Claude to execute `/clear`
5. **Bridge injection** - After `/clear`, automatically injects summary so Claude has awareness of previous work
6. **On-demand retrieval** - Full content retrievable via search when details needed

## Configuration

Configure Context Window Management by creating a config file. The system checks these locations in order:

1. `.claude/cwms/config.yaml` (project-specific)
2. `~/.claude/cwms/config.yaml` (user-level)

```yaml
context:
  threshold_tokens: auto            # auto | 32000 | 64000 | etc.
  swap_trigger_percent: 0.80        # Swap at 80% of threshold
  preserve_recent_tokens: 8000      # Always keep recent context
  chunk_size: 2000                  # Target chunk size
  chunk_overlap: 200                # Overlap for continuity

storage:
  directory: ~/.claude/cwms        # Storage location
  max_age_days: 30                  # Cleanup old chunks (0 = never)

embeddings:
  provider: none                    # none | local
  local_model: all-MiniLM-L6-v2    # For local provider

retrieval:
  top_k: 5                          # Number of chunks to retrieve
  min_similarity: 0.7               # Minimum similarity threshold
  recency_boost: 0.1                # Boost for recent chunks
  search_mode: auto                 # auto | keyword | semantic | hybrid
  bm25_k1: 1.2                      # BM25 term frequency saturation
  bm25_b: 0.75                      # BM25 document length normalization
  hybrid_keyword_weight: 0.3        # Weight for BM25 in hybrid mode
  hybrid_semantic_weight: 0.7       # Weight for semantic in hybrid mode
  ann_enabled: true                 # Use approximate nearest neighbors
  ann_threshold: 100                # Min chunks before enabling ANN

summarization:
  provider: regex                   # regex | api (default: regex)
  api_model: claude-3-haiku-20240307  # Model for API summarization
  api_max_tokens: 500               # Max tokens for summary response
  monthly_cost_limit_usd: 1.00      # Optional spending cap (null = no limit)
```

### LLM-Powered Summarization (Optional)

For higher-quality abstractive summaries, you can enable API-based summarization using your Anthropic API key. This produces more coherent and context-aware summaries compared to the default regex-based extraction.

#### Setup

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)

2. Set the environment variable:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

3. Enable in config:
   ```yaml
   # ~/.claude/cwms/config.yaml
   summarization:
     provider: api
     monthly_cost_limit_usd: 1.00  # Optional spending cap
   ```

4. Install the optional dependency:
   ```bash
   pip install anthropic
   # Or with poetry:
   poetry install --extras "api"
   ```

#### Cost

Uses Claude 3 Haiku by default (~$0.001-0.005 per swap). With typical usage:
- 10 swaps/day × 30 days = ~$0.30-1.50/month

Set `monthly_cost_limit_usd` to cap spending. When the limit is reached, summarization automatically falls back to regex.

#### Checking Usage

```bash
cwms status --summarization
```

Output:
```
Summarization Configuration:
  Provider: api
  Model: claude-3-haiku-20240307

Monthly Usage:
  Swaps this month: 47
  Estimated spend: $0.12
  Cost limit: $1.00
  Remaining: $0.88
```

#### Fallback Behavior

If the API is unavailable, rate limited, or cost limit is reached, summarization automatically falls back to regex-based extraction. This ensures the system always works, even without API access.

### Context Window Adaptation

Context Window Management automatically adapts to different Claude models:

| Model | Context Window | Default Threshold |
|-------|----------------|-------------------|
| Claude 4 / Opus 4.5 | 200k | 50k |
| Claude 4 / Sonnet 4 | 200k | 50k |
| Claude 3.x models | 200k | 50k |
| Claude 2.x models | 100k | 50k |

Set `threshold_tokens: auto` to let Context Window Management calculate the optimal threshold based on the model.

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CWMS_THRESHOLD` | Override threshold (int, "32k", or "auto") | `64000`, `64k`, `auto` |
| `CWMS_PRESERVE_RECENT` | Override preserve_recent_tokens | `8000` |
| `CWMS_LOG_LEVEL` | Log level: DEBUG, INFO, WARNING, ERROR | `DEBUG` |
| `CWMS_LOG_FILE` | Optional file path for log output | `/tmp/cc.log` |
| `CWMS_LOG_JSON` | Set to "1" for JSON log format | `1` |
| `CLAUDE_MODEL` | Model name for auto-threshold | `claude-opus-4-5` |

## Embedding Providers

Choose based on your needs:

| Provider | Setup | Pros | Cons |
|----------|-------|------|------|
| **none** | No setup | Works immediately, no dependencies | Keyword search only |
| **local** | `pip install 'cwms[local]'` | Offline, no API costs, privacy, ChromaDB vector store | ~400MB model, slower first load |

When `embeddings.provider: local` is set, Context Window Management automatically uses **ChromaDB** as the vector store backend. ChromaDB provides:
- Persistent storage of embeddings (survives restarts)
- Efficient approximate nearest neighbor (ANN) search
- Automatic indexing and query optimization

## CLI Commands

Context Window Management provides a comprehensive CLI for manual control and integration with Claude Code:

### Status

Check current memory status and statistics for a project:

```bash
cwms status --project "my-project"
```

### Swap

Store conversation messages to disk (used internally by the skill):

```bash
cwms swap --project "my-project" --messages-file /tmp/messages.json
```

Input file format:

```json
{
  "messages": [
    {"role": "user", "content": "What is authentication?"},
    {"role": "assistant", "content": "Authentication is..."}
  ]
}
```

### Search

Search stored context for relevant chunks:

```bash
cwms search --project "my-project" --query "authentication" --top-k 5
```

### Retrieve

Retrieve and format context for injection into conversations:

```bash
cwms retrieve --project "my-project" --query "login flow"
```

### Summaries

List summaries of all stored chunks:

```bash
cwms summaries --project "my-project"
```

### Clear

Clear all stored context for a project:

```bash
cwms clear --project "my-project" --confirm
```

### Config

Display current configuration:

```bash
cwms config
```

### Estimate

Estimate token count for messages:

```bash
cwms estimate --messages-file /tmp/messages.json --threshold 32000
```

### Context Window

Show context window configuration for a model:

```bash
cwms context-window
cwms context-window --model claude-opus-4-5
```

### Debug

Show debug information and performance metrics:

```bash
cwms debug --project "my-project"
cwms debug --project "my-project" --recent 20 --failures-only
```

### Validate

Validate storage integrity:

```bash
cwms validate --project "my-project" --verbose
cwms validate --project "my-project" --fix
```

### Validate Messages

Validate a messages file before swapping:

```bash
cwms validate-messages --messages-file messages.json
cwms validate-messages --messages-file session.jsonl --verbose --strict
```

### Import History

Import from Claude Code session files:

```bash
# Import from single session file
cwms import-history --project "my-project" \
    --history-file ~/.claude/projects/.../session.jsonl

# Import from sessions directory with filters
cwms import-history --project "my-project" \
    --sessions-dir ~/.claude/projects \
    --since "2025-01-01" \
    --filter-project "/path/to/project" \
    --dry-run
```

### Repair

Repair corrupted storage:

```bash
cwms repair --project "my-project"
```

## Skill Commands

When using Context Window Management as a Claude Code skill, you can use these slash commands:

- `/cwms status` - Show current memory status and statistics
- `/cwms search <query>` - Search stored context for a query
- `/cwms summary` - Show summaries of all stored chunks
- `/cwms clear` - Clear all stored context for current project
- `/cwms config` - Display current configuration

## When Context Window Management Activates

| Trigger | What Happens |
|---------|--------------|
| **Threshold exceeded** (~80% of limit) | Auto-swap hook saves content to disk, prompts Claude to execute `/clear` |
| **After /clear** | SessionStart hook injects bridge summary automatically |
| **User asks about past context** | Claude can search and retrieve relevant chunks |
| **New session starts** | Project index available for cross-session memory |

**Note:** The swap-to-disk and bridge summary injection are automatic. However, the `/clear` command must currently be executed by Claude when prompted (or manually by the user).

## Safe Swap Detection

Context Window Management only swaps context at safe points:

✅ **Safe to swap:**

- Assistant has just completed a response
- No code blocks are being generated
- No tool calls are pending
- User's last request is fully satisfied

❌ **Not safe to swap:**

- Currently generating code
- Tools are executing
- Mid-conversation or incomplete response
- Critical context is still needed

## Storage Format

Context Window Management stores chunks in a simple, human-readable JSONL format:

```
~/.claude/cwms/
├── {project-hash}/
│   ├── project.txt       # Original project name
│   ├── chunks.jsonl      # Append-only chunk storage
│   └── index.json        # Fast lookup index
├── chroma/               # ChromaDB vector store (when embeddings.provider: local)
│   └── ...               # ChromaDB internal files
```

Each chunk contains:

- **Content**: Full conversation text
- **Summary**: Brief summary for retrieval
- **Keywords**: Extracted keywords
- **Embedding**: Optional vector for semantic search
- **Metadata**: Timestamp, token count, file references

## Examples

### Example 1: Swap and Recovery Workflow

```
[Working on authentication feature - context reaches 25,600 tokens (80%)]

─────────────────────────────────────────────────────────────────────
🔄 CONTEXT SWAP COMPLETE - ACTION REQUIRED

Context was at 80.0% (25,600 tokens) - exceeds optimal threshold.
Successfully swapped 3 chunk(s) (17,500 tokens) to disk.

⚡ EXECUTE /clear NOW to reset context window for optimal performance.
─────────────────────────────────────────────────────────────────────

[Claude executes /clear as instructed, or user runs it manually]

─────────────────────────────────────────────────────────────────────
[Session restarted - Bridge summary automatically injected]

Claude now sees:
  ## Context Bridge (Auto-Swap Recovery)

  ### Summary of Swapped Content
  **Key Topics:** jwt, authentication, middleware, bcrypt
  **Files Referenced:** src/auth.py, src/middleware.py

  **Segment Summaries:**
  1. User asked about JWT authentication implementation...
  2. Created password hashing with bcrypt...
  3. Set up middleware for token validation...
─────────────────────────────────────────────────────────────────────

User: Now let's add refresh token support

[Claude continues with awareness of JWT work, can retrieve details if needed]
```

### Example 2: Retrieving Detailed Context When Needed

```
[After auto-swap, Claude has the summary but needs exact code]

Claude: I see we implemented JWT authentication earlier. Let me retrieve
        the exact implementation details.

$ cwms retrieve --project "myapp" --query "jwt middleware"

[Full conversation content returned, including the actual code written]

Claude: I found the middleware code. The validateToken function is at
        src/middleware.py:45. Now I'll add refresh token support that
        integrates with this existing implementation...
```

### Example 3: Cross-Session Memory

```
[New session, different day]

User: Continue working on the authentication system

[Claude searches stored context]
$ cwms search --project "myapp" --query "authentication"

✓ Found 12 stored chunks for this project
✓ Most relevant: JWT implementation, password hashing, middleware setup

Claude: I found our previous work on the authentication system. We
        implemented JWT tokens with bcrypt password hashing. The main
        files are src/auth.py and src/middleware.py. What aspect would
        you like to continue with?
```

### Example 4: Manual Search for Specific Topics

```
User: /cwms search "database migration"

Context Window Management Results:
1. [2024-01-15 10:30] Added Alembic for migrations (Score: 0.92)
   "Set up database migration system using Alembic..."

2. [2024-01-15 11:45] Created initial migration (Score: 0.85)
   "Generated first migration with user and post tables..."

3. [2024-01-14 15:20] Discussed migration strategies (Score: 0.78)
   "Decided on Alembic over raw SQL for maintainability..."
```

## Technical Details

### Token Estimation

Context Window Management uses tiktoken (cl100k_base) for accurate token counting, with a character-based fallback (chars/4) if tiktoken is unavailable.

### Chunking Strategy

- **Logical boundaries**: Splits at natural conversation breaks
- **Preserves coherence**: Never splits mid-code-block or mid-tool-call
- **Overlap**: Includes 200-token overlap between chunks for continuity
- **Complete exchanges**: Preserves user/assistant message pairs

### Retrieval Ranking

Results are ranked by:

- **Semantic similarity** (if embeddings enabled) - cosine similarity
- **Keyword overlap** - TF-IDF-style matching with summaries
- **Recency boost** - Slight preference for newer chunks
- **Importance metadata** - User-tagged or ML-detected importance

### Privacy and Security

- **Local storage**: All data stored locally in `~/.claude/cwms/`
- **Project isolation**: Each project has separate storage
- **Optional embeddings**: Choose local embeddings for full privacy
- **No telemetry**: Context Window Management never sends data externally (except to chosen embedding provider)

## Troubleshooting

### Issue: Context Window Management not activating

**Check:**

1. Configuration file exists: `~/.claude/cwms/config.yaml`
2. Storage directory is writable: `~/.claude/cwms/`
3. Token threshold is appropriate for your conversations

### Issue: Poor retrieval quality

**Solutions:**

- Enable embeddings: `embeddings.provider: local`
- Lower similarity threshold: `retrieval.min_similarity: 0.6`
- Increase retrieval count: `retrieval.top_k: 10`

### Issue: Embeddings not working

**Check:**

- Dependencies installed: `pip install 'cwms[local]'`
- Model name is correct in config

### Issue: Storage growing too large

**Solutions:**

- Set max age: `storage.max_age_days: 7` (cleanup old chunks)
- Use `/cwms clear` to remove old project data
- Manually delete `~/.claude/cwms/{project-hash}/` directories

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Token estimation | <1ms | Uses tiktoken or fallback |
| Chunk creation | 10-50ms | Depends on summary generation |
| Keyword search | 5-20ms | Scans index only |
| Semantic search | 50-500ms | Depends on provider and chunk count |
| Swap-out | 100-1000ms | Depends on chunk count and embedding |

## Installation

### From PyPI (when published)

```bash
pip install cwms

# With local embeddings
pip install 'cwms[local]'

# With API summarization
pip install 'cwms[api]'

# With all extras
pip install 'cwms[all]'
```

### From Source

```bash
git clone https://github.com/Taderich73/cwms.git
cd cwms
poetry install

# With local embeddings
poetry install --extras "local"

# With API summarization
poetry install --extras "api"
```

### As a Claude Code Skill

After installing the package, install the skill to Claude Code:

```bash
# Basic installation (skill commands only)
cwms install-skill

# With automatic context swapping (recommended)
cwms install-skill --auto-swap
```

This installs:

- **SKILL.md** to `~/.claude/skills/cwms/` (skill commands for Claude)
- **config.yaml** to `~/.claude/cwms/` (configuration template)
- **Auto-swap components** (optional): Status line and hooks for automatic swapping

**Auto-swap features:**

- Monitors context usage in real-time
- Automatically swaps when conversation exceeds 80% of threshold (default: 25,600 tokens)
- Preserves most recent 8,000 tokens for continuity
- Notifies you when swapping occurs

See `.claude/AUTO_SWAP_README.md` (after installation) for full auto-swap documentation.

## Resources

- **GitHub**: <https://github.com/Taderich73/cwms>
- **Documentation**: See `CLAUDE.md` for developer documentation
- **Codebase Analysis**: See `documents/codebase.md`
- **Issues**: Report bugs on GitHub Issues

## Version

Current version: 1.12.0

### v1.13.0 Highlights

- **LLM-Powered Summarization**: Optional API-based summarization using Claude for higher-quality abstractive summaries
- **Cost Controls**: Monthly spending limits and usage tracking for API summarization
- **CLI Status Enhancement**: `cwms status --summarization` shows provider config and usage stats

### v1.12.0 Highlights

- **ChromaDB Vector Store**: When local embeddings are enabled, ChromaDB is automatically used for persistent vector storage with efficient ANN search
- **Documentation Update**: Clarified current capabilities and limitations

### Roadmap

Planned features to achieve truly transparent extended memory:

- ~~**LLM-Powered Summarization**: Use Claude to generate abstractive summaries instead of regex extraction~~ ✅ **Implemented in v1.13.0** (opt-in via API)
- **Proactive Retrieval**: Automatically inject relevant swapped context when user queries relate to past conversations
- **Automatic /clear**: If Claude Code exposes session management APIs in the future

### v1.5.0 Highlights

- **Context Window Adaptation**: Auto-detect optimal threshold based on Claude model
- **Environment Variable Overrides**: Configure via `CWMS_THRESHOLD`, `CWMS_LOG_LEVEL`, etc.
- **Observability & Logging**: Structured logging, performance metrics, `debug` command
- **Error Handling**: Retry logic with exponential backoff, graceful degradation
- **Validation**: Message validation, storage integrity checks, `validate` and `validate-messages` commands
- **Format Detection**: Auto-detect JSON, JSONL, Claude session formats; `import-history` command
- **Multi-Session Safety**: File locking prevents concurrent write corruption
- **Atomic Operations**: Journaling and atomic writes prevent data loss during crashes
