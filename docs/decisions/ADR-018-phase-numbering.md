# ADR-018: How the build history maps to the revised handover phases

The handover was revised after three phases were built. Its phases are numbered differently from my commits,
memos and earlier ADRs. I'm not renaming history; this table maps one to the other.

| Built as | Contents | Revised handover |
|---|---|---|
| Phase 1 (memo `phase1`, ADR-001 to 009) | core loop, check fraud, BEC | Phase 1 |
| Phase 2 (memo `phase2`, ADR-010 to 015) | shells, mules, account takeover, month-12 pattern, monitoring, label delay | Phase 3 typologies, Phase 2 label delay |
| Phase 3 (memo `phase3`, ADR-016 to 017) | line of credit, bust-out, honest defaults, multi-page site | Phase 4 bust-out and polish |
| Extensions (ADR-018 on) | modules A to G | Phases 2 to 4 modules |

From here on, work is named by module (A to G), not by phase number. The champion and challenger stay as
ADR-016 defines them: the champion runs R1 to R9, and the challenger adds the credit rules R10 to R12.
