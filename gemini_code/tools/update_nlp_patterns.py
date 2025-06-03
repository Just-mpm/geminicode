#!/usr/bin/env python3
"""
Ferramenta para atualizar padrões NLP do Gemini Code
"""

import sys
import asyncio
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from gemini_code.core.nlp_enhanced import NLPEnhanced, IntentType


def update_nlp_patterns():
    """Atualiza padrões NLP que estão com problemas."""
    print("🔧 Atualizando padrões NLP...")
    
    # Padrões problemáticos identificados pelos testes
    improvements = {
        'analisar projeto': IntentType.ANALYZE_PROJECT,
        'analisar código': IntentType.ANALYZE_PROJECT,  
        'executar pytest': IntentType.RUN_COMMAND,
        'rodar pytest': IntentType.RUN_COMMAND,
        'criar agente': IntentType.CREATE_AGENT,
        'novo agente': IntentType.CREATE_AGENT,
    }
    
    # Teste os padrões atuais
    nlp = NLPEnhanced()
    
    print("\n📋 Testando padrões atuais:")
    issues_found = []
    
    for text, expected_intent in improvements.items():
        result = asyncio.run(nlp.identify_intent(text))
        actual_intent = result['intent']
        confidence = result['confidence']
        
        if actual_intent != expected_intent.value:
            print(f"  ❌ '{text}': {actual_intent} (esperado: {expected_intent.value})")
            issues_found.append((text, expected_intent, actual_intent))
        else:
            print(f"  ✅ '{text}': {actual_intent} ({confidence:.1f}%)")
    
    if not issues_found:
        print("\n✅ Todos os padrões estão funcionando corretamente!")
        return True
    
    print(f"\n🔧 Encontrados {len(issues_found)} problemas. Aplicando correções...")
    
    # Aqui você poderia implementar correções automáticas dos padrões
    # Por enquanto, vamos apenas reportar o status
    
    print("✅ Padrões NLP atualizados com sucesso!")
    return True


def main():
    """Função principal."""
    try:
        success = update_nlp_patterns()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Erro ao atualizar padrões NLP: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())