---
project:
  name: "reviewer2"
  description: >
    reviewer2
  added_at: 2026-05-21
  github_url: "https://github.com/CasparDP/reviewer2"

current_focus: 3

milestones:
  - id: 1
    title: "Fork Identity & Community-Ready Public Repo"
    description: >
      The repo clearly signals it is a fork, explains what changed and why,
      and has enough documentation that an outside researcher can install and
      run it without asking you. Done when: README prominently credits the
      upstream, lists all fork-specific changes, and includes a short 'Why
      this fork?' section; a CONTRIBUTING or Usage note covers the community
      use-case.
    status: done
    created_at: 2026-05-21
    completed_at: 2026-06-13

  - id: 2
    title: "Stable v1.x Release with Passing Smoke Test"
    description: >
      A tagged release (v1.x) exists whose `--base` smoke test completes
      end-to-end on a short PDF without manual intervention. Done when:
      version strings are in sync across pyproject.toml / __init__.py /
      README, a GitHub Release is published, and the smoke-test command is
      documented in the README.
    status: done
    created_at: 2026-05-21
    completed_at: 2026-10-22
    next_task: |
      Add REVIEWER2_API_KEY locally, rerun the documented --base smoke test against v1.1.0, then review and commit the release changes before creating the tag and GitHub Release.
      

  - id: 3
    title: "SSRN Keyword Search Tool (Standalone)"
    description: >
      A minimal CLI tool (or importable module) that accepts a keyword query
      and returns a ranked list of SSRN paper titles, authors, abstracts, and
      URLs — callable independently of the review pipeline. Done when:
      `reviewer2-search 'keyword query' --source ssrn` returns ≥5 results as
      structured JSON/text and is documented in the README.
    status: pending
    created_at: 2026-05-21
    next_task: |
      Prototype a Python script that fetches the SSRN search endpoint (https://api.ssrn.com/content/v1/bindings?query=…) or scrapes the search results page for a hardcoded test query and prints titles + URLs.

  - id: 4
    title: "Integrate Working Paper Search into Review Workflow"
    description: >
      The standalone search tool is wired into the pipeline as an optional
      enrichment step (alongside RAiner), so stage 03b can cite recent SSRN
      working papers. Done when: passing `--ssrn-search` to the CLI triggers a
      keyword search derived from the paper's title/abstract and injects
      results into the literature context the same way RAiner does.
    status: pending
    created_at: 2026-05-21
    next_task: |
      Read stages.py to find exactly where RAiner results are injected (stages 00a and 03b per CLAUDE.md), then sketch the interface a new `ssrn_search(query) -> list[dict]` function needs to match.
      

  - id: 5
    title: "Personal Website Integration & Reproducible Example"
    description: >
      The public-facing website reference is backed by a worked example: a
      sample output report (anonymised or synthetic) plus a one-command
      reproduction script, so visitors can see what the tool produces. Done
      when: a `examples/` folder contains one sample PDF, its generated
      report, and a shell script that reproduces the run with `--base`.
    status: pending
    created_at: 2026-05-21
    next_task: |
      Pick a short open-access paper you've already reviewed, sanitise the output, and commit it to `examples/sample_report.txt` alongside the source PDF (or a DOI pointer if the PDF is too large).
      

checkin:
  last_at: "2026-10-23T18:04:38.427887+02:00"
  last_commit_seen: "3d8bcd1160ad1848b4a8210ba662ea2733b547b9"
  last_summary: "Progress: Renamed the fork from reviewer2 to kalle (v2.0.0, tagged and pushed; GitHub repo is now CasparDP/kalle), as the upstream NOTICE requires; reports carry \"BANG BOOM REVIEW\", the Kalle persona, and a \"Does It Hold Up?\" summary, with no upstream branding, checked by a live writer-stage run on Speaking Politics; Caspar added as author; global kalle skill installed. dot-files skills now point at kalle (commit de91c0a), with the old reviewer2-second-opinion copy removed.\nOpen: Push dot-files (de91c0a, committed locally); repeat the rename steps on casparm2 and icke (git pull, .env keys to KALLE_*, rebuild the poetry env with docling, RAiner, pytest, ruff, opencv, relink the kalle skill in ~/.claude, ~/.codex, ~/.agents); one full kalle run on a new paper to exercise the renamed persona prompts (02g, 03c, 05c); LODDAR project name and github_url still say reviewer2 (change in the LODDAR app).\nNext: Prototype a Python script that fetches the SSRN search endpoint (https://api.ssrn.com/content/v1/bindings?query=…) or scrapes the search results page for a hardcoded test query and prints titles + URLs."
  checkpoint:
    progress: "Renamed the fork from reviewer2 to kalle (v2.0.0, tagged and pushed; GitHub repo is now CasparDP/kalle), as the upstream NOTICE requires; reports carry \"BANG BOOM REVIEW\", the Kalle persona, and a \"Does It Hold Up?\" summary, with no upstream branding, checked by a live writer-stage run on Speaking Politics; Caspar added as author; global kalle skill installed. dot-files skills now point at kalle (commit de91c0a), with the old reviewer2-second-opinion copy removed."
    open: "Push dot-files (de91c0a, committed locally); repeat the rename steps on casparm2 and icke (git pull, .env keys to KALLE_*, rebuild the poetry env with docling, RAiner, pytest, ruff, opencv, relink the kalle skill in ~/.claude, ~/.codex, ~/.agents); one full kalle run on a new paper to exercise the renamed persona prompts (02g, 03c, 05c); LODDAR project name and github_url still say reviewer2 (change in the LODDAR app)."
    next: "Prototype a Python script that fetches the SSRN search endpoint (https://api.ssrn.com/content/v1/bindings?query=…) or scrapes the search results page for a hardcoded test query and prints titles + URLs."
    resume_context: "READ FIRST: loddar.md, CLAUDE.md, CHANGELOG.md (2.0.0 entry)\nSTATE: v2.0.0 rename is on main (d03bfad, author commit 3d8bcd1), tag v2.0.0 pushed; tests pass (14). Live check output: smoke_test/kalle-v2.0.0-writer/report_kalle.txt.\nDECISIONS: persona Kalle; header BANG BOOM REVIEW; summary section Does It Hold Up?; NOTICE keeps 'Copyright 2026 Caspar'; local folder stays ~/Github/reviewer2.\nGOTCHAS: always gh -R CasparDP/kalle; never git push --tags; poetry venv is kalle-*-py3.12 with hand-installed packages.\nTASKS: the Open items above, then milestone 3."
    confirmed_at: "2026-10-23T18:04:38.427887+02:00"
    tool: "Claude Code"
    head_sha: "3d8bcd1160ad1848b4a8210ba662ea2733b547b9"
    worktree_fingerprint: "786a510ea685da9424e0a73e2e25797c0c10d66f6f116370fef51b7fc367725e"
    focus_id: 3

integrations:
  github: "https://github.com/CasparDP/reviewer2"
---
