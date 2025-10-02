#!/bin/bash
# ABOUTME: Cross-platform installation script for ccthink (Unix/macOS)
# ABOUTME: Installs to ~/.local with dependency checking and PATH setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="$HOME/.local/lib/ccthink"
BIN_DIR="$HOME/.local/bin"
BIN_LINK="$BIN_DIR/ccthink"

echo "==================================="
echo "  ccthink Installation Script"
echo "==================================="
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    echo "Please install Python 3.10 or later"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✓${NC} Found Python $PYTHON_VERSION"

# Check if Python version is sufficient (3.10+)
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo -e "${RED}Error: Python 3.10 or later required${NC}"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

# Create installation directories
echo ""
echo "Creating installation directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
echo -e "${GREEN}✓${NC} Directories created"

# Copy application files
echo ""
echo "Installing ccthink to $INSTALL_DIR..."
cp -r . "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/ccthink"
echo -e "${GREEN}✓${NC} Files copied"

# Create symlink
echo ""
echo "Creating executable symlink..."
ln -sf "$INSTALL_DIR/ccthink" "$BIN_LINK"
echo -e "${GREEN}✓${NC} Symlink created: $BIN_LINK"

# Check if ~/.local/bin is in PATH
echo ""
echo "Checking PATH configuration..."
if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
    echo -e "${GREEN}✓${NC} $BIN_DIR is in PATH"
else
    echo -e "${YELLOW}⚠${NC} $BIN_DIR is NOT in PATH"
    echo ""
    echo "Add this to your shell profile (~/.bashrc, ~/.zshrc, or ~/.profile):"
    echo ""
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# Check dependencies
echo ""
echo "Checking Python dependencies..."
MISSING_DEPS=()

# Check each dependency
for dep in "pydantic" "orjson" "pytest"; do
    if ! python3 -c "import $dep" 2>/dev/null; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All dependencies installed"
else
    echo -e "${YELLOW}⚠${NC} Missing dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo "Install dependencies with:"
    echo ""
    echo "    pip install -r $INSTALL_DIR/requirements.txt"
    echo ""
    echo "Or install individually:"
    echo ""
    echo "    pip install claude-agent-sdk pydantic orjson pytest"
    echo ""
fi

# Create config directory
mkdir -p "$HOME/.config/ccthink"

echo ""
echo "==================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "==================================="
echo ""
echo "Usage:"
echo "  1. Navigate to your project directory:"
echo "     cd /path/to/your/project"
echo ""
echo "  2. Run ccthink:"
echo "     ccthink              # Start monitoring"
echo "     ccthink --commit     # Enable git commits"
echo "     ccthink --help       # Show all options"
echo ""
echo "Each directory gets its own ccthink.conf file"
echo ""
echo "Uninstall:"
echo "  Run: bash $INSTALL_DIR/uninstall.sh"
echo ""
