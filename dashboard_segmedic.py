import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="SegMedic Case | Dashboard", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    #MainMenu, footer, header { visibility: hidden; }

    .kpi { background:#fff; border-radius:12px; padding:18px 20px;
           border:1px solid #e2e8f0; border-top:3px solid #ccc;
           box-shadow:0 1px 3px rgba(0,0,0,0.05); }
    .kpi.blue   { border-top-color:#3b82f6; }
    .kpi.green  { border-top-color:#10b981; }
    .kpi.purple { border-top-color:#8b5cf6; }
    .kpi.orange { border-top-color:#f59e0b; }
    .kpi-label  { font-size:0.7rem; color:#94a3b8; font-weight:600;
                  text-transform:uppercase; letter-spacing:0.8px; margin-bottom:6px; }
    .kpi-value  { font-size:1.75rem; font-weight:700; color:#1e293b; line-height:1.1; }

    .sec { display:flex; align-items:center; gap:10px; margin:28px 0 14px 0; }
    .sec-title { font-size:0.95rem; font-weight:600; color:#334155; white-space:nowrap; }
    .sec-line  { flex:1; height:1px; background:#e2e8f0; }

    .main-header { background:linear-gradient(135deg,#1e40af,#0ea5e9);
                   border-radius:14px; padding:24px 32px; margin-bottom:20px; }
    .main-header h1 { color:#fff; font-size:1.7rem; font-weight:700; margin:0; }
    .main-header p  { color:rgba(255,255,255,0.8); font-size:0.88rem; margin:4px 0 0 0; }
    .badge { display:inline-block; background:rgba(255,255,255,0.2); color:#e0f2fe;
             font-size:0.68rem; font-weight:600; padding:2px 10px; border-radius:20px;
             letter-spacing:1px; text-transform:uppercase; margin-bottom:8px; }

    .info-box { background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px;
                padding:14px 18px; color:#1d4ed8; font-size:0.875rem;
                font-weight:500; margin-bottom:16px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Carregamento e limpeza dos dados
# ============================================================
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "segmedic_dados.csv")
    if not os.path.exists(path):
        st.error("❌ Arquivo 'segmedic_dados.csv' não encontrado na pasta do projeto.")
        st.stop()
    df = pd.read_csv(path)

    df['data_atendimento'] = pd.to_datetime(df['data_atendimento'])
    df['mes_ano'] = df['data_atendimento'].dt.to_period('M').astype(str)
    df = df[df['valor'].notna()]
    df = df[df['especialidade'].notna() & (df['especialidade'].str.strip() != '')]

    df['sexo'] = df['sexo'].astype(str).str.strip()
    df = df[df['sexo'].isin(['Feminino', 'Masculino'])]

    df['cidade'] = df['cidade'].astype(str).str.strip().str.title()
    invalidas = {'', 'Nan', '-', 'X', 'Xx', 'Xxx', '0', '00', '000', '0000',
                 '000000', '00000000', '000000000', 'Ni', 'Rj', 'Centro',
                 'Miguel Couto', 'Meier', 'None', 'Null'}
    df = df[~df['cidade'].isin(invalidas)]
    df = df[~df['cidade'].str.match(r'^\d+$')]
    df['cidade'] = df['cidade'].replace({
        'Nova Iguacu': 'Nova Iguaçu', 'Nova Iguaçu/Rj': 'Nova Iguaçu',
        'Nova Guacu': 'Nova Iguaçu', 'Nilopolis': 'Nilópolis',
        'Rio De Janeir': 'Rio De Janeiro', 'Rio Janeiro': 'Rio De Janeiro',
        'Sao Joao De Meriti': 'São João De Meriti',
        'Sao João De Meriti': 'São João De Meriti',
        'São Joao': 'São João De Meriti',
        'São João Do Meriti': 'São João De Meriti',
        'Seropedica': 'Seropédica', 'Paracaambi': 'Paracambi',
        'Paraquanbi': 'Paracambi', 'Pirai': 'Piraí',
    })
    return df

# ── Funções auxiliares ────────────────────────────────────────

def formatar_valor(v):
    """Formata valores monetários de forma legível."""
    if v >= 1_000_000: return f"R$ {v/1_000_000:.1f}M"
    if v >= 1_000:     return f"R$ {v/1_000:.0f}K"
    return f"R$ {v:,.0f}"

PC = {"displayModeBar": False}

def base_layout(fig, title, height=350):
    """Aplica estilo visual padrão aos gráficos."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#475569", size=11),
        title=dict(text=f"<b>{title}</b>", font=dict(size=13, color="#1e293b")),
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(color="#475569"))
    fig.update_yaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(color="#475569"))
    return fig

def hbar(y, x, labels, title, color, height=420):
    """Gráfico de barras horizontais reutilizável."""
    y_list = list(y) if not isinstance(y, list) else y
    x_list = list(x) if not isinstance(x, list) else x
    labels_list = list(labels) if not isinstance(labels, list) else labels
    if not x_list:
        return go.Figure()
    max_label_len = max((len(str(l)) for l in labels_list), default=10)
    margin_r = max(max_label_len * 7, 80)
    x_max = max(x_list)
    fig = go.Figure(go.Bar(
        x=x_list, y=y_list, orientation='h',
        marker=dict(color=color, line=dict(width=0)),
        text=labels_list, textposition='outside',
        textfont=dict(size=10, color="#475569"),
        cliponaxis=False
    ))
    base_layout(fig, title, height)
    fig.update_layout(margin=dict(l=10, r=margin_r, t=40, b=10))
    fig.update_xaxes(range=[0, x_max * 1.35])
    return fig

# ── Dados ─────────────────────────────────────────────────────
df = load_data()

# ============================================================
# Sidebar — Filtros
# ============================================================
with st.sidebar:
    st.markdown("<div style='font-size:1rem;font-weight:700;color:#1e293b;padding:8px 0 4px'>🔎 Filtros</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.75rem;color:#94a3b8;margin-bottom:12px;'>Refine os dados</div>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.7rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;'>Especialidade</div>", unsafe_allow_html=True)
    esp_sel = st.selectbox("esp", ["Todas"] + sorted(df['especialidade'].unique().tolist()), label_visibility="collapsed")

    st.markdown("<div style='font-size:0.7rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;margin-top:12px;'>Cidade</div>", unsafe_allow_html=True)
    cid_sel = st.selectbox("cid", ["Todas"] + sorted(df['cidade'].unique().tolist()), label_visibility="collapsed")

    st.markdown("<div style='font-size:0.7rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;margin-top:12px;'>Mês</div>", unsafe_allow_html=True)
    mes_sel = st.selectbox("mes", ["Todos"] + sorted(df['mes_ano'].unique().tolist()), label_visibility="collapsed")

    st.markdown("---")
    ativos = []
    if esp_sel != "Todas": ativos.append(f"📌 {esp_sel}")
    if cid_sel != "Todas": ativos.append(f"📍 {cid_sel}")
    if mes_sel != "Todos": ativos.append(f"📅 {mes_sel}")
    if ativos:
        for a in ativos:
            st.markdown(f"<div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:6px 10px;font-size:0.78rem;color:#1d4ed8;margin-bottom:6px;'>{a}</div>", unsafe_allow_html=True)
    else:
        st.caption("Nenhum filtro ativo")
    st.markdown("<div style='font-size:0.7rem;color:#cbd5e1;text-align:center;margin-top:16px;'>SegMedic Analytics</div>", unsafe_allow_html=True)

# ── Aplicar filtros ───────────────────────────────────────────
d = df.copy()
if esp_sel != "Todas": d = d[d['especialidade'] == esp_sel]
if cid_sel != "Todas": d = d[d['cidade'] == cid_sel]
if mes_sel != "Todos": d = d[d['mes_ano'] == mes_sel]

if len(d) == 0:
    st.markdown("""
        <div class="main-header">
            <div class="badge">Análise Clínica</div>
            <h1>🏥 Dashboard — SegMedic Case</h1>
            <p>Monitoramento de atendimentos, faturamento e perfil de pacientes</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div style='background:#fef9c3;border:2px solid #fde047;border-radius:12px;
                    padding:20px 24px;margin-top:20px;'>
            <div style='font-size:1.1rem;font-weight:700;color:#854d0e;margin-bottom:6px;'>
                ⚠️ Nenhum dado encontrado para os filtros selecionados.
            </div>
            <div style='font-size:0.9rem;color:#92400e;'>
                Ajuste os filtros na barra lateral para visualizar os dados.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── CABEÇALHO ─────────────────────────────────────────────────
ano_min = d['data_atendimento'].dt.year.min()
ano_max = d['data_atendimento'].dt.year.max()
periodo = str(ano_max) if ano_min == ano_max else f"{ano_min}–{ano_max}"

st.markdown(f"""
<div class="main-header">
    <div class="badge">Análise Clínica · {periodo}</div>
    <h1>🏥 Dashboard — SegMedic Case</h1>
    <p>Monitoramento de atendimentos, faturamento e perfil de pacientes</p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────
total_atendimentos = len(d)
faturamento_total  = d['valor'].sum()
ticket_medio       = d['valor'].mean() if total_atendimentos > 0 else 0
pacientes_unicos   = d['id_paciente'].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="kpi blue"><div class="kpi-label">📋 Atendimentos</div><div class="kpi-value">{total_atendimentos:,}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi green"><div class="kpi-label">💰 Faturamento Total</div><div class="kpi-value">{formatar_valor(faturamento_total)}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="kpi purple"><div class="kpi-label">🎯 Ticket Médio</div><div class="kpi-value">{formatar_valor(ticket_medio)}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="kpi orange"><div class="kpi-label">👥 Pacientes Únicos</div><div class="kpi-value">{pacientes_unicos:,}</div></div>', unsafe_allow_html=True)

# ============================================================
# SEÇÃO 1 — Métricas de Atendimento
# - Valor por data de atendimento (agrupado por mês)
# - Quantidade de atendimentos por data (agrupado por mês)
# - Quantidade de atendimentos por especialidade
# ============================================================
st.markdown('<div class="sec"><span class="sec-title">📅 Métricas de Atendimento</span><div class="sec-line"></div></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    valor_mes = d.groupby('mes_ano')['valor'].sum().reset_index().sort_values('mes_ano')
    fig = go.Figure(go.Bar(
        x=valor_mes['mes_ano'], y=valor_mes['valor'],
        marker=dict(color='#3b82f6', line=dict(width=0)),
        text=[formatar_valor(v) for v in valor_mes['valor']],
        textposition='outside', textfont=dict(size=9), cliponaxis=False
    ))
    base_layout(fig, 'Valor por Data de Atendimento (Mensal)', 340)
    fig.update_xaxes(tickangle=-30, type='category')
    fig.update_yaxes(range=[0, valor_mes['valor'].max() * 1.25])
    st.plotly_chart(fig, use_container_width=True, config=PC)

with col2:
    qtd_mes = d.groupby('mes_ano').size().reset_index(name='qtd').sort_values('mes_ano')
    fig = go.Figure(go.Scatter(
        x=qtd_mes['mes_ano'], y=qtd_mes['qtd'], mode='lines+markers+text',
        line=dict(color='#059669', width=2.5),
        marker=dict(size=8, color='#059669', line=dict(color='white', width=2)),
        fill='tozeroy', fillcolor='rgba(5,150,105,0.08)',
        text=qtd_mes['qtd'], textposition='top center', textfont=dict(size=9)
    ))
    base_layout(fig, 'Qtd. de Atendimentos por Data (Mensal)', 340)
    fig.update_xaxes(tickangle=-30, type='category')
    fig.update_yaxes(range=[0, qtd_mes['qtd'].max() * 1.25])
    st.plotly_chart(fig, use_container_width=True, config=PC)

# Atendimentos por especialidade — Top 15
qtd_esp = d.groupby('especialidade').size().reset_index(name='qtd').sort_values('qtd', ascending=False)
top15_esp = qtd_esp.head(15).sort_values('qtd')
st.plotly_chart(
    hbar(top15_esp['especialidade'].tolist(), top15_esp['qtd'].tolist(),
         [f"{v:,}" for v in top15_esp['qtd'].tolist()],
         'Qtd. de Atendimentos por Especialidade (Top 15)', '#3b82f6', 440),
    use_container_width=True, config=PC
)

# ============================================================
# SEÇÃO 2 — Métricas Financeiras
# - Valor e quantidade de atendimentos por especialidade
# - Ticket médio por paciente
# ============================================================
st.markdown('<div class="sec"><span class="sec-title">💰 Métricas Financeiras</span><div class="sec-line"></div></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fat_esp = d.groupby('especialidade')['valor'].sum().reset_index().sort_values('valor').tail(15)
    st.plotly_chart(
        hbar(fat_esp['especialidade'].tolist(), fat_esp['valor'].tolist(),
             [formatar_valor(v) for v in fat_esp['valor'].tolist()],
             'Faturamento por Especialidade (Top 15)', '#10b981', 460),
        use_container_width=True, config=PC
    )

with col2:
    qtd_esp2 = d.groupby('especialidade').size().reset_index(name='qtd').sort_values('qtd').tail(15)
    st.plotly_chart(
        hbar(qtd_esp2['especialidade'].tolist(), qtd_esp2['qtd'].tolist(),
             [f"{v:,}" for v in qtd_esp2['qtd'].tolist()],
             'Qtd. Atendimentos por Especialidade (Top 15)', '#3b82f6', 460),
        use_container_width=True, config=PC
    )

# Ticket médio por paciente — distribuição
ticket_por_paciente = d.groupby('id_paciente')['valor'].mean().reset_index()
ticket_por_paciente.columns = ['id_paciente', 'ticket_medio']

col1, col2 = st.columns([2, 1])
with col1:
    fig = go.Figure(go.Histogram(
        x=ticket_por_paciente['ticket_medio'],
        nbinsx=30,
        marker=dict(color='#8b5cf6', line=dict(color='#7c3aed', width=1)),
        hovertemplate='Faixa: R$ %{x:.0f}<br>Pacientes: %{y}<extra></extra>'
    ))
    base_layout(fig, 'Distribuição do Ticket Médio por Paciente', 320)
    fig.update_xaxes(title_text='Ticket Médio (R$)', tickprefix='R$ ')
    fig.update_yaxes(title_text='Nº de Pacientes')
    st.plotly_chart(fig, use_container_width=True, config=PC)

with col2:
    media_geral = ticket_por_paciente['ticket_medio'].mean()
    mediana      = ticket_por_paciente['ticket_medio'].median()
    maximo       = ticket_por_paciente['ticket_medio'].max()
    st.markdown(f"""
    <div style="background:#fff;border-radius:12px;padding:20px;border:1px solid #e2e8f0;
                border-top:3px solid #8b5cf6;height:100%;">
        <div style="font-size:0.7rem;color:#94a3b8;font-weight:600;text-transform:uppercase;
                    letter-spacing:0.8px;margin-bottom:16px;">📊 Resumo do Ticket</div>
        <div style="margin-bottom:14px;">
            <div style="font-size:0.75rem;color:#64748b;">Média por Paciente</div>
            <div style="font-size:1.4rem;font-weight:700;color:#1e293b;">{formatar_valor(media_geral)}</div>
        </div>
        <div style="margin-bottom:14px;">
            <div style="font-size:0.75rem;color:#64748b;">Mediana</div>
            <div style="font-size:1.4rem;font-weight:700;color:#1e293b;">{formatar_valor(mediana)}</div>
        </div>
        <div>
            <div style="font-size:0.75rem;color:#64748b;">Maior Ticket</div>
            <div style="font-size:1.4rem;font-weight:700;color:#1e293b;">{formatar_valor(maximo)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# SEÇÃO 3 — Perfil dos Pacientes
# - Quantidade de atendimentos por sexo
# - Quantidade e valor de atendimentos por cidade
# - Média de atendimentos por paciente
# ============================================================
st.markdown('<div class="sec"><span class="sec-title">👥 Perfil dos Pacientes</span><div class="sec-line"></div></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    dist_sexo = d.groupby('sexo').size().reset_index(name='qtd')
    cores_sexo = [('#3b82f6' if s == 'Masculino' else '#f472b6') for s in dist_sexo['sexo']]

    # Mostro o número absoluto de pacientes de cada sexo junto com o percentual
    custom_labels = [
        f"{row['sexo']}<br><b>{row['qtd']:,}</b> pacientes"
        for _, row in dist_sexo.iterrows()
    ]

    fig = go.Figure(go.Pie(
        labels=dist_sexo['sexo'],
        values=dist_sexo['qtd'],
        hole=0.5,
        marker=dict(colors=cores_sexo, line=dict(color='white', width=3)),
        text=custom_labels,
        textinfo='text+percent',
        textfont=dict(size=11),
        hovertemplate='<b>%{label}</b><br>%{value:,} atendimentos<br>%{percent}<extra></extra>'
    ))
    base_layout(fig, 'Atendimentos por Sexo', 340)
    fig.update_layout(showlegend=True,
                      legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.12,
                                  font=dict(size=11, color='#1e293b')))
    st.plotly_chart(fig, use_container_width=True, config=PC)

with col2:
    # Quantidade por cidade — Top 10
    atend_cidade = d.groupby('cidade').size().reset_index(name='qtd').sort_values('qtd', ascending=False).head(10).sort_values('qtd')
    st.plotly_chart(
        hbar(atend_cidade['cidade'].tolist(), atend_cidade['qtd'].tolist(),
             [f"{v:,}" for v in atend_cidade['qtd'].tolist()],
             'Top 10 Cidades — Qtd. Atendimentos', '#3b82f6', 340),
        use_container_width=True, config=PC
    )

# Valor por cidade — Top 10
fat_cidade = d.groupby('cidade')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10).sort_values('valor')
st.plotly_chart(
    hbar(fat_cidade['cidade'].tolist(), fat_cidade['valor'].tolist(),
         [formatar_valor(v) for v in fat_cidade['valor'].tolist()],
         'Top 10 Cidades — Faturamento', '#10b981', 340),
    use_container_width=True, config=PC
)

# Destaque para a média de atendimentos por paciente
media_atend_paciente = d.groupby('id_paciente').size().mean() if total_atendimentos > 0 else 0
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.markdown(f"""
        <div style='background:#fff;border-radius:12px;padding:20px 22px;
                    border:1px solid #e2e8f0;border-top:3px solid #3b82f6;
                    box-shadow:0 1px 3px rgba(0,0,0,0.05);text-align:center;'>
            <div style='font-size:0.7rem;color:#94a3b8;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;'>
                📊 Média de Atendimentos por Paciente
            </div>
            <div style='font-size:2rem;font-weight:700;color:#1e293b;'>{media_atend_paciente:.1f}</div>
            <div style='font-size:0.78rem;color:#64748b;margin-top:4px;'>atendimentos/paciente</div>
        </div>
    """, unsafe_allow_html=True)
with col_m2:
    st.markdown(f"""
        <div style='background:#fff;border-radius:12px;padding:20px 22px;
                    border:1px solid #e2e8f0;border-top:3px solid #10b981;
                    box-shadow:0 1px 3px rgba(0,0,0,0.05);text-align:center;'>
            <div style='font-size:0.7rem;color:#94a3b8;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;'>
                👥 Pacientes Únicos
            </div>
            <div style='font-size:2rem;font-weight:700;color:#1e293b;'>{pacientes_unicos:,}</div>
            <div style='font-size:0.78rem;color:#64748b;margin-top:4px;'>pacientes no período</div>
        </div>
    """, unsafe_allow_html=True)
with col_m3:
    max_atend = int(d.groupby('id_paciente').size().max()) if total_atendimentos > 0 else 0
    st.markdown(f"""
        <div style='background:#fff;border-radius:12px;padding:20px 22px;
                    border:1px solid #e2e8f0;border-top:3px solid #8b5cf6;
                    box-shadow:0 1px 3px rgba(0,0,0,0.05);text-align:center;'>
            <div style='font-size:0.7rem;color:#94a3b8;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;'>
                🏆 Maior Frequência
            </div>
            <div style='font-size:2rem;font-weight:700;color:#1e293b;'>{max_atend}</div>
            <div style='font-size:0.78rem;color:#64748b;margin-top:4px;'>atendimentos (1 paciente)</div>
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# SEÇÃO 4 — Operação da Clínica
# - Quantidade de consultas realizadas por data de atendimento
# - Tabela completa de especialidades
# ============================================================
st.markdown('<div class="sec"><span class="sec-title">🏨 Operação da Clínica</span><div class="sec-line"></div></div>', unsafe_allow_html=True)

# Consultas por data — agrupa por semana para legibilidade
consultas_semana = d.set_index('data_atendimento').resample('W').size().reset_index(name='qtd')
consultas_semana.columns = ['semana', 'qtd']
consultas_semana['label'] = consultas_semana['semana'].dt.strftime('%d/%m/%y')

fig = go.Figure()
fig.add_trace(go.Bar(
    x=consultas_semana['label'], y=consultas_semana['qtd'],
    marker=dict(color='#60a5fa', line=dict(width=0)),
    hovertemplate='Semana de %{x}<br>%{y} consultas<extra></extra>'
))
fig.add_trace(go.Scatter(
    x=consultas_semana['label'], y=consultas_semana['qtd'],
    mode='lines', line=dict(color='#1d4ed8', width=2),
    hoverinfo='skip'
))
base_layout(fig, 'Consultas Realizadas por Data de Atendimento (Semanal)', 320)
fig.update_xaxes(type='category', tickangle=-40,
                 dtick=max(1, len(consultas_semana) // 15))
st.plotly_chart(fig, use_container_width=True, config=PC)

# Tabela completa de especialidades
col1, col2 = st.columns(2)
with col1:
    top15_op = qtd_esp.head(15).sort_values('qtd')
    st.plotly_chart(
        hbar(top15_op['especialidade'].tolist(), top15_op['qtd'].tolist(),
             [f"{v:,}" for v in top15_op['qtd'].tolist()],
             'Top 15 Especialidades — Volume', [[0, '#bfdbfe'], [1, '#1d4ed8']], 480),
        use_container_width=True, config=PC
    )

with col2:
    st.markdown("<div style='font-size:13px;font-weight:700;color:#1e293b;margin-bottom:10px;'>📋 Todas as Especialidades</div>", unsafe_allow_html=True)
    tab = qtd_esp.copy().reset_index(drop=True)
    tab.index += 1
    tab.columns = ['Especialidade', 'Atendimentos']
    tab['% do Total'] = (tab['Atendimentos'] / tab['Atendimentos'].sum() * 100).round(1).astype(str) + '%'
    st.dataframe(tab, use_container_width=True, height=440,
        column_config={
            'Especialidade': st.column_config.TextColumn(width='medium'),
            'Atendimentos':  st.column_config.NumberColumn(format='%d'),
            '% do Total':    st.column_config.TextColumn(width='small'),
        }
    )

# ── Rodapé ────────────────────────────────────────────────────
st.markdown("<div style='text-align:center;color:#94a3b8;font-size:0.75rem;margin-top:28px;padding-top:14px;border-top:1px solid #e2e8f0;'>SegMedic Case · Isaque Sena da Silva</div>", unsafe_allow_html=True)
