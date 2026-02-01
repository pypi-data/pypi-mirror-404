# svg2fbf Installation Guide

This guide covers the complete installation process for svg2fbf, including the optional viewBox repair utility.

## Table of Contents

1. [Quick Install (Python Only)](#quick-install-python-only)
2. [Full Install (with ViewBox Repair)](#full-install-with-viewbox-repair)
3. [Installation Methods](#installation-methods)
4. [Post-Install Verification](#post-install-verification)
5. [Troubleshooting](#troubleshooting)

---

## Quick Install (Python Only)

If you only need the core `svg2fbf` animation tool and your SVG files already have correct viewBox attributes:

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install svg2fbf
uv tool install svg2fbf --python 3.10

# 3. Verify
svg2fbf --version
```

**You're done!** Skip to [Usage](#usage) section.

---

## Full Install (with ViewBox Repair)

For the complete experience including the `svg-repair-viewbox` utility:

### Step 1: Install svg2fbf

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install svg2fbf
uv tool install svg2fbf --python 3.10
```

### Step 2: Install Node.js

**macOS** (using Homebrew):
```bash
brew install node
```

**Linux** (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install nodejs npm
```

**Linux** (Fedora/RHEL):
```bash
sudo dnf install nodejs npm
```

**Windows**:
- Download installer from [nodejs.org](https://nodejs.org)
- Run installer and follow prompts
- Restart terminal after installation

**Verify Node.js installation**:
```bash
node --version  # Should show v18.0.0 or higher
npm --version   # Should show 9.0.0 or higher
```

### Step 3: Install Puppeteer

```bash
# Install Puppeteer globally
npm install -g puppeteer

# Verify installation
npm list -g puppeteer
```

**Note**: Puppeteer will download a bundled Chromium browser (~170MB). This is normal and required for accurate SVG bounding box calculation.

### Step 4: Verify Complete Installation

```bash
# Check both commands are available
svg2fbf --version
svg-repair-viewbox --help

# Test viewBox repair (should show help, not errors)
svg-repair-viewbox --help
```

---

## Installation Methods

### Method 1: From PyPI (Recommended - When Published)

```bash
uv tool install svg2fbf --python 3.10
```

### Method 2: From GitHub Release Wheel

```bash
# Replace VERSION with actual release version
uv tool install https://github.com/Emasoft/svg2fbf/releases/download/vVERSION/svg2fbf-VERSION-py3-none-any.whl --python 3.10
```

### Method 3: From Git Repository

```bash
# Latest development version
uv tool install git+https://github.com/Emasoft/svg2fbf.git --python 3.10

# Specific release tag
uv tool install git+https://github.com/Emasoft/svg2fbf.git@v0.1.2a4 --python 3.10
```

### Method 4: From Local Wheel File

```bash
# If you have a downloaded .whl file
uv tool install /path/to/svg2fbf-VERSION-py3-none-any.whl --python 3.10
```

---

## Post-Install Verification

### Verify svg2fbf

```bash
# Check version
svg2fbf --version

# Display help
svg2fbf --help

# Test with simple animation (if you have SVG files)
svg2fbf -i /path/to/frames -o /path/to/output -f test.fbf.svg -s 24
```

### Verify svg-repair-viewbox

```bash
# Display help
svg-repair-viewbox --help

# Test on a directory (dry-run check)
svg-repair-viewbox /path/to/svg/files
```

---

## Troubleshooting

### Issue: `svg2fbf: command not found`

**Cause**: uv tools directory not in PATH

**Solution**:
```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

### Issue: `svg-repair-viewbox: command not found`

**Cause**: svg2fbf not properly installed

**Solution**:
```bash
# Reinstall
uv tool uninstall svg2fbf
uv tool install svg2fbf --python 3.10
```

### Issue: `❌ Node.js not found`

**Cause**: Node.js not installed or not in PATH

**Solution**:
```bash
# Verify Node.js installation
which node
node --version

# If not found, install Node.js (see Step 2 above)
```

### Issue: `❌ Puppeteer not found`

**Cause**: Puppeteer not installed globally

**Solution**:
```bash
# Install Puppeteer globally
npm install -g puppeteer

# Verify installation
npm list -g puppeteer
```

### Issue: `Cannot find module 'puppeteer'`

**Cause**: Puppeteer not in Node.js module path

**Solutions**:

**Option 1 - Install globally (recommended)**:
```bash
npm install -g puppeteer
```

**Option 2 - Install in scripts directory**:
```bash
# Find scripts directory
python3 -c "import sysconfig; print(sysconfig.get_path('data'))"

# Navigate to scripts directory and install
cd /path/to/share/svg2fbf  # Use path from above
npm install
```

### Issue: `calculate_bbox.js not found`

**Cause**: Incomplete installation or corrupted package

**Solution**:
```bash
# Reinstall completely
uv tool uninstall svg2fbf
uv tool install svg2fbf --python 3.10
```

### Issue: Puppeteer download fails or times out

**Cause**: Network issues or firewall blocking Chromium download

**Solutions**:

1. **Try with custom download host**:
   ```bash
   PUPPETEER_DOWNLOAD_HOST=https://registry.npmmirror.com/-/binary/chromium-browser-snapshots npm install -g puppeteer
   ```

2. **Skip Chromium download** (advanced - requires manual Chromium setup):
   ```bash
   PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true npm install -g puppeteer
   ```

3. **Use system Chrome** (if available):
   ```bash
   # Set environment variable before using svg-repair-viewbox
   export PUPPETEER_EXECUTABLE_PATH=/path/to/chrome
   ```

---

## Updating

### Update svg2fbf

```bash
# Uninstall current version
uv tool uninstall svg2fbf

# Install latest version
uv tool install svg2fbf --python 3.10
```

### Update Puppeteer

```bash
npm update -g puppeteer
```

---

## Uninstalling

### Uninstall svg2fbf

```bash
uv tool uninstall svg2fbf
```

### Uninstall Puppeteer (optional)

```bash
npm uninstall -g puppeteer
```

### Uninstall Node.js (optional)

**macOS** (Homebrew):
```bash
brew uninstall node
```

**Linux**:
```bash
sudo apt remove nodejs npm  # Ubuntu/Debian
sudo dnf remove nodejs      # Fedora/RHEL
```

**Windows**:
- Use "Add or Remove Programs"
- Uninstall "Node.js"

---

## FAQ

### Q: Do I need Node.js to use svg2fbf?

**A**: No, Node.js is only required for the **optional** `svg-repair-viewbox` utility. The core `svg2fbf` animation tool works without Node.js.

### Q: Can I use a different version of Node.js?

**A**: Yes, svg-repair-viewbox works with Node.js 16+ (v18+ recommended).

### Q: Can I install Puppeteer locally instead of globally?

**A**: Yes, but you'll need to install it in the svg2fbf scripts directory. See troubleshooting section for details.

### Q: Why does Puppeteer download Chromium?

**A**: Puppeteer bundles a specific version of Chromium to ensure consistent behavior across different systems. This is necessary for accurate SVG rendering and bounding box calculation.

### Q: Can I use my system's Chrome instead?

**A**: Yes, set the `PUPPETEER_EXECUTABLE_PATH` environment variable to point to your Chrome/Chromium binary.

### Q: What if I only want to repair viewBox on a few files?

**A**: You can skip the Puppeteer installation and manually edit the viewBox attributes in your SVG files using a text editor.

---

## Platform-Specific Notes

### macOS

- Homebrew is the recommended way to install Node.js
- M1/M2 Macs: Puppeteer works natively on ARM64

### Linux

- Ubuntu 20.04+, Debian 11+, Fedora 35+ are tested
- Some distributions may require additional libraries for Puppeteer/Chromium
- Install missing dependencies with: `sudo apt install -y libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxi6 libxtst6 libnss3 libcups2 libxss1 libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0`

### Windows

- Use PowerShell or Git Bash for installation commands
- WSL2 (Windows Subsystem for Linux) is fully supported and recommended for best experience

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/Emasoft/svg2fbf/issues)
2. Review the [main README](../README.md)
3. Open a new issue with:
   - Your OS and version
   - Python version (`python --version`)
   - Node.js version (`node --version`)
   - Error messages
   - Steps to reproduce
