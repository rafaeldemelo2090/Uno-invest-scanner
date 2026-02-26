"""
Alertas Telegram - UNO INVEST
==============================
Sistema de notificações via Telegram
"""

import os
import requests
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def enviar_alerta_telegram(mensagem: str, bot_token: str = None, chat_id: str = None) -> bool:
    """
    Envia mensagem via Telegram
    
    Args:
        mensagem: Texto a enviar
        bot_token: 8687997771:AAFDgl8SRdyzWt7w8p3-IEq-4GlZKbrf_eg
        chat_id: 47849458
    
    Returns:
        True se enviou com sucesso
    """
    
    # Pegar credenciais
    token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat = chat_id or os.getenv('TELEGRAM_CHAT_ID')
    
    # Validar
    if not token or not chat:
        logger.warning("Telegram não configurado (TOKEN ou CHAT_ID ausente)")
        return False
    
    # Montar URL
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Dados
    payload = {
        'chat_id': chat,
        'text': mensagem,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Alerta Telegram enviado")
            return True
        else:
            logger.error(f"❌ Telegram erro: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao enviar Telegram: {e}")
        return False


def alerta_oportunidade(oportunidade: dict) -> bool:
    """Alerta quando encontrar oportunidade"""
    
    ativo = oportunidade.get('ativo', '')
    estrategia = oportunidade.get('estrategia', '').replace('_', ' ')
    score = oportunidade.get('score', 0)
    
    # Montar mensagem
    mensagem = f"""🔥 <b>OPORTUNIDADE ENCONTRADA!</b>

💜 <b>UNO INVEST</b> - RCO Scanner

📈 <b>{ativo}</b> - {estrategia}
⭐ Score: <b>{score}/100</b>
"""
    
    # Adicionar detalhes conforme tipo
    if 'TRAVA' in oportunidade.get('estrategia', ''):
        mensagem += f"""
📤 <b>VENDE:</b> {oportunidade['quantidade_1']}x {oportunidade['codigo_opcao_1']} @ R$ {oportunidade['preco_1']:.2f}
📥 <b>COMPRA:</b> {oportunidade['quantidade_2']}x {oportunidade['codigo_opcao_2']} @ R$ {oportunidade['preco_2']:.2f}

💵 Crédito líquido: <b>R$ {oportunidade.get('resultado_liquido', 0):.2f}</b>
   Risco máximo: R$ {oportunidade.get('risco_maximo', 0):.2f}
   Retorno: <b>{oportunidade.get('retorno_percentual', 0):.1f}%</b>
"""
    else:
        mensagem += f"""
📋 <b>{oportunidade['quantidade_1']}x {oportunidade['codigo_opcao_1']}</b>
💰 Strike: R$ {oportunidade['strike_1']:.2f}
💵 Preço: R$ {oportunidade['preco_1']:.2f}
📊 Retorno: <b>{oportunidade.get('retorno_percentual', 0):.1f}%</b>
"""
    
    mensagem += f"\n⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    
    return enviar_alerta_telegram(mensagem)


def alerta_fechar_60_lucro(posicao: dict) -> bool:
    """Alerta quando atingir 60% lucro"""
    
    mensagem = f"""🔥 <b>ALERTA - FECHAR AGORA!</b>

💜 <b>UNO INVEST</b>

📈 <b>{posicao['ativo']}</b> - {posicao['estrategia'].replace('_', ' ')}
✅ Lucro: <b>{posicao.get('lucro_percentual', 0):.1f}%</b>

⚡ <b>Hora de fechar a posição!</b>

Entrada: R$ {posicao.get('resultado_entrada', 0):.2f}
Atual: R$ {posicao.get('resultado_atual', 0):.2f}
Lucro: <b>+R$ {posicao.get('resultado_atual', 0) - posicao.get('resultado_entrada', 0):.2f}</b>

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
    
    return enviar_alerta_telegram(mensagem)


def alerta_stop_loss(posicao: dict) -> bool:
    """Alerta stop loss"""
    
    mensagem = f"""⚠️ <b>STOP LOSS ACIONADO</b>

💜 <b>UNO INVEST</b>

📉 <b>{posicao['ativo']}</b> - {posicao['estrategia'].replace('_', ' ')}
❌ Prejuízo: <b>{posicao.get('lucro_percentual', 0):.1f}%</b>

🛑 <b>Considere fechar para limitar perdas</b>

Entrada: R$ {posicao.get('resultado_entrada', 0):.2f}
Atual: R$ {posicao.get('resultado_atual', 0):.2f}
Perda: <b>R$ {posicao.get('resultado_atual', 0) - posicao.get('resultado_entrada', 0):.2f}</b>

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
    
    return enviar_alerta_telegram(mensagem)


def alerta_vencimento_proximo(posicao: dict, dias_restantes: int) -> bool:
    """Alerta vencimento próximo"""
    
    mensagem = f"""⏰ <b>VENCIMENTO PRÓXIMO</b>

💜 <b>UNO INVEST</b>

📈 <b>{posicao['ativo']}</b> - {posicao['estrategia'].replace('_', ' ')}
📅 Vence em: <b>{dias_restantes} dias</b>

💡 Considere fechar ou ajustar a posição

Lucro atual: {posicao.get('lucro_percentual', 0):.1f}%

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
    
    return enviar_alerta_telegram(mensagem)


def alerta_scanner_completo(total_encontradas: int, top_3: list) -> bool:
    """Alerta quando scanner automático terminar"""
    
    mensagem = f"""🔍 <b>SCANNER AUTOMÁTICO COMPLETO</b>

💜 <b>UNO INVEST</b>

✅ {total_encontradas} oportunidades encontradas

<b>TOP 3:</b>
"""
    
    for i, opp in enumerate(top_3[:3], 1):
        mensagem += f"\n{i}. <b>{opp['ativo']}</b> {opp['estrategia'].replace('_', ' ')}"
        mensagem += f"\n   Score: {opp['score']}/100 | Retorno: {opp.get('retorno_percentual', 0):.1f}%\n"
    
    mensagem += f"\n⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    
    return enviar_alerta_telegram(mensagem)


# Teste
if __name__ == "__main__":
    print("🧪 Testando Telegram...")
    
    # Teste simples
    sucesso = enviar_alerta_telegram("🎉 Telegram configurado com sucesso!\n\n💜 UNO INVEST - Scanner RCO")
    
    if sucesso:
        print("✅ Telegram funcionando!")
    else:
        print("❌ Verifique TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env")
