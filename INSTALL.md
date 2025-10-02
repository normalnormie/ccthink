# ccthink Installation Guide

## Overview

ccthink supports cross-platform installation on Linux, macOS, and Windows. Choose the installation method that works best for you.

## Prerequisites

- **Python 3.10+** required
- **Dependencies**: Will be checked during installation
  - claude-agent-sdk>=0.0.25
  - pydantic>=2.0.0
  - orjson>=3.9.0
  - pytest>=7.0.0 (for testing)

## Installation Methods

### Option 1: Shell Script (Linux/macOS) - RECOMMENDED

**Install:**

```bash
bash install.sh
```

**Features:**

- Installs to `~/.local/lib/ccthink`
- Creates symlink in `~/.local/bin/ccthink`
- Checks Python version and dependencies
- No sudo required (user-local installation)

**Uninstall:**

```bash
bash uninstall.sh
```

---

### Option 2: Batch Script (Windows)

**Install:**

```cmd
install.bat
```

**Features:**

- Installs to `%LOCALAPPDATA%\Programs\ccthink`
- Creates launcher in `%LOCALAPPDATA%\Microsoft\WindowsApps\ccthink.bat`
- Checks Python version and dependencies
- No administrator privileges required

**Uninstall:**

```cmd
uninstall.bat
```

---

## Post-Installation

### 1. Verify Installation

```bash
ccthink --help
```

If command not found, ensure your PATH includes the bin directory:

**Linux/macOS:** Add to `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Windows:** Usually `%LOCALAPPDATA%\Microsoft\WindowsApps` is already in PATH on Windows 10+

### 2. Install Dependencies

If dependencies are missing:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install claude-agent-sdk pydantic orjson pytest
```

### 3. Run ccthink

Navigate to your project directory and run:

```bash
cd /path/to/your/project
ccthink                # Start monitoring
ccthink --commit       # Enable git commits
ccthink --sonnet       # Enable Sonnet phrase transformation
```

## How It Works

ccthink tracks the **directory from which you launch it**:

1. Each project directory gets its own `ccthink.conf` configuration file
2. The launch directory is mapped to a Claude project directory
3. State (last processed UUID, file position, etc.) is stored per-directory
4. You can run ccthink in multiple directories simultaneously

**Example:**

```bash
# Project A
cd ~/projects/my-app
ccthink  # Creates ~/projects/my-app/ccthink.conf

# Project B (in another terminal)
cd ~/projects/another-app
ccthink  # Creates ~/projects/another-app/ccthink.conf
```

Each instance operates independently with its own configuration and state.

## Installation Locations

### Linux/macOS

- **Application**: `~/.local/lib/ccthink/`
- **Executable**: `~/.local/bin/ccthink` (symlink)
- **Config**: Project-specific `ccthink.conf` + `~/.config/ccthink/`

### Windows

- **Application**: `%LOCALAPPDATA%\Programs\ccthink\`
- **Executable**: `%LOCALAPPDATA%\Microsoft\WindowsApps\ccthink.bat`
- **Config**: Project-specific `ccthink.conf` + `%APPDATA%\ccthink\`

## Troubleshooting

### Command not found

**Linux/macOS:**

```bash
# Check if directory is in PATH
echo $PATH | grep .local/bin

# Add to PATH temporarily
export PATH="$HOME/.local/bin:$PATH"

# Add permanently
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Windows:**

```cmd
# Check if WindowsApps is in PATH
echo %PATH%

# If not, add it through System Properties > Environment Variables
# Or use it with full path
%LOCALAPPDATA%\Microsoft\WindowsApps\ccthink.bat
```

### Python version error

Ensure Python 3.10 or later is installed:

```bash
python3 --version  # Linux/macOS
python --version   # Windows
```

### Missing dependencies

Install all dependencies:

```bash
cd ~/.local/lib/ccthink  # Linux/macOS
cd %LOCALAPPDATA%\Programs\ccthink  # Windows

pip install -r requirements.txt
```

## Uninstallation

### What the uninstall script deletes:

- Installation directory (binaries and source)
- Executable symlink/wrapper

### What the uninstall script preserves:

- Project-specific `ccthink.conf` files in your project directories
- Global config directory (`~/.config/ccthink` or `%APPDATA%\ccthink`)

### Complete removal (optional):

**Linux/macOS:**

```bash
rm -rf ~/.config/ccthink
find ~ -name 'ccthink.conf' -delete
```

**Windows:**

```cmd
rmdir /S %APPDATA%\ccthink
```

Then manually delete `ccthink.conf` files from your project directories.
