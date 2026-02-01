# Security Policy

## Supported Versions

Currently supported versions of svg2fbf with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x (alpha)   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Security Measures

svg2fbf implements multiple layers of security protection:

### 1. Secret Scanning with TruffleHog v3

All commits and code are automatically scanned for:
- API keys and tokens
- Private keys and certificates
- Database credentials
- Cloud service credentials
- Generic secrets

**Pre-commit hook**: TruffleHog runs automatically before every commit to prevent accidental secret exposure.

**CI/CD scanning**: All pull requests and pushes are scanned in GitHub Actions.

**Exclusions**: TruffleHog uses `.trufflehog-exclude-paths.txt` to exclude all gitignored items (`.git/`, `.venv/`, `*_dev/`, logs, temp files, build artifacts, etc.) ensuring efficient scans focused only on tracked source code. See `.trufflehog-README.md` for details.

### 2. Pre-commit Hooks

The project uses comprehensive pre-commit hooks to enforce security best practices:
- Secret detection (TruffleHog)
- Private key detection
- Large file detection (prevents binary/credential files)
- Merge conflict detection
- Branch protection (prevents direct commits to main)

### 3. Code Quality Checks

- **Ruff**: Linting and formatting with security-focused rules
- **MyPy**: Static type checking to prevent type-related vulnerabilities
- **pytest**: Comprehensive test coverage

### 4. Dependency Management

- **uv**: Fast, reliable dependency resolution
- Regular dependency updates via Dependabot
- Security advisories monitoring

## Reporting a Vulnerability

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them privately using one of these methods:

### Option 1: GitHub Security Advisories (Preferred)

1. Go to the [Security tab](https://github.com/Emasoft/svg2fbf/security)
2. Click "Report a vulnerability"
3. Fill out the form with details

### Option 2: Direct Email

Send an email to: **713559+Emasoft@users.noreply.github.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 5 business days
- **Status updates**: Every 7 days until resolved
- **Fix timeline**: Depends on severity
  - Critical: Within 7 days
  - High: Within 30 days
  - Medium: Within 90 days
  - Low: Best effort

## Security Best Practices for Contributors

### 1. Never Commit Secrets

❌ **DON'T:**
```python
API_KEY = "sk_live_1234567890abcdef"
DATABASE_URL = "postgresql://user:password@localhost/db"
```

✅ **DO:**
```python
import os
API_KEY = os.environ.get("API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
```

### 2. Use Environment Variables

Create a `.env` file (gitignored) for local development:
```bash
# .env (never commit this file!)
API_KEY=your_key_here
DATABASE_URL=your_connection_string
```

### 3. Review Changes Before Committing

Always review your changes before committing:
```bash
git diff
git status
```

### 4. Use Pre-commit Hooks

Install pre-commit hooks to catch issues automatically:
```bash
pre-commit install
```

### 5. Keep Dependencies Updated

```bash
# Update dependencies
uv sync --upgrade

# Check for security advisories
pip-audit  # or use GitHub Dependabot
```

## Allowed Public Information

The following information is **safe to commit** and **publicly available**:

- **GitHub Username**: `Emasoft`
- **GitHub No-Reply Email**: `713559+Emasoft@users.noreply.github.com`
- **Repository URL**: `https://github.com/Emasoft/svg2fbf`
- **Package Name**: `svg2fbf`
- **License**: Apache 2.0

TruffleHog is configured to allow these values in `.trufflehog.yaml`.

## Security Features in svg2fbf

### SVG File Processing

svg2fbf processes SVG files with security in mind:

1. **No JavaScript execution**: SVG files are parsed as XML, not executed
2. **No external resource loading**: External references are not fetched
3. **Sandboxed processing**: File operations are limited to designated directories
4. **Input validation**: SVG files are validated before processing

### FBF Output Security

Generated FBF files:

- **Minimal JavaScript**: Only mesh gradient polyfill (~16KB) when needed
- **No external dependencies**: Self-contained animations
- **No data exfiltration**: No network requests or external resource loading
- **Safe for embedding**: Can be safely embedded in web pages

## Security Disclosures

Past security issues (none currently):

| Date | Severity | Description | Fixed Version |
|------|----------|-------------|---------------|
| -    | -        | -           | -             |

## Security Hall of Fame

We appreciate security researchers who help keep svg2fbf secure. Contributors who responsibly disclose vulnerabilities will be acknowledged here (with permission).

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [TruffleHog Documentation](https://github.com/trufflesecurity/trufflehog)
- [Pre-commit Documentation](https://pre-commit.com/)

## Contact

For general questions about security practices in svg2fbf, please open a [discussion](https://github.com/Emasoft/svg2fbf/discussions) or [issue](https://github.com/Emasoft/svg2fbf/issues).

---

**Last Updated**: 2025-01-07
**Version**: 1.0
