#!/bin/bash

# ==============================================================================
# WiFi Manager (Aquila Soft Azure Night)
# ==============================================================================

# Silencia o terminal e limpa a tela para imersão total
clear
# Define o diretório atual
# Define o diretório atual
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$DIR/venv"

if [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON_CMD="$VENV_DIR/bin/python"
elif command -v python3 > /dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD=""
fi

if [ -n "$PYTHON_CMD" ] && [ -f "$DIR/aquila_wifi_tui.py" ]; then
    $PYTHON_CMD "$DIR/aquila_wifi_tui.py"
    clear
    exit 0
fi

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

# Função para mostrar o status do WiFi
show_status() {
    local status=$(nmcli radio wifi)
    local ssid=$(nmcli -t -f ACTIVE,SSID dev wifi | grep "^yes" | cut -d: -f2)
    local signal=$(nmcli -t -f ACTIVE,SIGNAL dev wifi | grep "^yes" | cut -d: -f2)

    if [ "$status" == "enabled" ]; then
        if [ -n "$ssid" ]; then
            whiptail --title "Status do WiFi" --msgbox "WiFi: ATIVADO\nConectado a: $ssid\nSinal: ${signal}%\n\nRede estável e operacional." 10 50
        else
            whiptail --title "Status do WiFi" --msgbox "WiFi: ATIVADO\nNão conectado a nenhuma rede.\n\nUse 'Conectar WiFi' para listar redes disponíveis." 10 50
        fi
    else
        whiptail --title "Status do WiFi" --msgbox "WiFi: DESATIVADO\n\nUse a opção 'Ligar WiFi' no menu principal." 10 50
    fi
}

# Função para ligar/desligar WiFi
toggle_wifi() {
    local status=$(nmcli radio wifi)
    if [ "$status" == "enabled" ]; then
        nmcli radio wifi off
        whiptail --title "Power" --msgbox "WiFi desligado com sucesso." 8 40
    else
        nmcli radio wifi on
        whiptail --title "Power" --msgbox "WiFi ligado com sucesso." 8 40
    fi
}

# Função para escanear e conectar a uma rede WiFi
connect_wifi() {
    # Garante que o WiFi está ON
    nmcli radio wifi on

    # Obtém lista de redes disponíveis
    local networks=$(nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list --rescan yes 2>/dev/null | awk -F: '!seen[$1]++ && $1 && $1 != "--" {print $1, $2"%", $3}')

    if [ -z "$networks" ]; then
        whiptail --title "Erro" --msgbox "Nenhuma rede WiFi encontrada." 8 40
        return
    fi

    # Formata para o whiptail (SSID "Sinal Segurança")
    local menu_options=()
    while IFS= read -r line; do
        ssid=$(echo "$line" | awk '{print $1}')
        signal=$(echo "$line" | awk '{print $2}')
        sec=$(echo "$line" | cut -d' ' -f3-)
        if [ -n "$sec" ]; then
            menu_options+=("$ssid" "$signal 🔒 $sec")
        else
            menu_options+=("$ssid" "$signal 🔓 Aberta")
        fi
    done <<< "$networks"

    choice=$(whiptail --title "Conectar WiFi" --menu "Escolha uma rede para conectar:" 15 60 7 "${menu_options[@]}" 3>&1 1>&2 2>&3)

    if [ -n "$choice" ]; then
        local security=$(nmcli -t -f SSID,SECURITY dev wifi | grep "^$choice:" | head -1 | cut -d: -f2)

        if [ -n "$security" ] && [ "$security" != "--" ]; then
            password=$(whiptail --title "Senha" --passwordbox "Digite a senha para $choice:" 8 50 3>&1 1>&2 2>&3)
            if [ -z "$password" ]; then
                return
            fi
            {
                echo 10
                nmcli dev wifi connect "$choice" password "$password" > /tmp/wifi_output 2>&1
                echo 100
            } | whiptail --title "Conectando" --gauge "Tentando estabelecer conexão com $choice..." 8 50 0
        else
            {
                echo 10
                nmcli dev wifi connect "$choice" > /tmp/wifi_output 2>&1
                echo 100
            } | whiptail --title "Conectando" --gauge "Tentando estabelecer conexão com $choice..." 8 50 0
        fi

        if grep -q "successfully" /tmp/wifi_output; then
            whiptail --title "Sucesso" --msgbox "Conectado com sucesso!" 8 40
        else
            whiptail --title "Erro" --msgbox "Falha ao conectar.\n$(cat /tmp/wifi_output)" 10 50
        fi
    fi
}

# Função para desconectar WiFi
disconnect_wifi() {
    local connected=$(nmcli -t -f ACTIVE,SSID,DEVICE dev wifi | grep "^yes" | head -1)

    if [ -z "$connected" ]; then
        whiptail --title "Aviso" --msgbox "Não há conexão WiFi ativa no momento." 8 40
        return
    fi

    local ssid=$(echo "$connected" | cut -d: -f2)
    local device=$(echo "$connected" | cut -d: -f3)

    choice=$(whiptail --title "Desconectar" --menu "Escolha qual rede desconectar:" 15 60 7 "$device" "🔴 Desconectar: $ssid" 3>&1 1>&2 2>&3)

    if [ -n "$choice" ]; then
        nmcli dev disconnect "$choice" > /dev/null
        whiptail --title "Sucesso" --msgbox "Rede desconectada." 8 40
    fi
}

# Menu Principal
while true; do
    CHOICE=$(whiptail --title "Gerenciador WiFi" --menu "Selecione uma opção:" 15 50 6 \
        "1" "📊 Ver Status" \
        "2" "⚡ Ligar/Desligar WiFi" \
        "3" "🔗 Conectar WiFi" \
        "4" "✂️ Desconectar WiFi" \
        "5" "🔍 Escanear Redes" \
        "6" "🚪 Sair" 3>&1 1>&2 2>&3)

    case $CHOICE in
        1) show_status ;;
        2) toggle_wifi ;;
        3) connect_wifi ;;
        4) disconnect_wifi ;;
        5)
            whiptail --title "Scan" --msgbox "Iniciando scan de 10 segundos. Certifique-se que o roteador está visível." 8 50
            nmcli dev wifi list --rescan yes > /dev/null 2>&1
            whiptail --title "Scan" --msgbox "Scan finalizado. Agora você pode tentar conectar via menu 'Conectar WiFi'." 8 50
            ;;
        6) exit 0 ;;
        *) break ;;
    esac
done
