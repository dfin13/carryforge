# Claude Code — Davinci Workspace

## 1. Workspace Structure

| Directory | Purpose |
|-----------|---------|
| `/docs/` | Documentation, guides, reference material |
| `/scripts/` | Utility scripts, automation, data processing |
| `/outputs/` | Generated content and deliverables |
| `/data/` | Data files, snapshots, exports |
| `/.claude/` | Claude Code configuration — agents, hooks, skills, brain |

**Never save files to the root folder unless they belong there (e.g. config files).**

---

## 2. Core Rules

- Do exactly what has been asked — nothing more, nothing less
- Always read a file before editing it
- Never create files unless absolutely necessary to achieve the goal
- Prefer editing existing files over creating new ones
- Never commit secrets, credentials, or `.env` files
- Never send external messages, emails, or notifications autonomously
- Never deploy or push to remote autonomously
- Never delete or massively rewrite important files without clear justification
- Never silently change safety-critical configuration

---

## 3. Planning Before Execution

**For any task that is multi-step, ambiguous, or touches multiple files:**

1. State your understanding of the goal
2. List the files you will read and modify
3. Describe your approach in 3-5 bullet points
4. Then execute

**For simple, clear, single-step tasks:** execute directly without preamble.

If an assumption turns out to be wrong mid-execution, stop, state the correction, reassess, and continue.

---

## 4. Autonomy and Permission Boundaries

**Move fast — use tools aggressively for:**
- Reading, searching, and editing local files
- Running local scripts and multi-step workflows
- Chaining tool calls without waiting for permission

**Always confirm before:**
- `git push` or any remote git operation
- Any deploy command (production, staging, etc.)
- Any external API call or outbound message
- Deleting or significantly overwriting existing work

When uncertain between two approaches, choose the more reversible one and state why.

---

## 5. Tool-Use Preferences

- Use Read, Edit, Grep, Glob — not `cat`, `grep`, `find` via Bash
- Use Edit over Write for existing files
- Batch all independent operations in a single message
- Reserve Bash for system operations that require shell execution

---

## 6. Context Management

- At natural checkpoints in long tasks, briefly summarize current state
- If context compaction is approaching, write task state to `.claude/task-state.md` before it triggers
- On session start, check `.claude/task-state.md` for in-progress work to restore
- Do not re-explain things already confirmed in this session
- Do not repeat tool calls that already succeeded

---

## 7. Completion / Quality Gate

**Before declaring any task complete, verify all of the following:**

1. **Objective met?** Does the output actually satisfy the stated goal — not merely perform a related action?
2. **Files valid?** Are all edited files syntactically correct and logically coherent?
3. **Side effects checked?** Have you considered impact on adjacent files or functionality?
4. **Assumptions verified?** Are there paths, states, or values you assumed but did not confirm?
5. **Fully complete?** Is any step deferred, skipped, or left partial?

If any answer is "no" or "unsure" — do not declare done. Fix it first, then re-verify.

---

## 8. Memory and Brain

- `.claude/brain.md` is the curated persistent knowledge base for this workspace
- Read it when starting unfamiliar work in this workspace
- Update it when you learn something important that should persist across sessions
- To update: say "I'll update the brain" and edit `.claude/brain.md` directly
- Session context disappears on close — brain.md persists

---

## 9. Agent Usage

Core agents are in `.claude/agents/core/`:
- `researcher` — web research, documentation, competitive analysis, trend discovery
- `coder` — implementation, scripts, utilities, data processing
- `reviewer` — code review, output quality check, consistency validation
- `architect` — system design, planning, technical decision-making
- `writer` — documentation, copy, content creation

**When to spawn agents:**
- Use the Agent tool for genuinely parallel subtasks where independent execution adds speed
- Spawn all agents needed for a task in one message
- Wait for results — do not poll after spawning
- Do not spawn agents for simple sequential tasks

---

## 10. Commit Policy

- Never auto-commit
- Commits are manual and explicit
- When asked to commit: write a specific message, stage only relevant files
- Never push to remote without explicit instruction

---

## 11. Brain vs Task-State Discipline

- Durable knowledge (project facts, architecture decisions, verified learnings) → `.claude/brain.md`
- Current in-progress work (what you're doing now, where you are, what remains) → `.claude/task-state.md`
- Transient reasoning → not preserved
- Update brain.md when you learn something that should persist across sessions. Do not add ephemeral task details to the brain.
