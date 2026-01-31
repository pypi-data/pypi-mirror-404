# ⚠️ CRITICAL: Do NOT Create .venv in tests/

**IMPORTANT**: This directory should NEVER contain a `.venv/` subdirectory.

## Why?

The project uses **ONE virtual environment** at the project root:

```
svg2fbf/
└── .venv/        ← THE ONLY VENV
```

## Common Causes of Rogue .venv Creation

1. **Running `uv venv` from tests/ directory** ❌
   ```bash
   cd tests && uv venv  # DON'T DO THIS!
   ```

2. **IDE auto-creating venv** (VSCode, PyCharm)
   - Check your IDE settings
   - Disable "auto-create virtualenv" for subdirectories

3. **Running test commands from tests/ directory**
   ```bash
   # ❌ WRONG:
   cd tests && uv run python testrunner.py
   
   # ✅ CORRECT:
   uv run python tests/testrunner.py
   ```

## If .venv Appears

```bash
# Delete it immediately
rm -rf tests/.venv

# Always work from project root
cd /path/to/svg2fbf
uv sync
```

## Monitoring for .venv Creation

A monitoring script is available to detect and alert on `.venv` creation:

```bash
# Run the monitor in background (from project root)
uv run python tests/monitor_venv.py &

# The monitor will alert if .venv is created in tests/
```

This helps identify what process is creating the unwanted `.venv`.

## Testing

All tests work perfectly with the project root `.venv` - no local venv needed!

```bash
# From project root
uv run python tests/testrunner.py create --random 50 -- "FBF.SVG/SVG 1.1 W3C Test Suit/w3c_50frames/"
just test-random-w3c 50
```
