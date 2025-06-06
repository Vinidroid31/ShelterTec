# cd C:\Users\vinim\PycharmProjects\FIAP_geral\GS_1s_eventos_extremos
# streamlit run dash_sheltertech.py   

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA STREAMLIT ---
st.set_page_config(
    page_title="Gestão Eficiente de Abrigos",
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .stMetricValue { font-size: 28px !important; }
    .stMetricLabel { font-size: 14px !important; color: #555 !important; }
</style>
""", unsafe_allow_html=True)


# --- FUNÇÕES AUXILIARES ---
def recalcular_previsoes_suprimentos(df_suprimentos):
    """Recalcula a autonomia estimada com base no estoque atual e consumo."""
    if df_suprimentos is None or df_suprimentos.empty:
        return df_suprimentos
    # Garante que 'Consumo Diário Previsto (IA)' exista e seja numérico
    if 'Consumo Diário Previsto (IA)' not in df_suprimentos.columns:
        df_suprimentos['Consumo Diário Previsto (IA)'] = 0.1 # Valor padrão se não existir
    
    consumo = pd.to_numeric(df_suprimentos['Consumo Diário Previsto (IA)'], errors='coerce').replace(0, np.nan)
    estoque = pd.to_numeric(df_suprimentos['Estoque Atual'], errors='coerce')

    df_suprimentos['Autonomia Estimada (IA)'] = (estoque / consumo).replace([np.inf, -np.inf], 0).fillna(0).round(1)
    df_suprimentos.loc[estoque <= 0, 'Autonomia Estimada (IA)'] = 0
    return df_suprimentos

@st.cache_data(ttl=3600)
def gerar_dados_abrigo_completos(nome_abrigo, detalhes_abrigo, seed_offset=0):
    np.random.seed(42 + seed_offset)
    capacidade_maxima = np.random.randint(80, 250)
    abrigados_atuais = np.random.randint(int(capacidade_maxima * 0.4), capacidade_maxima + 1)
    
    # Gênero apenas Feminino e Masculino
    generos_nomes = ['Feminino', 'Masculino']
    quantidades_genero = np.random.multinomial(abrigados_atuais, [0.49, 0.51]) if abrigados_atuais > 0 else [0,0]
    df_perfil_genero = pd.DataFrame({'Gênero': generos_nomes, 'Quantidade': quantidades_genero})
    n_mulheres = int(df_perfil_genero[df_perfil_genero['Gênero'] == 'Feminino']['Quantidade'].sum())
    n_homens = int(df_perfil_genero[df_perfil_genero['Gênero'] == 'Masculino']['Quantidade'].sum())
    
    faixas_etarias_nomes = ['Bebês (0-2a)', 'Crianças (3-5a)', 'Crianças (6-12a)', 'Adolescentes (13-17a)', 'Adultos (18-59a)', 'Idosos (60-74a)', 'Idosos (75+a)']
    quantidades_faixas = np.random.multinomial(abrigados_atuais, [0.05, 0.08, 0.12, 0.10, 0.40, 0.15, 0.10]) if abrigados_atuais > 0 else [0]*len(faixas_etarias_nomes)
    df_perfil_etario = pd.DataFrame({'Faixa Etária': faixas_etarias_nomes, 'Quantidade': quantidades_faixas})
    n_criancas_0_12 = int(df_perfil_etario[df_perfil_etario['Faixa Etária'].isin(['Bebês (0-2a)', 'Crianças (3-5a)', 'Crianças (6-12a)'])]['Quantidade'].sum())
    n_idosos_60_mais = int(df_perfil_etario[df_perfil_etario['Faixa Etária'].isin(['Idosos (60-74a)', 'Idosos (75+a)'])]['Quantidade'].sum())
    
    n_pets_total = np.random.randint(max(0,int(abrigados_atuais * 0.05)), int(abrigados_atuais * 0.15) +1 ) if abrigados_atuais > 0 else 0
    tipos_pet = ['Cães', 'Gatos', 'Pequenos Animais']
    quantidades_pets = np.random.multinomial(n_pets_total, [0.6, 0.35, 0.05]) if n_pets_total > 0 else [0, 0, 0]
    df_perfil_pets = pd.DataFrame({'Tipo': tipos_pet, 'Quantidade': quantidades_pets})
    n_caes = int(df_perfil_pets[df_perfil_pets['Tipo'] == 'Cães']['Quantidade'].sum())
    n_gatos = int(df_perfil_pets[df_perfil_pets['Tipo'] == 'Gatos']['Quantidade'].sum())

    tipos_necessidade = ['Diabetes Tipo 1 (Insulina)', 'Diabetes Tipo 2 (Oral)', 'Hipertensão Severa', 'Mobilidade Reduzida - Cadeirante', 'Mobilidade Reduzida - Andador', 'Gestante (Baixo Risco)', 'Gestante (Alto Risco)', 'Lactante', 'Alergia Alimentar (Glúten)', 'Alergia Alimentar (Lactose)', 'Transtorno do Espectro Autista (TEA)', 'Apoio Psicológico Urgente']
    n_pessoas_com_necessidades = np.random.randint(max(0, int(abrigados_atuais * 0.05)), max(1, int(abrigados_atuais * 0.20)) +1 ) if abrigados_atuais > 0 else 0
    necessidades_especiais_data = []
    if n_pessoas_com_necessidades > 0:
        for i in range(n_pessoas_com_necessidades):
            necessidades_especiais_data.append({'ID Abrigado': f"PNE{i + 1:03d}_{nome_abrigo[:3].upper()}", 'Tipo de Necessidade': np.random.choice(tipos_necessidade), 'Observações': np.random.choice(['Requer medicação X', 'Dieta especial', 'Acompanhamento', ''])})
    df_necessidades_especiais = pd.DataFrame(necessidades_especiais_data)
    n_necessidades_criticas_medicas = df_necessidades_especiais[df_necessidades_especiais['Tipo de Necessidade'].str.contains('Insulina|Hipertensão|Gestante Alto Risco', case=False)].shape[0] if not df_necessidades_especiais.empty else 0
    
    suprimentos_base = [ 
        {'Item': 'Água Potável', 'Unidade': 'Litros', 'Categoria': 'Alimento/Bebida', 'Importancia_Base': 10}, 
        {'Item': 'Arroz', 'Unidade': 'Kg', 'Categoria': 'Alimento/Bebida', 'Importancia_Base': 9},
        {'Item': 'Feijão', 'Unidade': 'Kg', 'Categoria': 'Alimento/Bebida', 'Importancia_Base': 9},
        {'Item': 'Óleo de Soja', 'Unidade': 'Litros', 'Categoria': 'Alimento/Bebida', 'Importancia_Base': 7},
        {'Item': 'Fórmula Infantil Tipo A', 'Unidade': 'Latas 800g', 'Categoria': 'Alimento/Bebida', 'Importancia_Base': 10}, 
        {'Item': 'Kit Higiene Pessoal Adulto', 'Unidade': 'Kits', 'Categoria': 'Higiene', 'Importancia_Base': 7}, 
        {'Item': 'Fralda Infantil M', 'Unidade': 'Pacotes', 'Categoria': 'Higiene', 'Importancia_Base': 8}, 
        {'Item': 'Fralda Geriátrica G', 'Unidade': 'Pacotes', 'Categoria': 'Higiene', 'Importancia_Base': 8}, 
        {'Item': 'Colchão Solteiro', 'Unidade': 'Unidades', 'Categoria': 'Abrigo/Conforto', 'Importancia_Base': 6}, 
        {'Item': 'Cobertor Casal', 'Unidade': 'Unidades', 'Categoria': 'Abrigo/Conforto', 'Importancia_Base': 6}, 
        {'Item': 'Insulina Regular', 'Unidade': 'Frascos 10ml', 'Categoria': 'Medicamento', 'Importancia_Base': 10}, 
        {'Item': 'Analgésico Comum', 'Unidade': 'Comprimidos', 'Categoria': 'Medicamento', 'Importancia_Base': 5}, 
        {'Item': 'Máscaras Descartáveis', 'Unidade': 'Caixas 100un', 'Categoria': 'Saúde/Proteção', 'Importancia_Base': 4}, 
        {'Item': 'Álcool em Gel 70%', 'Unidade': 'Frascos 500ml', 'Categoria': 'Higiene', 'Importancia_Base': 6}, 
        {'Item': 'Ração para Cães', 'Unidade': 'Kg', 'Categoria': 'Pet', 'Importancia_Base': 8}, 
        {'Item': 'Ração para Gatos', 'Unidade': 'Kg', 'Categoria': 'Pet', 'Importancia_Base': 8}, 
        {'Item': 'Areia Sanitária', 'Unidade': 'Pacotes', 'Categoria': 'Pet', 'Importancia_Base': 6}, 
    ]
    df_suprimentos = pd.DataFrame(suprimentos_base)
    df_suprimentos['Estoque Atual'] = np.random.randint(5, 200, len(df_suprimentos))
    consumo = []
    if abrigados_atuais > 0:
        for _, row in df_suprimentos.iterrows():
            base_c = np.random.uniform(0.05, 0.3)
            consumo_item = abrigados_atuais * base_c # Default
            if row['Item'] == 'Água Potável': consumo_item = abrigados_atuais * 3
            elif row['Item'] == 'Arroz': consumo_item = abrigados_atuais * 0.15 
            elif row['Item'] == 'Feijão': consumo_item = abrigados_atuais * 0.1 
            elif row['Item'] == 'Óleo de Soja': consumo_item = abrigados_atuais * 0.03
            elif 'Fórmula Infantil' in row['Item']: consumo_item = df_perfil_etario.iloc[0]['Quantidade'] * 0.2 if not df_perfil_etario.empty else 0
            elif 'Fralda Infantil' in row['Item']: consumo_item = n_criancas_0_12 * 0.15
            elif 'Fralda Geriátrica' in row['Item']: consumo_item = n_idosos_60_mais * 0.1
            elif 'Insulina' in row['Item']: consumo_item = n_necessidades_criticas_medicas * 0.1
            elif 'Ração para Cães' in row['Item']: consumo_item = n_caes * 0.4
            elif 'Ração para Gatos' in row['Item']: consumo_item = n_gatos * 0.15
            elif 'Areia Sanitária' in row['Item']: consumo_item = n_pets_total * 0.1
            consumo.append(max(0.1, round(consumo_item, 1)))
    else: 
        consumo = [0.1] * len(df_suprimentos)


    df_suprimentos['Consumo Diário Previsto (IA)'] = consumo
    df_suprimentos = recalcular_previsoes_suprimentos(df_suprimentos.copy()) 

    dias_historico = 7
    df_historico_consumo = []
    if not df_suprimentos.empty:
        for _, row in df_suprimentos.iterrows():
            consumo_diario = row.get('Consumo Diário Previsto (IA)', 0.1)
            consumo_hist = np.maximum(0, consumo_diario + np.random.normal(0, consumo_diario * 0.3, dias_historico)).round(1)
            for i, c_val in enumerate(consumo_hist):
                df_historico_consumo.append({'Data': pd.to_datetime('today').normalize() - timedelta(days=dias_historico - 1 - i), 'Item': row['Item'], 'Categoria': row['Categoria'], 'Consumo': c_val})
    df_historico_consumo = pd.DataFrame(df_historico_consumo)

    return {"nome_abrigo": nome_abrigo, "endereco": detalhes_abrigo['endereco'], "administrador": detalhes_abrigo['administrador'], "telefone": detalhes_abrigo['telefone'], "capacidade_maxima": capacidade_maxima, "abrigados_atuais": abrigados_atuais, "df_perfil_etario": df_perfil_etario, "n_criancas_0_12": n_criancas_0_12, "n_idosos_60_mais": n_idosos_60_mais, "df_necessidades_especiais": df_necessidades_especiais, "n_necessidades_criticas_medicas": n_necessidades_criticas_medicas, "df_suprimentos": df_suprimentos, "df_historico_consumo": df_historico_consumo, "n_pets_total": n_pets_total, "df_perfil_pets": df_perfil_pets, "df_perfil_genero": df_perfil_genero, "n_homens": n_homens, "n_mulheres": n_mulheres}

def calcular_saude_geral_abrigo(dados_abrigo):
    df_s = dados_abrigo.get('df_suprimentos', pd.DataFrame())
    if df_s.empty: return "⚪ Dados Insuficientes"
    
    if 'Autonomia Estimada (IA)' not in df_s.columns:
        df_s = recalcular_previsoes_suprimentos(df_s.copy()) 

    autonomia_agua = df_s.loc[df_s['Item'] == 'Água Potável', 'Autonomia Estimada (IA)'].iloc[0] if not df_s[df_s['Item'] == 'Água Potável'].empty else 0
    autonomia_comida = df_s.loc[df_s['Item'] == 'Arroz', 'Autonomia Estimada (IA)'].iloc[0] if not df_s[df_s['Item'] == 'Arroz'].empty else 0
    
    capacidade = dados_abrigo.get("capacidade_maxima", 1)
    abrigados = dados_abrigo.get("abrigados_atuais", 0)
    taxa_ocupacao = abrigados / capacidade if capacidade > 0 else 1
    
    score = 0
    if autonomia_agua < 1 or autonomia_comida < 1: score += 50
    elif autonomia_agua < 2 or autonomia_comida < 2: score += 25
    if taxa_ocupacao >= 1: score += 30
    elif taxa_ocupacao > 0.9: score += 15
    if dados_abrigo.get('n_necessidades_criticas_medicas', 0) > abrigados * 0.1 and abrigados > 0: score += 10
    
    if score >= 50: return "🔴 Crítico"
    if score >= 25: return "🟡 Atenção"
    return "🟢 Estável"

def calcular_criticidade_impacto(row):
    autonomia = row.get('Autonomia Estimada (IA)', 0)
    importancia = row.get('Importancia_Base', 0)
    score_impacto = (10 - min(autonomia, 10)) * importancia
    if autonomia <= 0: return f"🆘 Zerado! ({score_impacto:.0f})"
    if score_impacto >= 70: return f"🔴 Crítico ({score_impacto:.0f})"
    if score_impacto >= 40: return f"🟡 Atenção ({score_impacto:.0f})"
    return f"🟢 OK ({score_impacto:.0f})"

# --- LAYOUT PRINCIPAL ---
try:
    st.sidebar.image("ShelterTech.svg", width=250) 
except Exception:
    try:
        st.sidebar.image("C:\\Users\\vinim\\Downloads\\ShelterTech.svg", width=250) 
    except Exception:
        st.sidebar.warning("Logo 'ShelterTech.svg' não encontrado.")

st.sidebar.title("Visão do Abrigo")

if 'lista_abrigos_simulados' not in st.session_state:
    st.session_state.lista_abrigos_simulados = { "Escola Bem-Viver": {"endereco": "Av. da Esperança, 100", "administrador": "Ana Silva", "telefone": "(11) 98765-1234"}, "Ginásio Mãos Unidas": {"endereco": "Rua dos Atletas, 200", "administrador": "Carlos Mendes", "telefone": "(11) 98765-2345"}, "Centro Comunitário Harmonia": {"endereco": "Praça da União, 300", "administrador": "Beatriz Costa", "telefone": "(11) 98765-3456"}, "Igreja Matriz Acolhimento": {"endereco": "Largo da Sé, 01", "administrador": "Padre João", "telefone": "(11) 98765-4567"}, "Salão Paroquial Boa Nova": {"endereco": "Travessa da Fé, 77", "administrador": "Irmã Lúcia", "telefone": "(11) 98765-5678"} }

abrigo_selecionado_nome = st.sidebar.selectbox("Selecione o Abrigo:", options=list(st.session_state.lista_abrigos_simulados.keys()), key="select_abrigo")

if 'dados_abrigo' not in st.session_state or \
   st.session_state.get('abrigo_carregado') != abrigo_selecionado_nome:
    detalhes_abrigo = st.session_state.lista_abrigos_simulados[abrigo_selecionado_nome]
    seed_offset = list(st.session_state.lista_abrigos_simulados.keys()).index(abrigo_selecionado_nome)
    st.session_state.dados_abrigo = gerar_dados_abrigo_completos(abrigo_selecionado_nome, detalhes_abrigo, seed_offset)
    st.session_state.abrigo_carregado = abrigo_selecionado_nome


with st.sidebar.expander("⚙️ Ajustar Estoque (Abrigo Selecionado)", expanded=True):
    dados_abrigo_atual = st.session_state.get('dados_abrigo', {})
    df_suprimentos_sidebar = dados_abrigo_atual.get('df_suprimentos', pd.DataFrame())

    with st.form("form_ajustar_estoque", clear_on_submit=True):
        lista_itens_atuais = df_suprimentos_sidebar['Item'].tolist() if not df_suprimentos_sidebar.empty else []
        
        item_para_atualizar = st.selectbox(
            "Selecione o Item para Ajustar Estoque:", 
            options=lista_itens_atuais,
            key="item_estoque_sidebar",
            help="Lista de itens do abrigo atualmente selecionado."
        )
        tipo_movimentacao = st.radio("Selecione a Ação:", ["Entrada", "Saída"], horizontal=True, key="tipo_mov_sidebar")
        quantidade = st.number_input("Quantidade:", min_value=1, step=1, key="qtd_mov_sidebar")
        submitted = st.form_submit_button("Confirmar Movimentação")

        if submitted and item_para_atualizar:
            df_suprimentos_sessao = st.session_state.dados_abrigo.get('df_suprimentos', pd.DataFrame()).copy()
            
            if not df_suprimentos_sessao.empty:
                idx_list = df_suprimentos_sessao.index[df_suprimentos_sessao['Item'] == item_para_atualizar].tolist()
                if idx_list:
                    idx = idx_list[0]
                    estoque_atual_item = df_suprimentos_sessao.loc[idx, 'Estoque Atual']
                    if tipo_movimentacao == "Entrada":
                        df_suprimentos_sessao.loc[idx, 'Estoque Atual'] += quantidade
                        st.success(f"✅ {quantidade} un. de '{item_para_atualizar}' adicionadas!")
                    elif tipo_movimentacao == "Saída":
                        if quantidade <= estoque_atual_item:
                            df_suprimentos_sessao.loc[idx, 'Estoque Atual'] -= quantidade
                            st.warning(f"📉 {quantidade} un. de '{item_para_atualizar}' retiradas.")
                        else:
                            st.error(f"❌ Estoque de '{item_para_atualizar}' insuficiente ({estoque_atual_item} un.) para retirar {quantidade} un.")
                    
                    st.session_state.dados_abrigo['df_suprimentos'] = recalcular_previsoes_suprimentos(df_suprimentos_sessao)
                    st.rerun() 
                else:
                    st.error(f"Item '{item_para_atualizar}' não encontrado nos suprimentos.")
            else:
                st.error("Dados de suprimentos não carregados.")
        elif submitted and not item_para_atualizar:
            st.warning("Por favor, selecione um item para ajustar o estoque.")

try:
    st.sidebar.image("https://www.fiap.com.br/graduacao/global-solution/svg/header/title.svg", width=250)
except Exception:
    st.sidebar.warning("Logo FIAP não encontrado.")

st.title("🏨 Gestão Eficiente de Abrigos")
st.caption(f"Dados de São Paulo, Brasil | Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

tab_consolidado, tab_detalhado = st.tabs(["📊 Visão Consolidada", "📄 Visão Detalhada do Abrigo"])

with tab_consolidado:
    st.header("Situação Geral dos Abrigos")
    dados_consolidados_list = []
    total_capacidade_geral = 0
    total_abrigados_geral = 0
    total_homens_geral = 0
    total_mulheres_geral = 0
    total_criancas_geral = 0
    total_idosos_geral = 0
    total_nec_med_criticas_geral = 0
    total_pets_geral = 0

    for i, (nome_abrigo_loop, detalhes_abrigo_loop) in enumerate(st.session_state.lista_abrigos_simulados.items()):
        if nome_abrigo_loop == st.session_state.get('abrigo_carregado') and 'dados_abrigo' in st.session_state:
            dados_abrigo_temp = st.session_state.dados_abrigo
        else: 
            dados_abrigo_temp = gerar_dados_abrigo_completos(nome_abrigo_loop, detalhes_abrigo_loop, seed_offset=i)
        
        total_capacidade_geral += dados_abrigo_temp.get("capacidade_maxima", 0)
        total_abrigados_geral += dados_abrigo_temp.get("abrigados_atuais", 0) 
        total_homens_geral += dados_abrigo_temp.get("n_homens", 0)
        total_mulheres_geral += dados_abrigo_temp.get("n_mulheres", 0)
        total_criancas_geral += dados_abrigo_temp.get("n_criancas_0_12", 0)
        total_idosos_geral += dados_abrigo_temp.get("n_idosos_60_mais", 0)
        total_nec_med_criticas_geral += dados_abrigo_temp.get("n_necessidades_criticas_medicas", 0)
        total_pets_geral += dados_abrigo_temp.get("n_pets_total", 0)

        saude = calcular_saude_geral_abrigo(dados_abrigo_temp)
        capacidade_temp = dados_abrigo_temp.get('capacidade_maxima', 1)
        taxa_ocup_perc = (dados_abrigo_temp.get('abrigados_atuais', 0) / capacidade_temp) * 100 if capacidade_temp > 0 else 0
        
        df_s_temp = dados_abrigo_temp.get('df_suprimentos', pd.DataFrame())
        if 'Autonomia Estimada (IA)' not in df_s_temp.columns and not df_s_temp.empty:
             df_s_temp = recalcular_previsoes_suprimentos(df_s_temp.copy())

        item_critico, autonomia_critica = ("N/A", 0)
        if not df_s_temp.empty and 'Autonomia Estimada (IA)' in df_s_temp.columns and not df_s_temp['Autonomia Estimada (IA)'].empty: 
            item_critico_row = df_s_temp.loc[df_s_temp['Autonomia Estimada (IA)'].idxmin()]
            item_critico, autonomia_critica = item_critico_row['Item'], item_critico_row['Autonomia Estimada (IA)']
        
        resumo = { "Abrigo": nome_abrigo_loop, "Saúde Geral": saude, "Ocupação": f"{dados_abrigo_temp.get('abrigados_atuais', 0)}/{dados_abrigo_temp.get('capacidade_maxima', 0)}", "Taxa Ocup. (%)": taxa_ocup_perc, "Homens": dados_abrigo_temp.get('n_homens', 0), "Mulheres": dados_abrigo_temp.get('n_mulheres', 0), "Crianças (0-12a)": dados_abrigo_temp.get('n_criancas_0_12', 0), "Idosos (60+)": dados_abrigo_temp.get('n_idosos_60_mais', 0), "Nec. Méd. Críticas": dados_abrigo_temp.get('n_necessidades_criticas_medicas', 0), "Pets": dados_abrigo_temp.get('n_pets_total', 0), "Item Mais Crítico": item_critico, "Autonomia (dias)": autonomia_critica }
        dados_consolidados_list.append(resumo)
    
    df_consolidado = pd.DataFrame(dados_consolidados_list)
    
    st.markdown("---")
    st.subheader("Painel de Indicadores Consolidados")
    taxa_ocupacao_consolidada = (total_abrigados_geral / total_capacidade_geral * 100) if total_capacidade_geral > 0 else 0

    st.markdown("##### Visão Geral e Capacidade")
    kpi_gerais_cols1 = st.columns(4)
    kpi_gerais_cols1[0].metric("🏨 Abrigos Monitorados", len(df_consolidado) if not df_consolidado.empty else 0)
    kpi_gerais_cols1[1].metric("👥 Total de Abrigados", f"{total_abrigados_geral}")
    kpi_gerais_cols1[2].metric("🛏️ Capacidade Total", f"{total_capacidade_geral}", f"{taxa_ocupacao_consolidada:.1f}% Ocupada")
    kpi_gerais_cols1[3].metric("⚕️ Total Nec. Críticas", total_nec_med_criticas_geral)
    
    st.markdown("---") 
    st.markdown("##### Demografia e Pets")
    kpi_gerais_cols2 = st.columns(4)
    kpi_gerais_cols2[0].metric("👨 Total Homens", total_homens_geral)
    kpi_gerais_cols2[1].metric("👩 Total Mulheres", total_mulheres_geral)
    kpi_gerais_cols2[2].metric("👶 Total Crianças (0-12a)", total_criancas_geral)
    kpi_gerais_cols2[3].metric("🐾 Total de Pets", total_pets_geral)
    st.markdown("---")

    st.dataframe(df_consolidado, use_container_width=True, hide_index=True,
                 column_config={ "Taxa Ocup. (%)": st.column_config.ProgressColumn("Taxa Ocup. (%)", format="%.1f%%", min_value=0, max_value=120), "Autonomia (dias)": st.column_config.NumberColumn("Autonomia (dias)", help="Dias restantes para o item de suprimento mais crítico.", format="%.1f d") }
    )

with tab_detalhado:
    dados_detalhe = st.session_state.get('dados_abrigo', {}) 
    
    saude_geral_detalhe = calcular_saude_geral_abrigo(dados_detalhe)
    col_header_det1, col_header_det2 = st.columns([3,1])
    with col_header_det1:
        st.header(f"Abrigo: {dados_detalhe.get('nome_abrigo', 'N/A')}")
        st.caption(f"{dados_detalhe.get('endereco', 'N/A')} | Administrador(a): {dados_detalhe.get('administrador', 'N/A')} | Tel: {dados_detalhe.get('telefone', 'N/A')}")
    with col_header_det2:
        if saude_geral_detalhe == "🔴 Crítico": st.error(f"SAÚDE GERAL: {saude_geral_detalhe}")
        elif saude_geral_detalhe == "🟡 Atenção": st.warning(f"SAÚDE GERAL: {saude_geral_detalhe}")
        else: st.success(f"SAÚDE GERAL: {saude_geral_detalhe}")
    st.markdown("---")

    st.subheader("Painel de Acompanhamento")
    st.markdown("##### Demografia e Ocupação")
    kpi_det_cols1 = st.columns(5) 
    abrigados_det = dados_detalhe.get('abrigados_atuais', 0)
    capacidade_det = dados_detalhe.get('capacidade_maxima', 1)
    taxa_ocup_perc_det = (abrigados_det / capacidade_det) * 100 if capacidade_det > 0 else 0
    kpi_det_cols1[0].metric("👥 Ocupação", f"{abrigados_det}/{capacidade_det}", f"{taxa_ocup_perc_det:.1f}%")
    kpi_det_cols1[1].metric("👨 Homens", dados_detalhe.get('n_homens', 0))
    kpi_det_cols1[2].metric("👩 Mulheres", dados_detalhe.get('n_mulheres', 0))
    kpi_det_cols1[3].metric("👶 Crianças (0-12a)", dados_detalhe.get('n_criancas_0_12', 0))
    kpi_det_cols1[4].metric("👵 Idosos (60+a)", dados_detalhe.get('n_idosos_60_mais', 0))

    st.markdown("---") 
    st.markdown("##### Operacional e Suprimentos")
    kpi_det_cols2 = st.columns(3) 
    df_s_detalhe = dados_detalhe.get('df_suprimentos', pd.DataFrame())
    if 'Autonomia Estimada (IA)' not in df_s_detalhe.columns and not df_s_detalhe.empty:
        df_s_detalhe = recalcular_previsoes_suprimentos(df_s_detalhe.copy())
        
    item_critico_det, autonomia_critica_det = ("N/A", 0)
    if not df_s_detalhe.empty and 'Autonomia Estimada (IA)' in df_s_detalhe.columns and not df_s_detalhe['Autonomia Estimada (IA)'].empty:
        item_critico_row_det = df_s_detalhe.loc[df_s_detalhe['Autonomia Estimada (IA)'].idxmin()]
        item_critico_det, autonomia_critica_det = item_critico_row_det['Item'], item_critico_row_det['Autonomia Estimada (IA)']
    
    kpi_det_cols2[0].metric("⚕️ Nec. Médicas Críticas", dados_detalhe.get('n_necessidades_criticas_medicas', 0))
    kpi_det_cols2[1].metric("🐾 Pets no Abrigo", dados_detalhe.get('n_pets_total', 0))
    kpi_det_cols2[2].metric(f"📉 Ítem crítico ({item_critico_det})", f"{autonomia_critica_det:.1f} dias")
    st.markdown("---")

    st.subheader("🫂 Perfil dos Abrigados e Necessidades")
    col_perfil_det1, col_perfil_det2, col_perfil_det3 = st.columns([0.32, 0.32, 0.36]) 
    with col_perfil_det1:
        st.markdown("##### Gênero")
        df_genero_det = dados_detalhe.get('df_perfil_genero', pd.DataFrame())
        if not df_genero_det.empty and df_genero_det['Quantidade'].sum() > 0: 
            fig_genero = px.pie(df_genero_det, values='Quantidade', names='Gênero', hole=0.5, color_discrete_sequence=['#636EFA', '#EF553B']) 
            fig_genero.update_layout(margin=dict(l=0, r=0, t=25, b=0), height=280, showlegend=False) 
            fig_genero.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='white', size=11))
            st.plotly_chart(fig_genero, use_container_width=True)
        else: st.caption("Sem dados de gênero.")
    with col_perfil_det2:
        st.markdown("##### Faixa Etária")
        df_etario_det = dados_detalhe.get('df_perfil_etario', pd.DataFrame())
        if not df_etario_det.empty and df_etario_det['Quantidade'].sum() > 0:
            fig_faixa_etaria = px.pie(df_etario_det, values='Quantidade', names='Faixa Etária', hole=0.5, color_discrete_sequence=px.colors.sequential.Blues_r)
            fig_faixa_etaria.update_layout(margin=dict(l=0, r=0, t=25, b=0), height=280, showlegend=False)
            fig_faixa_etaria.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='white', size=10), texttemplate='%{percent:.0%}')
            st.plotly_chart(fig_faixa_etaria, use_container_width=True)
        else: st.caption("Sem dados de faixa etária.")
    with col_perfil_det3:
        st.markdown("##### Necessidades Especiais")
        df_necessidades_det = dados_detalhe.get('df_necessidades_especiais', pd.DataFrame())
        if not df_necessidades_det.empty:
            df_necessidades_agrupado_temp = df_necessidades_det.groupby('Tipo de Necessidade').agg(NumPessoas=('ID Abrigado', 'count')).reset_index()
            df_necessidades_agrupado_temp.rename(columns={'NumPessoas': 'Pessoas'}, inplace=True)
            st.dataframe(df_necessidades_agrupado_temp[['Tipo de Necessidade', 'Pessoas']], height=280, use_container_width=True, hide_index=True)
        else: st.caption("Nenhum registro de necessidade especial.")
    st.markdown("---")

    st.subheader("🐾 Perfil dos Pets no Abrigo")
    col_pets_det1, col_pets_det2 = st.columns([0.4, 0.6])
    with col_pets_det1:
        df_pets_det = dados_detalhe.get('df_perfil_pets', pd.DataFrame())
        if not df_pets_det.empty and df_pets_det['Quantidade'].sum() > 0:
            fig_perfil_pets = px.pie(df_pets_det, values='Quantidade', names='Tipo', title='Distribuição por Tipo de Pet', hole=0.5, color_discrete_sequence=px.colors.sequential.Oranges_r)
            fig_perfil_pets.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=300, legend_title_text='')
            fig_perfil_pets.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='white', size=12))
            st.plotly_chart(fig_perfil_pets, use_container_width=True)
        else:
            st.info("Não há pets registrados neste abrigo ou dados indisponíveis.")
    with col_pets_det2:
        st.info("💡 **Lembretes para Pets:**\n\n- Verificar estoque de ração específica (cães/gatos).\n- Controlar a disponibilidade de areia sanitária.\n- Manter uma lista de pets com necessidades especiais (medicação, dieta).")
    st.markdown("---")

    st.subheader("🥫 Controle de Suprimentos e Previsões por IA")
    df_suprimentos_para_filtros = dados_detalhe.get('df_suprimentos', pd.DataFrame()).copy() 
    if not df_suprimentos_para_filtros.empty:
        if 'Autonomia Estimada (IA)' not in df_suprimentos_para_filtros.columns:
            df_suprimentos_para_filtros = recalcular_previsoes_suprimentos(df_suprimentos_para_filtros)
        df_suprimentos_para_filtros['Criticidade por Impacto'] = df_suprimentos_para_filtros.apply(calcular_criticidade_impacto, axis=1)

        col_filt1, col_filt2, col_filt3 = st.columns(3)
        categorias_suprimentos_det = ['Todas'] + sorted(df_suprimentos_para_filtros['Categoria'].unique())
        filtro_categoria_det = col_filt1.selectbox("Filtrar por Categoria:", options=categorias_suprimentos_det, key="filtro_cat_det")
        
        niveis_criticidade_filtro_det = ['Todos', '🆘 Zerado!', '🔴 Crítico', '🟡 Atenção', '🟢 OK']
        filtro_criticidade_det = col_filt2.selectbox("Filtrar por Criticidade (Impacto):", options=niveis_criticidade_filtro_det, key="filtro_crit_det")
        
        # ALTERADO: Slider com valor máximo fixo de 90
        filtro_autonomia_det = col_filt3.slider(
            "Autonomia Estimada (IA) menor ou igual a (dias):", 
            min_value=0, 
            max_value=90, 
            value=90, 
            step=1, 
            key="filtro_aut_det", 
            format="%d dias"
        )

        df_suprimentos_filtrado_det = df_suprimentos_para_filtros.copy()
        if filtro_categoria_det != 'Todas':
            df_suprimentos_filtrado_det = df_suprimentos_filtrado_det[df_suprimentos_filtrado_det['Categoria'] == filtro_categoria_det]
        if filtro_criticidade_det != 'Todos':
            df_suprimentos_filtrado_det = df_suprimentos_filtrado_det[df_suprimentos_filtrado_det['Criticidade por Impacto'].str.startswith(filtro_criticidade_det.split(' ')[0])]
        df_suprimentos_filtrado_det = df_suprimentos_filtrado_det[df_suprimentos_filtrado_det['Autonomia Estimada (IA)'] <= filtro_autonomia_det]

        st.markdown("##### Inventário Detalhado e Projeção de Suprimentos")
        st.dataframe( df_suprimentos_filtrado_det[['Item', 'Categoria', 'Estoque Atual', 'Unidade', 'Consumo Diário Previsto (IA)', 'Autonomia Estimada (IA)', 'Criticidade por Impacto', 'Importancia_Base']], height=400, use_container_width=True, 
                      column_config={ "Estoque Atual": st.column_config.NumberColumn(format="%d"), "Unidade": st.column_config.TextColumn("Unid."), "Autonomia Estimada (IA)": st.column_config.NumberColumn(format="%.1f d"), "Consumo Diário Previsto (IA)": st.column_config.NumberColumn(format="%.1f /dia"), "Importancia_Base": st.column_config.NumberColumn("Importância (1-10)"), "Criticidade por Impacto": st.column_config.TextColumn("Impacto (Score)") } )
        
        st.markdown("##### Alertas Priorizados")
        alertas_df_det = df_suprimentos_filtrado_det[df_suprimentos_filtrado_det['Criticidade por Impacto'].str.contains('🆘 Zerado|🔴 Crítico|🟡 Atenção')].sort_values(by='Importancia_Base', ascending=False)
        if alertas_df_det.empty:
            st.success("✅ Nenhum alerta urgente de suprimentos com os filtros aplicados.")
        else:
            for _, row_alerta in alertas_df_det.iterrows():
                impact_score_str = row_alerta['Criticidade por Impacto'].split('(')[-1].replace(')', '')
                mensagem = f"**{row_alerta['Item']}** (Cat: {row_alerta['Categoria']}) - Autonomia: {row_alerta['Autonomia Estimada (IA)']} dias. Impacto: {impact_score_str}."
                if '🆘 Zerado!' in row_alerta['Criticidade por Impacto'] or '🔴 Crítico' in row_alerta['Criticidade por Impacto']:
                    st.error(f"🆘 URGENTE: {mensagem} Reposição imediata!")
                elif '🟡 Atenção' in row_alerta['Criticidade por Impacto']:
                    st.warning(f"🟡 ATENÇÃO: {mensagem} Planejar reposição.")
    else:
        st.info("Dados de suprimentos não disponíveis para este abrigo.")
    st.markdown("---")

    st.subheader("🔬 Análises Adicionais de Suprimentos")
    col_analise_det1, col_analise_det2 = st.columns(2)
    with col_analise_det1:
        st.markdown("##### Visualização Temporal da Demanda (Itens Selecionados)")
        df_hist_det = dados_detalhe.get('df_historico_consumo', pd.DataFrame())
        df_sup_det_analise = dados_detalhe.get('df_suprimentos', pd.DataFrame())

        if not df_hist_det.empty and not df_sup_det_analise.empty:
            itens_para_grafico_temporal = df_sup_det_analise.sort_values(by='Importancia_Base', ascending=False)['Item'].unique()[:3]
            df_hist_filtrado_det = df_hist_det[df_hist_det['Item'].isin(itens_para_grafico_temporal)]
            if not df_hist_filtrado_det.empty:
                fig_temporal_det = px.line(df_hist_filtrado_det, x='Data', y='Consumo', color='Item', markers=True, title=f"Histórico de Consumo (Últimos 7 dias)")
                fig_temporal_det.update_layout(height=350, legend_title_text='')
                st.plotly_chart(fig_temporal_det, use_container_width=True)
            else:
                st.info("Sem dados históricos suficientes para os itens mais importantes.")
        else:
            st.info("Dados de histórico ou suprimentos não disponíveis para esta análise.")
    with col_analise_det2:
        st.markdown("##### Análise de Consumo - Curva ABC (Conceitual)")
        st.caption("A Curva ABC (Princípio de Pareto 80/20) ajuda a identificar os itens mais significativos.")
        df_abc_analise = dados_detalhe.get('df_suprimentos', pd.DataFrame()).copy()
        if not df_abc_analise.empty and 'Consumo Diário Previsto (IA)' in df_abc_analise.columns and 'Importancia_Base' in df_abc_analise.columns :
            df_abc_analise['Valor_Consumo_Simulado'] = pd.to_numeric(df_abc_analise['Consumo Diário Previsto (IA)'], errors='coerce').fillna(0) * pd.to_numeric(df_abc_analise['Importancia_Base'], errors='coerce').fillna(0)
            df_abc_analise = df_abc_analise.sort_values(by='Valor_Consumo_Simulado', ascending=False)
            st.markdown("**Top 5 Itens por 'Valor de Consumo' (Simulado):**")
            for i, row_abc in df_abc_analise.head(5).iterrows():
                st.markdown(f"- **{row_abc['Item']}**: Valor Consumo Simulado = {row_abc['Valor_Consumo_Simulado']:.1f}")
        else:
            st.write("Nenhum item para exibir na análise ABC (dados insuficientes).")
        st.info("💡 **Ação:** Priorizar controle para itens da 'Classe A' (alto valor de consumo).")
    st.markdown("---")

    st.subheader("🤖 Assistência Inteligente e Comunicação")
    col_ia_rec_det, col_ia_com_det = st.columns(2)
    with col_ia_rec_det:
        st.markdown("##### Recomendações Automatizadas (IA) - Exemplo")
        st.info("ℹ️ *Conceitual: Em um sistema completo, a IA poderia sugerir transferências entre abrigos ou otimizar pedidos.*")
        df_suprimentos_ia_rec = dados_detalhe.get('df_suprimentos', pd.DataFrame())
        if not df_suprimentos_ia_rec.empty and 'Autonomia Estimada (IA)' in df_suprimentos_ia_rec.columns:
             if not df_suprimentos_ia_rec['Autonomia Estimada (IA)'].empty and df_suprimentos_ia_rec['Autonomia Estimada (IA)'].min() < 1.5 and dados_detalhe.get('nome_abrigo') == "Escola Bem-Viver":
                st.success("✅ **Sugestão IA:** Transferir 200L de Água do 'Ginásio Mãos Unidas' (Estoque: Alto) para 'Escola Bem-Viver'.")
             else:
                st.write("Nenhuma recomendação crítica de IA no momento para este abrigo.")
        else:
            st.write("Dados de suprimentos não disponíveis para recomendações.")
            
    with col_ia_com_det:
        st.markdown("##### Módulo de Comunicação Direta (Placeholder)")
        st.text_area("Enviar mensagem para Coordenação Central:", height=100, placeholder="Digite sua mensagem aqui...", key="msg_coord_central")
        if st.button("📨 Enviar Mensagem", key="btn_enviar_msg_coord"):
            st.success("Mensagem enviada (simulação)!")

    st.markdown("---")
    st.caption(f"Projeto Shelter Tech - FIAP Global Solution {datetime.now().year} (Dashboard com dados simulados)")
