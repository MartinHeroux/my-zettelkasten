#!/usr/bin/env bash
set -Eeuo pipefail

# 1. Install dependencies
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip python3-tk

# 2. Clone My Zettelkasten
APP_DIR="$HOME/.local/share/personal-zettelkasten"
mkdir -p "$APP_DIR" "$HOME/.local/bin" "$HOME/.local/share/applications"

if [ -d "$APP_DIR/source/.git" ]; then
    git -C "$APP_DIR/source" pull --ff-only
else
    git clone https://github.com/MartinHeroux/my-zettelkasten.git "$APP_DIR/source"
fi

# 3. Create virtual environment and install app
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/python" -m pip install -e "$APP_DIR/source"

# 4. Create terminal launcher
cat > "$HOME/.local/bin/my-zettelkasten" <<'EOF'
#!/usr/bin/env bash
exec "$HOME/.local/share/personal-zettelkasten/.venv/bin/python" -m zettelkasten "$@"
EOF

chmod +x "$HOME/.local/bin/my-zettelkasten"

# 5. Find the branded icon from the repository
ICON=$(find "$APP_DIR/source" -type f \
    \( -iname '*icon*.svg' -o -iname '*icon*.png' \
       -o -iname '*logo*.svg' -o -iname '*logo*.png' \) \
    -not -path '*/.git/*' | head -n 1)

ICON="${ICON:-accessories-text-editor}"

# 6. Create Linux Mint menu entry
cat > "$HOME/.local/share/applications/my-zettelkasten.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=My Zettelkasten
Comment=Personal Zettelkasten note manager
Exec=$HOME/.local/bin/my-zettelkasten
TryExec=$HOME/.local/bin/my-zettelkasten
Icon=$ICON
Terminal=false
Categories=Office;Utility;
StartupNotify=true
EOF

chmod 644 "$HOME/.local/share/applications/my-zettelkasten.desktop"

echo
echo "My Zettelkasten installed successfully."
echo "Installed version:"
"$APP_DIR/.venv/bin/python" -m zettelkasten --version
echo
echo "Launch from the Linux Mint menu or run:"
echo "  $HOME/.local/bin/my-zettelkasten"
