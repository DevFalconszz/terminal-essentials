#!/bin/bash

# ==============================================================================
# Bluetooth Manager (Aquila Soft Azure Night)
# ==============================================================================

# Silencia o terminal e limpa a tela para imersão total
clear
# Define o diretório atual e o ambiente virtual
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$DIR/venv"

if [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON_CMD="$VENV_DIR/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD=""
fi

if [ -n "$PYTHON_CMD" ] && [ -f "$DIR/aquila_bluetooth_tui.py" ]; then
    # Executa o TUI e limpa a tela ao sair para não deixar rastros no shell
    $PYTHON_CMD "$DIR/aquila_bluetooth_tui.py"
    clear
    exit 0
fi
# Fallback silencioso para TUI original com visual harmonizado
clear

# Configura as cores do whiptail para combinar com a paleta Azure Night
export NEWT_COLORS='
  window=,black
  border=brightblue,black
  title=brightblue,black
  textbox=lightgray,black
  button=white,black
  actbutton=black,brightblue
  listbox=lightgray,black
  actlistbox=black,brightblue
  checkbox=lightgray,black
  actcheckbox=black,brightblue
'

# Cores e Ícones
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
CHECK_MARK="✔"
CROSS_MARK="✖"

# Função para mostrar o status do Bluetooth
show_status() {
    local status=$(bluetoothctl show | grep "Powered:" | awk '{print $2}')
    local name=$(bluetoothctl show | grep "Name:" | cut -d ' ' -f 2-)
    
    if [ "$status" == "yes" ]; then
        whiptail --title "Status do Bluetooth" --msgbox "Bluetooth: ATIVADO\nDispositivo: $name\n\nO serviço está rodando normalmente." 10 50
    else
        whiptail --title "Status do Bluetooth" --msgbox "Bluetooth: DESATIVADO\n\nUse a opção 'Ligar Bluetooth' no menu principal." 10 50
    fi
}

# Função para ligar/desligar Bluetooth
toggle_power() {
    local status=$(bluetoothctl show | grep "Powered:" | awk '{print $2}')
    if [ "$status" == "yes" ]; then
        bluetoothctl power off > /dev/null
        whiptail --title "Power" --msgbox "Bluetooth desligado com sucesso." 8 40
    else
        bluetoothctl power on > /dev/null
        whiptail --title "Power" --msgbox "Bluetooth ligado com sucesso." 8 40
    fi
}

# Função para listar e conectar a um dispositivo pareado
connect_device() {
    # Garante que o power está ON
    bluetoothctl power on > /dev/null
    
    # Obtém lista de dispositivos pareados
    local devices=$(bluetoothctl devices | awk '{print $2, $3}')
    
    if [ -z "$devices" ]; then
        whiptail --title "Erro" --msgbox "Nenhum dispositivo pareado encontrado." 8 40
        return
    fi

    # Formata para o whiptail (ID "Name")
    local menu_items=()
    while read -r id name; do
        # Verifica se está conectado para adicionar um marcador
        if bluetoothctl info "$id" | grep -q "Connected: yes"; then
            menu_items+=("$id" "[CONECTADO] $name")
        else
            menu_items+=("$id" "$name")
        fi
    done <<< "$(bluetoothctl devices | awk '{$1=""; print $0}' | sed 's/^ //')"
    
    # Re-obtendo com IDs corretos
    local raw_list=$(bluetoothctl devices)
    local menu_options=()
    while read -r line; do
        mac=$(echo "$line" | awk '{print $2}')
        name=$(echo "$line" | cut -d ' ' -f 3-)
        if bluetoothctl info "$mac" | grep -q "Connected: yes"; then
            menu_options+=("$mac" "⭐ $name (Conectado)")
        else
            menu_options+=("$mac" "  $name")
        fi
    done <<< "$raw_list"

    choice=$(whiptail --title "Conectar Dispositivo" --menu "Escolha um dispositivo para conectar:" 15 60 7 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    
    if [ -n "$choice" ]; then
        {
            echo 10; bluetoothctl connect "$choice" > /tmp/bt_output 2>&1
            echo 100
        } | whiptail --title "Conectando" --gauge "Tentando estabelecer conexão com $choice..." 8 50 0
        
        if grep -q "Connection successful" /tmp/bt_output || bluetoothctl info "$choice" | grep -q "Connected: yes"; then
            whiptail --title "Sucesso" --msgbox "Conectado com sucesso!" 8 40
        else
            whiptail --title "Erro" --msgbox "Falha ao conectar.\n$(cat /tmp/bt_output)" 10 50
        fi
    fi
}

# Função para desconectar dispositivo
disconnect_device() {
    local raw_list=$(bluetoothctl devices)
    local menu_options=()
    local count=0
    
    while read -r line; do
        mac=$(echo "$line" | awk '{print $2}')
        name=$(echo "$line" | cut -d ' ' -f 3-)
        if bluetoothctl info "$mac" | grep -q "Connected: yes"; then
            menu_options+=("$mac" "🔴 Desconectar: $name")
            ((count++))
        fi
    done <<< "$raw_list"

    if [ $count -eq 0 ]; then
        whiptail --title "Aviso" --msgbox "Não há dispositivos conectados no momento." 8 40
        return
    fi

    choice=$(whiptail --title "Desconectar" --menu "Escolha qual dispositivo desconectar:" 15 60 7 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    
    if [ -n "$choice" ]; then
        bluetoothctl disconnect "$choice" > /dev/null
        whiptail --title "Sucesso" --msgbox "Dispositivo desconectado." 8 40
    fi
}

# Menu Principal
while true; do
    CHOICE=$(whiptail --title "Gerenciador Bluetooth" --menu "Selecione uma opção:" 15 50 6 \
        "1" "📊 Ver Status" \
        "2" "⚡ Ligar/Desligar Bluetooth" \
        "3" "🔗 Conectar Dispositivo" \
        "4" "✂️ Desconectar Dispositivo" \
        "5" "🔍 Scan (Parear novo)" \
        "6" "🚪 Sair" 3>&1 1>&2 2>&3)

    case $CHOICE in
        1) show_status ;;
        2) toggle_power ;;
        3) connect_device ;;
        4) disconnect_device ;;
        5) 
            whiptail --title "Scan" --msgbox "Iniciando scan de 10 segundos. Certifique-se que o dispositivo está em modo de pareamento." 8 50
            (echo "scan on"; sleep 10; echo "scan off") | bluetoothctl > /dev/null
            whiptail --title "Scan" --msgbox "Scan finalizado. Agora você pode tentar conectar via menu 'Conectar'." 8 50
            ;;
        6) exit 0 ;;
        *) break ;;
    esac
done
