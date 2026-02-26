"""
Scanner de Opções B3 - CÓDIGOS REAIS
=====================================
Busca opções reais da B3 (PETRC402, VALEP350, etc)
Identifica setups RCO conforme curso Jimmy Carvalho
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScannerOpcoesB3:
    """Scanner de opções reais da B3"""
    
    def __init__(self):
        self.ativos_base = ['PETR4', 'VALE3', 'BBAS3', 'ITUB4', 'BOVA11']
        self.cache_opcoes = {}
        
    def buscar_opcoes_disponiveis(self, ativo: str) -> Dict:
        """
        Busca TODAS as opções disponíveis de um ativo
        
        Retorna códigos REAIS: PETRC402, VALEP350, etc
        """
        ticker_yf = f"{ativo}.SA"
        
        try:
            ticker = yf.Ticker(ticker_yf)
            
            # Pegar preço atual
            hist = ticker.history(period="1d")
            if hist.empty:
                logger.warning(f"Sem dados para {ativo}")
                return {'erro': 'Sem dados'}
            
            preco_ativo = hist['Close'].iloc[-1]
            
            # Buscar opções
            try:
                vencimentos = ticker.options
            except:
                logger.warning(f"Sem opções disponíveis para {ativo}")
                return {'erro': 'Sem opções'}
            
            if not vencimentos:
                return {'erro': 'Sem vencimentos'}
            
            todas_opcoes = {
                'ativo': ativo,
                'preco_atual': preco_ativo,
                'vencimentos': [],
                'calls': [],
                'puts': []
            }
            
            # Para cada vencimento
            for venc_str in vencimentos:
                try:
                    venc_date = datetime.strptime(venc_str, '%Y-%m-%d')
                    dias_venc = (venc_date - datetime.now()).days
                    
                    # Filtrar apenas 20-90 dias (foco RCO)
                    if dias_venc < 20 or dias_venc > 90:
                        continue
                    
                    # Buscar chain
                    chain = ticker.option_chain(venc_str)
                    
                    # Processar CALLS
                    for _, row in chain.calls.iterrows():
                        # Extrair código real da opção
                        codigo = row.get('contractSymbol', '')
                        # Limpar código (remover .SA)
                        codigo = codigo.replace('.SA', '')
                        
                        if not codigo:
                            continue
                        
                        call = {
                            'codigo': codigo,  # Ex: PETRC402
                            'tipo': 'CALL',
                            'ativo': ativo,
                            'strike': row['strike'],
                            'vencimento': venc_str,
                            'vencimento_date': venc_date,
                            'dias_vencimento': dias_venc,
                            'ultimo_preco': row['lastPrice'],
                            'bid': row.get('bid', 0),
                            'ask': row.get('ask', 0),
                            'volume': row.get('volume', 0),
                            'open_interest': row.get('openInterest', 0),
                            'iv': row.get('impliedVolatility', 0) * 100,
                            'itm': preco_ativo > row['strike'],
                            'dist_preco_pct': ((row['strike'] - preco_ativo) / preco_ativo) * 100
                        }
                        
                        # Calcular delta aproximado
                        call['delta'] = self._calcular_delta_aproximado(
                            'call', preco_ativo, call['strike'], dias_venc, call['iv']/100
                        )
                        
                        todas_opcoes['calls'].append(call)
                    
                    # Processar PUTS
                    for _, row in chain.puts.iterrows():
                        codigo = row.get('contractSymbol', '').replace('.SA', '')
                        
                        if not codigo:
                            continue
                        
                        put = {
                            'codigo': codigo,  # Ex: PETRP385
                            'tipo': 'PUT',
                            'ativo': ativo,
                            'strike': row['strike'],
                            'vencimento': venc_str,
                            'vencimento_date': venc_date,
                            'dias_vencimento': dias_venc,
                            'ultimo_preco': row['lastPrice'],
                            'bid': row.get('bid', 0),
                            'ask': row.get('ask', 0),
                            'volume': row.get('volume', 0),
                            'open_interest': row.get('openInterest', 0),
                            'iv': row.get('impliedVolatility', 0) * 100,
                            'itm': preco_ativo < row['strike'],
                            'dist_preco_pct': ((preco_ativo - row['strike']) / preco_ativo) * 100
                        }
                        
                        put['delta'] = self._calcular_delta_aproximado(
                            'put', preco_ativo, put['strike'], dias_venc, put['iv']/100
                        )
                        
                        todas_opcoes['puts'].append(put)
                    
                    todas_opcoes['vencimentos'].append(venc_str)
                    
                except Exception as e:
                    logger.error(f"Erro processando vencimento {venc_str}: {e}")
                    continue
            
            return todas_opcoes
            
        except Exception as e:
            logger.error(f"Erro buscando opções {ativo}: {e}")
            return {'erro': str(e)}
    
    def _calcular_delta_aproximado(self, tipo: str, S: float, K: float, dias: int, iv: float) -> float:
        """Calcula delta aproximado"""
        if tipo == 'call':
            if S > K:  # ITM
                return min(50 + (S-K)/S * 50, 100)
            else:  # OTM
                return max(50 - (K-S)/S * 50, 0)
        else:  # put
            if S < K:  # ITM
                return -min(50 + (K-S)/S * 50, 100)
            else:  # OTM
                return -max(50 - (S-K)/S * 50, 0)
    
    def identificar_venda_coberta(self, ativo: str) -> List[Dict]:
        """
        Identifica oportunidades de VENDA COBERTA
        
        Critérios RCO:
        - Delta 30 (calls OTM)
        - IV > 30%
        - Prazo 30-60 dias
        - Liquidez mínima
        """
        opcoes = self.buscar_opcoes_disponiveis(ativo)
        
        if 'erro' in opcoes:
            return []
        
        oportunidades = []
        
        for call in opcoes['calls']:
            # Filtros RCO
            if call['iv'] < 30:  # IV mínima
                continue
            
            if call['dias_vencimento'] < 30 or call['dias_vencimento'] > 60:
                continue
            
            if call['volume'] < 10 and call['open_interest'] < 50:  # Liquidez
                continue
            
            if call['bid'] <= 0:  # Sem preço bid
                continue
            
            # Delta ideal (25-35)
            delta_abs = abs(call['delta'])
            if delta_abs < 20 or delta_abs > 40:
                continue
            
            # Calcular retorno
            retorno_pct = (call['bid'] / opcoes['preco_atual']) * 100
            retorno_mensal = retorno_pct * (30 / call['dias_vencimento'])
            
            # Score
            score = self._calcular_score_venda_coberta(call, retorno_mensal, opcoes['preco_atual'])
            
            if score < 60:  # Score mínimo
                continue
            
            setup = {
                'estrategia': 'VENDA_COBERTA',
                'ativo': ativo,
                'score': score,
                
                # Operação
                'codigo_opcao_1': call['codigo'],
                'tipo_opcao_1': 'CALL',
                'direcao_1': 'VENDA',
                'strike_1': call['strike'],
                'preco_1': call['bid'],
                'quantidade_1': 100,  # Lote padrão
                
                # Não tem perna 2
                'codigo_opcao_2': None,
                
                # Resultado
                'credito_total': call['bid'] * 100,
                'debito_total': 0,
                'resultado_liquido': call['bid'] * 100,
                'risco_maximo': None,  # Risco é queda da ação
                'retorno_percentual': retorno_pct,
                'probabilidade_sucesso': 100 - delta_abs,  # Prob OTM
                
                # Dados
                'vencimento': call['vencimento'],
                'dias_vencimento': call['dias_vencimento'],
                'delta': call['delta'],
                'iv': call['iv'],
                'preco_ativo_atual': opcoes['preco_atual'],
                'retorno_mensal': retorno_mensal
            }
            
            oportunidades.append(setup)
        
        # Ordenar por score
        oportunidades.sort(key=lambda x: x['score'], reverse=True)
        return oportunidades[:5]  # Top 5
    
    def identificar_venda_put(self, ativo: str) -> List[Dict]:
        """
        Identifica oportunidades de VENDA PUT
        
        Critérios RCO:
        - Delta 30-35 (puts OTM)
        - IV > 30%
        - Preço médio atrativo
        """
        opcoes = self.buscar_opcoes_disponiveis(ativo)
        
        if 'erro' in opcoes:
            return []
        
        oportunidades = []
        
        for put in opcoes['puts']:
            # Filtros
            if put['iv'] < 30:
                continue
            
            if put['dias_vencimento'] < 30 or put['dias_vencimento'] > 60:
                continue
            
            if put['volume'] < 10 and put['open_interest'] < 50:
                continue
            
            if put['bid'] <= 0:
                continue
            
            # Delta ideal (-25 a -35)
            delta_abs = abs(put['delta'])
            if delta_abs < 25 or delta_abs > 40:
                continue
            
            # Calcular PM e desconto
            pm = put['strike'] - put['bid']
            desconto_pct = ((opcoes['preco_atual'] - pm) / opcoes['preco_atual']) * 100
            
            if desconto_pct < 3:  # Mínimo 3% desconto
                continue
            
            # Retorno
            retorno_pct = (put['bid'] / opcoes['preco_atual']) * 100
            retorno_mensal = retorno_pct * (30 / put['dias_vencimento'])
            
            # Score
            score = self._calcular_score_venda_put(put, retorno_mensal, desconto_pct)
            
            if score < 60:
                continue
            
            setup = {
                'estrategia': 'VENDA_PUT',
                'ativo': ativo,
                'score': score,
                
                'codigo_opcao_1': put['codigo'],
                'tipo_opcao_1': 'PUT',
                'direcao_1': 'VENDA',
                'strike_1': put['strike'],
                'preco_1': put['bid'],
                'quantidade_1': 100,
                
                'codigo_opcao_2': None,
                
                'credito_total': put['bid'] * 100,
                'debito_total': 0,
                'resultado_liquido': put['bid'] * 100,
                'risco_maximo': put['strike'] * 100,
                'retorno_percentual': retorno_pct,
                'probabilidade_sucesso': 100 - delta_abs,
                
                'vencimento': put['vencimento'],
                'dias_vencimento': put['dias_vencimento'],
                'delta': put['delta'],
                'iv': put['iv'],
                'preco_ativo_atual': opcoes['preco_atual'],
                'retorno_mensal': retorno_mensal,
                'preco_medio': pm,
                'desconto_pct': desconto_pct
            }
            
            oportunidades.append(setup)
        
        oportunidades.sort(key=lambda x: x['score'], reverse=True)
        return oportunidades[:5]
    
    def identificar_trava_alta(self, ativo: str) -> List[Dict]:
        """
        Identifica TRAVAS DE ALTA (vende put + compra put strike menor)
        
        Exemplo REAL:
        VENDE: PETRP402 (Strike 40.20) por R$ 1,58
        COMPRA: PETRP412 (Strike 41.20) por R$ 1,10
        Crédito: R$ 0,48 (R$ 48 por contrato)
        """
        opcoes = self.buscar_opcoes_disponiveis(ativo)
        
        if 'erro' in opcoes:
            return []
        
        oportunidades = []
        
        # Agrupar puts por vencimento
        puts_por_venc = {}
        for put in opcoes['puts']:
            if put['iv'] < 30:
                continue
            if put['volume'] < 50 and put['open_interest'] < 100:  # Liquidez maior para travas
                continue
            
            venc = put['vencimento']
            if venc not in puts_por_venc:
                puts_por_venc[venc] = []
            puts_por_venc[venc].append(put)
        
        # Para cada vencimento, montar travas
        for venc, puts_list in puts_por_venc.items():
            # Ordenar por strike
            puts_list.sort(key=lambda x: x['strike'], reverse=True)
            
            for i, put_vend in enumerate(puts_list):
                # Buscar put comprada (strike menor)
                for put_comp in puts_list[i+1:]:
                    # Spread máximo R$1 para ações até R$25
                    spread = put_vend['strike'] - put_comp['strike']
                    if spread > 1.0 or spread < 0.5:
                        continue
                    
                    # Calcular crédito
                    credito = put_vend['bid'] - put_comp['ask']
                    if credito <= 0:
                        continue
                    
                    prejuizo_max = spread - credito
                    if prejuizo_max <= 0:
                        continue
                    
                    risco_retorno = credito / prejuizo_max
                    
                    # Filtrar por risco/retorno (mínimo 0,25 = 1:4)
                    if risco_retorno < 0.25:
                        continue
                    
                    retorno_pct = (credito / prejuizo_max) * 100
                    
                    # Score
                    score = self._calcular_score_trava(risco_retorno, retorno_pct, put_vend['iv'])
                    
                    if score < 60:
                        continue
                    
                    setup = {
                        'estrategia': 'TRAVA_ALTA_PUT',
                        'ativo': ativo,
                        'score': score,
                        
                        # Perna 1: VENDE put strike maior
                        'codigo_opcao_1': put_vend['codigo'],
                        'tipo_opcao_1': 'PUT',
                        'direcao_1': 'VENDA',
                        'strike_1': put_vend['strike'],
                        'preco_1': put_vend['bid'],
                        'quantidade_1': 100,
                        
                        # Perna 2: COMPRA put strike menor
                        'codigo_opcao_2': put_comp['codigo'],
                        'tipo_opcao_2': 'PUT',
                        'direcao_2': 'COMPRA',
                        'strike_2': put_comp['strike'],
                        'preco_2': put_comp['ask'],
                        'quantidade_2': 100,
                        
                        # Resultado
                        'credito_total': put_vend['bid'] * 100,
                        'debito_total': put_comp['ask'] * 100,
                        'resultado_liquido': credito * 100,
                        'risco_maximo': prejuizo_max * 100,
                        'retorno_percentual': retorno_pct,
                        'probabilidade_sucesso': 65,  # Estimado
                        'risco_retorno': risco_retorno,
                        
                        'vencimento': venc,
                        'dias_vencimento': put_vend['dias_vencimento'],
                        'delta': put_vend['delta'],
                        'iv': (put_vend['iv'] + put_comp['iv']) / 2,
                        'preco_ativo_atual': opcoes['preco_atual'],
                        'spread': spread
                    }
                    
                    oportunidades.append(setup)
        
        oportunidades.sort(key=lambda x: x['score'], reverse=True)
        return oportunidades[:5]
    
    def _calcular_score_venda_coberta(self, call: Dict, ret_mensal: float, preco_ativo: float) -> int:
        """Calcula score para venda coberta"""
        score = 0
        
        # Retorno mensal (0-40 pts)
        score += min(ret_mensal * 10, 40)
        
        # IV alta (0-20 pts)
        score += min(call['iv'] / 2, 20)
        
        # Delta próximo 30 (0-20 pts)
        delta_ideal = 30
        delta_diff = abs(abs(call['delta']) - delta_ideal)
        score += max(0, 20 - delta_diff)
        
        # Liquidez (0-20 pts)
        if call['volume'] > 100 or call['open_interest'] > 500:
            score += 20
        elif call['volume'] > 50 or call['open_interest'] > 200:
            score += 10
        
        return int(min(score, 100))
    
    def _calcular_score_venda_put(self, put: Dict, ret_mensal: float, desconto: float) -> int:
        """Calcula score para venda put"""
        score = 0
        
        # Retorno mensal (0-30 pts)
        score += min(ret_mensal * 8, 30)
        
        # Desconto (0-30 pts)
        score += min(desconto * 3, 30)
        
        # IV alta (0-20 pts)
        score += min(put['iv'] / 2, 20)
        
        # Delta próximo 35 (0-20 pts)
        delta_diff = abs(abs(put['delta']) - 35)
        score += max(0, 20 - delta_diff)
        
        return int(min(score, 100))
    
    def _calcular_score_trava(self, rr: float, ret_pct: float, iv: float) -> int:
        """Calcula score para trava"""
        score = 0
        
        # Risco/Retorno (0-40 pts)
        score += min(rr * 100, 40)
        
        # Retorno % (0-30 pts)
        score += min(ret_pct, 30)
        
        # IV (0-20 pts)
        score += min(iv / 2, 20)
        
        # Bonus se R/R > 0.33 (0-10 pts)
        if rr >= 0.33:
            score += 10
        
        return int(min(score, 100))


# Teste
if __name__ == "__main__":
    scanner = ScannerOpcoesB3()
    
    print("🔍 Buscando oportunidades PETR4...")
    
    print("\n📈 VENDA COBERTA:")
    vendas_cob = scanner.identificar_venda_coberta('PETR4')
    for op in vendas_cob[:3]:
        print(f"\n  Score: {op['score']}")
        print(f"  {op['codigo_opcao_1']} Strike {op['strike_1']}")
        print(f"  Crédito: R$ {op['credito_total']:.2f}")
        print(f"  Retorno: {op['retorno_percentual']:.1f}%")
    
    print("\n📉 VENDA PUT:")
    vendas_put = scanner.identificar_venda_put('PETR4')
    for op in vendas_put[:3]:
        print(f"\n  Score: {op['score']}")
        print(f"  {op['codigo_opcao_1']} Strike {op['strike_1']}")
        print(f"  PM: R$ {op['preco_medio']:.2f} (desc {op['desconto_pct']:.1f}%)")
    
    print("\n🔧 TRAVA ALTA:")
    travas = scanner.identificar_trava_alta('PETR4')
    for op in travas[:3]:
        print(f"\n  Score: {op['score']}")
        print(f"  VENDE: {op['codigo_opcao_1']} @ R$ {op['preco_1']:.2f}")
        print(f"  COMPRA: {op['codigo_opcao_2']} @ R$ {op['preco_2']:.2f}")
        print(f"  Crédito líquido: R$ {op['resultado_liquido']:.2f}")
        print(f"  R/R: 1:{1/op['risco_retorno']:.1f}")
