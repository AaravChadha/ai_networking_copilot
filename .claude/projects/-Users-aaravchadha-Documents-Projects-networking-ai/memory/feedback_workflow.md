---
name: workflow-preferences
description: How the user wants to collaborate — task-driven, grouped subtasks, auto-checkoff, auto-commit, no coauthor
type: feedback
---

User drives task selection. They say which subtask to do (e.g., "lets do 2.1.1") with optional description. I execute it, then suggest grouping nearby subtasks that are small enough to do together — but ask first, don't just do them.

**Commit rules:**
- Commit after completing subtask(s)
- Message format: `completed task x.y.z (brief description)` or just `brief description` if no task number applies
- Do NOT add Co-Authored-By line

**Checkoff rules:**
- When subtask(s) are done, check them off in CLAUDE.md BEFORE committing
- The checkoff edit should be included in the same commit as the work
- Check off parent tasks when all subtasks are complete

**Why:** User wants a conversational, incremental workflow — not big autonomous batches. They want to stay in control of pacing and scope.

**How to apply:** Always wait for user to pick the next task. After finishing, suggest logical next groupings but don't proceed without confirmation.
