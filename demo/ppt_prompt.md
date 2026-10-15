You are designing a 6-slide hackathon submission deck in Canva. Build it by editing a copy of my uploaded template "Abhiyantriki- Hacktoberfest Submission.pptx". Keep its layout, logos and styling exactly. Only fill in content. Accuracy matters more than decoration: every number below is a real, measured result, so do not add, round up or invent anything.

=== DESIGN RULES (match the template) ===
- Format: 4:3 (10.16 x 7.62 in). Keep exactly 6 slides, in the template's order, with its section titles.
- Keep the template's header logos (Hacktoberfest 26, Abhiyantriki 2026, ISTE, Somaiya Vidyavihar University), the date field and the slide number. Set the date to 15/10/2026.
- Background white. Colours: dark red #930B0B and red #C00000 for titles and key highlights, orange #ED7D31 for secondary accents, black #000000 for body text. No other colour families.
- Fonts: Times New Roman Bold for titles, Times New Roman for body text, JetBrains Mono for code, commands, package names and version numbers (e.g. `pydantic==1.10.13`).
- At most 5-6 short bullets or one diagram plus 3 bullets per slide. Body text no smaller than 14 pt. Prefer diagrams, small tables and icons over paragraphs.
- Use simple flat icons in red/orange line style (shield, magnifier, gears, check mark, people) only where they label something.
- Clearly mark three kinds of claims with small tags: "VERIFIED" (a test actually ran), "OBSERVED" (read from the code/metadata), "AI" (the model's opinion). This honesty labelling is a core idea of the project, so make it visible.
- Put the speaker notes I give for each slide into Canva's notes for that slide.

=== SLIDE 1 - Title slide (template fields: Team Name / College Name / Track) ===
- Project title (large, red): "resilience_agent - Evidence-Driven Dependency Maintenance"
- Subtitle: "An open-weight multi-agent council that finds, repairs and PROVES dependency fixes - with a human in the loop"
- Team Name: GravityFalls
- College Name: [FILL IN]
- Track: Track 2 - Maintenance Agent Skill (Hacktoberfest 2026, Hack Day Mumbai x ISTE KJSSE)
- Small line at the bottom: "Target repo: LinkWatch (Python CLI uptime checker) | Repo: github.com/ShriyansBharuka/H26_GravityFalls_Protocol"
- Team members: [FILL IN NAMES]
Speaker notes: "Open-source projects rot because dependencies drift. AI can suggest fixes, but a suggestion is not proof. We built an agent that only trusts what it can execute."

=== SLIDE 2 - Solution & Workflow ===
Main visual: a horizontal 3-level pipeline diagram (red boxes, orange arrows), with two "HUMAN GATE" icons:
  Level 1 Context Engine -> Level 2 Discovery Council -> [HUMAN GATE 1: maintainer approves issue + scope] -> Level 3 Repair Council -> Verifier -> Dependency Exit Capsule -> [HUMAN GATE 2: approve publication / PR]
  Add a small loop arrow from "Verifier" back to "Repair Council" labelled "failure logs -> revise (max 3 attempts)".
Bullets under the diagram:
- Level 1: reads the repo live - git commit, AST of every module, all declared dependencies, where each is used, PyPI metadata, Graphify knowledge graph.
- Level 2: runs the REAL tests first (Python 3.12 + 3.13 x install from requirements.txt and from pyproject.toml), then 3 independent AI voters (Discovery, Skeptic, Evidence) + an Adjudicator judge numbered evidence. Deterministic evidence rules have the final say, not the majority vote.
- Level 3: 3 competing repair strategies (Minimal / Migration / Alternative), anonymous peer review, deterministic ranking, patch applied in an isolated git worktree, verified, retried with the verifier's exact logs.
- Output: a Dependency Exit Capsule (Markdown + JSON) labelling every statement OBSERVED / VERIFIED / AI, plus patch, rollback steps and PR text.
Speaker notes: "Nothing is fixed without a maintainer saying yes, and nothing is called fixed unless the tests say so."

=== SLIDE 3 - Technical Approach ===
Left half: tech-stack block (small logos or text badges):
- Python 3.12 / 3.13, LangGraph 1.2 (state machine, SQLite checkpoints, interrupt() for human gates, resumable runs)
- Open-weight model: Qwen2.5-Coder-3B-Instruct via Ollama 0.40.4, running locally (Qwen2.5-Coder-7B, Apache-2.0, also supported). No cloud inference.
- Pydantic 2 schema-constrained JSON output; seed, temperature, token counts and raw exchanges logged for every call
- uv virtualenvs, git worktrees, pytest + independent acceptance suite
- Graphify knowledge graph, DeepWiki over MCP, Streamlit dashboard, GitHub Actions CI (3.12 + 3.13)
- Packaged as Agent Skills (agentskills.io standard: .agents/skills/dependency-exit and linkwatch-maintainer), loadable by Hermes Agent
Right half: "What the verifier checks" as a 2x3 check grid with check-mark icons: Install | Dependency conflicts (uv pip check) | Import smoke test | CLI --help | Existing pytest suite | Independent acceptance tests (config loading, whitespace stripping, invalid input rejected, local HTTP check, cache + HTML report)
Bottom strip, labelled "Safety": allow-listed commands only (python, uv, git, graphify), no shell, timeouts, secrets scrubbed from env, patches only in isolated worktrees, AI may not edit tests.
Speaker notes: "The model proposes; the verifier decides. Reviewers see anonymised patches so they cannot favour their own."

=== SLIDE 4 - Feasibility & Viability (fix the template's spelling "Feasability" to "Feasibility") ===
Title: "Feasibility & Viability - real run on LinkWatch"
Main visual: a small results table with the header "VERIFIED baseline (before any change)":
| Environment | Result |
| Py 3.12 / requirements.txt | FAILS - Jinja2 2.11.3 crashes: cannot import 'soft_unicode' from markupsafe |
| Py 3.12 / pyproject.toml | FAILS - same crash + pydantic resolves 2.14.1 instead of 1.10.13 |
| Py 3.13 / both paths | same failures |
Callout box (red border) "Hidden behaviour change, found by executing": installing from pyproject.toml gives Pydantic v2, which silently stops stripping whitespace from site names/URLs (the v1 setting anystr_strip_whitespace was renamed). The acceptance test passes via requirements.txt and FAILS via pyproject.toml.
Bullets:
- Indexed 15 modules, 14 declared dependencies, 169 provenance-tagged facts, 13 candidate issues (also found: undeclared certifi, unused six and idna, a private requests API, a monkeypatch).
- Council disagreed (Discovery: real; Skeptic + Evidence: "not an issue") - evidence rules still marked Jinja2 and Pydantic SUPPORTED because tests proved the failures; two weaker issues were downgraded to NEEDS_INVESTIGATION.
- Runs on a CPU-only laptop (Intel i5, 16 GB RAM, no GPU): about 2.5 min per council vote, about 2 min per full verification matrix. Zero API cost.
- Repair results (VERIFIED): RA-jinja2 -> VERIFIED_RESOLUTION on attempt 3 (Jinja2==3.1.6 in both manifests; 18 checks/tests fixed, 0 regressions; on branch ra/RA-jinja2-C1, awaiting publication approval). RA-pydantic -> NO_VERIFIED_SOLUTION (the 3B model only re-pinned versions and never migrated the code; the verifier blocked every attempt). Show these as two small result badges: green check for jinja2, amber "not verified" for pydantic.
Speaker notes: "Everything on this slide came from commands we actually ran on the organisers' repository."

=== SLIDE 5 - Impacts & Benefits ===
Layout: 3 columns with icons (shield / people / magnifier):
1. For maintainers: finds problems that version numbers alone don't show (e.g. a silent validation change), and never touches the main branch without two approvals.
2. Trust in AI: every claim is labelled OBSERVED / VERIFIED / AI; when no fix passes, the capsule says NO_VERIFIED_SOLUTION instead of pretending.
3. For the community: open-weight, local, free to run, reusable as an Agent Skill on other Python repos.
Bottom band "What we learned from real failures (and fixed)":
- The 3B model truncated pyproject.toml when asked to rewrite whole files -> switched to exact find/replace edits with parse and truncation guards.
- A runaway generation ran past 15 minutes -> output cap (num_predict) and timeouts.
- Early repair candidates only aligned version pins; the verifier caught 2 regressions and fed the logs back; an earlier run honestly ended NO_VERIFIED_SOLUTION after 3 bounded attempts.
- When a human maintainer explained why pin-only patches fail (labelled HUMAN, never passed off as AI), a proposer attempted the real Pydantic v2 code migration for the first time; its edits were still too imprecise to pass the validator, and patches identical to ones that already failed are now rejected automatically.
Speaker notes: "Our failures are on record in the repo's demo folder. That is the point: the system shows when it could not prove a fix."

=== SLIDE 6 - Research & References ===
Two columns, small text (12-14 pt), JetBrains Mono for URLs:
Left - Standards and tools:
- Agent Skills specification - agentskills.io/specification
- Hermes Agent skills docs - hermes-agent.nousresearch.com/docs/user-guide/features/skills
- LangGraph (persistence, interrupts) - github.com/langchain-ai/langgraph
- Ollama - ollama.com | Qwen2.5-Coder model cards (Qwen Research License for 3B, Apache-2.0 for 7B) - huggingface.co/Qwen
- Graphify - github.com/Graphify-Labs/graphify | DeepWiki MCP - mcp.deepwiki.com
Right - Domain references and inspiration:
- PyPI JSON API; PEP 503 (name normalisation); PEP 792 (project status markers)
- Pydantic V2 migration guide - docs.pydantic.dev/latest/migration
- MarkupSafe 2.1 changelog (removal of soft_unicode)
- Karpathy's llm-council (inspiration for anonymous peer review; ideas only, no code reused)
- Target repository: github.com/rishrek/LinkWatch
Footer line: "Known limitations: no Docker sandbox yet (worktree + venv isolation); LinkWatch not yet indexed on DeepWiki; Google Code Wiki via manual import; small-model output quality varies."
Speaker notes: "We list our limitations openly; they are also in the README."

=== IMAGES I WILL UPLOAD (use if provided) ===
- demo/dashboard-overview.png (Streamlit dashboard) -> slide 3 or 5, small, with a thin red border.
- Graphify graph screenshot -> slide 3, small.
If an image is missing, leave a neat placeholder box labelled with the image name. Do not generate fake screenshots.

Before finishing, check: 6 slides, template logos intact, no invented numbers, VERIFIED / OBSERVED / AI tags visible on slides 2, 4 and 5, and the slide-4 repair results stated exactly as given.
