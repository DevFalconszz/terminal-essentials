#!/bin/bash

# Encerra o script em caso de erro
set -e

# Cores
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
cat << "EOF"
    ___               _ __        ____  __           __              __  __
   /   | ____ ___  __(_) /___ _  / __ )/ /_  _____  / /_____  ____  / /_/ /_ 
  / /| |/ __ `/ / / / / / __ `/ / __  / / / / / _ \/ __/ __ \/ __ \/ __/ __ \
 / ___ / /_/ / /_/ / / / /_/ / / /_/ / / /_/ /  __/ /_/ /_/ / /_/ / /_/ / / /
/_/  |_\__, /\__,_/_/_/\__,_/ /_____/_/\__,_/\___/\__/\____/\____/\__/_/ /_/ 
         /_/                                                                 
EOF
echo -e "${NC}"

echo -e "${BLUE}Iniciando a instalação do Aquila Bluetooth Manager...${NC}\n"

INSTALL_DIR="$HOME/.local/share/aquila-bluetooth"
BIN_DIR="$HOME/.local/bin"

echo -e "📦 [1/4] Criando diretório de instalação em ${CYAN}$INSTALL_DIR${NC}..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

echo -e "📄 [2/4] Copiando scripts..."
cp bluetooth_manager.sh "$INSTALL_DIR/"
cp aquila_bluetooth_tui.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/bluetooth_manager.sh"

echo -e "🐍 [3/4] Criando ambiente virtual (venv) e instalando a biblioteca textual..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet textual

echo -e "🔗 [4/4] Criando link simbólico em ${CYAN}$BIN_DIR/aquila-bt${NC}..."
ln -sf "$INSTALL_DIR/bluetooth_manager.sh" "$BIN_DIR/aquila-bt"

echo -e "\n${GREEN}✅ Instalação concluída com sucesso!${NC}"
echo -e "----------------------------------------------------------------"
echo -e "Para usar o gerenciador, certifique-se de que ${CYAN}$BIN_DIR${NC} está no seu PATH,"
echo -e "e digite o comando abaixo de qualquer lugar no terminal:\n"
echo -e "    ${GREEN}aquila-bt${NC}\n"
