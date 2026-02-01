# CONTINUATION.md — Pre-Swap Session State Template

> **Purpose**: Capture active working state before context swap. Read this first after /clear to immediately know where you were and what to do next.

---

## Active Task

**What**: [Brief description of current task]
**Status**: IN PROGRESS | BLOCKED ON X | DECISION NEEDED | PAUSED
**Started**: [YYYY-MM-DD HH:MM]
**Last checkpoint**: [YYYY-MM-DD HH:MM]

### Current State

[Describe exactly where you are in the task. Not just what you're doing, but where in the process.]

### Why This Task Matters

[Context that future-you needs to understand the importance and urgency]

### What You Were Reaching Toward

[The goal, the "shape" of what you were trying to achieve]

---

## Pending Decisions

| Decision | Options Considered | Leaning Toward | Blocker |
|----------|-------------------|----------------|---------|
| [Decision 1] | A, B, C | B | Waiting for X |

---

## Open Threads

- [ ] [Thread 1 - description and next action]
- [ ] [Thread 2 - description and next action]

---

## Key Context (Don't Lose This)

### Approaches Tried

| Approach | Result | Why It Failed/Worked |
|----------|--------|---------------------|
| [Approach 1] | Failed | [Reason] |

### Current Hypothesis

[Your working theory or direction — this is what summaries often lose]

---

## Files & References

**Currently editing**:
- [file1.py] — [what you were doing with it]

**Key artifacts created this session**:
- [artifact1] — [purpose]

---

## Recovery Instructions

### If This Task: Continue

1. [Step 1 — specific next action]
2. [Step 2 — what comes after]

### Search Queries for Full Context

If you need more detail:
```bash
cwms retrieve --project "PROJECT" --query "relevant topic"
```

---

## Status Markers Reference

- `IN PROGRESS` — Actively working, mid-task
- `BLOCKED ON [X]` — Waiting for something external
- `DECISION NEEDED` — Cannot proceed without choosing
- `PAUSED` — Intentionally stopped, can resume
- `COMPLETED` — Done, ready to archive

---

*Core principle: Text > Brain, always. Write for your amnesiac future self.*
