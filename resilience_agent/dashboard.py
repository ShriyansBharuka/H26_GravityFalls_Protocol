"""Streamlit dashboard over the SAME backend and database as the CLI.

Run: streamlit run resilience_agent/dashboard.py
"""
import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from resilience_agent.config import Settings  # noqa: E402

s = Settings()
db = s.db()
st.set_page_config(page_title="resilience_agent", layout="wide")
st.title("resilience_agent - evidence-driven maintenance")

ix = db.get("index:latest")
if not ix:
    st.warning("No index yet. Run `python -m resilience_agent scan` first.")
    st.stop()

meta = ix["meta"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Commit", meta["commit"][:12])
c2.metric("Direct dependencies", len(ix["scan"]["packages"]))
c3.metric("Indexed modules", len(ix["modules"]))
c4.metric("Facts", ix["fact_count"])
st.caption("Knowledge sources: " + ", ".join(f"{k}: {v.get('status')}" for k, v in ix["external"].items()))

tab_overview, tab_issues, tab_repair, tab_evidence = st.tabs(["Repository", "Issues + discovery council",
                                                               "Repair council", "Evidence"])

with tab_overview:
    rows = [{"package": p["name"], "pinned": p["pinned_version"], "latest": (p.get("pypi") or {}).get("latest_version"),
             "declared in": ", ".join(x["file"] for x in p["sources"]),
             "used in": ", ".join(sorted({u["file"] for u in ix["usages"]["packages"].get(p["name"], {}).get("usages", [])})),
             "risk flags": ", ".join(k for k, v in p["risk_flags"].items() if v)} for p in ix["scan"]["packages"]]
    st.dataframe(rows, use_container_width=True)
    graph = Path(ix["artifact_dir"]) / "graphify" / "graph.html"
    if graph.exists():
        st.subheader("Graphify knowledge graph")
        st.components.v1.html(graph.read_text(encoding="utf-8"), height=600, scrolling=True)

with tab_issues:
    issues = sorted(db.issues(), key=lambda i: -i.get("score", 0))
    st.dataframe([{k: i[k] for k in ("issue_id", "classification", "severity", "reproduction_status",
                                     "approval_status", "title")} for i in issues], use_container_width=True)
    pick = st.selectbox("Inspect issue", [i["issue_id"] for i in issues])
    i = db.issue(pick)
    st.markdown(f"**{i['title']}** - {i['classification']} ({i['confidence_label']})\n\n{i['description']}")
    st.markdown("**Evidence (OBSERVED / EXECUTED)**")
    st.table([{k: x[k] for k in ("id", "kind", "text", "source")} for x in i["evidence"]])
    st.markdown("**Discovery council (AI, independent votes)**")
    cols = st.columns(3)
    for col, voter in zip(cols, ("discovery", "skeptic", "evidence")):
        v = i["discovery_votes"].get(voter)
        col.markdown(f"**{voter}**")
        col.write(v and {k: v[k] for k in ("verdict", "severity", "rationale", "cited_evidence", "counterevidence")})
    st.write("Adjudication:", i["adjudication"])
    st.markdown("**Human gate 1**")
    scope = st.text_input("Scope (comma-separated dependencies)", ",".join(i.get("scope", [])))
    note = st.text_input("Note")
    b1, b2, b3 = st.columns(3)
    for btn, decision, status in ((b1, "approve", "approved"), (b2, "reject", "rejected"),
                                  (b3, "investigate", "needs_investigation")):
        if btn.button(decision.capitalize(), key=decision):
            i["scope"], i["approval_status"] = sorted(set(scope.split(","))), status
            db.save_issue(i)
            db.record_approval(pick, "issue", decision, note, actor="human-dashboard")
            st.success(f"{decision} recorded")
    st.write("Approval history:", db.approvals(pick))

with tab_repair:
    pick = st.selectbox("Issue", [i["issue_id"] for i in db.issues()], key="repair_issue")
    if st.button("Run / resume repair (same backend as CLI)"):
        st.info("Running `python -m resilience_agent repair` - this can take many minutes on CPU.")
        out = subprocess.run([sys.executable, "-m", "resilience_agent", "repair", pick], cwd=s.repo,
                             capture_output=True, text=True)
        st.code((out.stdout + out.stderr)[-6000:])
    cands = db.candidates(pick)
    if cands:
        cols = st.columns(max(1, len(cands)))
        for col, c in zip(cols, cands):
            col.markdown(f"**{c['cand_id']} - {c['strategy_name']}**  \nstatus: {c.get('status')}  valid: {c['valid']}")
            col.write(c["proposal"]["solution"])
            col.code(c["diff"] or "(no diff)", language="diff")
            if c.get("gate"):
                col.write(c["gate"])
        st.markdown("**Anonymous peer reviews**")
        st.dataframe([{k: v["data"].get(k) for k in ("reviewer", "proposal_label", "cand_id", "verdict", "summary")}
                      | {"defects": "; ".join(v["data"].get("defects", []))} for v in db.votes(pick, "repair-review")],
                     use_container_width=True)
    st.markdown("**Human gate 2 (publication)**")
    p1, p2 = st.columns(2)
    if p1.button("Approve publication"):
        db.record_approval(pick, "publication", "approve", actor="human-dashboard")
        st.success("recorded - run repair again to resume the workflow")
    if p2.button("Reject publication"):
        db.record_approval(pick, "publication", "reject", actor="human-dashboard")

with tab_evidence:
    base = db.get("baseline:latest")
    st.markdown("**Baseline (VERIFIED)**")
    st.dataframe([{"env": f"py{e['python']}/{e['mode']}", "status": e["status"],
                   **{k: c["ok"] for k, c in e.get("checks", {}).items()}} for e in base["matrix"]], use_container_width=True)
    pick = st.selectbox("Issue", [i["issue_id"] for i in db.issues()], key="ev_issue")
    for v in db.verifications(pick):
        st.markdown(f"**{v['label']}** - gate passed: {v['data']['gate']['passed']} {v['data']['gate']['reasons']}")
        st.dataframe([{"env": f"py{e['python']}/{e['mode']}", "status": e["status"],
                       **{k: c["ok"] for k, c in e.get("checks", {}).items()}} for e in v["data"]["result"]["matrix"]])
    cap = s.work / "artifacts" / "capsules" / pick / "capsule.md"
    if cap.exists():
        st.markdown("**Dependency Exit Capsule**")
        st.markdown(cap.read_text(encoding="utf-8"))
        st.download_button("capsule.json", (cap.parent / "capsule.json").read_text(encoding="utf-8"), "capsule.json")
