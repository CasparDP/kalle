---
project:
  name: "reviewer2"
  description: >
    reviewer2
  added_at: 2026-05-21
  github_url: "https://github.com/CasparDP/reviewer2"

current_focus: 2

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
    status: pending
    created_at: 2026-05-21
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
  last_at: null
  last_commit_seen: null
  last_summary: null

integrations:
  github: "https://github.com/CasparDP/reviewer2"
---
