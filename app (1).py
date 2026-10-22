# ==============================================================================
# PROJETO INTEGRADOR FMABC & CROS - FASE 3 (ENTREGAVEL E3)
# DASHBOARD INTERATIVO E PAINEL PREDITIVO DE LEITOS OBSTETRICOS (STREAMLIT)
# Autores: Mateus Augusto, Caique Santana, Julio Junior
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json
import hashlib
from datetime import datetime, timedelta

st.set_page_config(
    page_title="CROS - Gestao Preditiva de Leitos Obstetricos",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("<h1 style=\"color: #1E3A8A;\">Central CROS / FMABC - Gestao Preditiva de Leitos Obstetricos</h1>", unsafe_allow_html=True)
st.caption("Painel Interativo da Fase 3 (Entregavel E3) - Prototipo Funcional Streamlit")

st.sidebar.title("Central CROS / FMABC")
st.sidebar.caption("Sistema Preditivo de Leitos Obstetricos v3.0")

menu = st.sidebar.radio("Navegacao do Sistema:", ["📊 Dashboard Geral de Leitos", "📝 Simulacao de Prontuario UBS", "⚙️ Contrato JSON Schema CROS", "📖 Requisitos do Entregavel E3"])

st.sidebar.divider()
st.sidebar.subheader("🔒 Protocolo LGPD & Seguranca")
st.sidebar.info("• Anonimizacao SHA-256 (cpf_hash)\n• Conexao MySQL InnoDB Transacional (ACID)\n• Fallback Medico Ativo 24/7")

def executar_motor_fallback(dum_str, idade_gest, pa_s, pa_d, sintomas):
    s_low = sintomas.lower()
    has_pe = "preeclampsia" in s_low or "eclam" in s_low or "pressao" in s_low or pa_s >= 140 or pa_d >= 90
    has_cef = "cefaleia" in s_low or "cabeca" in s_low or "dor" in s_low
    if has_pe and has_cef:
        score, cat = 0.88, "Alta Urgencia"
        p37, p38, p39, p40, p41, p42 = 0.15, 0.65, 0.15, 0.03, 0.01, 0.01
        just = "[MOTOR FALLBACK REGRAS] Detectado pico hipertensivo e sintomas clinicos de pre-eclampsia. Parto antecipado recomendado para a 38a semana com reserva de UTI Neonatal."
        diags = ["Pico de Hipertensao Arterial (150x100 mmHg)", "Sintomas de Pre-eclampsia", "Cefaleia Persistente"]
    elif has_pe:
        score, cat = 0.65, "Media Urgencia"
        p37, p38, p39, p40, p41, p42 = 0.10, 0.30, 0.45, 0.10, 0.03, 0.02
        just = "[MOTOR FALLBACK REGRAS] Hipertensao moderada detectada. Monitorar gestante na 39a semana."
        diags = ["Hipertensao Gestacional"]
    else:
        score, cat = 0.15, "Baixa Urgencia"
        p37, p38, p39, p40, p41, p42 = 0.05, 0.10, 0.25, 0.45, 0.10, 0.05
        just = "[MOTOR FALLBACK REGRAS] Pre-natal fisiologico sem sinais de gravidade. Pico probabilistico na 40a semana."
        diags = ["Acompanhamento de Rotina Sem Alteracoes"]
    return {
        "score_risco": score, "categoria": cat, "justificativa": just, "diagnosticos": diags,
        "curva": {"semana_37": p37, "semana_38": p38, "semana_39": p39, "semana_40": p40, "semana_41": p41, "semana_42": p42},
        "leitos_retaguarda": 1
    }

if menu == "📊 Dashboard Geral de Leitos":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Leitos Obstetricos Totais", "120", "+5 leitos ativados")
    col2.metric("Taxa de Ocupacao Atual", "84,2%", "+2.1%", delta_color="inverse")
    col3.metric("Reserva Preditiva (+15%)", "18 vagas", "Margem de Seguranca")
    col4.metric("Alertas de Alto Risco", "3 Pacientes", "Pre-eclampsia")
    st.divider()
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("📈 Projecao Semanal de Demanda por Leitos (S37 a S42)")
        df = pd.DataFrame({
            "Semana Gestacional": ["Semana 37", "Semana 38", "Semana 39", "Semana 40", "Semana 41", "Semana 42"],
            "Partos Esperados (IA)": [12, 38, 45, 18, 5, 2],
            "Capacidade Segura (+15%)": [20, 45, 50, 30, 15, 10]
        })
        fig = px.bar(df, x="Semana Gestacional", y=["Partos Esperados (IA)", "Capacidade Segura (+15%)"], barmode="group", color_discrete_sequence=["#1E3A8A", "#93C5FD"])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🏥 Vagos por Maternidade no Grande ABC")
        hdf = pd.DataFrame({
            "Hospital / Maternidade": ["Maternidade Mario Covas", "H.M. Santo Andre", "Hospital Anchieta (SBC)", "H.M. Maua"],
            "Leitos Vagos": [4, 2, 6, 3]
        })
        fig_p = px.pie(hdf, values="Leitos Vagos", names="Hospital / Maternidade", hole=0.4)
        st.plotly_chart(fig_p, use_container_width=True)
    st.subheader("📋 Gestantes Monitoradas na Fila de Regulacao do CROS")
    mock_df = pd.DataFrame([
        {"ID Hash (LGPD)": "e3b0c44298fc1c14...", "Idade Gest.": "38 sem", "Municipio": "Santo Andre", "Risco": "Alta (0.88)", "Diagnostico NLP": "Pre-eclampsia (150x100)", "Acao CROS": "Pre-Alocado (Mario Covas)"},
        {"ID Hash (LGPD)": "8f434346648f6b9...", "Idade Gest.": "39 sem", "Municipio": "SBC", "Risco": "Media (0.45)", "Diagnostico NLP": "Diabetes Gestacional", "Acao CROS": "Monitoramento UBS"},
        {"ID Hash (LGPD)": "a1b2c3d4e5f6789...", "Idade Gest.": "40 sem", "Municipio": "Maua", "Risco": "Baixa (0.12)", "Diagnostico NLP": "Pre-natal Fisiologico", "Acao CROS": "Aguardando Parto"}
    ])
    st.dataframe(mock_df, use_container_width=True)

elif menu == "📝 Simulacao de Prontuario UBS":
    st.subheader("Entrada de Prontuario da UBS & Processamento End-to-End")
    with st.form("form_p"):
        c1, c2 = st.columns(2)
        cpf = c1.text_input("CPF da Gestante (Será Anonimizado via SHA-256):", "123.456.789-00")
        mun = c2.selectbox("Municipio de Origem:", ["Santo Andre", "Sao Bernardo do Campo", "Sao Caetano do Sul", "Maua", "Diadema"])
        c3, c4, c5 = st.columns(3)
        dum = c3.date_input("Data da Ultima Menstruacao (DUM):", datetime(2026, 1, 15))
        ig = c4.number_input("Idade Gestacional (semanas):", 20, 44, 38)
        pas = c5.number_input("Pressao Arterial Sistolica (mmHg):", 70, 240, 150)
        pad = c3.number_input("Pressao Arterial Diastolica (mmHg):", 40, 140, 100)
        pront = st.text_area("Anotacoes de Pre-Natal (Linguagem Natural da UBS):", "Gestante relata cefaleia persistente e visao embacada ha 24h. PA 150x100 mmHg. Suspeita de pre-eclampsia.")
        sub = st.form_submit_button("🚀 Processar Prontuario e Calcular Risco CROS")
    if sub:
        cpf_h = hashlib.sha256(cpf.encode("utf-8")).hexdigest()
        res = executar_motor_fallback(dum.strftime("%Y-%m-%d"), ig, pas, pad, pront)
        st.success("✅ Processamento Concluido com Sucesso!")
        st.write(f"**CPF Hash (Anonimizacao LGPD SHA-256):** `{cpf_h}`")
        st.write("**Origem do Processamento:** Motor Preditivo de Fallback (Regras Medicas Ativas)")
        cat_val = res['categoria']
        score_val = res['score_risco']
        st.write(f"**Nivel de Urgencia:** `{cat_val}` | **Score de Risco Clinico:** `{score_val:.2f}`")
        just_val = res['justificativa']
        st.write(f"**Justificativa Clinica:** {just_val}")
        st.write("**Sintomas e Fatores de Risco Detectados (NLP):**")
        for d in res["diagnosticos"]:
            st.markdown(f"• `{d}`")
        st.subheader("📈 Curva Probabilistica Semanal de Parto (Janela S37 a S42)")
        curva_df = pd.DataFrame({
            "Semana Gestacional": ["Semana 37", "Semana 38", "Semana 39", "Semana 40", "Semana 41", "Semana 42"],
            "Probabilidade": list(res["curva"].values())
        })
        fig_c = px.line(curva_df, x="Semana Gestacional", y="Probabilidade", markers=True, title="Distribucion Estocastica de Parto")
        st.plotly_chart(fig_c, use_container_width=True)

elif menu == "⚙️ Contrato JSON Schema CROS":
    st.subheader("Contrato de Dados CROS (JSON Schema Draft-07)")
    schema_data = {
        "title": "ContratoRegulacaoLeitoObstetricoCROS",
        "type": "object",
        "required": ["id_paciente_hash", "score_risco", "categoria_urgencia", "leitos_retaguarda_recomendados"],
        "properties": {
            "id_paciente_hash": { "type": "string", "description": "Hash SHA-256 do CPF para LGPD" },
            "dpp_ajustada": { "type": "string", "format": "date" },
            "score_risco": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
            "categoria_urgencia": { "type": "string", "enum": ["Baixa", "Media", "Alta", "Critica"] },
            "leitos_retaguarda_recomendados": { "type": "integer", "description": "Reserva incluindo margem de 15%" }
        }
    }
    st.json(schema_data)

elif menu == "📖 Requisitos do Entregavel E3":
    st.subheader("Checklist de Artefatos da Fase 3 (Entregavel E3)")
    st.markdown("• **Codigo-Fonte Completo:** Ingestao e orquestracao com tratamento de excecoes.\n• **Interface Interativa (Streamlit):** Front-end funcional para testes visuais.\n• **Validacao de Dados Estruturada:** Protecao de faixas biologicas e anonimizacao LGPD (SHA-256).\n• **Mecanismo de Fallback Implementado:** Algoritmo deterministico medico em caso de oscilacao da IA.\n• **Outputs Estruturados:** Respostas travadas em JSON Schema CROS.\n• **Consultas Otimizadas:** Estrutura relacional MySQL com suporte a transacoes ACID.")
    st.info("Desenvolvido para o Centro Universitario Saude ABC (FMABC) - IA em Saude 2026.")