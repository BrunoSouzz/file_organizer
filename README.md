# File Organizer

Aplicativo para organizar arquivos por extensão. Ele pode ser usado por uma tela
gráfica ou pelo terminal e não sobrescreve arquivos existentes.

## Usando a tela

Com Python 3.9 ou superior instalado, execute:

```bash
python -m pip install -r requirements.txt
python main.py
```

Escolha a pasta **De** (origem) e a pasta **Para** (destino), depois clique em
**Organizar arquivos**. As configurações avançadas ficam escondidas em
**Opções**, para deixar o uso mais rápido. Nessa seção é possível incluir
subpastas, simular a operação e alterar regras:

```text
Imagens=.jpg,.png
Documentos=.pdf,.docx,.txt
```

Também é possível incluir subpastas ou executar uma simulação sem mover nada.

## Usando o terminal

```bash
python main.py --cli --source "C:\Users\Bruno\Downloads" --destination "C:\Users\Bruno\Arquivos"
```

Opções disponíveis:

* `--rules regras.json`: usa categorias e extensões definidas em um JSON.
* `--recursive`: procura arquivos dentro das subpastas da origem.
* `--dry-run`: exibe as movimentações sem alterar arquivos.

Exemplo de `regras.json`:

```json
{
  "Imagens": [".jpg", ".png", ".svg"],
  "Trabalho": [".pdf", ".docx", ".xlsx"]
}
```

## Como a lógica funciona

1. O programa valida a origem e o destino. O destino não pode ser a própria
   origem nem uma subpasta dela, evitando que o programa processe seus próprios
   resultados.
2. As regras são convertidas em um índice de extensão para categoria. A
   comparação ignora maiúsculas e minúsculas (`.JPG` e `.jpg` são equivalentes).
3. O programa percorre apenas arquivos (ou subpastas, quando `--recursive` é
   usado). Extensões não cadastradas são ignoradas.
4. Para cada arquivo reconhecido, cria `destino/Categoria` quando necessário e
   move o arquivo para lá.
5. Se já existir um arquivo com o mesmo nome, o programa escolhe um nome seguro,
   como `relatorio (1).pdf`, em vez de substituir o arquivo original.
6. Ao final, o terminal informa quantos arquivos foram movidos, ignorados e
   quais falharam. A tela apresenta o resumo da operação.

O núcleo da organização está na função `organize`, separado das interfaces.
Isso permite testar ou reutilizar a lógica sem abrir a tela.

## Gerando um executável no Windows

Instale o PyInstaller e gere um executável de arquivo único:

```bash
python -m pip install pyinstaller
pyinstaller --onefile --windowed --name FileOrganizer main.py
```

O arquivo `dist\FileOrganizer.exe` será criado. Ao abri-lo, a tela gráfica será
exibida. Para usar o modo terminal no executável, abra o Prompt de Comando na
pasta do arquivo e execute:

```text
FileOrganizer.exe --cli --source "C:\origem" --destination "C:\destino"
```

Para enxergar as mensagens do terminal ao gerar o executável, use `--console`
no lugar de `--windowed`.

## Requisitos

* Python 3.9 ou superior (para executar o código-fonte).
* `tkinter`, incluído na instalação padrão do Python para Windows.
* `ttkbootstrap`, instalado com `python -m pip install -r requirements.txt`,
  fornece o tema visual moderno. Se ele não estiver instalado, o programa usa
  automaticamente os componentes nativos do Tkinter.

## Licença

MIT. Consulte [LICENSE](LICENSE).
