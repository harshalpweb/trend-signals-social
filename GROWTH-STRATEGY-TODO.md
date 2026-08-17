# Growth strategy work — done

Completed 2026-08-17. This file originally tracked a research task that was cancelled
mid-run and deferred; it was executed in a later session per explicit founder
instruction ("don't stop and get this all completed") while the founder was away.

What was built, matching the original plan below almost exactly:

- Research (algorithm mechanics, content psychology, fast-growth case studies, plus an
  added fourth pillar — Canva/carousel visual design trends) → synthesized into
  `.claude/skills/instagram-growth/` (`SKILL.md` + `references/*.md`, each claim tagged
  confirmed/speculative, + `config.yaml` for founder-tunable knobs).
- Four supporting skills: `instagram-signals`, `instagram-caption`, `instagram-carousel`,
  `instagram-weekly-routine` (the orchestrator the scheduler actually invokes).
- A locked Canva master template (`DAHSjFtuvnU`, in the `TrendRadar` Canva folder) —
  documented in `instagram-carousel/SKILL.md` with its element map, since no Canva
  Brand Kit API exists to automate that piece instead.
- A weekly scheduled cloud agent (see the `schedule` skill) running
  `instagram-weekly-routine`.
- The analytics/performance-feedback loop remains explicitly NOT built, per the
  founder's original "not now" — stubbed as future work in `instagram-growth/SKILL.md`.

See `.claude/skills/instagram-growth/SKILL.md` as the entry point going forward; this
file is kept only as a historical pointer.

---

<details>
<summary>Original plan (superseded, kept for history)</summary>

Status: not started (research was kicked off 2026-08-17 then explicitly cancelled by
the founder mid-run — "dont research and all now" / "Do it later"). This doc exists so
a fresh session has the full task without re-deriving it.

## What the founder wants (their words, paraphrased)

"Eventually I want you to handle my Instagram brilliantly... come up with strategies
[like accounts that hit 500k followers in 60 days]... I should just be involved to
change configs or so, rest all should be automatic."

Concretely:
1. Build a persistent, research-backed Instagram growth strategy — not generic advice,
   grounded in (a) how Instagram's algorithm actually distributes content, (b) the
   psychology of what makes people share/save/comment, (c) what genuinely drove
   documented fast-growth accounts (honestly separating real mechanisms from
   survivorship bias or against-ToS tactics that would risk this account).
2. Package it as something any future session can pick up and act on autonomously —
   structure it as a proper Claude Code **skill** (SKILL.md + references/), not just a
   one-off doc, so the weekly content-generation routine can read and apply it without
   the founder re-explaining anything.
3. The founder's ongoing involvement should be limited to adjusting a small set of
   **config knobs** (cadence, tone/aggressiveness, content-type mix, etc.) — everything
   else (strategy execution, content decisions) should run automatically.
4. **Explicitly NOT now**: analytics/performance-feedback loop — don't build this yet,
   just note it as a clearly-scoped future phase.

</details>
