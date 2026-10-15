"""PROTOCOL dashboard - Streamlit UI over the SAME backend and database as the CLI.

Run: streamlit run resilience_agent/dashboard.py
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from resilience_agent.config import Settings  # noqa: E402

st.set_page_config(page_title="PROTOCOL", page_icon="◆", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');
:root { --bg:#0d0f14; --panel:#151922; --panel2:#1b2030; --line:#262d3b; --text:#e8e6e3; --muted:#8d95a3;
        --red:#e5484d; --deep:#930b0b; --amber:#ed7d31; --green:#46c46a; }
html, body, .stApp, .stMarkdown, button, input, textarea { font-family:'Space Grotesk', system-ui, sans-serif; }
.stApp { background: radial-gradient(900px 320px at 50% -80px, rgba(229,72,77,.20), transparent 70%), var(--bg); }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.6rem; max-width: 1280px; }
code, .mono { font-family:'JetBrains Mono', monospace !important; }

.brand { text-align:center; font-weight:700; font-size:3.4rem; letter-spacing:.42em; margin:0 0 .1rem .42em; line-height:1.1; }
.brand-sub { text-align:center; color:var(--muted); font-family:'JetBrains Mono'; font-size:.78rem; letter-spacing:.16em;
             text-transform:uppercase; margin-bottom:1.4rem; }
.brand-sub b { color:var(--red); font-weight:600; }
.rule { height:2px; width:84px; margin:.5rem auto .8rem; background:linear-gradient(90deg, var(--deep), var(--red), var(--amber)); border-radius:2px; }

.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin:.4rem 0 1.4rem; }
.card { background:linear-gradient(180deg, var(--panel2), var(--panel)); border:1px solid var(--line); border-radius:12px;
        padding:14px 18px; position:relative; overflow:hidden; }
.card:before { content:""; position:absolute; left:0; top:0; bottom:0; width:3px; background:var(--red); }
.card .k { color:var(--muted); font-size:.7rem; text-transform:uppercase; letter-spacing:.12em; white-space:nowrap; }
.card .v { font-family:'JetBrains Mono'; font-size:1.6rem; font-weight:600; margin-top:2px; white-space:nowrap; }
.card .s { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.card .s { color:var(--muted); font-size:.78rem; }

.pill { display:inline-block; padding:1px 9px; border-radius:999px; font-size:.72rem; font-family:'JetBrains Mono';
        border:1px solid var(--line); color:var(--muted); margin:2px 4px 2px 0; white-space:nowrap; }
.pill.ok   { color:var(--green); border-color:rgba(70,196,106,.45); background:rgba(70,196,106,.08); }
.pill.warn { color:var(--amber); border-color:rgba(237,125,49,.45); background:rgba(237,125,49,.08); }
.pill.bad  { color:var(--red);   border-color:rgba(229,72,77,.5);  background:rgba(229,72,77,.09); }

table.grid { width:100%; border-collapse:separate; border-spacing:0; font-size:.88rem; }
table.grid th { text-align:left; color:var(--muted); font-weight:500; font-size:.74rem; text-transform:uppercase;
                letter-spacing:.1em; padding:10px 12px; border-bottom:1px solid var(--line); }
table.grid td { padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
table.grid tr:hover td { background:rgba(255,255,255,.02); }
table.grid td.pkg { font-family:'JetBrains Mono'; font-weight:600; }
table.grid td.ver { font-family:'JetBrains Mono'; color:var(--muted); }

.section { font-size:1.05rem; font-weight:700; margin:1.2rem 0 .5rem; display:flex; align-items:center; gap:.5rem; }
.section:before { content:""; width:8px; height:8px; background:var(--red); transform:rotate(45deg); display:inline-block; }

.issue { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px 16px; margin-bottom:10px; }
.issue .t { font-weight:600; } .issue .id { font-family:'JetBrains Mono'; color:var(--muted); font-size:.78rem; }

.pipe { display:flex; gap:6px; margin:.3rem 0 1rem; }
.step { flex:1; text-align:center; padding:9px 6px; border-radius:10px; border:1px solid var(--line); color:var(--muted);
        font-size:.76rem; background:var(--panel); }
.step.done { color:var(--green); border-color:rgba(70,196,106,.45); }
.step.now  { color:var(--text); border-color:var(--red); box-shadow:0 0 0 1px var(--red) inset; }
.step.fail { color:var(--red); border-color:rgba(229,72,77,.5); }

.evi { border-left:2px solid var(--line); padding:4px 0 4px 12px; margin:6px 0; font-size:.88rem; }
.evi .src { color:var(--muted); font-family:'JetBrains Mono'; font-size:.74rem; }
.voter { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px 14px; height:100%; }
.voter h4 { margin:0 0 .3rem; font-size:.95rem; text-transform:capitalize; }
.note { color:var(--muted); font-size:.82rem; }
div[data-testid="stTabs"] button p { font-size:.95rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

FLAG_LABELS = {
    "exact_pin": ("pinned exactly", ""), "unpinned": ("no version pin", "warn"),
    "specs_differ": ("manifests disagree", "bad"), "pinned_behind_latest": ("behind latest", "warn"),
    "stale_last_release": ("no release in 2+ years", "bad"), "pinned_yanked": ("yanked release", "bad"),
    "pinned_not_on_pypi": ("pin not on PyPI", "bad"), "status_not_active": ("archived / deprecated", "bad"),
    "python_classifiers_older_than_target": ("not marked for target Python", "warn"),
}
CLASS_STYLE = {"SUPPORTED": "bad", "NEEDS_INVESTIGATION": "warn", "UNSUPPORTED": ""}
VERDICT_STYLE = {"real_issue": "bad", "uncertain": "warn", "not_an_issue": "ok"}
E = html.escape


def pill(text, kind=""):
    return f'<span class="pill {kind}">{E(str(text))}</span>'


def section(title):
    st.markdown(f'<div class="section">{E(title)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- repositories

REGISTRY = ROOT / ".resilience" / "repos.json"


def load_repos():
    repos = [{"name": ROOT.name + " (this repo)", "path": str(ROOT)}]
    try:
        repos += json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return repos


def save_repo(entry):
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    extra = [r for r in load_repos()[1:] if r["path"] != entry["path"]] + [entry]
    REGISTRY.write_text(json.dumps(extra, indent=2), encoding="utf-8")


def run_cli(repo, *args, background=False, log_name="ui"):
    cmd = [sys.executable, "-m", "resilience_agent", "--repo", str(repo), *args]
    if background:
        log = Path(repo) / ".resilience" / f"{log_name}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(cmd, cwd=ROOT, stdout=open(log, "w", encoding="utf-8"), stderr=subprocess.STDOUT)
        return f"started in the background - log: {log}"
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (out.stdout + out.stderr)[-4000:]


with st.sidebar:
    st.markdown("### Repositories")
    repos = load_repos()
    names = [r["name"] for r in repos]
    current = st.radio("Active repository", names, index=0, label_visibility="collapsed")
    repo = Path(next(r["path"] for r in repos if r["name"] == current))

    with st.expander("Add repository", expanded=False):
        src = st.text_input("GitHub URL or local folder", placeholder="https://github.com/owner/project")
        if st.button("Add and index", use_container_width=True) and src.strip():
            src = src.strip()
            if re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+?(\.git)?/?", src):
                owner, name = src.rstrip("/").removesuffix(".git").split("/")[-2:]
                dest = ROOT / ".resilience" / "repos" / f"{owner}__{name}"
                if not dest.exists():
                    with st.spinner(f"Cloning {owner}/{name} ..."):
                        r = subprocess.run(["git", "clone", "--depth", "50", src, str(dest)], capture_output=True, text=True)
                    if r.returncode != 0:
                        st.error(r.stderr[-800:])
                        st.stop()
                entry = {"name": f"{owner}/{name}", "path": str(dest), "url": src}
            elif Path(src).is_dir() and (Path(src) / ".git").exists():
                entry = {"name": Path(src).name, "path": str(Path(src).resolve())}
            else:
                st.error("Use a https://github.com/owner/repo URL or a local folder that is a git repository.")
                st.stop()
            with st.spinner("Indexing (reads code and PyPI metadata; runs nothing from the repo) ..."):
                st.code(run_cli(entry["path"], "index")[-1500:])
            save_repo(entry)
            st.success(f"Added {entry['name']}. Select it above.")
    st.caption("Indexing only reads files. A discovery scan installs the repository and runs its tests "
               "in local virtualenvs: only scan code you trust.")

s = Settings()
s.repo = repo
db = s.db()
ix = db.get("index:latest")

st.markdown('<div class="brand">PROTOCOL</div><div class="rule"></div>'
            '<div class="brand-sub">evidence-driven dependency maintenance &middot; <b>observed</b> &middot; '
            '<b>verified</b> &middot; <b>ai</b></div>', unsafe_allow_html=True)

if not ix:
    st.info(f"**{current}** has not been indexed yet.")
    c1, c2 = st.columns(2)
    if c1.button("Index this repository"):
        st.code(run_cli(repo, "index"))
        st.rerun()
    if c2.button("Run discovery scan (background)"):
        st.write(run_cli(repo, "scan", background=True, log_name="scan"))
    st.stop()

meta, issues = ix["meta"], db.issues()
supported = sum(i["classification"] == "SUPPORTED" for i in issues)
st.markdown(f"""<div class="cards">
  <div class="card"><div class="k">Commit</div><div class="v">{E(meta['commit'][:7])}</div>
       <div class="s">{E(meta.get('branch') or '')}</div></div>
  <div class="card"><div class="k">Dependencies</div><div class="v">{len(ix['scan']['packages'])}</div>
       <div class="s">declared directly</div></div>
  <div class="card"><div class="k">Modules read</div><div class="v">{len(ix['modules'])}</div>
       <div class="s">{ix['fact_count']} facts recorded</div></div>
  <div class="card"><div class="k">Open issues</div><div class="v">{len(issues)}</div>
       <div class="s">{supported} backed by evidence</div></div>
</div>""", unsafe_allow_html=True)

tab_repo, tab_issues, tab_repair, tab_evidence = st.tabs(["Dependencies", "Issues & council", "Repairs", "Evidence"])

# ---------------------------------------------------------------- dependencies
with tab_repo:
    usage = ix["usages"]["packages"]
    rows = []
    for p in ix["scan"]["packages"]:
        f = p.get("pypi") or {}
        used = sorted({u["file"] for u in usage.get(p["name"], {}).get("usages", [])})
        flags = "".join(pill(*FLAG_LABELS.get(k, (k, ""))) for k, v in p["risk_flags"].items() if v) or pill("looks fine", "ok")
        rows.append(f"<tr><td class='pkg'>{E(p['declared_as'])}</td><td class='ver'>{E(p['pinned_version'] or 'any')}</td>"
                    f"<td class='ver'>{E(f.get('latest_version', '?'))}</td>"
                    f"<td>{'<br>'.join(E(x['file']) for x in p['sources'])}</td>"
                    f"<td>{'<br>'.join(E(u) for u in used) or '<span class=note>not imported</span>'}</td><td>{flags}</td></tr>")
    st.markdown("<table class='grid'><tr><th>Package</th><th>Pinned version</th><th>Latest release</th>"
                "<th>Declared in</th><th>Used by</th><th>What we noticed</th></tr>" + "".join(rows) + "</table>",
                unsafe_allow_html=True)
    extra = ix["usages"]
    notes = []
    if extra["undeclared_imports"]:
        notes.append(f"Imported but never declared: {', '.join(extra['undeclared_imports'])}")
    if extra["declared_unused"]:
        notes.append(f"Declared but never imported: {', '.join(extra['declared_unused'])}")
    for n in notes:
        st.markdown(f"<div class='note'>{E(n)}</div>", unsafe_allow_html=True)
    graph = Path(ix["artifact_dir"]) / "graphify" / "graph.html"
    if graph.exists():
        section("Knowledge graph")
        st.components.v1.html(graph.read_text(encoding="utf-8"), height=560, scrolling=True)


def pipeline(issue):
    cands = db.candidates(issue["issue_id"])
    verifs = db.verifications(issue["issue_id"])
    gate1 = db.latest_decision(issue["issue_id"], "issue")
    gate2 = db.latest_decision(issue["issue_id"], "publication")
    passed = any(v["data"]["gate"]["passed"] for v in verifs)
    steps = [("Evidence", "done"), ("Council", "done" if issue["discovery_votes"] else "now"),
             ("Maintainer approval", "done" if gate1 == "approve" else ("fail" if gate1 == "reject" else "now")),
             ("Repair proposals", "done" if cands else ("now" if gate1 == "approve" else "")),
             ("Verification", "done" if passed else ("fail" if verifs else ("now" if cands else ""))),
             ("Publication", "done" if gate2 == "approve" else ("now" if passed else ""))]
    seen_now, html_steps = False, []
    for name, state in steps:
        if state == "now":
            state = "now" if not seen_now else ""
            seen_now = True
        html_steps.append(f"<div class='step {state}'>{E(name)}</div>")
    st.markdown("<div class='pipe'>" + "".join(html_steps) + "</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- issues
with tab_issues:
    if not issues:
        st.info("No issues yet - run a discovery scan.")
        if st.button("Run discovery scan (background)"):
            st.write(run_cli(repo, "scan", background=True, log_name="scan"))
        st.stop()
    ordered = sorted(issues, key=lambda i: -i.get("score", 0))
    left, right = st.columns([2, 3], gap="large")
    with left:
        section("Findings")
        for i in ordered:
            v = i["discovery_votes"] or {}
            votes = "".join(pill(f"{k[0].upper()}: {x['verdict'].replace('_', ' ')}", VERDICT_STYLE.get(x["verdict"], ""))
                            for k, x in v.items() if x)
            st.markdown(f"<div class='issue'><div class='id'>{E(i['issue_id'])}</div>"
                        f"<div class='t'>{E(i['affected_dependencies'][0])}</div>"
                        f"{pill(i['classification'].replace('_', ' ').lower(), CLASS_STYLE[i['classification']])}"
                        f"{pill(i['reproduction_status'].replace('_', ' '), 'bad' if i['reproduction_status'] == 'reproduced' else '')}"
                        f"{pill(i['approval_status'].replace('_', ' '), 'ok' if i['approval_status'] == 'approved' else '')}"
                        f"<div>{votes}</div></div>", unsafe_allow_html=True)
    with right:
        pick = st.selectbox("Inspect", [i["issue_id"] for i in ordered])
        i = db.issue(pick)
        pipeline(i)
        st.markdown(f"#### {E(i['title'])}")
        if i.get("description"):
            st.markdown(f"<div class='note'>{E(i['description'])}</div>", unsafe_allow_html=True)
        section("Evidence")
        for x in i["evidence"]:
            kind = {"executed": "bad", "metadata": "warn"}.get(x["kind"], "")
            st.markdown(f"<div class='evi'>{pill(x['id'])}{pill(x['kind'], kind)} {E(x['text'])}"
                        f"<div class='src'>{E(str(x['source']))}</div></div>", unsafe_allow_html=True)
        if i["discovery_votes"]:
            section("What the council said")
            cols = st.columns(3)
            for col, voter in zip(cols, ("discovery", "skeptic", "evidence")):
                v = i["discovery_votes"].get(voter)
                if v:
                    col.markdown(f"<div class='voter'><h4>{voter}</h4>{pill(v['verdict'].replace('_', ' '), VERDICT_STYLE.get(v['verdict'], ''))}"
                                 f"<p class='note'>{E(v['rationale'])}</p></div>", unsafe_allow_html=True)
            notes = i["adjudication"].get("rule_notes") or []
            st.markdown(f"<p class='note'>Final call after evidence rules: <b>{E(i['classification'])}</b>"
                        + "".join(f"<br>&middot; {E(n)}" for n in notes) + "</p>", unsafe_allow_html=True)
        section("Your decision")
        scope = st.text_input("Repair scope (packages, comma-separated)", ",".join(i.get("scope", [])))
        note = st.text_input("Note for the record")
        b1, b2, b3 = st.columns(3)
        for btn, decision, status in ((b1, "approve", "approved"), (b2, "reject", "rejected"),
                                      (b3, "investigate", "needs_investigation")):
            if btn.button(decision.capitalize(), key=f"{decision}-{pick}", use_container_width=True):
                i["scope"], i["approval_status"] = sorted({x.strip() for x in scope.split(",") if x.strip()}), status
                db.save_issue(i)
                db.record_approval(pick, "issue", decision, note, actor="human-dashboard")
                st.success(f"Recorded: {decision}")

# ---------------------------------------------------------------- repairs
with tab_repair:
    pick = st.selectbox("Issue", [i["issue_id"] for i in issues], key="repair_issue")
    issue = db.issue(pick)
    pipeline(issue)
    for g in issue.get("maintainer_guidance", []):
        st.markdown(f"<div class='evi'>{pill('maintainer guidance', 'warn')} {E(g['text'])}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 3])
    if c1.button("Start / resume repair", use_container_width=True):
        c2.write(run_cli(repo, "repair", pick, background=True, log_name=f"repair-{pick}"))
    cands = db.candidates(pick)
    if cands:
        section("Competing repairs")
        cols = st.columns(min(3, len(cands)))
        for n, c in enumerate(cands):
            col = cols[n % len(cols)]
            status = c.get("status", "")
            kind = {"verified": "ok", "failed": "bad", "invalid": "bad"}.get(status, "warn")
            col.markdown(f"<div class='issue'><div class='id'>{E(c['cand_id'])} &middot; {E(c['strategy_name'])}</div>"
                         f"{pill(status or 'proposed', kind)}<p class='note'>{E(c['proposal'].get('solution', '')[:260])}</p></div>",
                         unsafe_allow_html=True)
            if c["diff"]:
                col.code(c["diff"], language="diff")
            for p in c.get("problems", []):
                col.markdown(f"<div class='note'>&times; {E(p)}</div>", unsafe_allow_html=True)
            if c.get("gate"):
                col.markdown("".join(pill(r, "bad") for r in c["gate"]["reasons"]) or pill("gate passed", "ok"),
                             unsafe_allow_html=True)
        reviews = db.votes(pick, "repair-review")
        if reviews:
            section("Anonymous peer review")
            rows = "".join(f"<tr><td class='pkg'>{E(r['data'].get('proposal_label', ''))}</td><td>{E(r['data'].get('cand_id', ''))}</td>"
                           f"<td>{pill(r['data'].get('verdict', ''), 'ok' if r['data'].get('verdict') == 'accept' else 'bad')}</td>"
                           f"<td class='note'>{E(r['data'].get('summary', ''))}<br>{E('; '.join(r['data'].get('defects', [])))}</td></tr>"
                           for r in reviews)
            st.markdown("<table class='grid'><tr><th>Shown as</th><th>Actually</th><th>Verdict</th><th>Comments</th></tr>"
                        + rows + "</table>", unsafe_allow_html=True)
    section("Publication")
    p1, p2 = st.columns(2)
    if p1.button("Approve publication", use_container_width=True):
        db.record_approval(pick, "publication", "approve", actor="human-dashboard")
        st.success("Recorded - resume the repair to prepare the PR.")
    if p2.button("Reject publication", use_container_width=True):
        db.record_approval(pick, "publication", "reject", actor="human-dashboard")

# ---------------------------------------------------------------- evidence
with tab_evidence:
    def matrix(result):
        keys = sorted({k for e in result["matrix"] for k in e.get("checks", {})})
        nice = {"install": "Install", "dependency_conflicts": "Conflicts", "import_smoke": "Imports", "pytest": "Tests",
                "acceptance": "Acceptance"}
        head = "".join(f"<th>{E(nice.get(k, k.replace('cli_help:', 'CLI ')))}</th>" for k in keys)
        body = ""
        for e in result["matrix"]:
            cells = "".join(f"<td>{pill('pass', 'ok') if e['checks'][k]['ok'] else pill('fail', 'bad')}</td>"
                            if k in e.get("checks", {}) else "<td class='note'>-</td>" for k in keys)
            body += f"<tr><td class='pkg'>Python {E(e['python'])} &middot; {E(e['mode'])}</td>{cells}</tr>"
        st.markdown(f"<table class='grid'><tr><th>Environment</th>{head}</tr>{body}</table>", unsafe_allow_html=True)

    base = db.get("baseline:latest")
    if base:
        section("Before any change")
        matrix(base)
    pick = st.selectbox("Issue", [i["issue_id"] for i in issues], key="ev_issue")
    for v in db.verifications(pick):
        g = v["data"]["gate"]
        section(f"{v['label']}")
        st.markdown(pill("gate passed", "ok") if g["passed"] else "".join(pill(r, "bad") for r in g["reasons"]),
                    unsafe_allow_html=True)
        matrix(v["data"]["result"])
    cap = repo / ".resilience" / "artifacts" / "capsules" / pick / "capsule.md"
    if cap.exists():
        section("Dependency Exit Capsule")
        with st.expander("Read the capsule", expanded=False):
            st.markdown(cap.read_text(encoding="utf-8"))
        st.download_button("Download capsule.json", (cap.parent / "capsule.json").read_text(encoding="utf-8"),
                           "capsule.json", use_container_width=False)
