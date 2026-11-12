# Portfolio release evidence

This record distinguishes a reproducible local demonstration from a hosted deployment.

## Fresh-user verification

- Source commit: `ae73c645ec9b68c1a4ea899d10e56da9f0d94efb` (`main`, 12 November 2026).
- Environment: a new tracked-file-only checkout and a new Python 3.12.14 virtual environment.
- Installation: `python -m pip install -r requirements-tested.txt` completed and `python -m pip check` reported no broken requirements.
- Deterministic suite: 150/150 non-UI tests passed in the isolated checkout.
- The two local Streamlit `AppTest` cases reproduced the documented sandbox stall; the GitHub Actions clean runners remain the authoritative evidence for those cases.
- Browser target: the isolated checkout started successfully on `127.0.0.1:8504`.

## Reproducible workspace links

The workspace control is bound to the `workspace` query parameter. A reviewer can open a specific surface directly, for example:

- `?workspace=Analyst%20watchlist`
- `?workspace=Research%20workflow`
- `?workspace=Evidence%20graph%20%26%20operations`

Invalid workspace values are rejected by Streamlit and removed from the URL.

## Screenshot contract

Release screenshots in `docs/screenshots/` were captured from the running D9.2 candidate on 12 November 2026. They are evidence of the rendered local product, not mockups and not evidence of hosting.

| File | Workspace | Viewport | Visible evidence |
| --- | --- | --- | --- |
| `analyst-watchlist.png` | Analyst watchlist | 1280×720 | URL-selected workspace, bounded ALP/BET/GAM universe, historical cutoff, search, session watchlist, and comparison metrics |
| `research-workflow.png` | Research workflow | 1280×720 | URL-selected workspace, five-step typed trace, explicit missing News role, zero conflicts, and offline boundary |
| `evidence-operations.png` | Evidence graph & operations | 1280×720 | URL-selected workspace, six nodes, five edges, zero dangling links, graph identity, and non-causal language |

The images were captured only after the browser accessibility state confirmed the requested workspace and its visible acceptance values. The exact D9.2 source commit is recorded in the development status after the artifact commit is created.

## Boundaries

The application still uses a bounded fictional market/fundamental fixture and local single-process persistence. These screenshots do not imply live market coverage, production authentication, licensed news, scheduled processing, multi-worker durability, or investment advice.
