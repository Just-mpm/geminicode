# 🚀 Como Usar o Gemini Code

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **API Key do Gemini** (obtenha em: https://makersuite.google.com/app/apikey)

## ⚡ Início Rápido

### Opção 1: Arquivo .bat (Windows) - RECOMENDADO
1. **Duplo-clique em `start_gemini_code.bat`**
2. Escolha a opção desejada no menu

### Opção 2: Início Direto
1. Configure sua API Key:
   ```bash
   setx GEMINI_API_KEY "sua-chave-aqui"
   ```
2. Duplo-clique em `gemini_code_quick.bat`

### Opção 3: Via Terminal
```bash
# Configure a API Key
export GEMINI_API_KEY="sua-chave-aqui"  # Linux/Mac
set GEMINI_API_KEY=sua-chave-aqui       # Windows

# Instale dependências (primeira vez)
pip install -r requirements.txt

# Inicie o REPL
python gemini_repl.py

# OU inicie a interface principal
python main.py
```

## 🎯 Opções de Inicialização

### 1. REPL Interativo (Recomendado)
- **Arquivo**: `gemini_repl.py`
- **Como usar**: Interface de linha de comando
- **Comandos**:
  - `/help` - Ajuda completa
  - `/cost` - Monitoramento de custos
  - `/doctor` - Diagnóstico do sistema
  - `/memory` - Status da memória
  - `/clear` - Limpar contexto
  - `/compact` - Compactar contexto
  - `Ctrl+D` - Sair

### 2. Interface Principal
- **Arquivo**: `main.py`
- **Como usar**: Interface programática
- **Uso**: Para integração com outros sistemas

### 3. Menu Completo
- **Arquivo**: `start_gemini_code.bat`
- **Como usar**: Menu interativo com todas as opções
- **Funcionalidades**:
  - Testes do sistema
  - Verificação de saúde
  - Configuração de API
  - Limpeza de cache

## 🔧 Comandos Disponíveis

### Comandos Slash (no REPL)
- `/help` - Mostra ajuda completa
- `/cost` - Relatório de custos de uso
- `/clear` - Limpa contexto da sessão
- `/compact [instruções]` - Compacta contexto
- `/doctor` - Diagnóstico completo do sistema
- `/memory` - Status da memória e contexto
- `/config [chave] [valor]` - Configurações

### Comandos Naturais (português)
- `"crie um arquivo teste.py com print('Hello')"`
- `"analise a estrutura do projeto"`
- `"mostre os arquivos Python"`
- `"explique como funciona o código"`
- `"otimize a performance"`
- `"corrija os erros"`

## 📂 Estrutura de Pastas

```
gemini_code/
├── start_gemini_code.bat    # Inicializador completo
├── gemini_code_quick.bat    # Início rápido
├── gemini_repl.py           # REPL interativo
├── main.py                  # Interface principal
├── requirements.txt         # Dependências
├── gemini_code/            # Código principal
│   ├── core/               # Componentes centrais
│   ├── cognition/          # Módulos de IA avançada
│   ├── tools/              # Ferramentas
│   ├── security/           # Segurança
│   └── ...
├── tests/                  # Todos os testes
├── docs/                   # Documentação
└── reports/               # Relatórios de testes
```

## 🔐 Configuração da API Key

### Windows (Permanente):
```cmd
setx GEMINI_API_KEY "sua-chave-aqui"
```

### Linux/Mac (Temporário):
```bash
export GEMINI_API_KEY="sua-chave-aqui"
```

### Linux/Mac (Permanente):
```bash
echo 'export GEMINI_API_KEY="sua-chave-aqui"' >> ~/.bashrc
source ~/.bashrc
```

## 🧪 Testando o Sistema

### Teste Rápido
```bash
python tests/test_system_ready.py
```

### Teste Completo
```bash
python tests/test_complete_system_integration.py
```

## 🆘 Solução de Problemas

### Erro: "API key not valid"
- Verifique se a API key está correta
- Obtenha uma nova em: https://makersuite.google.com/app/apikey

### Erro: "No module named 'google.generativeai'"
```bash
pip install -r requirements.txt
```

### Erro: "Permission denied"
```bash
# Execute como administrador (Windows)
# Ou com sudo (Linux/Mac)
```

### Sistema travando
1. Execute `/doctor` para diagnóstico
2. Use `/clear` para limpar contexto
3. Reinicie o sistema

## 🎯 Funcionalidades Principais

### 🧠 Cognição Avançada
- **Análise Arquitetural**: Entende estrutura de projetos
- **Detecção de Padrões**: Reconhece design patterns
- **Resolução de Problemas**: Corrige erros automaticamente
- **Aprendizado Contínuo**: Melhora com uso

### 🛠️ Ferramentas
- **11 ferramentas integradas**: bash, file operations, search
- **Execução segura**: Sistema de permissões
- **Context awareness**: Entende o projeto completo

### 💾 Memória Inteligente
- **Persistência**: Lembra conversas anteriores
- **Compactação**: Otimiza uso de contexto
- **Aprendizado**: Adapta-se às preferências

## 🏆 Diferenciais

### vs Claude Code
- ✅ 100% de paridade funcional
- 🚀 Módulos de cognição superiores
- 🧠 Aprendizado contínuo
- 🔧 Self-healing automático
- 📊 Business Intelligence integrado

## 📞 Suporte

Para problemas ou dúvidas:
1. Execute `/doctor` para diagnóstico
2. Consulte a documentação em `docs/`
3. Verifique os logs em `.gemini_code/logs/`

---

🎉 **Aproveite o Gemini Code - Seu assistente IA superior!** 🚀