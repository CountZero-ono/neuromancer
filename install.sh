#!/bin/bash
# Neuromancer — 1-Step Installer Script for Antigravity CLI
set -euo pipefail

TARGET_DIR="$HOME/.antigravity"
SETTINGS_FILE="$HOME/.gemini/antigravity-cli/settings.json"

echo "⚡ Installing Neuromancer Cyberpunk Statusline HUD..."

# Create target directory
mkdir -p "$TARGET_DIR"

# Backup existing statusline.sh if present
if [ -f "$TARGET_DIR/statusline.sh" ]; then
  cp "$TARGET_DIR/statusline.sh" "$TARGET_DIR/statusline.sh.bak.$(date +%Y%m%d_%H%M%S)"
fi

# Copy engine files
cp status.py "$TARGET_DIR/status.py"
chmod +x "$TARGET_DIR/status.py"

# Write statusline.sh wrapper
cat << 'EOF' > "$TARGET_DIR/statusline.sh"
#!/bin/bash
exec python3 "$HOME/.antigravity/status.py" "$@"
EOF
chmod +x "$TARGET_DIR/statusline.sh"

# Ensure settings.json points to statusline.sh
if [ -f "$SETTINGS_FILE" ]; then
  echo "🔧 Verifying $SETTINGS_FILE statusLine configuration..."
  # If jq is available, update statusLine.command
  if command -v jq &>/dev/null; then
    tmp_json=$(mktemp)
    jq --arg cmd "$TARGET_DIR/statusline.sh" '.statusLine.command = $cmd | .statusLine.enabled = true' "$SETTINGS_FILE" > "$tmp_json" && mv "$tmp_json" "$SETTINGS_FILE"
  fi
fi

echo "✅ Neuromancer installed successfully!"
echo "Enjoy your Cyberpunk Onyx Telemetry Deck!"
