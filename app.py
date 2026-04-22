import streamlit as st
import pandas as pd
import json
import hashlib
from datetime import datetime, date, timedelta
import io
import base64
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

# ── ESTILOS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

  /* Esconde elementos padrão do Streamlit */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }

  /* Cards de métricas */
  .metric-card {
    background: #181c26; border: 1px solid #2a2f42; border-radius: 10px;
    padding: 16px 18px; text-align: center;
  }
  .metric-label { font-size: 11px; text-transform: uppercase; letter-spacing: .8px; color: #6b7280; margin-bottom: 6px; }
  .metric-value { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 700; }
  .metric-sub   { font-size: 11px; color: #6b7280; margin-top: 4px; }

  /* Badges de status */
  .badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
  .badge-pending    { background:rgba(239,68,68,.15);  color:#ef4444; }
  .badge-contacted  { background:rgba(245,158,11,.15); color:#f59e0b; }
  .badge-promise    { background:rgba(249,115,22,.15); color:#f97316; }
  .badge-negotiating{ background:rgba(79,124,255,.15); color:#4f7cff; }
  .badge-paid       { background:rgba(34,197,94,.15);  color:#22c55e; }

  /* Pendências */
  .pend-card {
    background:#181c26; border:1px solid #2a2f42; border-radius:10px;
    padding:12px 16px; margin-bottom:8px;
  }
  .pend-promise  { border-left:3px solid #f97316; }
  .pend-retorno  { border-left:3px solid #4f7cff; }
  .pend-semcont  { border-left:3px solid #f59e0b; }

  /* TOP badge */
  .top-badge { background:rgba(239,68,68,.2); color:#ff6b6b; font-size:10px; padding:2px 7px; border-radius:10px; font-weight:700; }

  /* Linha TOP */
  .top-row { border-left:3px solid rgba(239,68,68,.5) !important; background:rgba(239,68,68,.04) !important; }

  /* Login */
  .login-container { max-width:400px; margin:80px auto; }

  /* Header */
  .app-header {
    background:#181c26; border-bottom:1px solid #2a2f42; padding:12px 24px;
    display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;
    border-radius:10px;
  }

  /* Dias badge */
  .dias-hoje { background:rgba(34,197,94,.15); color:#22c55e; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
  .dias-30   { background:rgba(245,158,11,.15); color:#f59e0b; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
  .dias-60   { background:rgba(249,115,22,.15); color:#f97316; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
  .dias-90   { background:rgba(239,68,68,.15);  color:#ef4444; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
  .dias-mais { background:rgba(139,0,0,.2); color:#ff6b6b; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }

  .stButton > button {
    background: #7cc243 !important; color: #1a1a1a !important;
    font-weight: 700 !important; border: none !important; border-radius: 8px !important;
  }
  .stButton > button:hover { opacity: .88 !important; }
</style>
""", unsafe_allow_html=True)

# ── STORAGE (Streamlit session + st.session_state persistido) ─────────────────
def get_store():
    """Retorna o dicionário de dados persistido via st.session_state."""
    if "store" not in st.session_state:
        st.session_state["store"] = {
            "usuarios": {},       # uid -> {nome, email, senha_hash, role}
            "clientes": [],       # lista de clientes
            "historico": {},      # uid_usuario -> {id_cliente: {...}}
            "regularizados": [],  # lista de regularizados
            "ultima_atualizacao": None,
        }
        # Cria admin padrão se não existir
        admin_email = "priscila.oliveira@inchurch.com.br"
        admin_hash  = hashlib.sha256("inchurch2024".encode()).hexdigest()
        uid = hashlib.md5(admin_email.encode()).hexdigest()
        st.session_state["store"]["usuarios"][uid] = {
            "nome": "Priscila Oliveira", "email": admin_email,
            "senha_hash": admin_hash, "role": "admin"
        }
    return st.session_state["store"]

def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

# ── AUTH ──────────────────────────────────────────────────────────────────────
def login(email, senha):
    store = get_store()
    for uid, u in store["usuarios"].items():
        if u["email"].lower() == email.lower() and u["senha_hash"] == hash_senha(senha):
            st.session_state["user_uid"]  = uid
            st.session_state["user_nome"] = u["nome"]
            st.session_state["user_role"] = u["role"]
            return True
    return False

def is_logged():
    return "user_uid" in st.session_state

def current_uid():
    return st.session_state.get("user_uid","")

def current_nome():
    return st.session_state.get("user_nome","")

def current_role():
    return st.session_state.get("user_role","atendente")

# ── HELPERS ───────────────────────────────────────────────────────────────────
def calc_dias_atraso(venc_str):
    if not venc_str:
        return None
    try:
        if "/" in str(venc_str):
            p = str(venc_str).split("/")
            d = date(int(p[2]), int(p[1]), int(p[0]))
        else:
            d = pd.to_datetime(venc_str).date()
        diff = (date.today() - d).days
        return max(diff, 0)
    except:
        return None

def dias_badge_html(dias):
    if dias is None:
        return "—"
    if dias == 0:
        return '<span class="dias-hoje">Hoje</span>'
    if dias <= 30:
        return f'<span class="dias-30">{dias}d</span>'
    if dias <= 60:
        return f'<span class="dias-60">{dias}d</span>'
    if dias <= 90:
        return f'<span class="dias-90">{dias}d</span>'
    return f'<span class="dias-mais">{dias}d</span>'

def status_badge_html(status):
    cls_map = {"pending":"badge-pending","contacted":"badge-contacted",
               "promise":"badge-promise","negotiating":"badge-negotiating","paid":"badge-paid"}
    lbl_map = {"pending":"🔴 Sem contato","contacted":"🟡 Contactado",
               "promise":"🟠 Prometeu pagar","negotiating":"🔵 Negociando","paid":"✅ Regularizado"}
    cls = cls_map.get(status, "badge-pending")
    lbl = lbl_map.get(status, "Sem contato")
    return f'<span class="badge {cls}">{lbl}</span>'

def fmt_moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except:
        return "—"

def parse_moeda(v):
    s = str(v).replace("R$","").replace(" ","").strip()
    if "," in s:
        s = s.replace(".","").replace(",",".")
    try:
        return float(s)
    except:
        return 0.0

def get_hist(cliente_id):
    store = get_store()
    uid   = current_uid()
    return store["historico"].get(uid, {}).get(cliente_id, {})

def save_hist(cliente_id, data):
    store = get_store()
    uid   = current_uid()
    if uid not in store["historico"]:
        store["historico"][uid] = {}
    store["historico"][uid][cliente_id] = data

# ── TELA DE LOGIN ─────────────────────────────────────────────────────────────
def tela_login():
    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        if LOGO_SRC:
            st.markdown(f'<div style="text-align:center;margin-bottom:20px"><img src="{LOGO_SRC}" style="height:48px"></div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-family:Syne,sans-serif;font-size:22px;font-weight:700;margin-bottom:4px">Controle de Cobranças</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#6b7280;font-size:13px;margin-bottom:24px">Entre com seu e-mail e senha</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("E-mail", placeholder="seu@inchurch.com.br")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Entrar", use_container_width=True)
            if submit:
                if login(email, senha):
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")

        st.markdown('<div style="text-align:center;color:#6b7280;font-size:11px;margin-top:16px">Primeiro acesso? Senha padrão: <b>inchurch2024</b></div>', unsafe_allow_html=True)

# ── IMPORTAR PLANILHAS ────────────────────────────────────────────────────────
def tela_importar():
    store = get_store()
    st.markdown("### 📊 Importar Planilhas")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Planilha 1 · Inadimplência**")
        st.caption("Cód. cliente · Nome · CPF/CNPJ · Vencimento")
        f1 = st.file_uploader("Planilha 1", type=["xlsx","xls","csv"], key="up1", label_visibility="collapsed")

    with col2:
        st.markdown("**Planilha 2 · Saldo e Parcelas**")
        st.caption("Cód. cliente · Saldo · Qtd. parcelas · Telefone")
        f2 = st.file_uploader("Planilha 2", type=["xlsx","xls","csv"], key="up2", label_visibility="collapsed")

    if f1 and f2:
        try:
            df1 = pd.read_excel(f1) if f1.name.endswith(("xlsx","xls")) else pd.read_csv(f1)
            df2 = pd.read_excel(f2) if f2.name.endswith(("xlsx","xls")) else pd.read_csv(f2)
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
            return

        st.markdown("---")
        st.markdown("**Confirme o mapeamento das colunas:**")

        cols1 = ["(ignorar)"] + list(df1.columns)
        cols2 = ["(ignorar)"] + list(df2.columns)

        def guess(cols, kws):
            for kw in kws:
                for c in cols:
                    if kw in str(c).lower():
                        return c
            return "(ignorar)"

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("*Planilha 1*")
            m_cod1  = st.selectbox("Código do cliente*", cols1, index=cols1.index(guess(df1.columns,["cód","cod","id do client","id_client"])) if guess(df1.columns,["cód","cod","id do client","id_client"]) in cols1 else 0, key="m_cod1")
            m_nome  = st.selectbox("Nome do cliente*",   cols1, index=cols1.index(guess(df1.columns,["nome","cliente","sacado"])) if guess(df1.columns,["nome","cliente","sacado"]) in cols1 else 0, key="m_nome")
            m_doc   = st.selectbox("CPF/CNPJ",           cols1, index=cols1.index(guess(df1.columns,["cpf","cnpj","doc"])) if guess(df1.columns,["cpf","cnpj","doc"]) in cols1 else 0, key="m_doc")
            m_venc  = st.selectbox("Vencimento",         cols1, index=cols1.index(guess(df1.columns,["venc","data"])) if guess(df1.columns,["venc","data"]) in cols1 else 0, key="m_venc")

        with c2:
            st.markdown("*Planilha 2*")
            m_cod2  = st.selectbox("Código do cliente*", cols2, index=cols2.index(guess(df2.columns,["cód","cod","id do client","id_client"])) if guess(df2.columns,["cód","cod","id do client","id_client"]) in cols2 else 0, key="m_cod2")
            m_valor = st.selectbox("Saldo/Valor*",       cols2, index=cols2.index(guess(df2.columns,["saldo","valor","débito"])) if guess(df2.columns,["saldo","valor","débito"]) in cols2 else 0, key="m_valor")
            m_parc  = st.selectbox("Qtd. Parcelas",      cols2, index=cols2.index(guess(df2.columns,["cobr","parcela","parc"])) if guess(df2.columns,["cobr","parcela","parc"]) in cols2 else 0, key="m_parc")
            m_tel   = st.selectbox("Telefone",           cols2, index=cols2.index(guess(df2.columns,["celular","telefone","fone"])) if guess(df2.columns,["celular","telefone","fone"]) in cols2 else 0, key="m_tel")

        if st.button("✅ Confirmar e Importar", use_container_width=True):
            # Indexa planilha 2 pelo código
            idx2 = {}
            for _, row in df2.iterrows():
                cod = str(row.get(m_cod2,"")).strip() if m_cod2 != "(ignorar)" else ""
                if cod:
                    idx2.setdefault(cod, []).append(row)

            clientes_novos = []
            for i, row in df1.iterrows():
                cod  = str(row.get(m_cod1,"")).strip() if m_cod1 != "(ignorar)" else str(i)
                nome = str(row.get(m_nome,"")).strip() if m_nome != "(ignorar)" else f"Cliente {i+1}"
                doc  = str(row.get(m_doc,"")).strip()  if m_doc  != "(ignorar)" else ""
                cid  = cod or doc or f"cli_{i}"

                venc = ""
                if m_venc != "(ignorar)" and pd.notna(row.get(m_venc)):
                    v = row[m_venc]
                    if isinstance(v, (datetime, pd.Timestamp)):
                        venc = v.strftime("%d/%m/%Y")
                    else:
                        venc = str(v)

                rows2 = idx2.get(cod, [])
                valor = 0.0
                parcelas = 0
                telefone = ""
                for r2 in rows2:
                    if m_valor != "(ignorar)": valor    += parse_moeda(r2.get(m_valor, 0))
                    if m_parc  != "(ignorar)": parcelas += int(r2.get(m_parc, 0) or 0)
                    if m_tel   != "(ignorar)" and not telefone: telefone = str(r2.get(m_tel,"")).strip()

                clientes_novos.append({
                    "id": cid, "cod": cod, "nome": nome, "doc": doc,
                    "valor": valor, "parcelas": parcelas,
                    "vencimento": venc, "telefone": telefone,
                    "dias_atraso": calc_dias_atraso(venc),
                })

            # Detecta removidos (regularizados automaticamente)
            ids_novos = {c["id"] for c in clientes_novos}
            removidos = [c for c in store["clientes"] if c["id"] not in ids_novos]
            hoje_str  = date.today().strftime("%d/%m/%Y")
            for c in removidos:
                store["regularizados"].append({
                    "id": c["id"], "nome": c["nome"], "doc": c["doc"],
                    "valor": c["valor"], "atendente": current_nome(),
                    "data": hoje_str, "tipo": "auto"
                })

            store["clientes"] = clientes_novos
            store["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            st.success(f"✓ {len(clientes_novos)} clientes importados! {len(removidos)} regularizados automaticamente.")
            st.rerun()

# ── PAINEL PRINCIPAL ──────────────────────────────────────────────────────────
def tela_principal():
    store  = get_store()
    clientes = store["clientes"]
    role   = current_role()

    # ── Header ──
    col_logo, col_info, col_btns = st.columns([2, 3, 2])
    with col_logo:
        if LOGO_SRC:
            st.markdown(f'<img src="{LOGO_SRC}" style="height:32px;margin-top:4px">', unsafe_allow_html=True)
    with col_info:
        upd = store.get("ultima_atualizacao","Nenhuma planilha importada")
        st.markdown(f'<div style="color:#6b7280;font-size:12px;margin-top:8px">Atualizado: {upd} · {current_nome()}</div>', unsafe_allow_html=True)
    with col_btns:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("↑ Atualizar", use_container_width=True):
                st.session_state["tela"] = "importar"
                st.rerun()
        with c2:
            if st.button("Sair", use_container_width=True):
                for k in ["user_uid","user_nome","user_role","tela"]:
                    st.session_state.pop(k, None)
                st.rerun()

    st.markdown("---")

    # ── Stats ──
    total = len(clientes)
    pending = contacted = promise = 0
    for c in clientes:
        h = get_hist(c["id"])
        s = h.get("status","pending")
        if s == "pending":    pending   += 1
        elif s == "contacted": contacted += 1
        elif s in ("promise","negotiating"): promise += 1

    hoje_str = date.today().strftime("%d/%m/%Y")
    reg_hoje = len([r for r in store["regularizados"] if r.get("data") == hoje_str])

    cols = st.columns(5)
    cards = [
        ("Total Inadimplentes", total, "#e8eaf0"),
        ("Sem Contato", pending, "#ef4444"),
        ("Contactado", contacted, "#f59e0b"),
        ("Prometeu Pagar", promise, "#f97316"),
        ("Regularizados Hoje", reg_hoje, "#22c55e"),
    ]
    for col, (label, value, color) in zip(cols, cards):
        with col:
            st.markdown(f"""<div class="metric-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="color:{color}">{value}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Pendências ──
    pendencias = []
    for c in clientes:
        h = get_hist(c["id"])
        s = h.get("status","pending")
        if s == "paid": continue
        hoje = date.today()
        if s == "promise" and h.get("promiseDate"):
            try:
                p = h["promiseDate"].split("/")
                dt = date(int(p[2]),int(p[1]),int(p[0]))
                if dt <= hoje:
                    pendencias.append((c, h, "promise", f"Prometeu pagar em {h['promiseDate']}"))
                    continue
            except: pass
        if h.get("retorno"):
            try:
                p = h["retorno"].split("/")
                dt = date(int(p[2]),int(p[1]),int(p[0]))
                if dt <= hoje:
                    pendencias.append((c, h, "retorno", f"Retorno agendado para {h['retorno']}"))
                    continue
            except: pass
        if h.get("lastContact"):
            try:
                p = h["lastContact"].split("/")
                dt = date(int(p[2]),int(p[1]),int(p[0]))
                diff = (hoje - dt).days
                if diff >= 5:
                    pendencias.append((c, h, "semcontato", f"Sem contato há {diff} dias"))
            except: pass

    if pendencias:
        with st.expander(f"🔔 Pendências do Dia ({len(pendencias)})", expanded=True):
            cols_pend = st.columns(min(3, len(pendencias)))
            icon_map  = {"promise":"🟠","retorno":"📞","semcontato":"⚠️"}
            for i, (c, h, tipo, msg) in enumerate(pendencias[:9]):
                with cols_pend[i % 3]:
                    valor_fmt = fmt_moeda(c["valor"])
                    st.markdown(f"""<div class="pend-card pend-{tipo}">
                      <b>{icon_map[tipo]} {c['nome']}</b><br>
                      <span style="font-size:12px;color:#6b7280">{msg}</span><br>
                      <span style="font-size:12px;color:#6b7280">{valor_fmt}</span>
                    </div>""", unsafe_allow_html=True)
                    if role != "gestor":
                        if st.button("✏ Atender", key=f"pend_{c['id']}"):
                            st.session_state["editing_id"] = c["id"]
                            st.session_state["show_edit"]  = True

    # ── Filtros ──
    st.markdown("")
    fc1, fc2, fc3 = st.columns([3,2,2])
    with fc1:
        busca = st.text_input("🔍 Buscar", placeholder="Nome, CPF/CNPJ...", label_visibility="collapsed")
    with fc2:
        filtro_status = st.selectbox("Status", ["Todos","Sem contato","Contactado","Prometeu pagar","Negociando"], label_visibility="collapsed")
    with fc3:
        filtro_atraso = st.selectbox("Atraso", ["Todos","1–30 dias","31–60 dias","61–90 dias","+90 dias"], label_visibility="collapsed")

    status_map = {"Sem contato":"pending","Contactado":"contacted","Prometeu pagar":"promise","Negociando":"negotiating"}

    # Aplica filtros
    df_cli = pd.DataFrame(clientes) if clientes else pd.DataFrame()
    if df_cli.empty:
        st.info("Nenhum dado carregado. Use '↑ Atualizar' para importar as planilhas.")
        return

    # Adiciona status e dias ao df
    df_cli["_status"] = df_cli["id"].apply(lambda i: get_hist(i).get("status","pending"))
    df_cli["_lastContact"] = df_cli["id"].apply(lambda i: get_hist(i).get("lastContact",""))
    df_cli["_atendente"]   = df_cli["id"].apply(lambda i: get_hist(i).get("atendente",""))
    df_cli["_notes"]       = df_cli["id"].apply(lambda i: get_hist(i).get("notes",""))

    # Oculta regularizados
    df_cli = df_cli[df_cli["_status"] != "paid"]

    if busca:
        mask = df_cli.apply(lambda r: busca.lower() in str(r.get("nome","")).lower() or busca.lower() in str(r.get("doc","")).lower(), axis=1)
        df_cli = df_cli[mask]

    if filtro_status != "Todos":
        df_cli = df_cli[df_cli["_status"] == status_map.get(filtro_status,"pending")]

    if filtro_atraso != "Todos":
        if filtro_atraso == "1–30 dias":
            df_cli = df_cli[df_cli["dias_atraso"].apply(lambda d: d is not None and 1<=d<=30)]
        elif filtro_atraso == "31–60 dias":
            df_cli = df_cli[df_cli["dias_atraso"].apply(lambda d: d is not None and 31<=d<=60)]
        elif filtro_atraso == "61–90 dias":
            df_cli = df_cli[df_cli["dias_atraso"].apply(lambda d: d is not None and 61<=d<=90)]
        elif filtro_atraso == "+90 dias":
            df_cli = df_cli[df_cli["dias_atraso"].apply(lambda d: d is not None and d>90)]

    # TOP 10 maiores valores
    top10_ids = set(
        pd.DataFrame(clientes).nlargest(10,"valor")["id"].tolist()
        if clientes else []
    )

    st.markdown(f"**{len(df_cli)} clientes** encontrados")

    # ── Tabela ──
    for _, row in df_cli.iterrows():
        is_top = row["id"] in top10_ids
        bg = "rgba(239,68,68,.04)" if is_top else "transparent"
        border = "border-left:3px solid rgba(239,68,68,.5);" if is_top else ""
        top_tag = '<span class="top-badge">★ TOP</span> ' if is_top else ""

        valor_color = "#ff6b6b" if is_top else "#e8eaf0"
        dias_html   = dias_badge_html(row.get("dias_atraso"))
        status_html = status_badge_html(row["_status"])
        valor_fmt   = fmt_moeda(row["valor"])
        parc        = f"{int(row['parcelas'])}x" if row.get("parcelas") else "—"
        tel         = row.get("telefone","") or "—"
        venc        = row.get("vencimento","") or "—"
        doc         = row.get("doc","") or ""
        notes       = str(row["_notes"])[:50] + "..." if len(str(row["_notes"])) > 50 else str(row["_notes"]) or "—"
        atend       = row["_atendente"] or "—"
        last_cont   = row["_lastContact"] or "—"

        col_info, col_val, col_parc, col_venc, col_dias, col_tel, col_st, col_ult, col_at, col_obs, col_act = st.columns([2.5,1.5,0.8,1.2,0.8,1.2,1.5,1.2,1.2,1.5,0.8])

        with col_info:
            st.markdown(f'<div style="font-weight:600;font-size:13px;{border}padding-left:6px;background:{bg}">{top_tag}{row["nome"]}<br><span style="font-size:11px;color:#6b7280">{doc}</span></div>', unsafe_allow_html=True)
        with col_val:
            st.markdown(f'<div style="font-weight:700;color:{valor_color};font-size:13px;margin-top:4px">{valor_fmt}</div>', unsafe_allow_html=True)
        with col_parc:
            st.markdown(f'<div style="font-size:13px;margin-top:4px">{parc}</div>', unsafe_allow_html=True)
        with col_venc:
            st.markdown(f'<div style="font-size:12px;color:#6b7280;margin-top:4px">{venc}</div>', unsafe_allow_html=True)
        with col_dias:
            st.markdown(f'<div style="margin-top:4px">{dias_html}</div>', unsafe_allow_html=True)
        with col_tel:
            st.markdown(f'<div style="font-size:12px;color:#6b7280;margin-top:4px">{tel}</div>', unsafe_allow_html=True)
        with col_st:
            st.markdown(f'<div style="margin-top:4px">{status_html}</div>', unsafe_allow_html=True)
        with col_ult:
            st.markdown(f'<div style="font-size:12px;color:#6b7280;margin-top:4px">{last_cont}</div>', unsafe_allow_html=True)
        with col_at:
            st.markdown(f'<div style="font-size:12px;color:#6b7280;margin-top:4px">{atend}</div>', unsafe_allow_html=True)
        with col_obs:
            notes_full = str(row["_notes"] or "")
            st.markdown(f'<div style="font-size:12px;color:#6b7280;margin-top:4px" title="{notes_full}">{notes}</div>', unsafe_allow_html=True)
        with col_act:
            if role != "gestor":
                if st.button("✏", key=f"edit_{row['id']}"):
                    st.session_state["editing_id"] = row["id"]
                    st.session_state["show_edit"]  = True
                    st.rerun()

        st.markdown('<hr style="margin:2px 0;border-color:#2a2f42">', unsafe_allow_html=True)

    # ── Modal de edição (simulado com expander) ──
    if st.session_state.get("show_edit") and st.session_state.get("editing_id"):
        eid = st.session_state["editing_id"]
        cliente = next((c for c in clientes if c["id"] == eid), None)
        if cliente:
            h = get_hist(eid)
            with st.sidebar:
                st.markdown(f"### ✏ {cliente['nome']}")
                st.caption(f"{cliente.get('doc','')} · {fmt_moeda(cliente['valor'])} · {cliente.get('parcelas',0)} parcelas")
                st.markdown("---")

                status_opts = {"🔴 Sem contato":"pending","🟡 Contactado":"contacted",
                               "🟠 Prometeu pagar":"promise","🔵 Negociando":"negotiating","✅ Regularizado":"paid"}
                status_rev  = {v:k for k,v in status_opts.items()}
                status_sel  = st.selectbox("Status", list(status_opts.keys()),
                    index=list(status_opts.values()).index(h.get("status","pending")))

                last_contact = st.date_input("Data do último contato",
                    value=datetime.strptime(h["lastContact"],"%d/%m/%Y").date() if h.get("lastContact") else date.today())

                retorno_date = st.date_input("📅 Agendar retorno",
                    value=datetime.strptime(h["retorno"],"%d/%m/%Y").date() if h.get("retorno") else None,
                    min_value=date.today())

                promise_date = None
                if status_opts[status_sel] == "promise":
                    promise_date = st.date_input("📅 Data que prometeu pagar",
                        value=datetime.strptime(h["promiseDate"],"%d/%m/%Y").date() if h.get("promiseDate") else date.today())

                notes = st.text_area("Observações", value=h.get("notes",""),
                    placeholder="Ex: Cliente prometeu pagar até sexta...")

                col_s, col_c = st.columns(2)
                with col_s:
                    if st.button("💾 Salvar", use_container_width=True):
                        prev_status = h.get("status","pending")
                        new_status  = status_opts[status_sel]
                        new_h = {
                            "status": new_status,
                            "lastContact": last_contact.strftime("%d/%m/%Y"),
                            "retorno": retorno_date.strftime("%d/%m/%Y") if retorno_date else "",
                            "promiseDate": promise_date.strftime("%d/%m/%Y") if promise_date else "",
                            "notes": notes,
                            "atendente": current_nome()
                        }
                        save_hist(eid, new_h)
                        if new_status == "paid" and prev_status != "paid":
                            store["regularizados"].append({
                                "id": eid, "nome": cliente["nome"], "doc": cliente.get("doc",""),
                                "valor": cliente["valor"], "atendente": current_nome(),
                                "data": date.today().strftime("%d/%m/%Y"), "tipo": "manual"
                            })
                            st.success("✅ Regularizado!")
                        else:
                            st.success("Salvo!")
                        st.session_state["show_edit"]  = False
                        st.session_state["editing_id"] = None
                        st.rerun()
                with col_c:
                    if st.button("✕ Fechar", use_container_width=True):
                        st.session_state["show_edit"]  = False
                        st.session_state["editing_id"] = None
                        st.rerun()

    # ── Export ──
    st.markdown("---")
    ec1, ec2 = st.columns([1,4])
    with ec1:
        if st.button("⬇ Exportar CSV", use_container_width=True):
            rows = []
            for c in clientes:
                h  = get_hist(c["id"])
                sl = {"pending":"Sem contato","contacted":"Contactado","promise":"Prometeu pagar",
                      "negotiating":"Negociando","paid":"Regularizado"}
                rows.append([h.get("atendente",""), c["nome"], c.get("doc",""),
                              c["valor"], c.get("parcelas",""), c.get("vencimento",""),
                              c.get("dias_atraso",""), sl.get(h.get("status","pending"),""),
                              h.get("lastContact",""), h.get("notes","")])
            df_exp = pd.DataFrame(rows, columns=["Atendente","Nome","CPF/CNPJ","Saldo","Parcelas","Vencimento","Dias Atraso","Status","Último Contato","Observações"])
            csv = df_exp.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 Baixar", csv, f"cobrancas_{current_nome().replace(' ','_')}_{date.today()}.csv", "text/csv")

    # ── Histórico regularizados ──
    with ec2:
        if st.button("📋 Ver histórico de regularizados", use_container_width=False):
            st.session_state["show_hist"] = not st.session_state.get("show_hist", False)

    if st.session_state.get("show_hist"):
        reg = store["regularizados"]
        if not reg:
            st.info("Nenhum cliente regularizado ainda.")
        else:
            df_reg = pd.DataFrame(reg)
            df_reg["tipo_fmt"] = df_reg["tipo"].map({"auto":"🟢 Automático","manual":"🔵 Manual"})
            df_reg["valor_fmt"] = df_reg["valor"].apply(fmt_moeda)
            st.dataframe(
                df_reg[["data","nome","doc","valor_fmt","atendente","tipo_fmt"]].rename(columns={
                    "data":"Data","nome":"Cliente","doc":"CPF/CNPJ","valor_fmt":"Valor","atendente":"Atendente","tipo_fmt":"Tipo"
                }),
                use_container_width=True, hide_index=True
            )

    # ── Admin: gerenciar usuários ──
    if current_role() == "admin":
        st.markdown("---")
        with st.expander("⚙️ Gerenciar Usuários"):
            store = get_store()
            st.markdown("**Criar novo usuário:**")
            cu1, cu2, cu3, cu4 = st.columns(4)
            with cu1: u_nome  = st.text_input("Nome completo", key="u_nome")
            with cu2: u_email = st.text_input("E-mail", key="u_email")
            with cu3: u_senha = st.text_input("Senha", type="password", key="u_senha")
            with cu4: u_role  = st.selectbox("Perfil", ["atendente","gestor","admin"], key="u_role")
            if st.button("➕ Criar usuário"):
                if u_nome and u_email and u_senha:
                    uid = hashlib.md5(u_email.encode()).hexdigest()
                    store["usuarios"][uid] = {"nome":u_nome,"email":u_email,"senha_hash":hash_senha(u_senha),"role":u_role}
                    st.success(f"Usuário {u_nome} criado!")
                else:
                    st.error("Preencha todos os campos.")

            st.markdown("**Usuários cadastrados:**")
            for uid, u in store["usuarios"].items():
                st.markdown(f"- **{u['nome']}** ({u['email']}) — {u['role']}")

# ── ROTEADOR PRINCIPAL ────────────────────────────────────────────────────────
def main():
    if not is_logged():
        tela_login()
        return

    store = get_store()
    tela  = st.session_state.get("tela","principal")

    if not store["clientes"] or tela == "importar":
        tela_importar()
        if store["clientes"] and tela == "importar":
            if st.button("← Voltar"):
                st.session_state["tela"] = "principal"
                st.rerun()
    else:
        st.session_state["tela"] = "principal"
        tela_principal()

if __name__ == "__main__":
    main()
