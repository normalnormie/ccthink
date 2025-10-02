#!/bin/bash
# ABOUTME: Uninstallation script for ccthink (Unix/macOS)
# ABOUTME: Removes installation while preserving project-specific configs

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="$HOME/.local/lib/ccthink"
BIN_LINK="$HOME/.local/bin/ccthink"

echo "==================================="
echo "  ccthink Uninstallation Script"
echo "==================================="
echo ""

# Confirm uninstallation
echo -e "${YELLOW}This will remove:${NC}"
echo "  - $INSTALL_DIR"
echo "  - $BIN_LINK"
echo ""
echo -e "${GREEN}This will be preserved:${NC}"
echo "  - Project-specific ccthink.conf files"
echo "  - ~/.config/ccthink directory"
echo ""
printf "Continue? (y/N) "
read -r REPLY
case "$REPLY" in
    [Yy]|[Yy][Ee][Ss])
        # Continue with uninstallation
        ;;
    *)
        echo "Uninstallation cancelled"
        exit 0
        ;;
esac

echo ""
echo "Uninstalling ccthink..."

# Remove symlink
if [ -L "$BIN_LINK" ]; then
    rm -f "$BIN_LINK"
    echo -e "${GREEN}✓${NC} Symlink removed: $BIN_LINK" # noqm - accurate description of uninstall action
else
    echo -e "${YELLOW}⚠${NC} Symlink not found: $BIN_LINK"
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}✓${NC} Installation removed: $INSTALL_DIR" # noqm - accurate description of uninstall action
else
    echo -e "${YELLOW}⚠${NC} Installation directory not found: $INSTALL_DIR"
fi

echo ""
echo "==================================="
echo -e "${GREEN}Uninstallation Complete!${NC}"
echo "==================================="
echo ""
echo "Note: Project-specific config files preserved"
echo "To remove all ccthink data:"
echo "  rm -rf ~/.config/ccthink"
echo "  find ~ -name 'ccthink.conf' -delete"
echo ""
