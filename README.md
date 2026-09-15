# Freedom Bot - `obatatoide`

Bot automatizado em Python que publica piadas aleatórias no [Freedom](https://freedom-0yku.onrender.com/).

## Características

- **Usuário**: `obatatoide`
- **Fonte**: [Tempo de Secura](https://tempo-de-secura.blogspot.com/) (anos 2005 a 2010).
- **Volume coletado**: Mais de **1.240 piadas** raspadas e filtradas.
- **Intervalo**: Posta a cada **2 minutos** (120 segundos).
- **Sem repetição**: Mantém o histórico de hashes (`posted_history.json`) das piadas já publicadas para nunca repetir uma mensagem.
- **Cache local**: Salva o acervo em `jokes_cache.json` para inicialização imediata.

## Estrutura da pasta `.bot`

- [bot.py](file:///d:/freedom/.bot/bot.py): Script principal do bot.
- [requirements.txt](file:///d:/freedom/.bot/requirements.txt): Dependências (`requests`, `beautifulsoup4`).
- [start.bat](file:///d:/freedom/.bot/start.bat): Atalho executável para iniciar o bot com 1 clique no Windows.
- `jokes_cache.json`: Cache das piadas coletadas.
- `posted_history.json`: Histórico das piadas que já foram postadas.

## Como Executar

### Opção 1: Via start.bat
Dê um duplo clique no arquivo `start.bat` ou rode no terminal:
```cmd
.bot\start.bat
```

### Opção 2: Linha de comando direta
```bash
python .bot/bot.py
```
*(ou apontando para o Python instalado)*
```cmd
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" .bot\bot.py
```
