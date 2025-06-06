import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA STREAMLIT ---
st.set_page_config(
    page_title="Gestão Eficiente de Abrigos",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .stMetricValue {
        font-size: 28px !important;
    }
    .stMetricLabel {
        font-size: 14px !important;
        color: #555 !important;
    }
</style>
""", unsafe_allow_html=True)


# --- FUNÇÕES AUXILIARES ---
@st.cache_data(ttl=3600)
def gerar_dados_abrigo_completos(nome_abrigo, detalhes_abrigo, seed_offset=0):
    np.random.seed(42 + seed_offset)
    
    capacidade_maxima = np.random.randint(80, 250)
    abrigados_atuais = np.random.randint(int(capacidade_maxima * 0.4), capacidade_maxima + 1)
    
    faixas_etarias_nomes = ['Bebês (0-2a)', 'Crianças (3-5a)', 'Crianças (6-12a)', 'Adolescentes (13-17a)', 'Adultos (18-59a)', 'Idosos (60-74a)', 'Idosos (75+a)']
    quantidades_faixas = np.random.multinomial(abrigados_atuais, [0.05, 0.08, 0.12, 0.10, 0.40, 0.15, 0.10])
    df_perfil_etario = pd.DataFrame({'Faixa Etária': faixas_etarias_nomes, 'Quantidade': quantidades_faixas})
    n_criancas_0_12 = df_perfil_etario[df_perfil_etario['Faixa Etária'].isin(['Bebês (0-2a)', 'Crianças (3-5a)', 'Crianças (6-12a)'])]['Quantidade'].sum()
    n_idosos_60_mais = df_perfil_etario[df_perfil_etario['Faixa Etária'].isin(['Idosos (60-74a)', 'Idosos (75+a)'])]['Quantidade'].sum()
    
    #=== PERFIL DOS PETS ===
    n_pets_total = np.random.randint(5, int(abrigados_atuais * 0.15))
    tipos_pet = ['Cães', 'Gatos', 'Pequenos Animais']
    quantidades_pets = np.random.multinomial(n_pets_total, [0.6, 0.35, 0.05])
    df_perfil_pets = pd.DataFrame({'Tipo': tipos_pet, 'Quantidade': quantidades_pets})
    n_caes = df_perfil_pets[df_perfil_pets['Tipo'] == 'Cães']['Quantidade'].sum()
    n_gatos = df_perfil_pets[df_perfil_pets['Tipo'] == 'Gatos']['Quantidade'].sum()


    tipos_necessidade = ['Diabetes Tipo 1 (Insulina)', 'Diabetes Tipo 2 (Oral)', 'Hipertensão Severa', 'Mobilidade Reduzida - Cadeirante', 'Mobilidade Reduzida - Andador', 'Gestante (Baixo Risco)', 'Gestante (Alto Risco)', 'Lactante', 'Alergia Alimentar (Glúten)', 'Alergia Alimentar (Lactose)', 'Transtorno do Espectro Autista (TEA)', 'Apoio Psicológico Urgente']
    n_pessoas_com_necessidades = np.random.randint(max(1, int(abrigados_atuais * 0.05)), max(2, int(abrigados_atuais * 0.20)))
    necessidades_especiais_data = []
    for i in range(n_pessoas_com_necessidades):
        necessidades_especiais_data.append({'ID Abrigado': f"PNE{i + 1:03d}_{nome_abrigo[:3].upper()}", 'Tipo de Necessidade': np.random.choice(tipos_necessidade), 'Observações': np.random.choice(['Requer medicação X', 'Dieta especial', 'Acompanhamento', ''])})
    df_necessidades_especiais = pd.DataFrame(necessidades_especiais_data)
    n_necessidades_criticas_medicas = df_necessidades_especiais[df_necessidades_especiais['Tipo de Necessidade'].str.contains('Insulina|Hipertensão|Gestante Alto Risco', case=False)].shape[0]
    suprimentos_base = [
        {'Item': 'Água Potável', 'Unidade': 'Litros', 'Categoria': 'Alimento/Bebida', 'Importancia_Base': 10},
        {'Item': 'Cesta Básica Padrão', 'Unidade': 'Unidades', 'Categoria': 'Alimento/Bebida', 'Importancia_Base': 9},
        {'Item': 'Fórmula Infantil Tipo A', 'Unidade': 'Latas 800g', 'Categoria': 'Alimento/Bebida', 'Importancia_Base': 10},
        {'Item': 'Kit Higiene Pessoal Adulto', 'Unidade': 'Kits', 'Categoria': 'Higiene', 'Importancia_Base': 7},
        {'Item': 'Fralda Infantil M', 'Unidade': 'Pacotes', 'Categoria': 'Higiene', 'Importancia_Base': 8},
        {'Item': 'Fralda Geriátrica G', 'Unidade': 'Pacotes', 'Categoria': 'Higiene', 'Importancia_Base': 8},
        {'Item': 'Colchão Solteiro', 'Unidade': 'Unidades', 'Categoria': 'Abrigo/Conforto', 'Importancia_Base': 6},
        {'Item': 'Cobertor Casal', 'Unidade': 'Unidades', 'Categoria': 'Abrigo/Conforto', 'Importancia_Base': 6},
        {'Item': 'Insulina Regular', 'Unidade': 'Frascos 10ml', 'Categoria': 'Medicamento', 'Importancia_Base': 10},
        {'Item': 'Analgésico Comum', 'Unidade': 'Comprimidos', 'Categoria': 'Medicamento', 'Importancia_Base': 5},
        {'Item': 'Máscaras Descartáveis', 'Unidade': 'Caixas 100unid', 'Categoria': 'Saúde/Proteção', 'Importancia_Base': 4},
        {'Item': 'Álcool em Gel 70%', 'Unidade': 'Frascos 500ml', 'Categoria': 'Higiene', 'Importancia_Base': 6},
        {'Item': 'Ração para Cães', 'Unidade': 'Kg', 'Categoria': 'Pet', 'Importancia_Base': 8},
        {'Item': 'Ração para Gatos', 'Unidade': 'Kg', 'Categoria': 'Pet', 'Importancia_Base': 8},
        {'Item': 'Areia Sanitária', 'Unidade': 'Pacotes', 'Categoria': 'Pet', 'Importancia_Base': 6},
    ]
    df_suprimentos = pd.DataFrame(suprimentos_base)
    df_suprimentos['Estoque Atual'] = np.random.randint(5, 200, len(df_suprimentos))
    consumo = []
    for _, row in df_suprimentos.iterrows():
        base_c = np.random.uniform(0.05, 0.3)
        if row['Item'] == 'Água Potável': consumo_item = abrigados_atuais * 3
        elif row['Item'] == 'Cesta Básica Padrão': consumo_item = abrigados_atuais / 4
        elif 'Fórmula Infantil' in row['Item']: consumo_item = df_perfil_etario.iloc[0]['Quantidade'] * 0.2
        elif 'Fralda Infantil' in row['Item']: consumo_item = n_criancas_0_12 * 0.15
        elif 'Fralda Geriátrica' in row['Item']: consumo_item = n_idosos_60_mais * 0.1
        elif 'Insulina' in row['Item']: consumo_item = df_necessidades_especiais[df_necessidades_especiais['Tipo de Necessidade'].str.contains('Insulina')].shape[0] * 0.1
        elif 'Ração para Cães' in row['Item']: consumo_item = n_caes * 0.4
        elif 'Ração para Gatos' in row['Item']: consumo_item = n_gatos * 0.15
        elif 'Areia Sanitária' in row['Item']: consumo_item = n_pets_total * 0.1
        else: consumo_item = abrigados_atuais * base_c
        consumo.append(max(0.1, round(consumo_item, 1)))
    
    #=== HISTÓRICO DE CONSUMO ===
    df_suprimentos['Consumo Diário Previsto (IA)'] = consumo
    dias_historico = 7
    df_historico_consumo = []
    for _, row in df_suprimentos.iterrows():
        consumo_hist = np.maximum(0, row['Consumo Diário Previsto (IA)'] + np.random.normal(0, row['Consumo Diário Previsto (IA)'] * 0.3, dias_historico)).round(1)
        for i, c in enumerate(consumo_hist):
            df_historico_consumo.append({'Data': pd.to_datetime('today').normalize() - timedelta(days=dias_historico - 1 - i), 'Item': row['Item'], 'Categoria': row['Categoria'], 'Consumo': c})
    df_historico_consumo = pd.DataFrame(df_historico_consumo)
    taxa_ocupacao_num = abrigados_atuais / capacidade_maxima
    condicoes_abrigo = {"Lotação Status": "🟢 OK" if taxa_ocupacao_num < 0.85 else ("🟡 Atenção" if taxa_ocupacao_num < 1 else "🔴 Crítico"), "Sanitários Info": f"{np.random.randint(max(1, int(abrigados_atuais / 30)), max(2, int(abrigados_atuais / 20)))} de {max(2, int(abrigados_atuais / 20))} (Ideal: {max(1, round(abrigados_atuais / 20))})", "Limpeza Geral": np.random.choice(["Boa", "Regular", "Precisa Melhoria"]), "Incidentes Segurança (24h)": np.random.randint(0, 2)}
    return {"nome_abrigo": nome_abrigo, "endereco": detalhes_abrigo['endereco'], "administrador": detalhes_abrigo['administrador'], "telefone": detalhes_abrigo['telefone'], "capacidade_maxima": capacidade_maxima, "abrigados_atuais": abrigados_atuais, "df_perfil_etario": df_perfil_etario, "n_criancas_0_12": n_criancas_0_12, "n_idosos_60_mais": n_idosos_60_mais, "df_necessidades_especiais": df_necessidades_especiais, "n_necessidades_criticas_medicas": n_necessidades_criticas_medicas, "df_suprimentos": df_suprimentos, "condicoes_abrigo": condicoes_abrigo, "df_historico_consumo": df_historico_consumo, "n_pets_total": n_pets_total, "df_perfil_pets": df_perfil_pets
}

def calcular_saude_geral_abrigo(dados_abrigo):
    df_s = dados_abrigo['df_suprimentos']
    autonomia_agua = df_s.loc[df_s['Item'] == 'Água Potável', 'Autonomia Estimada (IA)'].iloc[0] if not df_s[df_s['Item'] == 'Água Potável'].empty else 0
    autonomia_comida = df_s.loc[df_s['Item'] == 'Cesta Básica Padrão', 'Autonomia Estimada (IA)'].iloc[0] if not df_s[df_s['Item'] == 'Cesta Básica Padrão'].empty else 0
    taxa_ocupacao = dados_abrigo["abrigados_atuais"] / dados_abrigo["capacidade_maxima"]
    score = 0
    if autonomia_agua < 1 or autonomia_comida < 1: score += 50
    elif autonomia_agua < 2 or autonomia_comida < 2: score += 25
    if taxa_ocupacao >= 1: score += 30
    elif taxa_ocupacao > 0.9: score += 15
    if dados_abrigo['n_necessidades_criticas_medicas'] > dados_abrigo['abrigados_atuais'] * 0.1: score += 10
    if score >= 50: return "🔴 Crítico"
    if score >= 25: return "🟡 Atenção"
    return "🟢 Estável"

def calcular_criticidade_impacto(row):
    autonomia = row['Autonomia Estimada (IA)']
    importancia = row['Importancia_Base']
    score_impacto = (10 - min(autonomia, 10)) * importancia
    if autonomia <= 0: return f"🆘 Zerado! ({score_impacto:.0f})"
    if score_impacto >= 70: return f"🔴 Crítico ({score_impacto:.0f})"
    if score_impacto >= 40: return f"🟡 Atenção ({score_impacto:.0f})"
    return f"🟢 OK ({score_impacto:.0f})"


# --- INÍCIO DO LAYOUT DO STREAMLIT ---

st.sidebar.image("C:\\Users\\vinim\\Downloads\\ShelterTech.svg", width=250)
st.sidebar.title("Visão do Abrigo")

# --- INICIALIZAÇÃO E GERENCIAMENTO DE ESTADO ---
if 'lista_abrigos_simulados' not in st.session_state:
    st.session_state.lista_abrigos_simulados = {
        "Escola Bem-Viver": {"endereco": "Av. da Esperança, 100", "administrador": "Ana Silva", "telefone": "(11) 98765-1234"},
        "Ginásio Mãos Unidas": {"endereco": "Rua dos Atletas, 200", "administrador": "Carlos Mendes", "telefone": "(11) 98765-2345"},
        "Centro Comunitário Harmonia": {"endereco": "Praça da União, 300", "administrador": "Beatriz Costa", "telefone": "(11) 98765-3456"},
        "Igreja Matriz Acolhimento": {"endereco": "Largo da Sé, 01", "administrador": "Padre João", "telefone": "(11) 98765-4567"},
        "Salão Paroquial Boa Nova": {"endereco": "Travessa da Fé, 77", "administrador": "Irmã Lúcia", "telefone": "(11) 98765-5678"}
    }

abrigo_selecionado_nome = st.sidebar.selectbox(
    "Selecione o Abrigo:",
    options=list(st.session_state.lista_abrigos_simulados.keys()),
    key="select_abrigo"
)

# Lógica para carregar/recarregar dados apenas quando necessário
if 'abrigo_carregado' not in st.session_state or st.session_state.abrigo_carregado != abrigo_selecionado_nome:
    detalhes_abrigo = st.session_state.lista_abrigos_simulados[abrigo_selecionado_nome]
    seed_offset = list(st.session_state.lista_abrigos_simulados.keys()).index(abrigo_selecionado_nome)
    st.session_state.dados_abrigo = gerar_dados_abrigo_completos(abrigo_selecionado_nome, detalhes_abrigo, seed_offset)
    st.session_state.abrigo_carregado = abrigo_selecionado_nome

with st.sidebar.expander("⚙️ Ajustar Estoque de Itens", expanded=True):
    with st.form("form_ajustar_estoque", clear_on_submit=True):
        
        lista_itens_atuais = st.session_state.dados_abrigo['df_suprimentos']['Item'].tolist()
        
        item_para_atualizar = st.selectbox(
            "Ajuste de estoque", 
            options=lista_itens_atuais
        )
        
        tipo_movimentacao = st.radio(
            "Selecione a Ação", 
            ["Entrada", "Saída"],
            horizontal=True
        )

        quantidade = st.number_input(
            "Quantidade", 
            min_value=1, 
            step=1
        )
        
        submitted = st.form_submit_button("Confirmar Movimentação")
        
        if submitted:
            df_suprimentos = st.session_state.dados_abrigo['df_suprimentos']
            idx = df_suprimentos.index[df_suprimentos['Item'] == item_para_atualizar].tolist()[0]
            
            if tipo_movimentacao == "Entrada (Adicionar)":
                df_suprimentos.loc[idx, 'Estoque Atual'] += quantidade
                st.success(f"✅ {quantidade} un. de '{item_para_atualizar}' adicionadas ao estoque!")
            
            elif tipo_movimentacao == "Saída (Dar Baixa)":
                estoque_atual = df_suprimentos.loc[idx, 'Estoque Atual']
                if quantidade > estoque_atual:
                    st.error(f"❌ Não foi possível dar baixa. Estoque insuficiente.")
                else:
                    df_suprimentos.loc[idx, 'Estoque Atual'] -= quantidade
                    st.warning(f"📉 {quantidade} un. de '{item_para_atualizar}' retiradas do estoque.")
            st.rerun()

st.sidebar.image("https://www.fiap.com.br/graduacao/global-solution/svg/header/title.svg", width=250)


# --- LÓGICA PRINCIPAL DO DASHBOARD ---
dados = st.session_state.dados_abrigo
df_suprimentos = dados['df_suprimentos']

df_suprimentos['Autonomia Estimada (IA)'] = (
    df_suprimentos['Estoque Atual'] / df_suprimentos.get('Consumo Diário Previsto (IA)', 0.1)
).replace([np.inf, -np.inf, np.nan], 0).round(1)
df_suprimentos.loc[df_suprimentos['Estoque Atual'] <= 0, 'Autonomia Estimada (IA)'] = 0

saude_geral = calcular_saude_geral_abrigo(dados)

# --- CABEÇALHO DO DASHBOARD ---
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title(f"Abrigo: {dados['nome_abrigo']}")
    st.caption(f"{dados['endereco']} | São Paulo - SP | Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.caption(f"Administrador(a): {dados['administrador']} | Telefone: {dados['telefone']}")
    
with col_header2:
    if saude_geral == "🔴 Crítico":
        st.error(f"SAÚDE GERAL: {saude_geral}")
    elif saude_geral == "🟡 Atenção":
        st.warning(f"SAÚDE GERAL: {saude_geral}")
    else:
        st.success(f"SAÚDE GERAL: {saude_geral}")
st.markdown("---")

# --- LINHA DE KPIs PRINCIPAIS ---
st.subheader(" Painel de Indicadores Chave")
kpi_cols = st.columns(6) 
taxa_ocup_perc = (dados['abrigados_atuais'] / dados['capacidade_maxima']) * 100
kpi_cols[0].metric("👥 Ocupação", f"{dados['abrigados_atuais']}/{dados['capacidade_maxima']}", f"{taxa_ocup_perc:.1f}%", help="Número de abrigados atuais em relação à capacidade máxima do abrigo.")
kpi_cols[1].metric("👶 Crianças (0-12a)", dados['n_criancas_0_12'])
kpi_cols[2].metric("👵 Idosos (60+a)", dados['n_idosos_60_mais'])
kpi_cols[3].metric("⚕️ Nec. Médicas Críticas", dados['n_necessidades_criticas_medicas'], help="Número de abrigados com necessidades médicas que exigem atenção ou medicação específica (ex: Insulina).")

df_s = dados['df_suprimentos']
if not df_s.empty:
    item_critico_autonomia = df_s.loc[df_s['Autonomia Estimada (IA)'].idxmin()]
    kpi_cols[4].metric(f"📉 Ítem crítico ({item_critico_autonomia['Item']})", f"{item_critico_autonomia['Autonomia Estimada (IA)']:.1f} dias")
else:
    kpi_cols[4].metric("📉 Ítem crítico", "N/A")
if 'n_pets_total' in dados:
    kpi_cols[5].metric("🐾 Pets no Abrigo", dados['n_pets_total'])

st.markdown("---")

# --- SEÇÃO 1: PERFIL DOS ABRIGADOS E NECESSIDADES ESPECIAIS ---
st.subheader("🫂 Perfil dos Abrigados e Necessidades")
col_perfil1, col_perfil2 = st.columns([0.4, 0.6])

with col_perfil1:
    st.markdown("##### Distribuição por Faixa Etária")
    fig_faixa_etaria = px.pie(dados['df_perfil_etario'], values='Quantidade', names='Faixa Etária',
                              hole=0.5, color_discrete_sequence=px.colors.sequential.Blues_r)  # Cores suaves
    fig_faixa_etaria.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300, legend_title_text='',
                                   legend_orientation="h", legend_y=-0.2)
    fig_faixa_etaria.update_traces(textposition='inside', textinfo='percent+label',
                                   insidetextfont=dict(color='white', size=10))
    st.plotly_chart(fig_faixa_etaria, use_container_width=True)

# Dentro da seção: # --- SEÇÃO 1: PERFIL DOS ABRIGADOS E NECESSIDADES ESPECIAIS ---
with col_perfil2:
    st.markdown("##### Necessidades Especiais")

    if not dados['df_necessidades_especiais'].empty:
        # Agrupando por 'Tipo de Necessidade' e contando as pessoas
        df_necessidades_agrupado_temp = dados['df_necessidades_especiais'].groupby('Tipo de Necessidade').agg(
            # Mantemos a contagem numérica original para possíveis cálculos futuros ou ordenação
            _QuantidadeNumerica=('ID Abrigado', 'count'),
            Observacao_Exemplo=('Observações', lambda x: next((obs for obs in x if obs and str(obs).strip()), 'N/A'))
        ).reset_index()

        # Função para formatar a string da quantidade
        def formatar_quantidade_display(qtd):
            if qtd == 1:
                return "1 pessoa"
            else:
                # Garantir que é um inteiro antes de formatar na string
                return f"{int(qtd)} pessoas"
                # Aplicando a formatação para criar a coluna de exibição

        df_necessidades_agrupado_temp['Quantidade'] = df_necessidades_agrupado_temp['_QuantidadeNumerica'].apply(
            formatar_quantidade_display)

        # Selecionando e renomeando colunas para a exibição final
        df_para_exibir_necessidades = df_necessidades_agrupado_temp.rename(columns={
            'Tipo de Necessidade': 'Tipo de Necessidade Especial',
            # 'Quantidade' já está com o nome correto para exibição
            'Observacao_Exemplo': 'Exemplo de Observação'
        })

        # Exibindo as colunas desejadas na ordem desejada
        st.dataframe(
            df_para_exibir_necessidades[
                ['Tipo de Necessidade Especial', 'Quantidade', 'Exemplo de Observação']],
            height=380,
            use_container_width=True,
            column_config={
                # A coluna 'Quantidade' agora é uma string formatada, então usamos TextColumn
                "Quantidade": st.column_config.TextColumn("Quantidade de Pessoas"),
                "Exemplo de Observação": st.column_config.TextColumn(width="large")
            },
            hide_index=True  # Para não mostrar o índice do DataFrame
        )
    else:
        st.info("Nenhum registro de necessidade especial inserido para este abrigo.")
st.markdown("---")

#--- SEÇÃO DE PERFIL DOS PETS ---
st.subheader("🐾 Perfil dos Pets no Abrigo")
col_pets1, col_pets2 = st.columns([0.4, 0.6])
with col_pets1:
    if 'df_perfil_pets' in dados and not dados['df_perfil_pets'].empty:
        fig_perfil_pets = px.pie(dados['df_perfil_pets'], values='Quantidade', names='Tipo',
                                 title='Distribuição por Tipo de Pet',
                                 hole=0.5, color_discrete_sequence=px.colors.sequential.Oranges_r)
        fig_perfil_pets.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=300, legend_title_text='')
        fig_perfil_pets.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='white', size=12))
        st.plotly_chart(fig_perfil_pets, use_container_width=True)
with col_pets2:
    st.info("💡 **Lembretes para Pets:**\n\n"
            "- Verificar estoque de ração específica (cães/gatos).\n"
            "- Controlar a disponibilidade de areia sanitária.\n"
            "- Manter uma lista de pets com necessidades especiais (medicação, dieta).")
st.markdown("---")

# --- SEÇÃO 2: CONTROLE DE SUPRIMENTOS E PREVISÕES (IA) ---
st.subheader("🥫 Controle de Suprimentos e Previsões por IA")

# --- Filtros Dinâmicos para Suprimentos ---
col_filt1, col_filt2, col_filt3 = st.columns(3)
categorias_suprimentos = ['Todas'] + sorted(dados['df_suprimentos']['Categoria'].unique())
filtro_categoria = col_filt1.selectbox("Filtrar por Categoria:", options=categorias_suprimentos)

niveis_criticidade_filtro = ['Todos', '🆘 Zerado!', '🔴 Crítico', '🟡 Atenção', '🟢 OK']
filtro_criticidade = col_filt2.selectbox("Filtrar por Criticidade (Impacto):", options=niveis_criticidade_filtro)

# Alteração para definir o máximo do filtro de autonomia para 60 dias (aprox. 2 meses)
max_dias_filtro_autonomia = 60
filtro_autonomia = col_filt3.slider(
    "Autonomia Estimada (IA) menor ou igual a (dias):", # Label do slider
    min_value=0,                                         # Valor mínimo do slider
    max_value=max_dias_filtro_autonomia,                 # Valor máximo do slider (60 dias)
    value=max_dias_filtro_autonomia,                     # Valor padrão inicial do slider (60 dias)
    step=1                                               # Incremento do slider (de 1 em 1 dia)
)

# Aplicar filtros
df_suprimentos_filtrado = dados['df_suprimentos'].copy()
df_suprimentos_filtrado['Criticidade por Impacto'] = df_suprimentos_filtrado.apply(calcular_criticidade_impacto, axis=1)

if filtro_categoria != 'Todas':
    df_suprimentos_filtrado = df_suprimentos_filtrado[df_suprimentos_filtrado['Categoria'] == filtro_categoria]
if filtro_criticidade != 'Todos':
    # Precisa ajustar o filtro para pegar o início da string de criticidade
    df_suprimentos_filtrado = df_suprimentos_filtrado[
        df_suprimentos_filtrado['Criticidade por Impacto'].str.startswith(filtro_criticidade.split(' ')[0])]
df_suprimentos_filtrado = df_suprimentos_filtrado[
    df_suprimentos_filtrado['Autonomia Estimada (IA)'] <= filtro_autonomia]

st.markdown("##### Inventário Detalhado e Projeção de Suprimentos")
st.dataframe(
    df_suprimentos_filtrado[
        ['Item', 'Categoria', 'Estoque Atual', 'Consumo Diário Previsto (IA)', 'Autonomia Estimada (IA)',
         'Criticidade por Impacto', 'Importancia_Base']],
    height=400,
    use_container_width=True,
    column_config={
        "Autonomia Estimada (IA)": st.column_config.NumberColumn(format="%.1f d"),
        "Consumo Diário Previsto (IA)": st.column_config.NumberColumn(format="%.1f /dia"),
        "Importancia_Base": st.column_config.NumberColumn("Importância (1-10)",
                                                          help="Criticidade base do item (10=máx)"),
        "Criticidade por Impacto": st.column_config.TextColumn("Impacto (Score)",
                                                               help="Score ponderado: (10-Autonomia) * Importância. Quanto maior, mais crítico.")
    }
)

# --- Alertas Priorizados ---
st.markdown("##### Alertas Priorizados (Sistema de Priorização por Tempo e Gravidade)")
alertas_df = df_suprimentos_filtrado[
    df_suprimentos_filtrado['Criticidade por Impacto'].str.contains('🆘 Zerado|🔴 Crítico|🟡 Atenção')
].sort_values(by='Importancia_Base', ascending=False)  # Ordenar por importância base, pode ser mais complexo

if alertas_df.empty:
    st.success("✅ Nenhum alerta urgente de suprimentos com os filtros aplicados.")
else:
    for _, row in alertas_df.iterrows():
        impact_score_str = row['Criticidade por Impacto'].split('(')[-1].replace(')', '')
        mensagem = f"**{row['Item']}** (Cat: {row['Categoria']}) - Autonomia: {row['Autonomia Estimada (IA)']} dias. Impacto: {impact_score_str}."
        if '🆘 Zerado!' in row['Criticidade por Impacto'] or '🔴 Crítico' in row['Criticidade por Impacto']:
            st.error(f"🆘 URGENTE: {mensagem} Necessidade de reposição imediata!")
        elif '🟡 Atenção' in row['Criticidade por Impacto']:
            st.warning(f"🟡 ATENÇÃO: {mensagem} Planejar reposição em breve.")

st.markdown("---")

# --- Análises Adicionais de Suprimentos ---
st.subheader("🔬 Análises Adicionais de Suprimentos")
col_analise1, col_analise2 = st.columns(2)

with col_analise1:
    st.markdown("##### Visualização Temporal da Demanda (Itens Selecionados)")
    itens_para_grafico_temporal = df_suprimentos_filtrado.sort_values(by='Importancia_Base', ascending=False)[
                                      'Item'].unique()[:3]  # Top 3 por importância
    if len(itens_para_grafico_temporal) > 0:
        df_hist_filtrado = dados['df_historico_consumo'][
            dados['df_historico_consumo']['Item'].isin(itens_para_grafico_temporal)]
        if not df_hist_filtrado.empty:
            fig_temporal = px.line(df_hist_filtrado, x='Data', y='Consumo', color='Item', markers=True,
                                   title=f"Histórico de Consumo (Últimos 7 dias)")
            fig_temporal.update_layout(height=350, legend_title_text='')
            st.plotly_chart(fig_temporal, use_container_width=True)
        else:
            st.info("Sem dados históricos suficientes para os itens filtrados.")
    else:
        st.info("Selecione itens na tabela para ver o histórico.")

with col_analise2:
    st.markdown("##### Análise de Consumo - Curva ABC (Conceitual)")
    st.caption(
        "A Curva ABC (Princípio de Pareto 80/20) ajuda a identificar os itens mais significativos em termos de valor de consumo ou quantidade, para focar os esforços de gestão.")
    # Simulação simples: Ordenar por 'Consumo Diário Previsto (IA)' * 'Importancia_Base' (simulando valor de consumo)
    df_abc = df_suprimentos_filtrado.copy()
    df_abc['Valor_Consumo_Simulado'] = df_abc['Consumo Diário Previsto (IA)'] * df_abc['Importancia_Base']
    df_abc = df_abc.sort_values(by='Valor_Consumo_Simulado', ascending=False)

    st.markdown("**Top 5 Itens por 'Valor de Consumo' (Simulado):**")
    if not df_abc.empty:
        for i, row in df_abc.head(5).iterrows():
            st.markdown(f"- **{row['Item']}**: Valor Consumo Simulado = {row['Valor_Consumo_Simulado']:.1f}")
    else:
        st.write("Nenhum item para exibir com os filtros atuais.")
    st.info(
        "💡 **Ação:** Priorizar controle e negociação para itens da 'Classe A' (os ~20% de itens que representam ~80% do valor de consumo).")

# --- Placeholder para Recomendações de IA e Comunicação ---
st.markdown("---")
st.subheader("🤖 Assistência Inteligente e Comunicação")
col_ia_rec, col_ia_com = st.columns(2)

with col_ia_rec:
    st.markdown("##### Recomendações Automatizadas (IA) - Exemplo")
    st.info(
        "ℹ️ *Conceitual: Em um sistema completo, a IA poderia sugerir transferências entre abrigos ou otimizar pedidos.*")
    # Exemplo de recomendação simulada (não funcional)
    if dados['df_suprimentos'][
        'Autonomia Estimada (IA)'].min() < 1.5 and abrigo_selecionado_nome == "Escola Acolhedora Esperança":
        st.success(
            "✅ **Sugestão IA:** Transferir 200L de Água do 'Ginásio Mãos Unidas' (Estoque: Alto) para 'Escola Acolhedora Esperança'.")
    else:
        st.write("Nenhuma recomendação crítica no momento.")

with col_ia_com:
    st.markdown("##### Módulo de Comunicação Direta (Placeholder)")
    st.text_area("Enviar mensagem para Coordenação Central:", height=100, placeholder="Digite sua mensagem aqui...")
    if st.button("📨 Enviar Mensagem"):
        st.success("Mensagem enviada (simulação)!")

st.markdown("---")
st.caption(f"Projeto Shelter Tech - FIAP Global Solution {datetime.now().year} (Dashboard com dados simulados)")