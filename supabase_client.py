"""
Cliente Supabase - RCO Scanner
===============================
Integração com banco de dados PostgreSQL (Supabase)
"""

from supabase import create_client, Client
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseRCO:
    """Cliente para interagir com Supabase"""
    
    def __init__(self, url: str = None, key: str = None):
        # Tentar pegar de variáveis ambiente ou usar parâmetros
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY são obrigatórios")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info("✅ Conectado ao Supabase")
    
    # ========================================================================
    # OPORTUNIDADES
    # ========================================================================
    
    def salvar_oportunidade(self, oportunidade: Dict) -> Dict:
        """Salva uma oportunidade detectada"""
        try:
            result = self.client.table('oportunidades').insert(oportunidade).execute()
            logger.info(f"✅ Oportunidade salva: {oportunidade.get('estrategia')} {oportunidade.get('ativo')}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"❌ Erro ao salvar oportunidade: {e}")
            return {}
    
    def listar_oportunidades_recentes(self, limite: int = 10, score_min: int = 60) -> List[Dict]:
        """Lista oportunidades recentes com score alto"""
        try:
            result = self.client.table('oportunidades')\
                .select('*')\
                .gte('score', score_min)\
                .order('created_at', desc=True)\
                .limit(limite)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"❌ Erro ao listar oportunidades: {e}")
            return []
    
    def buscar_oportunidade_por_id(self, oportunidade_id: str) -> Optional[Dict]:
        """Busca uma oportunidade específica"""
        try:
            result = self.client.table('oportunidades')\
                .select('*')\
                .eq('id', oportunidade_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar oportunidade: {e}")
            return None
    
    # ========================================================================
    # POSIÇÕES ABERTAS
    # ========================================================================
    
    def abrir_posicao(self, oportunidade_id: str, oportunidade: Dict) -> Dict:
        """
        Marca que usuário ENTROU na operação
        Cria registro em posicoes_abertas para monitorar
        """
        posicao = {
            'oportunidade_id': oportunidade_id,
            'ativo': oportunidade['ativo'],
            'estrategia': oportunidade['estrategia'],
            'vencimento': oportunidade['vencimento'],
            
            # Perna 1
            'codigo_opcao_1': oportunidade['codigo_opcao_1'],
            'strike_1': oportunidade['strike_1'],
            'preco_entrada_1': oportunidade['preco_1'],
            'quantidade_1': oportunidade['quantidade_1'],
            'direcao_1': oportunidade['direcao_1'],
            
            # Perna 2 (se tiver)
            'codigo_opcao_2': oportunidade.get('codigo_opcao_2'),
            'strike_2': oportunidade.get('strike_2'),
            'preco_entrada_2': oportunidade.get('preco_2'),
            'quantidade_2': oportunidade.get('quantidade_2'),
            'direcao_2': oportunidade.get('direcao_2'),
            
            # Valores
            'credito_entrada': oportunidade.get('credito_total', 0),
            'debito_entrada': oportunidade.get('debito_total', 0),
            'resultado_entrada': oportunidade.get('resultado_liquido', 0),
            'risco_maximo': oportunidade.get('risco_maximo'),
            'lucro_maximo': oportunidade.get('resultado_liquido', 0),  # Para vendas
            
            # Status
            'ativa': True,
            'dias_aberta': 0
        }
        
        try:
            result = self.client.table('posicoes_abertas').insert(posicao).execute()
            logger.info(f"✅ Posição aberta: {posicao['estrategia']} {posicao['ativo']}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"❌ Erro ao abrir posição: {e}")
            return {}
    
    def listar_posicoes_ativas(self) -> List[Dict]:
        """Lista todas as posições abertas e ativas"""
        try:
            result = self.client.table('posicoes_abertas')\
                .select('*')\
                .eq('ativa', True)\
                .order('created_at', desc=False)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"❌ Erro ao listar posições ativas: {e}")
            return []
    
    def atualizar_posicao(self, posicao_id: str, dados: Dict) -> bool:
        """Atualiza dados de uma posição (preços atuais, lucro, etc)"""
        try:
            self.client.table('posicoes_abertas')\
                .update(dados)\
                .eq('id', posicao_id)\
                .execute()
            
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar posição: {e}")
            return False
    
    def fechar_posicao(self, posicao_id: str, motivo: str, resultado_final: float) -> bool:
        """Marca posição como fechada e move para histórico"""
        try:
            # Buscar posição
            pos = self.client.table('posicoes_abertas')\
                .select('*')\
                .eq('id', posicao_id)\
                .single()\
                .execute()
            
            if not pos.data:
                return False
            
            posicao = pos.data
            
            # Atualizar como fechada
            self.client.table('posicoes_abertas')\
                .update({
                    'ativa': False,
                    'data_fechamento': datetime.now().isoformat(),
                    'motivo_fechamento': motivo,
                    'resultado_final': resultado_final
                })\
                .eq('id', posicao_id)\
                .execute()
            
            # Adicionar ao histórico
            dias_mantida = (datetime.now() - datetime.fromisoformat(posicao['created_at'].replace('Z', '+00:00'))).days
            
            historico = {
                'posicao_id': posicao_id,
                'ativo': posicao['ativo'],
                'estrategia': posicao['estrategia'],
                'data_entrada': posicao['created_at'],
                'data_saida': datetime.now().isoformat(),
                'dias_mantida': dias_mantida,
                'valor_entrada': posicao['resultado_entrada'],
                'valor_saida': resultado_final,
                'resultado': resultado_final - posicao['resultado_entrada'],
                'retorno_percentual': ((resultado_final - posicao['resultado_entrada']) / abs(posicao['resultado_entrada'])) * 100 if posicao['resultado_entrada'] != 0 else 0,
                'motivo': motivo
            }
            
            self.client.table('historico_operacoes').insert(historico).execute()
            
            logger.info(f"✅ Posição fechada: {motivo}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao fechar posição: {e}")
            return False
    
    # ========================================================================
    # HISTÓRICO E PERFORMANCE
    # ========================================================================
    
    def obter_performance(self) -> Dict:
        """Obtém estatísticas de performance"""
        try:
            result = self.client.table('v_performance').select('*').single().execute()
            return result.data if result.data else {}
        except Exception as e:
            logger.error(f"❌ Erro ao obter performance: {e}")
            return {}
    
    def obter_melhores_setups(self) -> List[Dict]:
        """Obtém melhores estratégias por taxa de acerto"""
        try:
            result = self.client.table('v_melhores_setups').select('*').execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"❌ Erro ao obter melhores setups: {e}")
            return []
    
    # ========================================================================
    # CONFIGURAÇÕES
    # ========================================================================
    
    def obter_config(self, chave: str) -> Optional[str]:
        """Obtém valor de uma configuração"""
        try:
            result = self.client.table('configuracoes')\
                .select('valor')\
                .eq('chave', chave)\
                .single()\
                .execute()
            
            return result.data['valor'] if result.data else None
        except:
            return None
    
    def salvar_config(self, chave: str, valor: str) -> bool:
        """Salva/atualiza uma configuração"""
        try:
            self.client.table('configuracoes')\
                .upsert({'chave': chave, 'valor': valor})\
                .execute()
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar config: {e}")
            return False
    
    def obter_todas_configs(self) -> Dict:
        """Obtém todas as configurações como dicionário"""
        try:
            result = self.client.table('configuracoes').select('*').execute()
            return {item['chave']: item['valor'] for item in result.data} if result.data else {}
        except Exception as e:
            logger.error(f"❌ Erro ao obter configs: {e}")
            return {}
    
    # ========================================================================
    # LOGS
    # ========================================================================
    
    def log(self, nivel: str, categoria: str, mensagem: str, dados: Dict = None):
        """Registra um log"""
        try:
            self.client.table('logs').insert({
                'nivel': nivel,
                'categoria': categoria,
                'mensagem': mensagem,
                'dados': dados
            }).execute()
        except Exception as e:
            logger.error(f"❌ Erro ao salvar log: {e}")


# Teste
if __name__ == "__main__":
    # Exemplo de uso
    print("Para testar, configure SUPABASE_URL e SUPABASE_KEY")
    print("\nExemplo:")
    print("export SUPABASE_URL='https://xxxxx.supabase.co'")
    print("export SUPABASE_KEY='eyJhbGc...'")
    
    # Se tiver configurado, testa
    if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_KEY'):
        db = SupabaseRCO()
        
        # Testar conexão
        configs = db.obter_todas_configs()
        print(f"\n✅ Conectado! Configs: {list(configs.keys())}")
