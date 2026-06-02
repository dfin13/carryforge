# CarryForge Dev Workflow Protocol
## "Minimum Token, Maximum Output"

### Core Rules (enforced every session)

1. **Read once, write once.** Never re-read a file you just read. Never make 3 small edits when 1 batch edit works. Write a transform script when changing >3 locations.

2. **Simulate before you commit.** Any balance/mechanic change gets run through audit_sim.py first. Commit only when sim shows improvement over baseline.

3. **Parallel > Sequential.** Use Agent spawns for independent research tasks (no shared state). Use Bash parallel commands for independent verifications.

4. **Batch transforms over iterative edits.** When changing N locations in a file, write a Python transform script, run it, verify compile, then discard the script. Faster, fewer tokens, less error-prone.

5. **One commit message captures everything.** Never commit mid-fix. Group logically related changes.

6. **Audit report as work queue.** AUDIT_REPORT.md is the canonical prioritized backlog. Mark items done inline rather than creating new tracking docs.

---

### Standard Fix Cycle (for any change set)

```
1. Read AUDIT_REPORT.md → pick N items
2. Read carryforge.py ONCE (or targeted sections)
3. Write patch.py (transform script) in one shot
4. python3 patch.py → verify compile
5. python3 audit_sim.py → verify sim improvement
6. git add + git commit (all changes together)
7. Annotate AUDIT_REPORT.md with [DONE] markers
8. Reflect: what would have been faster?
```

---

### Reflection After This Session

**What worked:**
- Writing `audit_sim.py` as a standalone validation harness meant fixes could be verified without touching the game
- Batch Python transform script (patch.py) let us change 6+ locations in carryforge.py with one read → one write → one verify
- Parallel structure: crash fix deployed immediately while audit ran

**What wasted tokens:**
- Multiple small `Edit` calls to carryforge.py for emoji removal (71 locations) instead of one `sed`/Python transform
- Reading file sections to find line numbers that could have been grepped first
- Writing audit_sim.py inline in conversation instead of streaming to a file directly
- Repeated compile checks that could have been bundled with the transform

**What to do next time:**
- Lead with `grep -n "pattern"` to locate targets before reading
- Use `python3 -c "with open() as f: src=f.read(); ... ; open('w').write(src)"` for multi-location changes
- Run `python3 -m py_compile && python3 audit_sim.py` as a single chained command
- Never spawn an agent for a task that takes < 200 tokens to do inline

---

### Token Budget Guidelines

| Task type | Method | Token cost |
|-----------|--------|------------|
| Find N lines matching pattern | `grep -n` via Bash | ~20 |
| Read file section | Read with offset+limit | ~file_size/1000 |
| Change 1–2 locations | Edit tool | ~50/edit |
| Change 3+ locations | Python transform script | ~100 flat |
| Verify balance | audit_sim.py via Bash | ~50 |
| Compile check | python3 -m py_compile via Bash | ~10 |
| Full file rewrite | Write tool | ~file_size/4 |
