"""
Dashboard RCO Scanner - UNO INVEST
===================================
Scanner de Opções B3 com automação
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import time
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner_opcoes import ScannerOpcoesB3
from supabase_client import SupabaseRCO

# Configuração da página
st.set_page_config(
    page_title="UNO INVEST - RCO Scanner",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado - UNO INVEST
st.markdown("""
<style>
    /* Sidebar roxo */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #9b59b6 0%, #8e44ad 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Logo UNO INVEST */
    .sidebar-logo {
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
        font-size: 32px;
        font-weight: 700;
        color: white !important;
        text-align: center;
        margin: 20px 0;
        letter-spacing: 2px;
    }
    
    /* Botões roxos */
    .stButton > button {
        background-color: #8e44ad;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #9b59b6;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(142, 68, 173, 0.4);
    }
    
    /* Botões primários */
    button[kind="primary"] {
        background-color: #6c3483 !important;
    }
    
    button[kind="primary"]:hover {
        background-color: #8e44ad !important;
    }
    
    .oportunidade-high {
        border-left: 5px solid #00cc00;
        padding-left: 15px;
        margin: 15px 0;
        background-color: #f0fff0;
    }
    .oportunidade-medium {
        border-left: 5px solid #ffaa00;
        padding-left: 15px;
        margin: 15px 0;
        background-color: #fffaf0;
    }
    .posicao-lucro {
        border-left: 5px solid #00cc00;
        padding-left: 15px;
        background-color: #f0fff0;
    }
    .posicao-alerta {
        border-left: 5px solid #ff0000;
        padding-left: 15px;
        background-color: #fff0f0;
    }
    .codigo-opcao {
        font-family: 'Courier New', monospace;
        font-weight: bold;
        color: #8e44ad;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Lista dos 30 melhores ativos para opções
ATIVOS_TOP30 = [
    'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'BBAS3',
    'BPAC11', 'ABEV3', 'RENT3', 'GGBR4', 'SUZB3',
    'USIM5', 'CSNA3', 'WEGE3', 'RADL3', 'JBSS3',
    'BEEF3', 'MGLU3', 'VIIA3', 'CIEL3', 'AZUL4',
    'EMBR3', 'GOAU4', 'BRFS3', 'B3SA3', 'ELET3',
    'CMIG4', 'SANB11', 'CYRE3', 'MRFG3', 'BOVA11'
]

# Inicializar componentes
@st.cache_resource
def init_components():
    try:
        scanner = ScannerOpcoesB3()
        db = SupabaseRCO(
            url=os.getenv('SUPABASE_URL'),
            key=os.getenv('SUPABASE_KEY')
        )
        return scanner, db
    except Exception as e:
        st.error(f"❌ Erro ao conectar: {e}")
        st.info("Configure SUPABASE_URL e SUPABASE_KEY nas variáveis de ambiente")
        return None, None

scanner, db = init_components()

# Inicializar session state
if 'auto_scan_enabled' not in st.session_state:
    st.session_state.auto_scan_enabled = False
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []

# Sidebar
st.sidebar.markdown('<div class="sidebar-logo">UNO INVEST</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

# Modo de operação
modo = st.sidebar.radio(
    "Modo de Operação:",
    ["🎯 Ativo Único", "🔍 Scanner Top 30", "📊 Minhas Posições"]
)

# Se modo ativo único
if modo == "🎯 Ativo Único":
    ativo_selecionado = st.sidebar.selectbox("Selecione o Ativo:", ATIVOS_TOP30)
else:
    ativo_selecionado = None

# Scanner automático
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Automação")

auto_scan = st.sidebar.checkbox(
    "🔄 Scanner Automático (30min)",
    value=st.session_state.auto_scan_enabled,
    help="Escaneia todos os ativos a cada 30 minutos automaticamente"
)

if auto_scan != st.session_state.auto_scan_enabled:
    st.session_state.auto_scan_enabled = auto_scan
    if auto_scan:
        st.sidebar.success("✅ Scanner automático ATIVADO")
    else:
        st.sidebar.info("⏸️ Scanner automático PAUSADO")

# Mostrar status
if st.session_state.auto_scan_enabled:
    if st.session_state.last_scan_time:
        tempo_decorrido = (datetime.now() - st.session_state.last_scan_time).total_seconds() / 60
        proximo_scan = max(0, 30 - tempo_decorrido)
        st.sidebar.markdown(f"⏰ Próximo scan: **{proximo_scan:.0f}min**")
    else:
        st.sidebar.markdown("⏰ Aguardando primeiro scan...")

# Botão atualizar
if st.sidebar.button("🔄 Atualizar Agora", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Última atualização:**  \n{datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Título principal
st.title("🤖 UNO INVEST - Scanner de Opções B3")
st.markdown(f"### 💜 Estratégia RCO | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# Função para escanear múltiplos ativos
def escanear_multiplos_ativos(ativos_lista, limite_por_ativo=2):
    """Escaneia múltiplos ativos e retorna top oportunidades"""
    todas_oportunidades = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(ativos_lista)
    
    for i, ativo in enumerate(ativos_lista):
        status_text.text(f"🔍 Escaneando {ativo}... ({i+1}/{total})")
        progress_bar.progress((i + 1) / total)
        
        try:
            # Buscar oportunidades
            vendas_cob = scanner.identificar_venda_coberta(ativo)[:limite_por_ativo]
            vendas_put = scanner.identificar_venda_put(ativo)[:limite_por_ativo]
            travas = scanner.identificar_trava_alta(ativo)[:limite_por_ativo]
            
            todas_oportunidades.extend(vendas_cob)
            todas_oportunidades.extend(vendas_put)
            todas_oportunidades.extend(travas)
            
        except Exception as e:
            st.warning(f"⚠️ Erro em {ativo}: {str(e)[:50]}")
            continue
    
    progress_bar.empty()
    status_text.empty()
    
    # Ordenar por score
    todas_oportunidades.sort(key=lambda x: x['score'], reverse=True)
    
    return todas_oportunidades[:10]  # Top 10

# Automação: checar se deve escanear
if st.session_state.auto_scan_enabled and scanner and db:
    agora = datetime.now()
    
    deve_escanear = False
    if st.session_state.last_scan_time is None:
        deve_escanear = True
    else:
        minutos_desde_ultimo = (agora - st.session_state.last_scan_time).total_seconds() / 60
        if minutos_desde_ultimo >= 30:
            deve_escanear = True
    
    if deve_escanear:
        st.info("🔄 Scanner automático executando...")
        resultados = escanear_multiplos_ativos(ATIVOS_TOP30, limite_por_ativo=1)
        st.session_state.scan_results = resultados
        st.session_state.last_scan_time = datetime.now()
        
        # Salvar no banco
        for opp in resultados[:3]:  # Top 3
            db.salvar_oportunidade(opp)
        
        st.success(f"✅ Scan completo! {len(resultados)} oportunidades encontradas")
        st.rerun()

# ============================================================================
# MODO: ATIVO ÚNICO
# ============================================================================
if modo == "🎯 Ativo Único" and scanner and db:
    
    st.subheader(f"🎯 Análise: {ativo_selecionado}")
    
    with st.spinner(f'🔍 Escaneando {ativo_selecionado}...'):
        vendas_cob = scanner.identificar_venda_coberta(ativo_selecionado)
        vendas_put = scanner.identificar_venda_put(ativo_selecionado)
        travas = scanner.identificar_trava_alta(ativo_selecionado)
        
        total_ops = len(vendas_cob) + len(vendas_put) + len(travas)
        
        if total_ops == 0:
            st.warning(f"⚠️ Nenhuma oportunidade encontrada para {ativo_selecionado} no momento")
        else:
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Vendas Cobertas", len(vendas_cob))
            with col2:
                st.metric("Vendas Put", len(vendas_put))
            with col3:
                st.metric("Travas", len(travas))
            with col4:
                st.metric("Total", total_ops)
            
            st.markdown("---")
            
            # Combinar e ordenar
            todas_ops = []
            todas_ops.extend([(op, 'VENDA_COBERTA') for op in vendas_cob])
            todas_ops.extend([(op, 'VENDA_PUT') for op in vendas_put])
            todas_ops.extend([(op, 'TRAVA_ALTA_PUT') for op in travas])
            todas_ops.sort(key=lambda x: x[0]['score'], reverse=True)
            
            # Exibir top 5
            for i, (op, tipo) in enumerate(todas_ops[:5], 1):
                score = op['score']
                classe_css = "oportunidade-high" if score >= 80 else "oportunidade-medium"
                
                with st.container():
                    st.markdown(f'<div class="{classe_css}">', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### #{i} - {op['estrategia'].replace('_', ' ')}")
                        st.markdown(f"**{op['ativo']}** | Score: **{score}/100** {'⭐' * (score // 20)}")
                    with col2:
                        st.markdown(f"**Vencimento:**  \n{datetime.strptime(op['vencimento'], '%Y-%m-%d').strftime('%d/%m/%Y')}  \n({op['dias_vencimento']} dias)")
                    
                    # Detalhes conforme tipo
                    if tipo == 'TRAVA_ALTA_PUT':
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**📤 PERNA 1 (VENDER):**")
                            st.markdown(f'<p class="codigo-opcao">{op["quantidade_1"]}x {op["codigo_opcao_1"]}</p>', unsafe_allow_html=True)
                            st.markdown(f"Strike: **R$ {op['strike_1']:.2f}** | Preço: **R$ {op['preco_1']:.2f}**")
                        with col2:
                            st.markdown("**📥 PERNA 2 (COMPRAR):**")
                            st.markdown(f'<p class="codigo-opcao">{op["quantidade_2"]}x {op["codigo_opcao_2"]}</p>', unsafe_allow_html=True)
                            st.markdown(f"Strike: **R$ {op['strike_2']:.2f}** | Preço: **R$ {op['preco_2']:.2f}**")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Crédito Líquido", f"R$ {op['resultado_liquido']:.2f}")
                        with col2:
                            st.metric("Risco Máximo", f"R$ {op['risco_maximo']:.2f}")
                        with col3:
                            st.metric("Retorno", f"{op['retorno_percentual']:.1f}%")
                        with col4:
                            st.metric("R/R", f"1:{1/op['risco_retorno']:.1f}")
                    else:
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f'<p class="codigo-opcao">{op["quantidade_1"]}x {op["codigo_opcao_1"]}</p>', unsafe_allow_html=True)
                            st.markdown(f"Strike: **R$ {op['strike_1']:.2f}** | Preço: **R$ {op['preco_1']:.2f}**")
                            if 'preco_medio' in op:
                                st.markdown(f"PM: **R$ {op['preco_medio']:.2f}** (desc {op['desconto_pct']:.1f}%)")
                        with col2:
                            st.metric("Crédito", f"R$ {op['credito_total']:.2f}")
                            st.metric("Retorno", f"{op['retorno_percentual']:.1f}%")
                    
                    # Botões
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if st.button("✅ JÁ ENTREI", key=f"entrei_{i}", type="primary"):
                            opp_salva = db.salvar_oportunidade(op)
                            if opp_salva and 'id' in opp_salva:
                                posicao = db.abrir_posicao(opp_salva['id'], op)
                                if posicao:
                                    st.success("✅ Posição aberta!")
                                    st.balloons()
                    
                    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# MODO: SCANNER TOP 30
# ============================================================================
elif modo == "🔍 Scanner Top 30" and scanner and db:
    
    st.subheader("🔍 Scanner Top 30 Ativos")
    
    if st.button("🚀 ESCANEAR TODOS OS ATIVOS", type="primary"):
        resultados = escanear_multiplos_ativos(ATIVOS_TOP30, limite_por_ativo=2)
        st.session_state.scan_results = resultados
        st.session_state.last_scan_time = datetime.now()
    
    # Mostrar resultados
    if st.session_state.scan_results:
        st.success(f"✅ {len(st.session_state.scan_results)} oportunidades encontradas")
        
        for i, op in enumerate(st.session_state.scan_results[:10], 1):
            score = op['score']
            with st.expander(f"#{i} - {op['ativo']} {op['estrategia'].replace('_', ' ')} - Score: {score}/100"):
                st.write(f"**Código:** {op['codigo_opcao_1']}")
                st.write(f"**Strike:** R$ {op['strike_1']:.2f}")
                st.write(f"**Retorno:** {op.get('retorno_percentual', 0):.1f}%")
                
                if st.button("✅ Entrei", key=f"multi_{i}"):
                    opp_salva = db.salvar_oportunidade(op)
                    if opp_salva:
                        db.abrir_posicao(opp_salva['id'], op)
                        st.success("✅ Posição registrada!")

# ============================================================================
# MODO: POSIÇÕES
# ============================================================================
elif modo == "📊 Minhas Posições" and db:
    
    st.subheader("📊 Minhas Posições Abertas")
    
    posicoes = db.listar_posicoes_ativas()
    
    if not posicoes:
        st.info("Você ainda não tem posições abertas.")
    else:
        st.markdown(f"**Total:** {len(posicoes)} posições")
        
        for pos in posicoes:
            lucro = pos.get('lucro_percentual', 0)
            status = "🔥 FECHAR AGORA" if lucro >= 60 else "📊 Monitorando"
            
            with st.expander(f"{status} - {pos['ativo']} {pos['estrategia']}"):
                st.write(f"**Código:** {pos['codigo_opcao_1']}")
                st.write(f"**Lucro:** {lucro:.1f}%")
                st.write(f"**Dias aberta:** {pos.get('dias_aberta', 0)}")
                
                if st.button("🚪 Fechar", key=f"close_{pos['id']}"):
                    if db.fechar_posicao(pos['id'], "Manual", pos.get('resultado_atual', 0)):
                        st.success("✅ Fechada!")
                        st.rerun()

# Footer
st.markdown("---")
st.markdown("💜 **UNO INVEST** | Scanner Inteligente de Opções B3 | Estratégia RCO Validada")
