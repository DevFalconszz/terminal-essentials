<div align="center">

# ⚡ Aquila Bluetooth Manager

Uma interface gráfica de terminal (TUI) premium, minimalista e completamente em modo texto para gerenciar seus dispositivos Bluetooth no Linux. Otimizada para terminais modernos (como o Kitty).

</div>

---

## 🚀 Sobre o Projeto

O **Aquila Bluetooth Manager** é a evolução de um script bash utilitário transformado em uma **Terminal User Interface (TUI)** de nível profissional. Feito em Python utilizando o ecossistema [Textual](https://textual.textualize.io/), ele oferece um design em duas colunas, reconhecimento de tipos de dispositivos (Fones, Teclados, Celulares) exibindo emojis híbridos, bordas arredondadas perfeitamente alinhadas, e uma performance ultrarrápida.

Seu "backend" é operado diretamente pela ferramenta nativa `bluetoothctl` do Linux, garantindo altíssima compatibilidade.

### ✨ Destaques
- **Estética Azure Night:** Um esquema de cores curado e moderno combinando azuis, roxos e vermelhos discretos sobre um fundo escuro glacial.
- **Detecção Inteligente:** Faz parse do `bluetoothctl info` em background e sabe se seu dispositivo é um 🎧 fone de ouvido, ⌨️ teclado ou 📱 celular, ajustando o ícone dinamicamente!
- **Zero Lags:** Todas as chamadas para o sistema operacional ocorrem fora da thread principal utilizando asyncio, o que significa que o cursor e os efeitos CSS rodam fluidos na sua tela.
- **Fallback Automático:** Caso falte a biblioteca Python, o shell script recai inteligentemente para um menu em `whiptail` customizado com o mesmo esquema de cores.

---

## 🛠️ Pré-requisitos

Certifique-se de que o sistema possua:
- `bash` e `python3` (com suporte a virtual environment / `python3-venv`)
- O serviço `bluetoothd` (BlueZ) instalado e rodando.
- Utilidade `bluetoothctl` (geralmente instalada por padrão com o BlueZ no Ubuntu/Debian/Arch).
- Uma fonte Nerd Font instalada (opcional, porém fortemente recomendada para exibição ideal de ícones).

---

## 📦 Instalação

Disponibilizamos um arquivo `setup.sh` pronto que cuida de toda a configuração do seu ambiente sem sujar o sistema: ele cria um virtual environment isolado, instala a dependência e gera um atalho diretamente no seu PATH (`~/.local/bin/aquila-bt`).

Para instalar:

```bash
git clone https://github.com/DevFalconszz/terminal-essentials.git
cd terminal-essentials
./setup.sh
```

## 🎮 Como usar

Depois de instalado via `setup.sh`, basta executar em qualquer janela do terminal:

```bash
aquila-bt
```

### Comandos da Interface:
- **POWER:** Alterna a alimentação do seu adaptador Bluetooth primário.
- **SCAN:** Dispara uma varredura de 5 segundos em segundo plano. Pressione-o se o seu fone ou dispositivo novo ainda não estiver aparecendo na lista da direita.
- **Botões Conectar/Desconectar:** Em cada cartão de dispositivo, permitem fazer o pareamento instantaneamente.
- **Sair (ou Q):** Encerra a interface limpa e volta para a sua linha de comando padrão.

---

## 🤝 Contribuindo

Pull requests são muito bem-vindos. Para mudanças maiores, por favor abra uma *issue* primeiro para discutirmos o que você gostaria de mudar.

Feito para entusiastas de terminal e ricing de Linux. 🦅
