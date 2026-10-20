# jamalxcode (profile repo)

This repo holds the GitHub profile README and the Repo admin workflow that manages all of jamalxcode's repos.

## How to do GitHub work

Use the **github-autopilot** skill (`.claude/skills/github-autopilot/SKILL.md`). It covers the Repo admin workflow, the sala.company site pattern, deploy checks and commit identity. Don't repeat its contents here; update the skill instead.

Start any cleanup or review with the `audit` task, then read the report from the `audit-report` branch (job logs can't be fetched from a cloud session).

## House rules

- **Archive, don't delete.** Retired repos are archived (run `disable-pages` first if they still serve a site). Only delete when the user explicitly asks.
- **Work in progress stays off public pages.** weather, flattery, rocketsky and globe are not listed in the README or on go.sala.company until the user says they're ready.
- **Meridian (the `globe` repo) is never advertised.** It's public and in use, but don't name or link it in the README, on the portal, in other repos' READMEs or descriptions, or in anything posted publicly.
- **Links point to the right place.** go.sala.company is the portal; www.sala.company is the Shopify ebook store. Each site repo's homepage is its own `<name>.sala.company` address.
- **The README lists live sites only**, grouped as News & Markets, Games, AI & Media, Tools and Learn, each with a site link, a repo link and a one-line description. When a site goes live or is retired, update the README and go.sala.company together.
- The recent-articles list between `<!-- SUBSTACK:START -->` and `<!-- SUBSTACK:END -->` is updated by hand (the auto-update action was removed).

## Commits

Commit as the user and push this repo straight to `main`:

```
git -c user.name="jamal xcode" -c user.email="j.mutawa@gmail.com" commit -m "..."
```

Keep messages short and specific, prefixed by the area when it helps (`README: ...`, `repo-admin: ...`).
