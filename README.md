# 📁 File Organizer Pro

<p align="center">
  <img src="assets/icon.png" alt="File Organizer Logo" width="110" height="110" />
</p>

<p align="center">
  <strong>Organizador inteligente de arquivos e sentinela automatizado para Windows.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Platform" />
  <img src="https://img.shields.io/badge/UI-ttkbootstrap-20c997?style=flat-square" alt="ttkbootstrap" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License MIT" />
  <img src="https://img.shields.io/badge/Build-.exe%20Standalone-orange?style=flat-square" alt="Executable" />
</p>

---

## 💡 Sobre o Projeto

O **File Organizer Pro** é um aplicativo de automação de produtividade projetado para eliminar a desorganização em pastas como *Downloads*, *Área de Trabalho* ou pastas de projetos. 

Diferente de scripts convencionais que apenas separam por extensão, o File Organizer Pro conta com:
- **Interface Gráfica Fluida (Smooth UI)** sem travamentos (processamento assíncrono multithread).
- **Modo Sentinela (Zero-Click Automation)**: vigia pastas em segundo plano e move novos downloads assim que terminam.
- **Regras Avançadas**: suporte a filtros por extensão (`.pdf`, `.png`) ou por **padrões de nome / wildcards** (`*fatura*`, `nota_fiscal_*`), com opção de **pastas de destino customizadas** para regras específicas.
- **Sistema de Desfazer (Undo)**: reverte qualquer movimentação com apenas 1 clique através do histórico transacional.
- **Anti-corrupção**: ignora arquivos temporários em download ativo (`.crdownload`, `.part`, `.tmp`).
- **Executável Portátil (`.exe`)**: pronto para rodar sem precisar de Python instalado.

---

## 📥 Download Direto (.exe)

Você pode baixar a versão compilada diretamente na aba de **[Releases](../../releases)**:

1. Acesse **[Releases](../../releases)**.
2. Baixe o arquivo **`FileOrganizer.exe`**.
3. Dê dois cliques para abrir. Não requer instalação nem permissões de administrador.

---

## ✨ Funcionalidades Principais

| Recurso | Descrição |
| :--- | :--- |
| ⚡ **Organização Rápida** | Selecione a pasta de origem e destino, escolha se deseja incluir subpastas e acompanhe o progresso suave em tempo real. |
| 🛡️ **Modo Sentinela** | Deixe o app monitorando sua pasta de Downloads. Cada arquivo baixado é enviado imediatamente para o destino configurado. |
| 🎯 **Gerenciador de Regras** | Crie categorias personalizadas, defina padrões específicos (ex: arquivos com "contrato" vão para uma pasta de Contratos) e configure caminhos dedicados. |
| ⏪ **Histórico & Desfazer** | Moveu algo por engano? Clique em *Desfazer* para devolver cada arquivo exatamente para onde estava. |
| 🌓 **Temas Modernos** | Alternância com um clique entre tema Claro (*Cosmo*) e tema Escuro (*Darkly*). |
| 💻 **Linha de Comando (CLI)** | Suporte completo a automação via scripts, tarefas agendadas do Windows ou terminal. |

---

## 🚀 Como Executar pelo Código-Fonte

### Pré-requisitos
* **Python 3.9 ou superior** instalado.
* `git` instalado.

### Passo a passo
```bash
# 1. Clone o repositório
git clone https://github.com/SEU-USUARIO/file_organizer.git
cd file_organizer

# 2. Crie e ative um ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate   # No Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie o aplicativo com interface gráfica
python main.py
```

---

## 💻 Uso via Linha de Comando (CLI)

O File Organizer Pro também pode ser executado em servidores ou integrado a outros scripts:

```bash
# Organização direta com logs no terminal
python main.py --cli --source "C:\Users\SEU-USUARIO\Downloads" --destination "C:\Users\SEU-USUARIO\Arquivos"

# Simulação (Dry-run) sem mover arquivos
python main.py --source "C:\Downloads" --destination "C:\Arquivos" --dry-run

# Modo Sentinela contínuo no terminal
python main.py --sentinel --source "C:\Downloads" --destination "C:\Arquivos"

# Desfazer a última organização via terminal
python main.py --undo
```

### Argumentos Disponíveis
* `--source`: Pasta de origem.
* `--destination`: Pasta de destino padrão.
* `--rules`: Caminho para um arquivo `rules.json` customizado.
* `--recursive`: Inclui recursivamente todas as subpastas.
* `--dry-run`: Exibe o plano de ação sem tocar nos arquivos.
* `--sentinel`: Monitora a pasta de origem em loop até você pressionar `Ctrl+C`.
* `--undo`: Reverte o último lote de arquivos movidos.

---

## 🔨 Como Compilar o `.exe` Localmente

Para gerar seu próprio executável único:

```bash
# Instale o PyInstaller
pip install pyinstaller

# Execute o script automatizado de build
python build.py
```

Ou no Windows, dê dois cliques em **`build.bat`**. O executável será salvo em `dist/FileOrganizer.exe`.

---

## 🧪 Testes Automatizados

Para rodar a suíte de testes unitários com o `pytest`:

```bash
pip install pytest
pytest
```

---

## 🏛️ Arquitetura do Projeto

```text
file_organizer/
├── .github/
│   └── workflows/
│       └── build-release.yml   # CI/CD: Compila e lança o .exe em cada Release
├── assets/
│   ├── icon.ico                # Ícone do executável Windows
│   └── icon.png                # Imagem do logo
├── src/
│   ├── core/                   # Núcleo de regras e manipulação de arquivos
│   │   ├── engine.py           # Motor de movimentação e resolução de nomes
│   │   ├── history.py          # Histórico transacional e motor de Undo
│   │   ├── models.py           # Dataclasses tipadas (Rule, MovedFile, etc.)
│   │   ├── rules.py            # Gerenciador e avaliador de regras
│   │   └── watcher.py          # Modo Sentinela (vigia de pastas assíncrono)
│   └── ui/                     # Interface moderna ttkbootstrap
│       └── main_window.py      # Janela principal com abas e multithreading
├── tests/                      # Testes automatizados (pytest)
│   ├── test_engine.py
│   ├── test_rules.py
│   └── test_watcher.py
├── build.py                    # Script de compilação PyInstaller
├── build.bat                   # Atalho de compilação rápida no Windows
├── main.py                     # Ponto de entrada (GUI + CLI)
├── pyproject.toml              # Metadados e dependências PEP 517/621
├── requirements.txt            # Dependências de execução
└── README.md                   # Documentação completa
```

---

## 🤝 Como Contribuir

Contribuições são muito bem-vindas! Se você tiver uma ideia de melhoria ou encontrar um bug:

1. Faça um **Fork** do projeto.
2. Crie uma branch para sua funcionalidade (`git checkout -b feature/minha-melhoria`).
3. Commit suas alterações (`git commit -m 'feat: adiciona nova funcionalidade'`).
4. Envie para o branch (`git push origin feature/minha-melhoria`).
5. Abra um **Pull Request**.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais informações.
