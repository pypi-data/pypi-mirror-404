# Automatic Context Swapping

This directory contains the automatic context swapping implementation for the cwms skill.

## How It Works

### Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Claude Code Session                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  1. Continuous Monitoring: Status Line Updates                           │
│     └─> ~/.claude/scripts/statusline.py                    │
│         ├─ Receives context_window data from Claude Code                 │
│         ├─ Reads config from ~/.claude/cwms/config.yaml         │
│         ├─ Writes metrics to /tmp/claude-context-{session_id}.json       │
│         └─ Displays: 🟢 [Model] Context: 45.2% (14.5k/32k tokens)        │
│                                                                           │
│  2. After Each Response: Stop Hook Checks Threshold                      │
│     └─> ~/.claude/hooks/auto-swap.py                       │
│         ├─ Reads monitoring file from status line                        │
│         ├─ Checks if total_tokens > swap_threshold (80% of 32k)          │
│         ├─ If yes: Parse transcript → Call swap CLI                      │
│         ├─ Save bridge summary + continuation guide                      │
│         ├─ Reset metrics to prevent loop                                 │
│         └─ Output: {"decision": "block", "reason": "...clear now..."}    │
│                                                                           │
│  3. Swap Operation: CLI Stores Context                                   │
│     └─> cwms swap --project X --messages-file Y                 │
│         ├─ Creates chunks from older messages                            │
│         ├─ Stores to ~/.claude/cwms/{project}/chunks.jsonl      │
│         ├─ Generates summary, keywords, and embeddings                   │
│         └─ Returns: chunks_stored, tokens_stored, summary                │
│                                                                           │
│  4. User Executes: /clear                                                │
│     └─> Clears active context window                                     │
│                                                                           │
│  5. Session Restart: SessionStart Hook Injects Bridge                    │
│     └─> ~/.claude/hooks/session-start.py                   │
│         ├─ Triggered by /clear (source="clear")                          │
│         ├─ Reads bridge summary from /tmp/cwms-bridge-...txt   │
│         ├─ Reads continuation guide from /tmp/cwms-continuation │
│         ├─ Injects as additionalContext for Claude                       │
│         └─ Cleans up temporary files                                     │
│                                                                           │
│  6. Claude Receives Context Bridge                                       │
│     └─> Summary of swapped content + search queries for recovery         │
│         ├─ Understands what was swapped                                  │
│         ├─ Sees suggested queries to retrieve specific context           │
│         └─ Continues work with fresh context window                      │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### Components

#### 1. Status Line Monitor (`~/.claude/scripts/statusline.py`)

**When it runs:** Continuously, every time context window updates from Claude Code

**What it does:**

- Receives real-time context usage data from Claude Code
- Loads configuration from `~/.claude/cwms/config.yaml`
- Calculates if swap threshold is exceeded (default: 80% of 32k tokens = 25.6k)
- Writes monitoring data to `/tmp/claude-context-{session_id}.json`
- Displays visual indicator based on usage relative to configured threshold:
  - 🟢 (< 80% of configured threshold)
  - 🟡 (80-90% of configured threshold)
  - 🔴 (> 90% of configured threshold)

**Example output:**

```
🟡 [Claude Sonnet 4.5] Context: 82.3% (26,336/32,000 tokens)
```

#### 2. Auto-Swap Hook (`~/.claude/hooks/auto-swap.py`)

**When it runs:** After each assistant response completes (Stop event)

**What it does:**

1. Reads monitoring file from status line
2. Checks if `should_swap` flag is true (tokens > configured threshold)
3. Parses transcript JSONL to messages JSON format (deduplicates by UUID)
4. Calls `cwms swap` CLI command with parsed messages
5. Saves bridge summary to `/tmp/cwms-bridge-{session_id}.txt`
6. Extracts smart search queries from swap summary
7. Saves continuation guide to `/tmp/cwms-continuation-{session_id}.md`
8. **Resets metrics** to prevent infinite loop
9. Outputs JSON with `"decision": "block"` to instruct Claude to execute `/clear`

**Example output (blocking):**

```json
{
  "decision": "block",
  "reason": "🔄 **CONTEXT SWAP COMPLETE - ACTION REQUIRED**\n\nContext was at 82.3% (26,336 tokens)...\n\n**⚡ EXECUTE `/clear` NOW** to reset context window...",
  "systemMessage": "🔄 Auto-swap triggered at 82.3% (26,336 tokens). Swapped 3 chunk(s) (18,000 tokens) to disk. Execute /clear to continue."
}
```

#### 3. SessionStart Hook (`~/.claude/hooks/session-start.py`)

**When it runs:** After Claude starts a new session (specifically when `source="clear"`)

**What it does:**

1. Detects that session started due to `/clear` command
2. Reads bridge summary from `/tmp/cwms-bridge-{session_id}.txt`
3. Reads continuation guide from `/tmp/cwms-continuation-{session_id}.md`
4. Injects combined content as `additionalContext` for Claude
5. Cleans up temporary files

**Example injected context:**

```markdown
## Context Bridge (Auto-Swap Recovery)

Your context was automatically swapped to disk and cleared for optimal performance.

### Summary of Swapped Content

**Key Topics:** authentication, user registration, API endpoints
**Files Referenced:** src/auth.py, src/api/users.py
**Actions:** Implementation of user authentication flow

### Suggested Context Recovery Queries

Run these queries to retrieve the most relevant context:

1. Changes to src/auth.py
   cwms retrieve --project "my-project" --query "src/auth.py"

2. Work on authentication
   cwms retrieve --project "my-project" --query "authentication"
```

#### 4. Configuration (`~/.claude/settings.json`)

Configures the status line and both hooks (Stop and SessionStart):

```json
{
  "statusLine": {
    "type": "command",
    "command": "/Users/yourusername/.claude/scripts/statusline.py"
  },
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "/Users/yourusername/.claude/hooks/auto-swap.py"
      }]
    }],
    "SessionStart": [{
      "matcher": "clear",
      "hooks": [{
        "type": "command",
        "command": "/Users/yourusername/.claude/hooks/session-start.py"
      }]
    }]
  }
}
```

**Note:** The `install-skill --auto-swap` command outputs the correct paths for your system.

## Swap Behavior

### Thresholds

- **Trigger threshold:** 80% of configured threshold (default: 25,600 tokens for 32k limit)
- **Preserve recent:** 8,000 tokens always kept when swapping
- **Chunk size:** ~2,000 tokens per chunk
- **Configurable:** All thresholds can be adjusted in `~/.claude/cwms/config.yaml`

### What Happens During Auto-Swap

When the swap threshold is exceeded:

1. **Stop Hook Triggers** (after assistant response completes)
   - Reads transcript and parses to messages
   - Calls `cwms swap` CLI
   - Older messages (beyond 8k recent) are chunked and stored

2. **Context Stored to Disk**
   - ✅ Full message content saved to `~/.claude/cwms/{project}/chunks.jsonl`
   - ✅ Summary, keywords, and embeddings generated for each chunk
   - ✅ Search index updated for fast retrieval
   - ✅ Fully searchable with `cwms search` or `retrieve`

3. **Conversation Blocked**
   - Hook returns `{"decision": "block"}` to Claude Code
   - Claude receives instruction to execute `/clear`
   - Bridge summary and continuation guide saved to temp files
   - Metrics reset to prevent infinite loop

4. **User Executes /clear**
   - Active context window is cleared
   - Fresh start with empty conversation

5. **SessionStart Hook Injects Context**
   - Bridge summary automatically injected
   - Continuation guide with smart search queries provided
   - Claude understands what was swapped and how to retrieve it

### What Gets Preserved

- ❌ **Not in active context:** Swapped messages are removed after `/clear`
- ✅ **Stored on disk:** Full content in `~/.claude/cwms/{project}/`
- ✅ **Accessible:** Use `cwms retrieve` to bring back specific topics
- ✅ **Summary provided:** Claude knows what was swapped via bridge summary
- ✅ **Smart queries:** Continuation guide suggests relevant searches

### Safe Swap Points

Swapping only occurs at safe points to avoid disrupting Claude:

- ✅ After assistant completes a response (Stop event)
- ✅ Conversation is at rest (no streaming)
- ✅ User must manually execute `/clear` (gives control)
- ❌ Never mid-response or mid-streaming
- ❌ Never automatic without user action

## Configuration

### Adjusting Thresholds

Edit `~/.claude/cwms/config.yaml`:

```yaml
context:
  threshold_tokens: 32000          # Total context threshold (tokens)
  swap_trigger_percent: 0.80       # Trigger at 80% (0.80 = 25,600 tokens)
  preserve_recent_tokens: 8000     # Keep recent context when swapping
  chunk_size: 2000                 # Target chunk size for storage
  chunk_overlap: 200               # Overlap between chunks for continuity
```

The status line automatically reads this configuration and adjusts the swap threshold accordingly.

### Disabling Auto-Swap

**Temporary (this session):**

- Remove or rename `~/.claude/settings.json`
- Restart Claude Code session

**Permanent:**

- Remove the `statusLine` and `hooks` sections from `~/.claude/settings.json`
- Or delete the hook scripts:
  - `~/.claude/scripts/statusline.py`
  - `~/.claude/hooks/auto-swap.py`
  - `~/.claude/hooks/session-start.py`

### Manual Commands

Even with auto-swap enabled, you can use manual commands:

```bash
# Check current cache status
cwms status --project "$(basename $PWD)"

# Search stored context
cwms search --project "$(basename $PWD)" --query "your query"

# Retrieve formatted context
cwms retrieve --project "$(basename $PWD)" --query "your query"

# View all chunk summaries
cwms summaries --project "$(basename $PWD)"

# Clear stored context
cwms clear --project "$(basename $PWD)" --confirm
```

**Note:** Auto-swap does NOT prevent manual swapping. You can trigger manual swaps anytime, independent of the automatic workflow.

## Monitoring Files

### Status Line Output

**File:** `/tmp/claude-context-{session_id}.json`

**Purpose:** Written by status line, read by auto-swap hook

**Example content:**

```json
{
  "timestamp": 1705419600,
  "session_id": "abc123",
  "used_percentage": 82.3,
  "input_tokens": 26336,
  "total_tokens": 26336,
  "context_size": 200000,
  "should_swap": true,
  "swap_threshold_tokens": 25600,
  "configured_threshold": 32000,
  "swap_threshold_pct": 80.0,
  "working_directory": "/Users/name/project",
  "swap_completed": false,
  "token_baseline": 0
}
```

**Key fields:**

- `total_tokens`: Current conversation tokens (after subtracting baseline)
- `should_swap`: Whether swap threshold has been exceeded
- `swap_completed`: Prevents re-triggering after swap (set by auto-swap hook)
- `token_baseline`: Token count at last `/clear` (for counter reset)

### Token Counter Reset

After a swap+clear cycle, the token counter automatically resets to show only new conversation tokens:

1. **Before clear:** Counter shows cumulative tokens from session start (e.g., 225,000 tokens → 703%)
2. **After swap:** `swap_completed` flag is set to prevent loop
3. **After /clear:** `token_baseline` is set to current total (e.g., 225,000)
4. **Next update:** Counter shows `total_tokens - token_baseline` (e.g., 226,500 - 225,000 = 1,500 → 4.7%)

This ensures the status line accurately reflects the active context window, not the cumulative session tokens.

### Bridge Summary

**File:** `/tmp/cwms-bridge-{session_id}.txt`

**Purpose:** Written by auto-swap hook, read by session-start hook

**Contains:** Summary of swapped content including key topics, files, and actions

### Continuation Guide

**File:** `/tmp/cwms-continuation-{session_id}.md`

**Purpose:** Written by auto-swap hook, read by session-start hook

**Contains:** Smart search queries extracted from swap summary to help Claude recover specific context

## Troubleshooting

### Swap not triggering

1. **Check status line is working:**

   ```bash
   cat /tmp/claude-context-*.json
   # Should show current metrics with should_swap flag
   ```

2. **Check hooks are configured:**

   ```bash
   cat ~/.claude/settings.json
   # Should show statusLine and hooks.Stop configuration
   ```

3. **Check cwms CLI is installed:**

   ```bash
   cwms --version
   # Should output version number
   ```

4. **Check hook debug log:**

   ```bash
   tail -f /tmp/cwms-hook-debug.log
   # Shows hook execution details
   ```

### Swap failing

1. **Check CLI works manually:**

   ```bash
   cwms status --project "$(basename $PWD)"
   # Should return JSON with project status
   ```

2. **Check hook permissions:**

   ```bash
   ls -l ~/.claude/hooks/auto-swap.py
   chmod +x ~/.claude/hooks/auto-swap.py
   ```

3. **Review hook errors:**
   - Hook errors appear in the Claude Code conversation
   - Check systemMessage field in hook output
   - Review debug log: `/tmp/cwms-hook-debug.log`

4. **Verify swap timeout:**
   - Hook has 180s timeout for swap operation
   - Check if large conversations are timing out

### Status line not showing

1. **Verify script exists and is executable:**

   ```bash
   ls -l ~/.claude/scripts/statusline.py
   chmod +x ~/.claude/scripts/statusline.py
   ```

2. **Test manually:**

   ```bash
   echo '{"context_window":{"used_percentage":75.5,"current_usage":{"input_tokens":24000},"total_input_tokens":24000,"total_output_tokens":0,"context_window_size":200000},"model":{"display_name":"Test"},"session_id":"test"}' | ~/.claude/scripts/statusline.py
   # Should output: 🟢 [Test] Context: 75.0% (24,000/32,000 tokens)
   ```

### Token counter not resetting after /clear

**Fixed in v1.4.3+**: The token counter now automatically resets after a swap+clear cycle.

**If you're still seeing high percentages after `/clear`:**

1. **Verify you have the latest hooks:**

   ```bash
   grep -n "token_baseline" ~/.claude/scripts/statusline.py
   # Should show lines that read and use token_baseline

   grep -n "token_baseline" ~/.claude/hooks/session-start.py
   # Should show lines that set token_baseline
   ```

2. **Check the monitor file has baseline set:**

   ```bash
   cat /tmp/claude-context-*.json | jq '.token_baseline'
   # Should show a number > 0 after a swap+clear, or 0 before first swap
   ```

3. **If hooks are outdated:**

   ```bash
   # Reinstall the skill with auto-swap to get latest hooks
   cwms install-skill --auto-swap --force
   ```

4. **Manual workaround (if needed):**

   ```bash
   # Delete the monitor file to force reset
   rm /tmp/claude-context-*.json
   # The status line will recreate it on next update
   ```

5. **Check config file exists:**

   ```bash
   cat ~/.claude/cwms/config.yaml
   # Should show context configuration
   ```

### Bridge summary not appearing after /clear

1. **Check SessionStart hook is configured:**

   ```bash
   grep -A 10 'SessionStart' ~/.claude/settings.json
   # Should show session-start.py hook with source="clear" matcher
   ```

2. **Check bridge file was created:**

   ```bash
   ls -la /tmp/cwms-bridge-*.txt
   ls -la /tmp/cwms-continuation-*.md
   # Should exist after swap, before /clear
   ```

3. **Verify hook is executable:**

   ```bash
   ls -l ~/.claude/hooks/session-start.py
   chmod +x ~/.claude/hooks/session-start.py
   ```

## Performance

- **Status line:** Minimal overhead, updates only when context window changes
- **Hook execution:** ~100-500ms to check metrics (runs after each response)
- **Swap operation:** ~500-2000ms depending on message count and embedding provider
  - Without embeddings: ~500-1000ms
  - With local embeddings: ~1000-2000ms
- **Storage:** Append-only JSONL format, efficient writes
- **Index:** Metadata-only search index for fast lookups
- **User control:** User must execute `/clear`, so no unexpected interruptions

## Files Created

```
~/.claude/
├── settings.json                           # Configuration (hooks + statusline)
├── cwms/
│   └── config.yaml                         # cwms configuration
├── scripts/
│   └── statusline.py         # Status line monitor script
├── hooks/
│   ├── auto-swap.py          # Auto-swap hook (Stop event)
│   └── session-start.py      # Bridge injection hook (SessionStart)
└── skills/
    └── cwms/
        ├── SKILL.md                        # Skill commands for Claude
        └── AUTO_SWAP_README.md             # This file

~/.claude/cwms/
└── {project-hash}/
    ├── project.txt                         # Original project name
    ├── chunks.jsonl                        # Swapped context (append-only)
    └── index.json                          # Search index (metadata only)

/tmp/
├── claude-context-{session_id}.json        # Monitoring data (status line → hook)
├── cwms-bridge-{session_id}.txt   # Bridge summary (auto-swap → session-start)
├── cwms-continuation-{session_id}.md  # Recovery guide (auto-swap → session-start)
└── cwms-hook-debug.log            # Hook debug log (if debugging enabled)
```

## Testing the Auto-Swap Workflow

To verify auto-swap is working correctly:

1. **✅ Verify installation:**

   ```bash
   ls -l ~/.claude/scripts/statusline.py
   ls -l ~/.claude/hooks/auto-swap.py
   ls -l ~/.claude/hooks/session-start.py
   cat ~/.claude/settings.json
   ```

2. **✅ Start a Claude Code session and monitor status line:**
   - Should see: `🟢 [Model] Context: X% (tokens/threshold)`
   - Status updates as conversation grows

3. **⏳ Have a long conversation (exceeding threshold):**
   - Keep chatting until context reaches 80%+ (25,600+ tokens by default)
   - Status line should turn 🟡 or 🔴

4. **⏳ Wait for auto-swap to trigger:**
   - After Claude's next response, hook checks threshold
   - If exceeded, swap occurs and you see blocking message
   - Message instructs you to execute `/clear`

5. **⏳ Execute `/clear` command:**
   - Type `/clear` in Claude Code
   - Context window resets

6. **⏳ Verify bridge injection:**
   - After `/clear`, Claude should receive context bridge
   - Bridge includes summary of swapped content
   - Continuation guide with suggested search queries appears

7. **⏳ Test context retrieval:**

   ```bash
   cwms search --project "$(basename $PWD)" --query "your topic"
   cwms retrieve --project "$(basename $PWD)" --query "your topic"
   ```

8. **⏳ Continue conversation:**
   - Claude maintains awareness of swapped content
   - Can retrieve specific context using suggested queries
   - Fresh context window with optimal performance

## Support

For issues or questions:

- Check the main README.md
- Review SKILL.md for slash commands
- See documents/reference.md for CLI API
- Report issues on GitHub
