# Davinci

Universal Claude Code workspace template with pre-configured hooks, agents, intelligence layer, and documentation frameworks.

## Quick Start

1. Copy this folder to start a new project
2. Edit `.claude/brain.md` with your project's knowledge
3. Edit `CLAUDE.md` sections 1 and 9-11 for your project's specifics
4. Start Claude Code in this directory

## What's Included

### Hooks (7/7)
- **SessionStart** — restores session state + injects brain.md into context
- **PreToolUse/Bash** — blocks dangerous commands
- **PostToolUse/Edit** — tracks edit metrics + intelligence recording
- **UserPromptSubmit** — routes prompts through intelligence layer
- **PreCompact** (manual + auto) — preserves task state before context compaction

### Helpers
- `hook-handler.cjs` — central hook dispatcher
- `brain-inject.cjs` — injects brain.md at session start
- `router.cjs` — routes tasks to optimal agents
- `memory.cjs` — cross-session key-value memory
- `session.cjs` — session lifecycle management
- `intelligence.cjs` — pattern matching and context injection
- `statusline.cjs` — real-time status bar

### Agents (`/.claude/agents/core/`)
- `researcher` — web research, analysis, fact verification
- `coder` — implementation, scripts, automation
- `reviewer` — quality review, consistency checking
- `architect` — system design, planning, tradeoffs
- `writer` — documentation, copy, content

### Slash Commands (`/.claude/commands/`)
- `analysis/` — bottleneck detection, token efficiency, performance reports
- `automation/` — smart agent spawning, self-healing workflows
- `github/` — PR management, code review, issue tracking, release automation
- `hooks/` — hook management and monitoring
- `monitoring/` — agent metrics, real-time views, swarm monitoring
- `optimization/` — parallel execution, topology optimization, cache management
- `sparc/` — SPARC methodology modes (architect, coder, reviewer, etc.)

### Frameworks
- `CLAUDE.md` — master instruction file (read by Claude Code automatically)
- `.claude/brain.md` — persistent knowledge base (injected every session)
- `.claude/task-state.md` — current task context (survives compaction)
- `.claude/superpowers.md` — GitHub resource index for on-demand skill loading

## Structure

```
davinci/
├── CLAUDE.md              # Master instructions
├── README.md              # This file
├── CHANGELOG.md           # Version history
├── .gitignore
├── .claude/
│   ├── brain.md           # Persistent knowledge
│   ├── task-state.md      # Current task state
│   ├── superpowers.md     # GitHub resource index
│   ├── settings.json      # Hooks + permissions
│   ├── agents/core/       # Agent definitions
│   ├── commands/          # Slash commands
│   ├── helpers/           # Hook handler scripts
│   └── skills/            # Custom skills (add your own)
├── docs/
├── scripts/
├── outputs/
└── data/
```

## Customization

### For a new project:
1. Update `brain.md` with project-specific knowledge
2. Add domain-specific agents to `agents/core/`
3. Add custom skills to `skills/`
4. Update workspace structure in `CLAUDE.md` section 1
5. Add project-specific rules to `CLAUDE.md` section 11

### Adding skills:
```bash
npx skills add <github-url>
```
