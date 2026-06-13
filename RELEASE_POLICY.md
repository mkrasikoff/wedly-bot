# Release Policy

This document describes the branching model, versioning, and release process for Wedly.

---

## Branches

| Branch           | Purpose                                              | Protected |
|------------------|------------------------------------------------------|-----------|
| `trunk`          | Production. Railway deploys from here.               | ✅         |
| `develop`        | Integration branch. Collects ready features.         | ✅         |
| `feature/TASK-*` | One branch per task, created from `develop`.         | ❌         |
| `bugfix/TASK-*`  | One branch per bug / defect, created from `develop`. | ❌         |
| `hotfix/*`       | Urgent production fix, created from `trunk`.         | ❌         |

> **Note:** After each release, `develop` will always show as *N commits ahead of trunk*
> in GitHub. This is expected behaviour when using squash-merge: original feature commits
> remain in `develop` history but are collapsed into a single squash commit on `trunk`.
> The branch is considered in sync once `trunk → develop` merge is completed (Step 3).

**Rules:**
- Direct push to `trunk` and `develop` is blocked — only via PR.
- `trunk` requires at least one approval (owner may self-merge).
- `develop` requires a PR, no approval needed.
- Delete feature branches after merge.

---

## Versioning

Wedly follows [Semantic Versioning](https://semver.org): `MAJOR.MINOR.PATCH`.

| Change type                             | Example                             | Version bump    |
|-----------------------------------------|-------------------------------------|-----------------|
| Bug fixes, config, docs, logs           | Fix null pointer in QuoteController | `0.1.0 → 0.1.1` |
| New features, non-breaking improvements | Add favourites filter               | `0.1.0 → 0.2.0` |
| Breaking changes, major redesign        | Multi-user support                  | `0.x.x → 1.0.0` |

**Notes:**
- Version is tracked via git tags only — not in `requirements.txt`.
- All tags are annotated: `git tag -a v0.1.0 -m "Release v0.1.0"`.
- Tags are placed on `trunk` **after** merge, never on `develop`.

---

## Release Process

### Step 1 — Feature development
```bash
git checkout develop
git pull origin develop
git checkout -b feature/TASK-42
# ... work, commit ...
git push origin feature/TASK-42
```

Open PR: `feature/TASK-42 → develop`  
Merge with squash without approval.

### Step 2 — Prepare release PR
When `develop` is ready:
- Open PR: `develop → trunk`
- PR title: `Release v0.2.0`
- Squash merge commit message: `Release v0.2.0`

### Step 3 — Sync develop from trunk
After the release PR is merged into trunk, open a PR: `trunk → develop`
- Title: `Sync develop from trunk after Release v0.2.0`
- Merge method: **regular merge** (not squash - need to save the history graph)

This prevents diverged branches on the next release.

### Step 4 — Merge and tag trunk
```bash
# After PR is merged into trunk:
git checkout trunk
git pull origin trunk
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

### Step 5 — Publish GitHub Release
- Go to GitHub → Releases → Draft a new release
- Tag: `v0.2.0` (select existing tag)
- Title: `Release v0.2.0`
- Description: list what changed
- Click **Publish release**

Railway deploys automatically on merge to `trunk` — the tag and GitHub Release are for history and documentation only.

---

## Naming Conventions

| Entity                | Format                     | Example                               |
|-----------------------|----------------------------|---------------------------------------|
| Feature branch        | `feature/TASK-{n}`         | `feature/TASK-42`                     |
| Feature PR title      | `[TASK-{n}] {description}` | `[TASK-42] add favourites filter`     |
| Feature commit        | `[TASK-{n}] {description}` | `[TASK-42] add favourites filter`     |
|                       |                            |                                       |
| Release PR title      | `Release v{version}`       | `Release v0.2.0`                      |
| Release squash commit | `Release v{version}`       | `Release v0.2.0`                      |
| Release tag           | `v{version}`               | `v0.2.0`                              |
| GitHub Release title  | `Release v{version}`       | `Release v0.2.0`                      |
|                       |                            |                                       |
| Fix commit            | `[TASK-{n}] {description}` | `[TASK-42] handle empty author field` |
