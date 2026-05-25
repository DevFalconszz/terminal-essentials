#!/bin/bash
set -e

BLUE='\033[0;34m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
cat << "EOF"
    ___________       __             _      __
   / ____/ ___/____ _/ /_____  _____(_)____/ /__  _____
  / /    \__ \/ __ `/ __/ __ \/ ___/ / ___/ / _ \/ ___/
 / /___ ___/ / /_/ / /_/ /_/ / /  / (__  ) /  __/ /
 \____//____/\__,_/\__/\____/_/  /_/____/_/\___/_/

   ______      __                __     __          __
  / ____/___ _/ /___  _______   / /    / /___ _____/ /__
 / __/ / __ `/ __/ / / / ___/  / / /| / / __ `/ __  / _ \
/ /___/ /_/ / /_/ /_/ (__  )  / / ___/ / /_/ / /_/ /  __/
/_____/\__,_/\__/\__,_/____/  /_/_/  /_/\__,_/\__,_/\___/

EOF
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/terminal-essentials"
BIN_DIR="$HOME/.local/bin"

echo -e "${BLUE}⚡ Instalando Terminal-Essentials...${NC}\n"

echo -e "📦 [1/6] Criando diretório de instalação em ${CYAN}$INSTALL_DIR${NC}..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

echo -e "📄 [2/6] Copiando todos os módulos..."
cp "$SCRIPT_DIR"/aquila_*.py "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR"/bluetooth_manager.sh "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/wifi_manager.sh "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/widgets" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/assets" "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null || true

echo -e "🐍 [3/6] Criando ambiente virtual Python..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

echo -e "🔗 [4/6] Criando link simbólico ${CYAN}terminal-essentials${NC}..."
cat > "$INSTALL_DIR/terminal-essentials" << 'SCRIPT'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/.venv/bin/python3" "$DIR/aquila_desktop_tui.py" "$@"
SCRIPT
chmod +x "$INSTALL_DIR/terminal-essentials"
ln -sf "$INSTALL_DIR/terminal-essentials" "$BIN_DIR/terminal-essentials"

echo -e "🔗 [5/6] Criando link simbólico ${CYAN}aquila-bt${NC} (compatibilidade)..."
ln -sf "$INSTALL_DIR/bluetooth_manager.sh" "$BIN_DIR/aquila-bt"

echo -e "🧹 [6/6] Limpando cache..."
find "$INSTALL_DIR" -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo -e "\n${GREEN}✅ Terminal-Essentials instalado com sucesso!${NC}"
echo -e "----------------------------------------------------------------"
echo -e "Certifique-se de que ${CYAN}$BIN_DIR${NC} está no seu PATH."
echo -e "Se não estiver, adicione ao ~/.bashrc:\n"
echo -e "    ${YELLOW}export PATH=\"\$PATH:$BIN_DIR\"${NC}\n"
echo -e "Comandos disponíveis:\n"
echo -e "    ${GREEN}terminal-essentials${NC}  →  Desktop completo"
echo -e "    ${GREEN}aquila-bt${NC}            →  Bluetooth Manager (whiptail)\n"
