import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, date
from pathlib import Path

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InChurch · Cobranças",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── LOGO ─────────────────────────────────────────────────────────────────────
LOGO_PATH = Path(__file__).parent / "logo_b64.txt"
LOGO_B64 = LOGO_PATH.read_text().strip() if LOGO_PATH.exists() else ""
LOGO_SRC = f"data:image/jpeg;base64,{LOGO_B64}" if LOGO_B64 else ""

# ── ESTILOS (fiéis ao HTML de referência) ─────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

  :root {
    --bg:#0f1117; --surface:#181c26; --surface2:#1e2333; --border:#2a2f42;
    --accent:#4f7cff; --green:#22c55e; --yellow:#f59e0b;
    --red:#ef4444; --orange:#f97316; --text:#e8eaf0; --muted:#6b7280;
    --radius:10px; --inchurch:#7cc243;
  }

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
  }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 0 !important; padding-bottom: 1rem !important; max-width: 100% !important; }
  section[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border) !important; }

  /* ── HEADER ── */
  .app-header {
    background: var(--surface); border-bottom: 1px solid var(--border);
    padding: 0 28px; height: 60px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 24px;
  }
  .header-logo { display: flex; align-items: center; gap: 10px; }
  .header-logo img { height: 28px; object-fit: contain; }
  .header-logo span { color: var(--muted); font-size: 13px; }
  .last-update { font-size:12px; color:var(--muted); background:var(--surface2); padding:5px 12px; border-radius:20px; border:1px solid var(--border); }
  .user-chip { background:var(--surface2); border:1px solid var(--border); border-radius:20px; padding:5px 14px; font-size:12px; display:flex; align-items:center; gap:7px; }
  .user-dot { width:8px; height:8px; background:var(--inchurch); border-radius:50%; }

  /* ── STATS ── */
  .stats-row { display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:20px; }
  .stat-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:16px 18px; transition:border-color .2s; }
  .stat-card:hover { border-color:var(--accent); }
  .stat-label { font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:var(--muted); margin-bottom:8px; }
  .stat-value { font-family:'Syne',sans-serif; font-size:26px; font-weight:700; }
  .stat-sub { font-size:11px; color:var(--muted); margin-top:4px; }
  .c-total { color:var(--text); } .c-pending { color:var(--red); }
  .c-contacted { color:var(--yellow); } .c-promise { color:var(--orange); } .c-paid { color:var(--green); }

  /* ── PENDÊNCIAS ── */
  .pend-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:12px 14px; display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:8px; }

  /* ── IMPORT ── */
  .import-zone { border:2px dashed var(--border); border-radius:var(--radius); padding:24px; text-align:center; background:var(--surface); }
  .import-zone h3 { font-family:'Syne',sans-serif; font-size:15px; margin-bottom:6px; color:var(--text); }
  .import-zone p { color:var(--muted); font-size:12px; margin:0; }
  .empty-icon { font-size:36px; margin-bottom:10px; }

  /* ── TABLE ── */
  .table-wrap { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); overflow:hidden; overflow-x:auto; }
  table { width:100%; border-collapse:collapse; min-width:900px; }
  thead th { background:var(--surface2); padding:11px 14px; text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.7px; color:var(--muted); font-weight:500; white-space:nowrap; border-bottom:1px solid var(--border); }
  tbody tr { border-bottom:1px solid var(--border); transition:background .15s; }
  tbody tr:last-child { border-bottom:none; }
  tbody tr:hover { background:rgba(255,255,255,.03); }
  tbody td { padding:10px 14px; font-size:13px; vertical-align:middle; color:var(--text); }
  .td-name { font-weight:500; max-width:180px; }
  .td-doc { color:var(--muted); font-size:11px; margin-top:2px; }
  .td-value { font-weight:600; white-space:nowrap; }

  /* ── BADGES ── */
  .badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; white-space:nowrap; }
  .badge-pending    { background:rgba(239,68,68,.15);  color:var(--red); }
  .badge-contacted  { background:rgba(245,158,11,.15); color:var(--yellow); }
  .badge-promise    { background:rgba(249,115,22,.15); color:var(--orange); }
  .badge-negotiating{ background:rgba(79,124,255,.15); color:var(--accent); }
  .badge-paid       { background:rgba(34,197,94,.15);  color:var(--green); }
  .top-badge { background:rgba(239,68,68,.2); color:#ff6b6b; font-size:10px; padding:2px 7px; border-radius:10px; font-weight:700; margin-right:4px; }
  .dias-hoje { background:rgba(34,197,94,.15);  color:#22c55e; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
  .dias-30   { background:rgba(245,158,11,.15); color:#f59e0b; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
  .dias-60   { background:rgba(249,115,22,.15); color:#f97316; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
  .dias-90   { background:rgba(239,68,68,.15);  color:#ef4444; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
  .dias-mais { background:rgba(139,0,0,.2);     color:#ff6b6b; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }

  /* ── BTN-EDIT (tabela) ── */
  .btn-edit { background:transparent; border:1px solid var(--border); border-radius:6px; color:var(--inchurch); padding:4px 10px; cursor:pointer; font-size:11px; font-family:'DM Sans',sans-serif; transition:all .15s; }
  .btn-edit:hover { background:rgba(124,194,67,.1); }

  /* ── EMPTY STATE ── */
  .empty-state { text-align:center; padding:60px 20px; }
  .empty-state h3 { font-family:'Syne',sans-serif; font-size:18px; margin-bottom:8px; color:var(--text); }
  .empty-state p { color:var(--muted); font-size:13px; }

  /* ── SECTION HEADER ── */
  .section-title { font-family:'Syne',sans-serif; font-weight:700; font-size:15px; display:flex; align-items:center; gap:8px; color:var(--text); margin-bottom:10px; }
  .count-badge { background:var(--red); color:white; font-size:11px; padding:2px 8px; border-radius:20px; font-weight:600; }

  /* ── Streamlit overrides ── */
  .stButton > button {
    background:var(--inchurch) !important; color:#1a1a1a !important;
    font-weight:700 !important; border:none !important; border-radius:8px !important;
    font-family:'DM Sans',sans-serif !important;
  }
  .stButton > button:hover { opacity:.88 !important; }

  .stTextInput input, .stTextArea textarea {
    background:var(--surface2) !important; color:var(--text) !important;
    border:1px solid var(--border) !important; border-radius:8px !important;
    font-family:'DM Sans',sans-serif !important;
  }
  .stTextInput input:focus, .stTextArea textarea:focus { border-color:var(--inchurch) !important; box-shadow:none !important; }
  .stTextInput label, .stTextArea label, .stSelectbox label, .stDateInput label {
    color:var(--muted) !important; font-size:11px !important;
    text-transform:uppercase !important; letter-spacing:.7px !important;
  }
  .stDateInput input { background:var(--surface2) !important; color:var(--text) !important; border:1px solid var(--border) !important; border-radius:8px !important; }

  div[data-baseweb="select"] > div { background:var(--surface2) !important; border-color:var(--border) !important; }
  div[data-baseweb="select"] span { color:var(--text) !important; }
  div[data-baseweb="popover"], div[data-baseweb="menu"] { background:var(--surface2) !important; border:1px solid var(--border) !important; }
  div[data-baseweb="menu"] li { color:var(--text) !important; }
  div[data-baseweb="menu"] li:hover { background:var(--border) !important; }

  .streamlit-expanderHeader { background:var(--surface) !important; color:var(--text) !important; border:1px solid var(--border) !important; border-radius:var(--radius) !important; font-family:'Syne',sans-serif !important; }
  .streamlit-expanderContent { background:var(--surface2) !important; border:1px solid var(--border) !important; border-top:none !important; }

  hr { border-color:var(--border) !important; margin:8px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── STORAGE ───────────────────────────────────────────────────────────────────
def get_store():
    if "store" not in st.session_state:
        st.session_state["store"] = {
            "usuarios": {}, "clientes": [],
            "historico": {}, "regularizados": [], "ultima_atualizacao": None,
        }
        admin_email = "priscila.oliveira@inchurch.com.br"
        uid = hashlib.md5(admin_email.encode()).hexdigest()
        st.session_state["store"]["usuarios"][uid] = {
            "nome": "Priscila Oliveira", "email": admin_email,
            "senha_hash": hashlib.sha256("inchurch2024".encode()).hexdigest(), "role": "admin"
        }
    return st.session_state["store"]

def hash_senha(s): return hashlib.sha256(s.encode()).hexdigest()

def login(email, senha):
    for uid, u in get_store()["usuarios"].items():
        if u["email"].lower() == email.lower() and u["senha_hash"] == hash_senha(senha):
            st.session_state.update({"user_uid": uid, "user_nome": u["nome"], "user_role": u["role"]})
            return True
    return False

def is_logged():    return "user_uid" in st.session_state
def current_uid():  return st.session_state.get("user_uid", "")
def current_nome(): return st.session_state.get("user_nome", "")
def current_role(): return st.session_state.get("user_role", "atendente")

def calc_dias_atraso(venc_str):
    if not venc_str: return None
    try:
        if "/" in str(venc_str):
            p = str(venc_str).split("/")
            d = date(int(p[2]), int(p[1]), int(p[0]))
        else:
            d = pd.to_datetime(venc_str).date()
        return max((date.today() - d).days, 0)
    except: return None

def dias_badge_html(dias):
    if dias is None: return "—"
    if dias == 0:    return '<span class="dias-hoje">Hoje</span>'
    if dias <= 30:   return f'<span class="dias-30">{dias}d</span>'
    if dias <= 60:   return f'<span class="dias-60">{dias}d</span>'
    if dias <= 90:   return f'<span class="dias-90">{dias}d</span>'
    return f'<span class="dias-mais">{dias}d</span>'

def status_badge_html(status):
    cls = {"pending":"badge-pending","contacted":"badge-contacted","promise":"badge-promise","negotiating":"badge-negotiating","paid":"badge-paid"}
    lbl = {"pending":"🔴 Sem contato","contacted":"🟡 Contactado","promise":"🟠 Prometeu pagar","negotiating":"🔵 Negociando","paid":"✅ Regularizado"}
    return f'<span class="badge {cls.get(status,"badge-pending")}">{lbl.get(status,"Sem contato")}</span>'

def fmt_moeda(v):
    try: return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except: return "—"

def parse_moeda(v):
    s = str(v).replace("R$","").replace(" ","").strip()
    if "," in s: s = s.replace(".","").replace(",",".")
    try: return float(s)
    except: return 0.0

def get_hist(cid):
    return get_store()["historico"].get(current_uid(), {}).get(cid, {})

def save_hist(cid, data):
    store = get_store(); uid = current_uid()
    if uid not in store["historico"]: store["historico"][uid] = {}
    store["historico"][uid][cid] = data

# ── RENDER HEADER ─────────────────────────────────────────────────────────────
def render_header():
    store = get_store()
    upd   = store.get("ultima_atualizacao") or "Nenhuma planilha importada"
    logo_tag = f'<img src="{LOGO_SRC}" alt="InChurch">' if LOGO_SRC else '<span style="font-family:Syne,sans-serif;font-weight:800;color:#7cc243;font-size:18px">InChurch</span>'
    role_badge = ""
    if current_role() == "admin":
        role_badge = '<span style="background:rgba(124,194,67,.15);color:#7cc243;font-size:10px;padding:2px 8px;border-radius:10px;font-weight:700;margin-left:4px">ADMIN</span>'
    st.markdown(f"""
    <div class="app-header">
      <div class="header-logo">{logo_tag}<span>· Cobranças</span></div>
      <div style="display:flex;align-items:center;gap:10px">
        <span class="last-update">Atualizado: {upd}</span>
        <div class="user-chip"><div class="user-dot"></div><span>{current_nome()}</span>{role_badge}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── TELA LOGIN ────────────────────────────────────────────────────────────────
def tela_login():
    logo_html = f'<img src="{LOGO_SRC}" style="height:44px;object-fit:contain;margin-bottom:28px" alt="InChurch">' if LOGO_SRC else '<div style="font-family:Syne,sans-serif;font-size:28px;font-weight:800;color:#7cc243;margin-bottom:28px">InChurch</div>'
    st.markdown(f"""
    <div style="min-height:85vh;display:flex;align-items:center;justify-content:center;
      background:radial-gradient(ellipse at 60% 40%,rgba(124,194,67,.08),transparent 60%),
                 radial-gradient(ellipse at 20% 80%,rgba(79,124,255,.08),transparent 50%),var(--bg)">
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:16px;
        padding:40px 36px;width:400px;max-width:95vw;text-align:center">
        {logo_html}
        <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:700;margin-bottom:6px;color:var(--text)">Controle de Cobranças</div>
        <div style="color:var(--muted);font-size:13px;margin-bottom:28px">Entre com seu e-mail e senha para acessar</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            email  = st.text_input("E-mail", placeholder="seu@inchurch.com.br")
            senha  = st.text_input("Senha", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Entrar", use_container_width=True)
            if submit:
                if login(email, senha): st.rerun()
                else: st.error("E-mail ou senha incorretos.")
        st.markdown('<div style="text-align:center;color:#6b7280;font-size:11px;margin-top:12px">Primeiro acesso? Senha padrão: <b>inchurch2024</b></div>', unsafe_allow_html=True)

# ── TELA IMPORTAR ─────────────────────────────────────────────────────────────
def tela_importar():
    store = get_store()
    render_header()

    # Cabeçalho + botões
    col_h1, col_h2, col_h3 = st.columns([1, 1, 6])
    with col_h1:
        if store["clientes"] and st.button("← Voltar", use_container_width=True):
            st.session_state["tela"] = "principal"; st.rerun()
    with col_h2:
        if st.button("Sair", use_container_width=True):
            for k in ["user_uid","user_nome","user_role","tela"]: st.session_state.pop(k, None)
            st.rerun()

    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px">
      <div class="import-zone">
        <div class="empty-icon">📋</div>
        <h3>Planilha 1 · Inadimplência</h3>
        <p>Cód. cliente · Nome · CPF/CNPJ · Vencimento</p>
      </div>
      <div class="import-zone">
        <div class="empty-icon">💰</div>
        <h3>Planilha 2 · Saldo e Parcelas</h3>
        <p>Cód. cliente · Saldo · Qtd. parcelas · Telefone</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1: f1 = st.file_uploader("Planilha 1 · Inadimplência", type=["xlsx","xls","csv"], key="up1")
    with col2: f2 = st.file_uploader("Planilha 2 · Saldo e Parcelas", type=["xlsx","xls","csv"], key="up2")

    if not (f1 and f2): return

    try:
        df1 = pd.read_excel(f1) if f1.name.endswith(("xlsx","xls")) else pd.read_csv(f1)
        df2 = pd.read_excel(f2) if f2.name.endswith(("xlsx","xls")) else pd.read_csv(f2)
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}"); return

    st.markdown('<hr><div style="font-family:Syne,sans-serif;font-size:15px;font-weight:700;margin-bottom:12px;color:var(--text)">Confirme o mapeamento das colunas</div>', unsafe_allow_html=True)

    cols1 = ["(ignorar)"] + list(df1.columns)
    cols2 = ["(ignorar)"] + list(df2.columns)

    def guess(cols, kws):
        for kw in kws:
            for c in cols:
                if kw in str(c).lower(): return c
        return "(ignorar)"

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div style="color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px">Planilha 1</div>', unsafe_allow_html=True)
        m_cod1  = st.selectbox("Código do cliente *", cols1, index=cols1.index(guess(df1.columns,["cód","cod","código","id do client","id_client"])) if guess(df1.columns,["cód","cod","código","id do client","id_client"]) in cols1 else 0, key="m_cod1")
        m_nome  = st.selectbox("Nome do cliente *",   cols1, index=cols1.index(guess(df1.columns,["st_nome_sac","nome","cliente","sacado"])) if guess(df1.columns,["st_nome_sac","nome","cliente","sacado"]) in cols1 else 0, key="m_nome")
        m_doc   = st.selectbox("CPF / CNPJ",          cols1, index=cols1.index(guess(df1.columns,["cpf","cnpj","cgc","doc"])) if guess(df1.columns,["cpf","cnpj","cgc","doc"]) in cols1 else 0, key="m_doc")
        m_venc  = st.selectbox("Vencimento",          cols1, index=cols1.index(guess(df1.columns,["dt_venc","venc","data_venc"])) if guess(df1.columns,["dt_venc","venc","data_venc"]) in cols1 else 0, key="m_venc")
        m_parc1 = st.selectbox("Qtd. Cobranças (Pl.1)", cols1, index=cols1.index(guess(df1.columns,["quantidade_cobrancas","quantidade_mensalidades","cobr","parcela","parc","quant"])) if guess(df1.columns,["quantidade_cobrancas","quantidade_mensalidades","cobr","parcela","parc","quant"]) in cols1 else 0, key="m_parc1")
    with c2:
        st.markdown('<div style="color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px">Planilha 2</div>', unsafe_allow_html=True)
        m_cod2  = st.selectbox("Código do cliente *", cols2, index=cols2.index(guess(df2.columns,["cód","cod","código","id do client","id_client"])) if guess(df2.columns,["cód","cod","código","id do client","id_client"]) in cols2 else 0, key="m_cod2")
        m_valor = st.selectbox("Saldo / Valor *",     cols2, index=cols2.index(guess(df2.columns,["vl_total_recb","vl_total","vl_emitido","saldo","valor","débito"])) if guess(df2.columns,["vl_total_recb","vl_total","vl_emitido","saldo","valor","débito"]) in cols2 else 0, key="m_valor")
        m_parc  = st.selectbox("Qtd. Parcelas (Pl.2)", cols2, index=0, key="m_parc")
        m_tel   = st.selectbox("Telefone",            cols2, index=cols2.index(guess(df2.columns,["st_telefone","celular","telefone","fone"])) if guess(df2.columns,["st_telefone","celular","telefone","fone"]) in cols2 else 0, key="m_tel")
        m_venc2 = st.selectbox("Vencimento (Pl.2)",   cols2, index=cols2.index(guess(df2.columns,["dt_vencimento_recb","dt_venc","venc","data_venc"])) if guess(df2.columns,["dt_vencimento_recb","dt_venc","venc","data_venc"]) in cols2 else 0, key="m_venc2")

    if st.button("✅ Confirmar e Importar", use_container_width=True):
        idx2 = {}
        for _, row in df2.iterrows():
            cod = str(row.get(m_cod2,"")).strip() if m_cod2 != "(ignorar)" else ""
            if cod: idx2.setdefault(cod, []).append(row)

        clientes_novos = []
        for i, row in df1.iterrows():
            cod  = str(row.get(m_cod1,"")).strip() if m_cod1 != "(ignorar)" else str(i)
            nome = str(row.get(m_nome,"")).strip() if m_nome != "(ignorar)" else f"Cliente {i+1}"
            doc  = str(row.get(m_doc,"")).strip()  if m_doc  != "(ignorar)" else ""
            cid  = cod or doc or f"cli_{i}"

            venc = ""
            if m_venc != "(ignorar)" and pd.notna(row.get(m_venc)):
                v = row[m_venc]
                venc = v.strftime("%d/%m/%Y") if isinstance(v, (datetime, pd.Timestamp)) else str(v)

            parcelas = 0
            if m_parc1 != "(ignorar)":
                try: parcelas = int(row.get(m_parc1, 0) or 0)
                except: pass

            rows2 = idx2.get(cod, [])
            valor = 0.0; telefone = ""; venc2_val = ""
            for r2 in rows2:
                if m_valor != "(ignorar)": valor += parse_moeda(r2.get(m_valor, 0))
                if m_parc  != "(ignorar)":
                    try: parcelas += int(r2.get(m_parc, 0) or 0)
                    except: pass
                if m_tel != "(ignorar)" and not telefone:
                    telefone = str(r2.get(m_tel,"")).strip()
                if not venc and m_venc2 != "(ignorar)" and not venc2_val:
                    v2 = r2.get(m_venc2)
                    if v2 is not None and pd.notna(v2):
                        venc2_val = v2.strftime("%d/%m/%Y") if isinstance(v2, (datetime, pd.Timestamp)) else str(v2)

            if not venc and venc2_val: venc = venc2_val

            clientes_novos.append({
                "id": cid, "cod": cod, "nome": nome, "doc": doc,
                "valor": valor, "parcelas": parcelas,
                "vencimento": venc, "telefone": telefone,
                "dias_atraso": calc_dias_atraso(venc),
            })

        ids_novos = {c["id"] for c in clientes_novos}
        removidos = [c for c in store["clientes"] if c["id"] not in ids_novos]
        hoje_str  = date.today().strftime("%d/%m/%Y")
        for c in removidos:
            store["regularizados"].append({
                "id": c["id"], "nome": c["nome"], "doc": c.get("doc",""),
                "valor": c["valor"], "atendente": current_nome(), "data": hoje_str, "tipo": "auto"
            })

        store["clientes"] = clientes_novos
        store["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.success(f"✓ {len(clientes_novos)} clientes importados! {len(removidos)} regularizados automaticamente.")
        st.session_state["tela"] = "principal"
        st.rerun()

# ── PAINEL PRINCIPAL ──────────────────────────────────────────────────────────
def tela_principal():
    store    = get_store()
    clientes = store["clientes"]
    role     = current_role()

    render_header()

    # Botões de ação (header area)
    col_h1, col_h2, col_h3, col_h4 = st.columns([1, 1, 1, 5])
    with col_h1:
        if st.button("↑ Atualizar Planilhas", use_container_width=True):
            st.session_state["tela"] = "importar"; st.rerun()
    with col_h2:
        export_clicked = st.button("⬇ Exportar CSV", use_container_width=True)
    with col_h3:
        if st.button("Sair", use_container_width=True):
            for k in ["user_uid","user_nome","user_role","tela"]: st.session_state.pop(k, None)
            st.rerun()

    if export_clicked and clientes:
        rows = []
        for c in clientes:
            h  = get_hist(c["id"])
            sl = {"pending":"Sem contato","contacted":"Contactado","promise":"Prometeu pagar","negotiating":"Negociando","paid":"Regularizado"}
            rows.append([h.get("atendente",""), c["nome"], c.get("doc",""), c["valor"],
                         c.get("parcelas",""), c.get("vencimento",""), c.get("dias_atraso",""),
                         sl.get(h.get("status","pending"),""), h.get("lastContact",""), h.get("notes","")])
        df_exp = pd.DataFrame(rows, columns=["Atendente","Nome","CPF/CNPJ","Saldo","Parcelas","Vencimento","Dias Atraso","Status","Último Contato","Observações"])
        csv = df_exp.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 Baixar", csv,
            f"cobrancas_{current_nome().replace(' ','_')}_{date.today()}.csv", "text/csv")

    st.markdown("")

    # ── Stats ──
    total = len(clientes)
    pending = contacted = promise = 0
    for c in clientes:
        s = get_hist(c["id"]).get("status","pending")
        if s == "pending":                   pending   += 1
        elif s == "contacted":               contacted += 1
        elif s in ("promise","negotiating"): promise   += 1

    hoje_str = date.today().strftime("%d/%m/%Y")
    reg_hoje = len([r for r in store["regularizados"] if r.get("data") == hoje_str])

    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-card"><div class="stat-label">Total Inadimplentes</div><div class="stat-value c-total">{total}</div><div class="stat-sub">clientes</div></div>
      <div class="stat-card"><div class="stat-label">Sem Contato</div><div class="stat-value c-pending">{pending}</div><div class="stat-sub">aguardando</div></div>
      <div class="stat-card"><div class="stat-label">Contactado</div><div class="stat-value c-contacted">{contacted}</div><div class="stat-sub">em acompanhamento</div></div>
      <div class="stat-card"><div class="stat-label">Prometeu Pagar</div><div class="stat-value c-promise">{promise}</div><div class="stat-sub">aguardando pagamento</div></div>
      <div class="stat-card"><div class="stat-label">Regularizados Hoje</div><div class="stat-value c-paid">{reg_hoje}</div><div class="stat-sub">clique para ver histórico</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Pendências ──
    pendencias = []
    for c in clientes:
        h = get_hist(c["id"]); s = h.get("status","pending")
        if s == "paid": continue
        hoje = date.today()
        if s == "promise" and h.get("promiseDate"):
            try:
                p = h["promiseDate"].split("/"); dt = date(int(p[2]),int(p[1]),int(p[0]))
                if dt <= hoje: pendencias.append((c,h,"promise",f"Prometeu pagar em {h['promiseDate']}")); continue
            except: pass
        if h.get("retorno"):
            try:
                p = h["retorno"].split("/"); dt = date(int(p[2]),int(p[1]),int(p[0]))
                if dt <= hoje: pendencias.append((c,h,"retorno",f"Retorno agendado para {h['retorno']}")); continue
            except: pass
        if h.get("lastContact"):
            try:
                p = h["lastContact"].split("/"); dt = date(int(p[2]),int(p[1]),int(p[0]))
                diff = (hoje - dt).days
                if diff >= 5: pendencias.append((c,h,"semcontato",f"Sem contato há {diff} dias"))
            except: pass

    if pendencias:
        color_map = {"promise":"#f97316","retorno":"#4f7cff","semcontato":"#f59e0b"}
        icon_map  = {"promise":"🟠","retorno":"📞","semcontato":"⚠️"}
        st.markdown(f'<div class="section-title">🔔 Pendências do Dia <span class="count-badge">{len(pendencias)}</span></div>', unsafe_allow_html=True)
        cols_pend = st.columns(min(3, len(pendencias)))
        for i, (c, h, tipo, msg) in enumerate(pendencias[:9]):
            with cols_pend[i % 3]:
                st.markdown(f"""
                <div class="pend-card" style="border-left:3px solid {color_map[tipo]}">
                  <div style="flex:1;min-width:0">
                    <div style="font-weight:600;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{icon_map[tipo]} {c['nome']}</div>
                    <div style="font-size:11px;color:var(--muted);margin-top:3px">{msg}</div>
                    <div style="font-size:11px;color:var(--muted)">{fmt_moeda(c['valor'])}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if role != "gestor":
                    if st.button("✏ Atender", key=f"pend_{i}_{c['id']}", use_container_width=True):
                        st.session_state["editing_id"] = c["id"]; st.session_state["show_edit"] = True; st.rerun()
        st.markdown("")

    # ── Filtros ──
    fc1, fc2, fc3 = st.columns([3, 2, 2])
    with fc1:
        busca = st.text_input("", placeholder="🔍 Buscar por nome ou CPF/CNPJ...", label_visibility="collapsed", key="busca_input")
    with fc2:
        filtro_status = st.selectbox("", ["Todos","Sem contato","Contactado","Prometeu pagar","Negociando"], label_visibility="collapsed", key="filtro_status")
    with fc3:
        filtro_atraso = st.selectbox("", ["Todos","1–30 dias","31–60 dias","61–90 dias","+90 dias"], label_visibility="collapsed", key="filtro_atraso")

    status_map = {"Sem contato":"pending","Contactado":"contacted","Prometeu pagar":"promise","Negociando":"negotiating"}

    df_cli = pd.DataFrame(clientes) if clientes else pd.DataFrame()
    if df_cli.empty:
        st.markdown("""<div class="table-wrap"><div class="empty-state"><div class="empty-icon">📂</div><h3>Nenhum dado carregado</h3><p>Use ↑ Atualizar Planilhas para importar</p></div></div>""", unsafe_allow_html=True)
        _render_rodape(store, clientes, role); return

    df_cli["_status"]      = df_cli["id"].apply(lambda i: get_hist(i).get("status","pending"))
    df_cli["_lastContact"] = df_cli["id"].apply(lambda i: get_hist(i).get("lastContact",""))
    df_cli["_atendente"]   = df_cli["id"].apply(lambda i: get_hist(i).get("atendente",""))
    df_cli["_notes"]       = df_cli["id"].apply(lambda i: get_hist(i).get("notes",""))
    df_cli = df_cli[df_cli["_status"] != "paid"]

    if busca:
        mask = df_cli.apply(lambda r: busca.lower() in str(r.get("nome","")).lower() or busca.lower() in str(r.get("doc","")).lower(), axis=1)
        df_cli = df_cli[mask]
    if filtro_status != "Todos": df_cli = df_cli[df_cli["_status"] == status_map.get(filtro_status,"pending")]
    if filtro_atraso == "1–30 dias":   df_cli = df_cli[df_cli["dias_atraso"].apply(lambda d: d is not None and 1<=d<=30)]
    elif filtro_atraso == "31–60 dias": df_cli = df_cli[df_cli["dias_atraso"].apply(lambda d: d is not None and 31<=d<=60)]
    elif filtro_atraso == "61–90 dias": df_cli = df_cli[df_cli["dias_atraso"].apply(lambda d: d is not None and 61<=d<=90)]
    elif filtro_atraso == "+90 dias":   df_cli = df_cli[df_cli["dias_atraso"].apply(lambda d: d is not None and d>90)]

    top10_ids = set(pd.DataFrame(clientes).nlargest(10,"valor")["id"].tolist() if clientes else [])

    st.markdown(f'<div style="font-size:12px;color:var(--muted);margin-bottom:8px"><b style="color:var(--text)">{len(df_cli)}</b> clientes encontrados</div>', unsafe_allow_html=True)

    # Tabela
    rows_html = ""
    for row_idx, (_, row) in enumerate(df_cli.iterrows()):
        is_top     = row["id"] in top10_ids
        row_style  = "border-left:3px solid rgba(239,68,68,.5);background:rgba(239,68,68,.04)" if is_top else ""
        top_tag    = '<span class="top-badge">★ TOP</span>' if is_top else ""
        valor_color= "#ff6b6b" if is_top else "var(--text)"
        parc       = f'<span class="badge" style="background:rgba(79,124,255,.15);color:var(--accent)">{int(row["parcelas"])}x</span>' if row.get("parcelas") else "—"
        notes_full = str(row["_notes"] or "")
        notes_disp = (notes_full[:50]+"...") if len(notes_full)>50 else (notes_full or "—")
        rows_html += f"""
        <tr style="{row_style}">
          <td class="td-name">{top_tag}{row['nome']}<div class="td-doc">{row.get('doc','')}</div></td>
          <td class="td-value" style="color:{valor_color}">{fmt_moeda(row['valor'])}</td>
          <td style="text-align:center">{parc}</td>
          <td style="font-size:12px;color:var(--muted)">{row.get('vencimento','') or '—'}</td>
          <td>{dias_badge_html(row.get('dias_atraso'))}</td>
          <td style="font-size:12px;color:var(--muted)">{row.get('telefone','') or '—'}</td>
          <td>{status_badge_html(row['_status'])}</td>
          <td style="font-size:12px;color:var(--muted)">{row['_lastContact'] or '—'}</td>
          <td style="font-size:12px;color:var(--muted)">{row['_atendente'] or '—'}</td>
          <td><span style="font-size:12px;color:var(--muted);max-width:180px;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{notes_full}">{notes_disp}</span></td>
          <td>{"<span style='font-size:11px;color:var(--muted)'>—</span>" if role=='gestor' else f'<span style="font-size:11px;color:var(--inchurch);cursor:pointer">✏ Editar</span>'}</td>
        </tr>"""

    st.markdown(f"""
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Cliente</th><th>Saldo Total</th><th>Parcelas</th>
          <th>Vencimento</th><th>Atraso</th><th>Telefone</th>
          <th>Status</th><th>Último Contato</th><th>Atendente</th>
          <th>Observações</th><th>Ações</th>
        </tr></thead>
        <tbody>
          {rows_html if rows_html else '<tr><td colspan="11"><div class="empty-state"><div class="empty-icon">🔍</div><h3>Nenhum resultado</h3><p>Ajuste os filtros</p></div></td></tr>'}
        </tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    # Botões de edição Streamlit (um por linha, abaixo da tabela)
    if role != "gestor" and not df_cli.empty:
        st.markdown('<div style="margin-top:4px;font-size:11px;color:var(--muted)">Selecione o cliente para editar:</div>', unsafe_allow_html=True)
        btn_cols = st.columns(min(5, len(df_cli)))
        for row_idx, (_, row) in enumerate(df_cli.head(50).iterrows()):
            col_idx = row_idx % len(btn_cols)
            with btn_cols[col_idx]:
                if st.button(f"✏ {row['nome'][:20]}", key=f"e_{row_idx}_{row['id']}", help=row['nome'], use_container_width=True):
                    st.session_state["editing_id"] = row["id"]; st.session_state["show_edit"] = True; st.rerun()

    _render_rodape(store, clientes, role)

    # ── Modal de edição (sidebar) ──
    if st.session_state.get("show_edit") and st.session_state.get("editing_id"):
        eid     = st.session_state["editing_id"]
        cliente = next((c for c in clientes if c["id"] == eid), None)
        if cliente:
            h = get_hist(eid)
            with st.sidebar:
                st.markdown(f"""
                <div style="margin-bottom:16px">
                  <div style="font-family:Syne,sans-serif;font-size:17px;font-weight:700;color:var(--text)">{cliente['nome']}</div>
                  <div style="font-size:12px;color:var(--muted);margin-top:4px">{cliente.get('doc','')} · {fmt_moeda(cliente['valor'])} · {cliente.get('parcelas',0)} parcela(s)</div>
                </div>
                <hr>
                """, unsafe_allow_html=True)

                status_opts = {"🔴 Sem contato":"pending","🟡 Contactado":"contacted",
                               "🟠 Prometeu pagar":"promise","🔵 Negociando":"negotiating","✅ Regularizado":"paid"}
                status_sel = st.selectbox("Status de Cobrança", list(status_opts.keys()),
                    index=list(status_opts.values()).index(h.get("status","pending")))

                last_contact = st.date_input("Data do Último Contato",
                    value=datetime.strptime(h["lastContact"],"%d/%m/%Y").date() if h.get("lastContact") else date.today())
                retorno_date = st.date_input("📅 Agendar Retorno",
                    value=datetime.strptime(h["retorno"],"%d/%m/%Y").date() if h.get("retorno") else None,
                    min_value=date.today())
                promise_date = None
                if status_opts[status_sel] == "promise":
                    promise_date = st.date_input("📅 Data que prometeu pagar",
                        value=datetime.strptime(h["promiseDate"],"%d/%m/%Y").date() if h.get("promiseDate") else date.today())

                notes = st.text_area("Observações / Anotações", value=h.get("notes",""),
                    placeholder="Ex: Cliente prometeu pagar até sexta...")
                st.text_input("Atendente", value=current_nome(), disabled=True)

                col_s, col_c = st.columns(2)
                with col_s:
                    if st.button("💾 Salvar", use_container_width=True):
                        prev = h.get("status","pending"); new = status_opts[status_sel]
                        save_hist(eid, {
                            "status": new, "lastContact": last_contact.strftime("%d/%m/%Y"),
                            "retorno": retorno_date.strftime("%d/%m/%Y") if retorno_date else "",
                            "promiseDate": promise_date.strftime("%d/%m/%Y") if promise_date else "",
                            "notes": notes, "atendente": current_nome()
                        })
                        if new == "paid" and prev != "paid":
                            store["regularizados"].append({
                                "id": eid, "nome": cliente["nome"], "doc": cliente.get("doc",""),
                                "valor": cliente["valor"], "atendente": current_nome(),
                                "data": date.today().strftime("%d/%m/%Y"), "tipo": "manual"
                            })
                            st.success("✅ Regularizado!")
                        else:
                            st.success("Atendimento salvo!")
                        st.session_state["show_edit"] = False; st.session_state["editing_id"] = None; st.rerun()
                with col_c:
                    if st.button("✕ Fechar", use_container_width=True):
                        st.session_state["show_edit"] = False; st.session_state["editing_id"] = None; st.rerun()

def _render_rodape(store, clientes, role):
    st.markdown('<hr>', unsafe_allow_html=True)
    col_r1, col_r2 = st.columns([1, 4])
    with col_r2:
        if st.button("📋 Ver histórico de regularizados"):
            st.session_state["show_hist"] = not st.session_state.get("show_hist", False)

    if st.session_state.get("show_hist"):
        reg = store["regularizados"]
        if not reg:
            st.info("Nenhum cliente regularizado ainda.")
        else:
            df_reg = pd.DataFrame(reg)
            df_reg["tipo_fmt"]  = df_reg["tipo"].map({"auto":"🟢 Automático","manual":"🔵 Manual"})
            df_reg["valor_fmt"] = df_reg["valor"].apply(fmt_moeda)
            st.dataframe(df_reg[["data","nome","doc","valor_fmt","atendente","tipo_fmt"]].rename(columns={
                "data":"Data","nome":"Cliente","doc":"CPF/CNPJ","valor_fmt":"Valor","atendente":"Atendente","tipo_fmt":"Tipo"
            }), use_container_width=True, hide_index=True)

    if role == "admin":
        st.markdown('<hr>', unsafe_allow_html=True)
        with st.expander("⚙️ Gerenciar Usuários"):
            store2 = get_store()
            st.markdown("**Criar novo usuário:**")
            cu1, cu2, cu3, cu4 = st.columns(4)
            with cu1: u_nome  = st.text_input("Nome completo", key="u_nome")
            with cu2: u_email = st.text_input("E-mail", key="u_email")
            with cu3: u_senha = st.text_input("Senha", type="password", key="u_senha")
            with cu4: u_role  = st.selectbox("Perfil", ["atendente","gestor","admin"], key="u_role")
            if st.button("➕ Criar usuário"):
                if u_nome and u_email and u_senha:
                    uid = hashlib.md5(u_email.encode()).hexdigest()
                    store2["usuarios"][uid] = {"nome":u_nome,"email":u_email,"senha_hash":hash_senha(u_senha),"role":u_role}
                    st.success(f"Usuário {u_nome} criado!")
                else:
                    st.error("Preencha todos os campos.")
            st.markdown("**Usuários cadastrados:**")
            for uid, u in store2["usuarios"].items():
                st.markdown(f'<div style="font-size:13px;padding:4px 0;color:var(--text)">• <b>{u["nome"]}</b> <span style="color:var(--muted)">({u["email"]})</span> — <span style="color:var(--inchurch)">{u["role"]}</span></div>', unsafe_allow_html=True)

# ── ROTEADOR ──────────────────────────────────────────────────────────────────
def main():
    if not is_logged():
        tela_login(); return
    store = get_store()
    tela  = st.session_state.get("tela", "principal")
    if not store["clientes"] or tela == "importar":
        tela_importar()
    else:
        st.session_state["tela"] = "principal"
        tela_principal()

if __name__ == "__main__":
    main()
