# 🚀 Gemini Code - Assistente de Desenvolvimento Total

🤖 **Sistema completo de desenvolvimento com IA que funciona 100% em linguagem natural portuguesa**

Gemini Code é o primeiro assistente de desenvolvimento que combina **Inteligência Artificial Avançada**, **Monitoramento 24/7**, **Segurança Proativa**, **Analytics de Negócio** e **Colaboração em Tempo Real** em uma única plataforma conversacional.

## ✨ Características Revolucionárias

### 🧠 **Inteligência Artificial de Última Geração**
- **NLP Aprimorado**: Compreensão de linguagem natural em português com 95%+ de precisão
- **Pensamento Adaptativo**: 0-24,576 tokens de thinking do Gemini 2.5 Flash
- **Aprendizado Contínuo**: Sistema se adapta ao seu estilo de desenvolvimento

### 🔄 **Monitoramento e Automação 24/7**
- **Vigilância Contínua**: Monitora arquivos, detecta erros, otimiza performance
- **Auto-correção**: Corrige problemas automaticamente quando possível
- **Alertas Inteligentes**: Notifica sobre problemas críticos

### 🔐 **Segurança de Nível Empresarial**
- **Scanner Completo**: Detecta vulnerabilidades OWASP Top 10
- **Auto-fix**: Corrige problemas de segurança automaticamente
- **Classificação CWE**: Categoriza vulnerabilidades por padrões internacionais

### 📊 **Business Intelligence Integrado**
- **Métricas de Negócio**: "Quantas vendas tivemos esta semana?"
- **Dashboards Interativos**: Geração automática de relatórios visuais
- **KPIs em Tempo Real**: Acompanhamento de indicadores críticos
- **Análise Preditiva**: Previsões usando machine learning

### 👥 **Colaboração Avançada**
- **Gerenciamento de Equipe**: Convites, roles, permissões
- **Compartilhamento de Projetos**: Colaboração segura entre membros
- **Sincronização em Tempo Real**: Edição colaborativa como Google Docs
- **Code Review Integrado**: Processo de revisão automatizado

## 🎯 Instalação e Configuração

### Pré-requisitos
```bash
# Python 3.8+ obrigatório
python3 --version

# Clone o repositório
git clone https://github.com/seu-usuario/gemini-code.git
cd gemini-code
```

### Instalação de Dependências
```bash
# Instale as dependências básicas
pip install -r requirements.txt

# OU instale em ambiente virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
```

### Configuração da API
```bash
# Configure sua chave API do Gemini
export GEMINI_API_KEY="sua_chave_aqui"

# OU crie arquivo .env
echo "GEMINI_API_KEY=sua_chave_aqui" > .env

# Obtenha sua chave em: https://makersuite.google.com/app/apikey
```

### Primeiro Uso
```bash
# Teste básico do sistema
python3 test_basic.py

# Inicie o sistema completo
python3 main.py

# OU modo não-interativo
python3 main.py --command "analise o projeto"
```

## 💬 Exemplos de Comandos Naturais

### Desenvolvimento
- "Cria um novo agente chamado Mercenário"
- "Adiciona sistema de notificações"
- "Faz um botão de exportar Excel"

### Correções
- "Por que tá dando erro?"
- "O sistema está lento"
- "Corrige todos os problemas"

### Manutenção
- "Faz backup de tudo"
- "Atualiza as dependências"
- "Organiza melhor o projeto"

### Git
- "Salva tudo" → commit automático
- "Envia pro GitHub" → push
- "Volta como estava" → revert

## 🛠️ Configuração

O arquivo `.gemini_code/config.yaml` é criado automaticamente:

```yaml
model:
  name: "gemini-2.5-flash-preview-05-20"
  thinking_budget_default: 8192
  
user:
  mode: "non-programmer"
  language: "portuguese"
  
project:
  auto_fix: true
  preserve_style: true
```

## 📊 Estrutura do Projeto

```
gemini_code/
├── core/           # Cliente API e gerenciamento
├── analysis/       # Análise e correção de código
├── development/    # Construção de features
├── execution/      # Execução e debug
├── integration/    # Git, deploy, serviços
└── interface/      # Interface conversacional
```

## 🔑 Configurar API Key

```bash
# Via variável de ambiente
export GEMINI_API_KEY="sua-chave-aqui"

# Ou no arquivo .env
echo "GEMINI_API_KEY=sua-chave-aqui" > .env
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia nosso guia de contribuição antes de enviar PRs.

## 📄 Licença

MIT License - veja LICENSE para detalhes.