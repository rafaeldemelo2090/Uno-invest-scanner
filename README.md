# 🤖 RCO SCANNER - Inteligência para Opções B3

Sistema web para identificar oportunidades de opções seguindo a estratégia RCO do Jimmy Carvalho.

---

## 🎯 **O QUE FAZ:**

✅ **SCANNER 24/7** - Monitora PETR4, VALE3, BBAS3, ITUB4, BOVA11  
✅ **CÓDIGOS REAIS** - Mostra códigos exatos das opções (PETRC402, VALEP350, etc)  
✅ **SCORE INTELIGENTE** - Nota 0-100 baseada nos critérios RCO  
✅ **DETALHES COMPLETOS** - Strike, vencimento, preço, gregas, probabilidades  
✅ **TRAVAS COMPLETAS** - Mostra AMBAS as pernas (compra + venda)  
✅ **MONITORAMENTO** - Marca "Já entrei" e sistema monitora até 60% lucro  
✅ **ALERTAS** - Telegram quando atingir metas  

---

## 📦 **INSTALAÇÃO RÁPIDA (5 MIN)**

### **Passo 1: Configurar Supabase**

1. **Acesse seu Supabase:** https://supabase.com/dashboard
2. **Copie as credenciais:**
   - URL: `https://seu-projeto.supabase.co`
   - Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

3. **Execute o SQL:**
   - No Supabase, vá em: **SQL Editor**
   - Abra o arquivo: `database/supabase_schema.sql`
   - **Copie TODO o conteúdo** (Ctrl+A, Ctrl+C)
   - **Cole no SQL Editor** do Supabase
   - Clique em **RUN** ▶️

✅ **Pronto!** Tabelas criadas.

---

### **Passo 2: Instalar Python**

```bash
# 1. Clone ou baixe o projeto
cd robo_rco_web

# 2. Crie ambiente virtual (recomendado)
python -m venv venv

# Ativar:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt
```

---

### **Passo 3: Configurar Credenciais**

```bash
# 1. Copie o exemplo
cp .env.example .env

# 2. Edite o .env
nano .env  # ou abra no VS Code

# 3. Cole suas credenciais:
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### **Passo 4: RODAR!**

```bash
streamlit run dashboard.py
```

✅ **Abrirá automaticamente:** `http://localhost:8501`

---

## 🖥️ **USANDO O SISTEMA:**

### **DASHBOARD:**

```
┌─────────────────────────────────────────────┐
│  🤖 RCO Scanner - Opções B3                │
├─────────────────────────────────────────────┤
│                                              │
│  🔥 OPORTUNIDADE #1                         │
│  TRAVA DE ALTA - PETR4  |  Score: 89/100   │
│                                              │
│  📤 PERNA 1 (VENDER):                       │
│  1.000x PETRP402                            │
│  Strike: R$ 39,40  |  Preço: R$ 1,58       │
│                                              │
│  📥 PERNA 2 (COMPRAR):                      │
│  1.000x PETRP412                            │
│  Strike: R$ 40,40  |  Preço: R$ 1,10       │
│                                              │
│  💵 RESULTADO:                              │
│  Crédito líquido: R$ 480,00                 │
│  Risco máximo: R$ 520,00                    │
│  Retorno: 92%  |  R/R: 1:1,1               │
│                                              │
│  [✅ JÁ ENTREI]  [📋 COPIAR ORDEM]         │
└─────────────────────────────────────────────┘
```

### **WORKFLOW:**

1. **Scanner encontra oportunidade**
   - Score alto (>80)
   - Todos critérios RCO ✓

2. **Você analisa detalhes**
   - Código exato da opção
   - Strike, vencimento, preço
   - Probabilidade, risco/retorno

3. **Decide operar**
   - Copia ordem
   - Executa no home broker

4. **Marca "JÁ ENTREI"**
   - Sistema começa a monitorar
   - Alerta quando atingir 60% lucro
   - Alerta stop loss / vencimento

5. **Sistema avisa FECHAR**
   - Você fecha manual
   - Marca como fechada
   - Vai para histórico

---

## 📂 **ESTRUTURA:**

```
robo_rco_web/
│
├── database/
│   └── supabase_schema.sql      ← SQL para criar tabelas
│
├── scanner_opcoes.py            ← Scanner de opções B3
├── supabase_client.py           ← Cliente banco de dados
├── dashboard.py                 ← Interface web (PRINCIPAL)
│
├── requirements.txt             ← Dependências
├── .env.example                 ← Exemplo credenciais
├── .env                         ← Suas credenciais (criar)
│
└── README.md                    ← Este arquivo
```

---

## 🔧 **CONFIGURAÇÃO AVANÇADA:**

### **Telegram (Opcional):**

1. Crie bot: `@BotFather` no Telegram
2. Copie token
3. Adicione no `.env`:
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=123456789
   ```

### **Hospedar Online:**

**OPÇÃO 1: Streamlit Cloud (GRÁTIS)**
```bash
# 1. Commit no GitHub
git init
git add .
git commit -m "RCO Scanner"
git push

# 2. Deploy:
# - Acesse: https://streamlit.io/cloud
# - Conecte GitHub
# - Deploy!
# - Configure SUPABASE_URL e KEY nos "Secrets"
```

**OPÇÃO 2: Seu Domínio (VPS)**
```bash
# 1. SSH no servidor
ssh user@seu-dominio.com

# 2. Clone projeto
git clone ...

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure .env

# 5. Rode com PM2
pm2 start "streamlit run dashboard.py --server.port 8501"

# 6. Configure Nginx reverso proxy
# Seu domínio → 8501
```

---

## 🎯 **ESTRATÉGIAS SUPORTADAS:**

| Estratégia | Critérios RCO | Score se... |
|------------|---------------|-------------|
| **Venda Coberta** | Delta 30, IV>30%, 30-60d | IV alta + Delta ideal |
| **Venda Put** | Delta 35, PM atrativo | Desconto >5% + IV alta |
| **Trava Alta** | R/R 1:3+, spread <R$1 | R/R >0.33 + IV alta |

---

## 📊 **EXEMPLO REAL:**

### **Scanner encontra:**
```
TRAVA DE ALTA - PETR4
Score: 89/100

VENDE: 1.000x PETRP402 @ R$ 1,58
COMPRA: 1.000x PETRP412 @ R$ 1,10

Crédito líquido: R$ 480
Risco máximo: R$ 520
Retorno: 92%
```

### **Você:**
1. ✅ Analisa: "Bacana!"
2. 📋 Copia ordem
3. 💻 Executa no home broker
4. ✅ Marca "JÁ ENTREI"

### **Sistema monitora:**
```
Dia 1: Lucro 12%
Dia 2: Lucro 28%
Dia 3: Lucro 45%
Dia 4: Lucro 62% 🔥 FECHAR AGORA!
```

### **Telegram:**
```
🔥 ALERTA!

PETR4 Trava Alta
Lucro: 62% (meta 60%)

⚡ FECHAR POSIÇÃO AGORA!

Resultado: +R$ 297,60
```

---

## ❓ **FAQ:**

**P: Precisa de Profit Pro?**  
R: NÃO. Funciona com QUALQUER corretora B3.

**P: Executa automaticamente?**  
R: NÃO. Você decide e executa manual.

**P: Quanto custa?**  
R: R$ 0,00. Tudo grátis (Supabase free tier).

**P: Funciona com outros ativos?**  
R: SIM. Adicione em `scanner_opcoes.py` linha 19.

**P: Precisa ficar ligado 24/7?**  
R: NÃO. Acessa quando quiser pelo navegador.

**P: E se hospedar online?**  
R: Acessa de qualquer lugar (celular, tablet, etc).

---

## 🚀 **PRÓXIMOS PASSOS:**

1. ✅ Instalar (5 min)
2. ✅ Rodar dashboard
3. ✅ Testar com PETR4
4. ✅ Marcar primeira posição
5. ✅ Acompanhar até 60% lucro
6. ✅ Hospedar online (opcional)

---

## 📞 **SUPORTE:**

**Problemas instalação:**
- Verificar Python 3.8+
- Verificar credenciais Supabase
- Ver logs: terminal onde rodou `streamlit run`

**Sem oportunidades:**
- Normal se IV baixa no mercado
- Testar outros ativos
- Ajustar filtros em `scanner_opcoes.py`

**Erros Supabase:**
- Verificar se SQL foi executado
- Verificar credenciais no `.env`
- Ver logs no Supabase Dashboard

---

## 🎓 **BASEADO EM:**

✅ Curso RCO Jimmy Carvalho (51 aulas completas)  
✅ Validação CBOE 30 anos (1986-2016)  
✅ Estratégia delta 30 supera buy-and-hold  
✅ Taxa acerto 70-80% (vendas)  

---

**🤖 Sistema pronto para uso!**

*Encontra oportunidades reais de opções B3 baseadas na estratégia RCO validada.*
