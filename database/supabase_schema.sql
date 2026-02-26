-- ============================================================================
-- TABELAS SUPABASE - RCO SCANNER
-- ============================================================================

-- 1. OPORTUNIDADES
CREATE TABLE IF NOT EXISTS oportunidades (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ativo VARCHAR(10) NOT NULL,
    estrategia VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL,
    vencimento DATE NOT NULL,
    dias_vencimento INTEGER,
    codigo_opcao_1 VARCHAR(20) NOT NULL,
    tipo_opcao_1 VARCHAR(10),
    strike_1 DECIMAL(10,2),
    preco_1 DECIMAL(10,4),
    quantidade_1 INTEGER,
    direcao_1 VARCHAR(10),
    codigo_opcao_2 VARCHAR(20),
    tipo_opcao_2 VARCHAR(10),
    strike_2 DECIMAL(10,2),
    preco_2 DECIMAL(10,4),
    quantidade_2 INTEGER,
    direcao_2 VARCHAR(10),
    credito_total DECIMAL(10,2),
    debito_total DECIMAL(10,2),
    resultado_liquido DECIMAL(10,2),
    risco_maximo DECIMAL(10,2),
    retorno_percentual DECIMAL(10,2),
    probabilidade_sucesso DECIMAL(5,2),
    delta DECIMAL(10,4),
    gamma DECIMAL(10,4),
    theta DECIMAL(10,4),
    vega DECIMAL(10,4),
    iv DECIMAL(10,2),
    preco_ativo_atual DECIMAL(10,2),
    tendencia_1m VARCHAR(20),
    tendencia_1y VARCHAR(20),
    alerta_enviado BOOLEAN DEFAULT FALSE,
    dt_alerta TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_ativo ON oportunidades(ativo);
CREATE INDEX IF NOT EXISTS idx_score ON oportunidades(score DESC);
CREATE INDEX IF NOT EXISTS idx_created ON oportunidades(created_at DESC);

-- 2. POSIÇÕES ABERTAS
CREATE TABLE IF NOT EXISTS posicoes_abertas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    oportunidade_id UUID REFERENCES oportunidades(id),
    ativo VARCHAR(10) NOT NULL,
    estrategia VARCHAR(50) NOT NULL,
    data_entrada TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    vencimento DATE NOT NULL,
    codigo_opcao_1 VARCHAR(20) NOT NULL,
    strike_1 DECIMAL(10,2),
    preco_entrada_1 DECIMAL(10,4),
    quantidade_1 INTEGER,
    direcao_1 VARCHAR(10),
    codigo_opcao_2 VARCHAR(20),
    strike_2 DECIMAL(10,2),
    preco_entrada_2 DECIMAL(10,4),
    quantidade_2 INTEGER,
    direcao_2 VARCHAR(10),
    credito_entrada DECIMAL(10,2),
    debito_entrada DECIMAL(10,2),
    resultado_entrada DECIMAL(10,2),
    risco_maximo DECIMAL(10,2),
    lucro_maximo DECIMAL(10,2),
    preco_atual_1 DECIMAL(10,4),
    preco_atual_2 DECIMAL(10,4),
    resultado_atual DECIMAL(10,2),
    lucro_percentual DECIMAL(10,2),
    dias_aberta INTEGER,
    delta_atual DECIMAL(10,4),
    alerta_60_lucro BOOLEAN DEFAULT FALSE,
    dt_alerta_60_lucro TIMESTAMP WITH TIME ZONE,
    alerta_stop_loss BOOLEAN DEFAULT FALSE,
    dt_alerta_stop_loss TIMESTAMP WITH TIME ZONE,
    alerta_vencimento BOOLEAN DEFAULT FALSE,
    dt_alerta_vencimento TIMESTAMP WITH TIME ZONE,
    alerta_delta_alto BOOLEAN DEFAULT FALSE,
    dt_alerta_delta_alto TIMESTAMP WITH TIME ZONE,
    ativa BOOLEAN DEFAULT TRUE,
    data_fechamento TIMESTAMP WITH TIME ZONE,
    motivo_fechamento VARCHAR(100),
    resultado_final DECIMAL(10,2)
);

CREATE INDEX IF NOT EXISTS idx_ativa ON posicoes_abertas(ativa);
CREATE INDEX IF NOT EXISTS idx_ativo_pos ON posicoes_abertas(ativo);
CREATE INDEX IF NOT EXISTS idx_vencimento ON posicoes_abertas(vencimento);

-- 3. HISTÓRICO
CREATE TABLE IF NOT EXISTS historico_operacoes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    posicao_id UUID REFERENCES posicoes_abertas(id),
    ativo VARCHAR(10),
    estrategia VARCHAR(50),
    data_entrada TIMESTAMP WITH TIME ZONE,
    data_saida TIMESTAMP WITH TIME ZONE,
    dias_mantida INTEGER,
    valor_entrada DECIMAL(10,2),
    valor_saida DECIMAL(10,2),
    resultado DECIMAL(10,2),
    retorno_percentual DECIMAL(10,2),
    motivo VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ativo_hist ON historico_operacoes(ativo);
CREATE INDEX IF NOT EXISTS idx_resultado ON historico_operacoes(resultado DESC);

-- 4. CONFIGURAÇÕES
CREATE TABLE IF NOT EXISTS configuracoes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    chave VARCHAR(50) UNIQUE NOT NULL,
    valor TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO configuracoes (chave, valor) VALUES
    ('ativos_monitorar', 'PETR4,VALE3,BBAS3,ITUB4,BOVA11'),
    ('score_minimo_alerta', '80'),
    ('capital_total', '5000')
ON CONFLICT (chave) DO NOTHING;

-- 5. LOGS
CREATE TABLE IF NOT EXISTS logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    nivel VARCHAR(20),
    categoria VARCHAR(50),
    mensagem TEXT,
    dados JSONB
);

CREATE INDEX IF NOT EXISTS idx_nivel ON logs(nivel);
CREATE INDEX IF NOT EXISTS idx_created_log ON logs(created_at DESC);

-- VIEWS
CREATE OR REPLACE VIEW v_posicoes_ativas AS
SELECT 
    p.*,
    CASE 
        WHEN p.lucro_percentual >= 60 THEN 'FECHAR AGORA'
        WHEN p.lucro_percentual <= -30 THEN 'STOP LOSS'
        WHEN (p.vencimento - CURRENT_DATE) <= 7 THEN 'VENCIMENTO PRÓXIMO'
        ELSE 'MONITORANDO'
    END as status_alerta
FROM posicoes_abertas p
WHERE p.ativa = TRUE;

CREATE OR REPLACE VIEW v_performance AS
SELECT 
    COUNT(*) as total_operacoes,
    COUNT(*) FILTER (WHERE resultado > 0) as operacoes_lucrativas,
    ROUND(AVG(retorno_percentual), 2) as retorno_medio_pct,
    ROUND(SUM(resultado), 2) as resultado_total
FROM historico_operacoes;

CREATE OR REPLACE VIEW v_melhores_setups AS
SELECT 
    estrategia,
    COUNT(*) as quantidade,
    COUNT(*) FILTER (WHERE resultado > 0) as acertos,
    ROUND(100.0 * COUNT(*) FILTER (WHERE resultado > 0) / COUNT(*), 1) as taxa_acerto
FROM historico_operacoes
GROUP BY estrategia
HAVING COUNT(*) >= 3;

-- POLÍTICAS
ALTER TABLE oportunidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE posicoes_abertas ENABLE ROW LEVEL SECURITY;
ALTER TABLE historico_operacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuracoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Acesso público" ON oportunidades FOR ALL USING (true);
CREATE POLICY "Acesso público" ON posicoes_abertas FOR ALL USING (true);
CREATE POLICY "Acesso público" ON historico_operacoes FOR ALL USING (true);
CREATE POLICY "Acesso público" ON configuracoes FOR ALL USING (true);
CREATE POLICY "Acesso público" ON logs FOR ALL USING (true);
