# GitHub Branch Protection Rules

This document defines the required branch protection rules for the svg2fbf repository to enforce the 5-branch development pipeline.

## Overview

The svg2fbf project uses a strict 5-branch workflow:
```
dev → testing → review → master → main
```

**Critical Requirement**: All pull requests MUST target the `dev` branch (except admin hotfixes).

## Branch Protection Configuration

### Protected Branches

Apply protection rules to these branches:
- `master` - Production stable releases
- `main` - GitHub default (mirrors master)
- `review` - Pre-release review stage
- `testing` - QA and bug fixing stage (optional protection)

### `master` Branch Protection Rules

**Settings → Branches → Branch protection rules → `master`**

#### Required Settings:

1. **Require a pull request before merging**
   - ✅ Enabled
   - **Require approvals**: 1 (minimum)
   - ❌ Dismiss stale pull request approvals when new commits are pushed (optional)
   - ✅ Require review from Code Owners (if CODEOWNERS file exists)
   - ❌ Restrict who can dismiss pull request reviews (optional)
   - ✅ Allow specified actors to bypass required pull requests
     - **Allowed actors**: Repository administrators only

2. **Require status checks to pass before merging**
   - ✅ Enabled
   - ✅ Require branches to be up to date before merging
   - **Required status checks** (select these from CI runs):
     - `tests` - Pytest test suite
     - `ruff` - Code formatting and linting
     - `trufflehog` - Secret scanning
     - Any other CI checks that run on review/master

3. **Require conversation resolution before merging**
   - ✅ Enabled (recommended)

4. **Require signed commits**
   - ❌ Optional (depends on team preference)

5. **Require linear history**
   - ✅ Enabled (prevents merge commits, enforces rebasing)

6. **Require deployments to succeed before merging**
   - ❌ Not applicable for this project

7. **Lock branch**
   - ❌ Disabled (must allow promotion merges)

8. **Do not allow bypassing the above settings**
   - ❌ Disabled
   - **Reason**: Admins need to push hotfixes and run `just promote-to-stable`

9. **Restrict who can push to matching branches**
   - ✅ Enabled
   - **Allowed actors**:
     - Repository administrators
     - CI/CD service accounts (GitHub Actions)
   - **Reason**: Only automated promotions and admin hotfixes can push directly

10. **Allow force pushes**
    - ❌ Disabled (never force push to protected branches)

11. **Allow deletions**
    - ❌ Disabled (prevent accidental branch deletion)

### `main` Branch Protection Rules

**Settings → Branches → Branch protection rules → `main`**

**Same settings as `master`** (main is a mirror of master)

Key points:
- Same CI requirements
- Same push restrictions
- Same approval requirements
- Synchronized by `just sync-main` command

### `review` Branch Protection Rules

**Settings → Branches → Branch protection rules → `review`**

#### Required Settings:

1. **Require a pull request before merging**
   - ❌ Disabled
   - **Reason**: Receives promotions from `just promote-to-review`, not PRs

2. **Require status checks to pass before merging**
   - ✅ Enabled
   - ✅ Require branches to be up to date before merging
   - **Required status checks**: Same as master

3. **Restrict who can push to matching branches**
   - ✅ Enabled
   - **Allowed actors**:
     - Repository administrators
     - CI/CD service accounts (GitHub Actions)
   - **Reason**: Only automated promotions can push

4. **Allow force pushes**
   - ❌ Disabled

5. **Allow deletions**
   - ❌ Disabled

### `testing` Branch Protection (Optional)

**Settings → Branches → Branch protection rules → `testing`**

Protection is optional for testing branch (developers may want to force-push during debugging).

**Recommended minimal protection:**
1. **Allow force pushes**
   - ⚠️ Allowed (developers may need to reset during bug hunting)

2. **Allow deletions**
   - ❌ Disabled

### `dev` Branch Protection

**Settings → Branches → Branch protection rules → `dev`**

**⚠️ CRITICAL**: This is the ONLY branch that accepts PRs from contributors.

#### Required Settings:

1. **Require a pull request before merging**
   - ✅ Enabled
   - **Require approvals**: 1 (for external contributors)
   - ❌ Dismiss stale pull request approvals (optional)
   - ✅ Require review from Code Owners (if exists)
   - ✅ Allow specified actors to bypass required pull requests
     - **Allowed actors**: Repository administrators, maintainers
     - **Reason**: Core team can push directly for quick fixes

2. **Require status checks to pass before merging**
   - ❌ Disabled
   - **Reason**: CI is disabled on dev to allow rapid iteration
   - Developers run checks manually with `just test`, `just lint`

3. **Require conversation resolution before merging**
   - ✅ Enabled (recommended)

4. **Restrict who can push to matching branches**
   - ❌ Disabled
   - **Reason**: All contributors push to dev, protection is via PR reviews

5. **Allow force pushes**
   - ⚠️ Allowed (for maintainers only)
   - Configure: **Specify who can force push** → Administrators/Maintainers

6. **Allow deletions**
   - ❌ Disabled

## Rulesets (Alternative to Branch Protection Rules)

GitHub now recommends using **Rulesets** instead of classic branch protection rules. Rulesets offer more flexibility and better visibility.

### Creating a Ruleset

**Settings → Rules → Rulesets → New ruleset → New branch ruleset**

**Ruleset Name**: `Production Branches Protection`

**Target branches**:
- Include: `master`, `main`, `review`

**Rules**:
1. ✅ Restrict creations
2. ✅ Restrict updates
   - ✅ Require a pull request before merging
     - Required approvals: 1
     - Allow bypass: Administrators
   - ✅ Require status checks to pass
     - Required checks: tests, ruff, trufflehog
3. ✅ Restrict deletions
4. ✅ Restrict force pushes
5. ✅ Require linear history

**Bypass list**:
- Repository administrators (for hotfixes and promotions)
- GitHub Actions (for automated promotions)

**Enforcement status**: Active

### Creating Dev Branch Ruleset

**Ruleset Name**: `Development Branch Protection`

**Target branches**:
- Include: `dev`

**Rules**:
1. ✅ Require a pull request before merging
   - Required approvals: 1 (external contributors)
   - Allow bypass: Administrators, Maintainers
2. ✅ Require conversation resolution
3. ✅ Restrict deletions
4. ⚠️ Allow force push (maintainers only)

**Bypass list**:
- Administrators
- Maintainers (for quick fixes)

**Enforcement status**: Active

## Pull Request Template

Create `.github/PULL_REQUEST_TEMPLATE.md` to enforce dev branch targeting:

```markdown
## Pull Request Checklist

### ⚠️ CRITICAL: Target Branch

- [ ] **This PR targets the `dev` branch** (NOT testing, review, master, or main)
- [ ] Feature branch created from `dev`

**Exception**: Only admins/owners can create PRs targeting `master`/`main` for critical hotfixes.

### Changes

- [ ] Code follows project style guidelines
- [ ] Tests added/updated (if applicable)
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated (if applicable)

### Testing

- [ ] `just test` passes locally
- [ ] `just lint` passes locally
- [ ] Manual testing completed

### Description

<!-- Describe your changes here -->
```

## GitHub Actions CI Configuration

Update `.github/workflows/*.yml` to run CI ONLY on protected branches:

```yaml
name: CI

on:
  push:
    branches:
      - review    # Run on review branch
      - master    # Run on master branch
      - main      # Run on main branch
  pull_request:
    branches:
      - dev       # Run on PRs to dev branch

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          uv run pytest tests/
      # ... other steps ...
```

**Why this configuration:**
- ✅ CI runs on protected branches (review, master, main)
- ✅ CI runs on PRs to dev (validates PRs before merge)
- ❌ CI does NOT run on direct pushes to dev/testing (allows rapid iteration)

## Enforcement Summary

| Branch | PRs Allowed | Direct Push | Force Push | CI Required | Approval Required |
|--------|-------------|-------------|------------|-------------|-------------------|
| `dev` | ✅ YES (ONLY target for contributor PRs) | ✅ Maintainers | ⚠️ Maintainers only | ❌ No | ✅ Yes (external) |
| `testing` | ❌ No | ✅ Admins | ⚠️ Optional | ❌ No | N/A |
| `review` | ❌ No | ✅ Admins | ❌ No | ✅ Yes | N/A |
| `master` | ❌ No | ✅ Admins only (hotfixes) | ❌ No | ✅ Yes | ✅ Yes (if PR) |
| `main` | ❌ No | ✅ Admins only | ❌ No | ✅ Yes | ✅ Yes (if PR) |

**Key Points:**
- Contributors can ONLY create PRs to `dev`
- `testing`, `review`, `master`, `main` receive code via promotion commands
- Only admins can push hotfixes directly to `master`/`main`
- CI enforces quality on protected branches

## Verification

After configuring rules, verify:

1. **Try creating PR to master as non-admin**:
   ```bash
   gh pr create --base master --title "Test PR"
   ```
   - ✅ Should succeed (branch protection allows PRs with approval)
   - ❌ Merging should be blocked until approved and CI passes

2. **Try pushing directly to master as non-admin**:
   ```bash
   git push origin master
   ```
   - ❌ Should be rejected with permission error

3. **Try creating PR to dev**:
   ```bash
   gh pr create --base dev --title "feat: New feature"
   ```
   - ✅ Should succeed (dev accepts PRs)

4. **Verify CI runs only where expected**:
   - ✅ CI runs on PRs to dev
   - ✅ CI runs on push to review/master/main
   - ❌ CI does NOT run on push to dev/testing

## Migration Guide

If updating from old protection rules:

1. **Backup existing settings** - Document current configuration
2. **Create rulesets** - Use new rulesets instead of classic rules
3. **Update CI workflows** - Ensure proper branch triggers
4. **Create PR template** - Add dev branch requirement
5. **Test thoroughly** - Verify all workflows still function
6. **Announce changes** - Notify team of new rules

## Troubleshooting

**Problem**: Promotion command fails with "protected branch" error

**Solution**: Ensure GitHub Actions service account is in bypass list

**Problem**: Developers can't push to dev

**Solution**: Dev branch should NOT restrict pushes (only require PRs for external contributors)

**Problem**: CI not running on PRs

**Solution**: Check workflow triggers include `pull_request: branches: [dev]`

## References

- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Pull Request Template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository)
