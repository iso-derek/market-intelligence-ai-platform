# Typed research workflows

D5.1 implements five bounded roles—Company, Macro, News, Risk, and Synthesis—as an explicit workflow engine rather than an unconstrained autonomous agent.

Each request has a question, company, UTC as-of time, maximum step count, and wall-clock budget. Every role has a fixed tool allowlist. Tool results separate facts, citations, interpretations, and scenarios; every fact must carry at least one evidence identifier. Missing sources, conflicts, tool failures, and time-limit failures remain visible in the trace.

The final artifact includes the typed plan, complete step trace, budget usage, and a canonical SHA-256. Synthesis can copy supported facts and citations but surfaces conflicting values instead of resolving them silently.

The bundled dashboard example is deterministic and offline. It is workflow-mechanics evidence, not proof that multiple roles improve research quality; that comparison requires independently scored tasks in a later evaluation.
