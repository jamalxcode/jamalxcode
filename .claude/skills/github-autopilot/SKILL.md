---
name: github-autopilot
description: How to handle jamalxcode's GitHub end to end from a Claude cloud session without asking the user to click anything. Covers creating repos, pushing, deploying to GitHub Pages, custom *.sala.company domains, reading other repos, copying snippets between projects (GoatCounter etc.) and checking deploys. Use whenever a task touches GitHub beyond the current repo, needs a new repo, a website deploy, Pages or a domain, or when a GitHub call fails with 403 / "Resource not accessible by integration" / "not permitted through this proxy".
---

# GitHub autopilot for jamalxcode

The user wants GitHub handled fully, without being asked to do things. Do the work;
only ask the user for something on the "truly manual" list at the bottom.

## What works and what doesn't in a cloud session (verified 2026-10)

| Need | Works? | How |
|---|---|---|
| Push to an attached repo | yes | `git push origin <branch>` over HTTPS (proxy injects auth). Ignore the harmless `push negotiation failed; proceeding anyway` warning. |
| Attach another of the user's repos | yes | `add_repo {owner:"jamalxcode", repo, access:"push"}`, clone, then `register_repo_root`. All their repos are `can_push:true` (`list_repos`). |
| Read a public repo without attaching | yes | `git clone --depth 1 https://github.com/jamalxcode/<r> <scratchpad>/peek-<r>` |
| Trigger a workflow | yes | `mcp__github__actions_run_trigger {method:"run_workflow", owner, repo, ref:"main", workflow_id:"<file>.yml", inputs:{...}}` |
| Read runs / jobs / logs / deployments | yes | `gh api repos/<o>/<r>/actions/runs?per_page=1`, `mcp__github__get_job_logs`, `gh api repos/<o>/<r>/deployments` (repo must be attached) |
| Create a repo | **no** directly | `create_repository` → 403 "Resource not accessible by integration". Use the Repo admin workflow below. |
| Pages / custom domain / repo settings API | **no** directly | `gh api repos/.../pages` → 403 "not permitted through this proxy". Use the Repo admin workflow. |
| `configure-pages` with `enablement: true` | **no** | GITHUB_TOKEN can't create a Pages site. Use the Repo admin workflow. |
| Fetch *.github.io, *.sala.company, dns.google | blocked by the network policy | Check deployment statuses instead (see Verify). |
| GitHub archive zips (`/archive/*.zip`) | 403 | `git clone --depth 1 -b <tag>` instead; release assets via `curl -L` work. |

## The Repo admin workflow (does the "settings page" stuff)

`jamalxcode/jamalxcode/.github/workflows/repo-admin.yml` runs on GitHub with the
`ADMIN_TOKEN` secret (the user's fine-grained token), so the proxy doesn't apply.

1. `add_repo {owner:"jamalxcode", repo:"jamalxcode", access:"push"}` (needed to dispatch and read its runs).
2. Dispatch it:
   ```
   mcp__github__actions_run_trigger {method:"run_workflow", owner:"jamalxcode", repo:"jamalxcode",
     ref:"main", workflow_id:"repo-admin.yml",
     inputs:{task:"site", repo:"<name>", domain:"<name>.sala.company", private:"false", description:"..."}}
   ```
   Tasks: `create-repo`, `pages` (source = GitHub Actions, plus the domain if given), `domain`, `site` (all three), `settings` (description and homepage only), `reset-domain`, `remove-domain`, `disable-pages`, `archive` (run `disable-pages` first: archived repos are read-only), and `audit` (read-only report on every repo, written to `audit.txt` in the PRIVATE repo `jamalxcode/repo-audit`; job logs are blocked here, so `add_repo` that repo and clone it to read it; never publish the report to a branch of the public profile repo, it lists private repos and their files).
3. Wait for it: `gh api "repos/jamalxcode/jamalxcode/actions/runs?per_page=1" --jq '.workflow_runs[0]|"\(.status) \(.conclusion)"'`. Read the logs with `get_job_logs` if it fails.
4. For a new repo, now `add_repo` it with push access, clone it, and push.

If the run fails with "ADMIN_TOKEN secret is not set" or 401/403, the token is missing or expired.
That's the one thing to ask the user for (see the bottom).

## New website (the sala.company pattern: radio, video, last, heat, weather)

1. Repo admin `task:"site"` → creates the repo, enables Pages (Actions), sets the domain.
2. `add_repo` + clone. Add `.nojekyll`, a `CNAME` file with the domain (harmless, and it documents the domain), and `.github/workflows/pages.yml`:
   ```yaml
   name: Deploy site
   on: { push: { branches: [main] }, workflow_dispatch: {} }
   permissions: { contents: read, pages: write, id-token: write }
   concurrency: { group: pages, cancel-in-progress: false }
   jobs:
     deploy:
       runs-on: ubuntu-latest
       environment: { name: github-pages, url: "${{ steps.deployment.outputs.page_url }}" }
       steps:
         - uses: actions/checkout@v4
         - uses: actions/configure-pages@v5
         - uses: actions/upload-pages-artifact@v3
           with: { path: . }
         - id: deployment
           uses: actions/deploy-pages@v4
   ```
3. Add the shared GoatCounter snippet (copy it verbatim from `peek-radio/index.html`, the block starting with the `GoatCounter analytics` comment; endpoint `https://salacompany.goatcounter.com/count`).
4. Push to `main` (these site repos deploy from main). Commit as the user: `git -c user.name="jamal xcode" -c user.email="j.mutawa@gmail.com" commit ...`.
5. Verify (below), then tell the user the URL.

The order matters: if the workflow runs before Pages is enabled it fails. Then just re-dispatch `pages.yml`.

## Verify a deploy (the live site can't be fetched)

```
for i in $(seq 1 30); do out=$(gh api "repos/jamalxcode/<r>/actions/runs?per_page=1" --jq '.workflow_runs[0] | "\(.head_sha[0:7]) \(.status) \(.conclusion)"'); echo "$out"; case "$out" in *completed*) break;; esac; sleep 10; done
D=$(gh api repos/jamalxcode/<r>/deployments --jq '.[0].id'); gh api repos/jamalxcode/<r>/deployments/$D/statuses --jq '.[0]|{state,environment_url}'
```
`state: success` with `environment_url: https://<domain>/` means it's live.

## Syncing between projects

- Clone the source repos into the scratchpad (`peek-<r>`), grep the snippet, paste it verbatim, and `diff` the block against the source to prove it's identical.
- To change several repos, `add_repo` each with push access, then do one clone at a time (the proxy allows 2 git operations per repo at once). Run `git fetch origin main` before each push so commits made on GitHub's side (e.g. "Create CNAME") are merged in, not overwritten.
- Branches: the session's designated `claude/...` branch is for the session's primary repo. Site repos that deploy from main get pushed to main.

## Truly manual (ask only for these, as short numbered browser steps)

1. **One time only, the ADMIN_TOKEN.** Create it at github.com → Settings → Developer settings → Fine-grained tokens → Generate. Resource owner: jamalxcode. Repository access: All repositories. Permissions: Administration, Contents, Pages and Workflows read and write. Then save it at github.com/jamalxcode/jamalxcode → Settings → Secrets and variables → Actions → New repository secret, name `ADMIN_TOKEN`. Again only when it expires.
2. **DNS** for a new subdomain, unless a wildcard exists: CNAME `<name>` → `jamalxcode.github.io` at the sala.company DNS provider. A one-time `*.sala.company` wildcard CNAME removes this step. If you suggest the wildcard, also suggest verifying sala.company under GitHub → Settings → Pages → Verified domains, which blocks subdomain takeover.
3. GitHub account connection problems (`add_repo` says the app isn't installed or connected) → https://claude.ai/connect-github.

Never tell the user "I can't do settings from here" without first trying the Repo admin workflow.
