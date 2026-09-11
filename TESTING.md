# Testing policy

How STRATA's claims are kept true. Three levels of test, one rigor law.
Nothing here is aspirational — each level has machinery behind it.

## The three levels

### L1 — Fast guards (every push)

The pytest suite: unit logic, **pinned published numbers**, and **pinned
fired falsifiers**. Anything quoted in a paper, README, or deck has a test
asserting the artifact still says it. Falsifiers that fired stay fired —
a test guards each one so no later change can quietly un-fire it.

Runs on every push and pull request via GitHub Actions
(`.github/workflows/tests.yml`), badge on the README. Data-dependent tests
self-skip on a dataless runner; they must **skip**, never error.

```bash
uv run pytest -q
```

### L2 — Full re-run gate (before any release or claim)

`scripts/regress.py` regenerates every artifact from its source script and
diffs it against the committed copy, printing one verdict per artifact:

- `IDENTICAL` — the pipeline still produces exactly the committed number.
- `CHANGED (n paths, e.g. [...])` — names the JSON paths that moved.

```bash
uv run python scripts/regress.py --list   # the artifact -> command map
caffeinate -i uv run python scripts/regress.py
```

The runner restores the committed artifact after a CHANGED verdict, so a
diff never silently rewrites the record. Exit 0 only when all verdicts are
IDENTICAL. This is a multi-hour run — `caffeinate -i` it.

**The no-silent-CHANGED rule.** A `CHANGED` verdict is exactly one of two
things: a **bug**, or a **documented, committed decision** — a commit that
says what changed, why, and which published numbers move with it. It is
never merged unexplained, never explained only in conversation, and never
resolved by re-pinning the test to the new value without a written reason.

### L3 — The growing exam (every new dataset)

Every newly validated dataset becomes a permanent fixture: its artifacts
are committed and its guard tests join the suite forever. The exam only
grows, so proof compounds — a change that would have broken an old result
still breaks the build years later.

## The rigor law (governs every experiment)

1. **Pre-register** expectations *and falsifiers* before running — committed
   to git, before the experiment, never after.
2. Every result faces a **control or baseline** on the same exam.
3. **Statistical gates, never eyeballs** — channel-noise binomials, p < 1e-3.
4. **Held-out data only**; strictest form is the frozen-method, run-once
   protocol on a fresh system.
5. **Hostile audit** — independent recomputation — before any number is quoted.
6. **Every fired falsifier honored in print.**
7. **Every number regenerable by a stranger** from the public repo.

Corollary, and the rule that makes the rest enforceable: **quote no number
in any document until its artifact and its guard test both exist.**
