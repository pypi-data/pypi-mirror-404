# Pull Request Requirements

### ⚠️ CRITICAL: PR Target Branch

**ALL pull requests MUST target the `dev` branch.**

- [ ] **PR targets `dev` branch** (NOT testing, review, master, or main)
- [ ] Feature branch created from `dev` branch
- [ ] Changes follow the 5-branch promotion pipeline

**Exception:** Only repository admins/owners can create hotfix PRs targeting `master`/`main` for critical security issues.

### Pre-PR Checklist

- [ ] Run `ruff format` and `ruff check --fix`
- [ ] Run `trufflehog git file://. --since-commit origin/main --branch HEAD --results=verified,unknown` (expect no verified results)
- [ ] Keep lines ≤ 88 chars (`E501` enforced)
- [ ] Prefix intentionally unused loop vars with `_` (satisfies B007)
- [ ] Use `trufflehog:ignore` only for reviewed, specific exceptions
