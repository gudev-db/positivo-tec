import streamlit as st
import io
import google.generativeai as genai
from PIL import Image
import requests
import datetime
import os
from pymongo import MongoClient
import requests



# Configuração inicial
st.set_page_config(
    layout="wide",
    page_title="Agente Positivo_Tecnologia",
    page_icon="assets/page-icon.png"
)
st.image('assets/macLogo.png', width=300)

st.header('Agente Positivo_Tecnologia')
st.header(' ')




gemini_api_key = os.getenv("GEM_API_KEY")
genai.configure(api_key=gemini_api_key)
modelo_vision = genai.GenerativeModel("gemini-2.0-flash", generation_config={"temperature": 0.1})
modelo_texto = genai.GenerativeModel("gemini-1.5-flash")

# Conexão com MongoDB
client2 = MongoClient("mongodb+srv://gustavoromao3345:RqWFPNOJQfInAW1N@cluster0.5iilj.mongodb.net/auto_doc?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true")
db = client2['arquivos_planejamento']
collection = db['auto_doc']
banco = client2["arquivos_planejamento"]
db_clientes = banco["clientes"]  
db_briefings = banco["briefings_Positivo_Tecnologia"]  


# Carrega diretrizes
with open('data.txt', 'r') as file:
    conteudo = file.read()

tab_chatbot, tab_aprovacao, tab_geracao, tab_briefing, tab_briefing_gerados, tab_resumo = st.tabs([
    "💬 Chatbot Positivo_Tecnologia", 
    "✅ Aprovação de Conteúdo", 
    "✨ Geração de Conteúdo",
    "📋 Geração de Briefing Positivo_Tecnologia",  
    "📋 Briefings Gerados",
    "📝 Resumo de Textos",
])


with tab_chatbot:  
    st.header("Chat Virtual Positivo_Tecnologia")
    st.caption("Pergunte qualquer coisa sobre as diretrizes e informações da Positivo_Tecnologia")
    
    # Inicializa o histórico de chat na session_state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Exibe o histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input do usuário
    if prompt := st.chat_input("Como posso ajudar?"):
        # Adiciona a mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Prepara o contexto com as diretrizes
        contexto = f"""
        Você é um assistente virtual especializado na Positivo_Tecnologia
        Baseie todas as suas respostas nestas diretrizes oficiais da Positivo_Tecnologia
        {conteudo}


        
        Regras importantes:
        - Seja preciso e técnico
        - Mantenha o tom profissional mas amigável
        - Se a pergunta for irrelevante, oriente educadamente
        - Forneça exemplos quando útil
        """
        
        # Gera a resposta do modelo
        with st.chat_message("assistant"):
            with st.spinner('Pensando...'):
                try:
                    # Usa o histórico completo para contexto
                    historico_formatado = "\n".join(
                        [f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages]
                    )
                    
                    resposta = modelo_texto.generate_content(
                        f"{contexto}\n\nHistórico da conversa:\n{historico_formatado}\n\nResposta:"
                    )
                    
                    # Exibe a resposta
                    st.markdown(resposta.text)
                    
                    # Adiciona ao histórico
                    st.session_state.messages.append({"role": "assistant", "content": resposta.text})
                    
                except Exception as e:
                    st.error(f"Erro ao gerar resposta: {str(e)}")

# --- Estilização Adicional ---
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    [data-testid="stChatMessageContent"] {
        font-size: 1rem;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        padding: 0.5rem 1rem;
    }
    .stChatInput {
        bottom: 20px;
        position: fixed;
        width: calc(100% - 5rem);
    }
</style>
""", unsafe_allow_html=True)


with tab_aprovacao:
    st.header("Validação de Materiais")
    st.header(' ')
    subtab1, subtab2 = st.tabs(["🖼️ Análise de Imagens", "✍️ Revisão de Textos"])
    
    with subtab1:
        uploaded_image = st.file_uploader("Carregue imagem para análise (.jpg, .png)", type=["jpg", "jpeg", "png"], key="img_uploader")
        if uploaded_image:
            st.image(uploaded_image, use_column_width=True, caption="Pré-visualização")
            if st.button("Validar Imagem", key="analyze_img"):
                with st.spinner('Comparando com diretrizes da marca...'):
                    try:
                        image = Image.open(uploaded_image)
                        img_bytes = io.BytesIO()
                        image.save(img_bytes, format=image.format)
                        
                        resposta = modelo_vision.generate_content([
                            f"""Analise esta imagem considerando:
                            {conteudo}
                            Forneça um parecer técnico detalhado com:
                            - ✅ Acertos
                            - ❌ Desvios das diretrizes
                            - 🛠 Recomendações precisas
                            - Diga se a imagem é aprovada ou não""",
                            {"mime_type": "image/jpeg", "data": img_bytes.getvalue()}
                        ])
                        st.subheader("Resultado da Análise")
                        st.markdown(resposta.text)
                    except Exception as e:
                        st.error(f"Falha na análise: {str(e)}")

    with subtab2:
        texto_input = st.text_area("Insira o texto para validação:", height=200, key="text_input")
        if st.button("Validar Texto", key="validate_text"):
            with st.spinner('Verificando conformidade...'):
                resposta = modelo_texto.generate_content(
                    f"""Revise este texto conforme:
                    Diretrizes: {conteudo}
                    Texto: {texto_input}
                    
                    Formato requerido:
                    ### Texto Ajustado
                    [versão reformulada]
                    
                    ### Alterações Realizadas
                    - [lista itemizada de modificações]
                    ### Justificativas
                    [explicação técnica das mudanças]"""
                )
                st.subheader("Versão Validada")
                st.markdown(resposta.text)

with tab_geracao:
    st.header("Criação de Conteúdo")
    st.header(' ')
    campanha_brief = st.text_area("Briefing criativo:", help="Descreva objetivos, tom de voz e especificações", height=150)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Diretrizes Visuais")

        if st.button("Gerar Especificações", key="gen_visual"):
            with st.spinner('Criando guia de estilo...'):
                prompt = f"""
                Você é um designer que trabalha para a Macfor Marketing digital e você deve gerar conteúdo criativo para o cliente Positivo_Tecnologia.

                Crie um manual técnico para designers baseado em:
                Brief: {campanha_brief}
                Diretrizes: {conteudo}


                Inclua:
                1. 🎨 Paleta de cores (códigos HEX/RGB)
                2. 🖼️ Diretrizes de fotografia
                3. ✏️ Tipografia hierárquica
                4. 📐 Grid e proporções
                5. ⚠️ Restrições de uso
                6. Descrição exata e palpável da imagem a ser utilizada no criativo que atenda a todas as guias acima
                """
                resposta = modelo_texto.generate_content(prompt)
                st.markdown(resposta.text)

    with col2:
        st.subheader("Copywriting")

        if st.button("Gerar Textos", key="gen_copy"):
            with st.spinner('Desenvolvendo conteúdo textual...'):
                prompt = f"""
                Crie textos para campanha considerando:
                Brief: {campanha_brief}
                Diretrizes: {conteudo}


                
                Entregar:
                - 🎯 3 opções de headline
                - 📝 Corpo de texto (200 caracteres)
                - 📢 2 variações de CTA
                - 🔍 Meta description (SEO)
                """
                resposta = modelo_texto.generate_content(prompt)
                st.markdown(resposta.text)

# --- Estilização ---
st.markdown("""
<style>
    div[data-testid="stTabs"] {
        margin-top: -30px;
    }
    div[data-testid="stVerticalBlock"] > div:has(>.stTextArea) {
        border-left: 3px solid #4CAF50;
        padding-left: 1rem;
    }
    button[kind="secondary"] {
        background: #f0f2f6 !important;
    }
</style>
""", unsafe_allow_html=True)



with tab_briefing:
    st.header("Gerador de Briefing Positivo_Tecnologia")
    st.caption("Crie briefings completos para diferentes áreas de atuação da Positivo_Tecnologia")
    
    # Conexão com MongoDB para briefings
    db_briefings = client2['briefings_Positivo_Tecnologia']
    collection_briefings = db_briefings['briefings']
    
    # Tipos de briefing disponíveis organizados por categoria
    tipos_briefing = {
        "Social": [
            "Post único",
            "Planejamento Mensal"
        ],
        "CRM": [
            "Planejamento de CRM",
            "Fluxo de Nutrição",
            "Email Marketing"
        ],
        "Mídias": [
            "Campanha de Mídia"
        ],
        "Tech": [
            "Manutenção de Site",
            "Construção de Site",
            "Landing Page"
        ],
        "Analytics": [
            "Dashboards"
        ],
        "Design": [
            "Social",
            "CRM",
            "Mídia",
            "KV/Identidade Visual"
        ],
        "Redação": [
            "Email Marketing",
            "Site",
            "Campanha de Mídias"
        ],
        "Planejamento": [
            "Relatórios",
            "Estratégico",
            "Concorrência"
        ]
    }

    # Aba de configuração
    tab_new, tab_saved = st.tabs(["Novo Briefing", "Briefings Salvos"])
        
    with tab_new:
        # Seleção hierárquica do tipo de briefing
        categoria = st.selectbox("Categoria:", list(tipos_briefing.keys()))
        tipo_briefing = st.selectbox("Tipo de Briefing:", tipos_briefing[categoria])
        
        # Campos comuns a todos os briefings
        st.subheader("Informações Básicas")
        nome_projeto = st.text_input("Nome do Projeto:")
        responsavel = st.text_input("Responsável pelo Briefing:")
        data_entrega = st.date_input("Data de Entrega Prevista:")
        objetivo_geral = st.text_area("Objetivo Geral:")
        obs = st.text_area("Observações")
        
        # Seção dinâmica baseada no tipo de briefing
        st.subheader("Informações Específicas")
        
        # Dicionário para armazenar todos os campos
        campos_briefing = {
            "basicos": {
                "nome_projeto": nome_projeto,
                "responsavel": responsavel,
                "data_entrega": str(data_entrega),
                "objetivo_geral": objetivo_geral,
                "obs": obs
            },
            "especificos": {}
        }
            
        # Função para criar campos dinâmicos com seleção
        def criar_campo_selecionavel(rotulo, tipo="text_area", opcoes=None, padrao=None, key_suffix=""):
            # Cria uma chave única baseada no rótulo e sufixo
            key = f"{rotulo}_{key_suffix}_{tipo}"
            
            # Inicializa o valor no session_state se não existir
            if key not in st.session_state:
                st.session_state[key] = padrao if padrao is not None else ""
            
            col1, col2 = st.columns([4, 1])
            valor = None
            
            with col1:
                if tipo == "text_area":
                    valor = st.text_area(rotulo, value=st.session_state[key], key=f"input_{key}")
                elif tipo == "text_input":
                    valor = st.text_input(rotulo, value=st.session_state[key], key=f"input_{key}")
                elif tipo == "selectbox":
                    valor = st.selectbox(rotulo, opcoes, index=opcoes.index(st.session_state[key]) if st.session_state[key] in opcoes else 0, key=f"input_{key}")
                elif tipo == "multiselect":
                    valor = st.multiselect(rotulo, opcoes, default=st.session_state[key], key=f"input_{key}")
                elif tipo == "date_input":
                    valor = st.date_input(rotulo, value=st.session_state[key], key=f"input_{key}")
                elif tipo == "number_input":
                    valor = st.number_input(rotulo, value=st.session_state[key], key=f"input_{key}")
                elif tipo == "file_uploader":
                    return st.file_uploader(rotulo, key=f"input_{key}")  # Retorna direto pois não pode ser salvo no MongoDB
            
            with col2:
                incluir = st.checkbox("", value=True, key=f"incluir_{key}")
                auto_preencher = st.button("🪄", key=f"auto_{key}", help="Preencher automaticamente com LLM")
            
            if auto_preencher:
                # Carrega contexto do data.txt
                with open("data.txt", "r") as f:
                    contexto = f.read()
                
                prompt = f"Com base no seguinte contexto:\n{contexto}\n\n E o objetivo do briefing {objetivo_geral} \n\nPreencha o campo '{rotulo}' para um briefing do tipo {tipo_briefing} no Positivo_Tecnologia. Retorne APENAS o valor para o campo, sem comentários ou formatação adicional."
                
                try:
                    resposta = modelo_texto.generate_content(prompt)
                    # Atualiza o session_state com a resposta da LLM
                    st.session_state[key] = resposta.text
                    # Força o rerun para atualizar a interface
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gerar sugestão: {str(e)}")
                    st.session_state[key] = ""
            
            # Atualiza o valor no session_state se foi modificado manualmente
            if valor is not None and valor != st.session_state[key]:
                st.session_state[key] = valor
            
            return st.session_state[key] if incluir else None
            
        # ========== SOCIAL ==========
        if tipo_briefing == "Post único":
            campos_briefing['especificos']['fotos'] = criar_campo_selecionavel("Fotos necessárias:")
            campos_briefing['especificos']['texto'] = criar_campo_selecionavel("Texto do post:")
            campos_briefing['especificos']['expectativa'] = criar_campo_selecionavel("Expectativa de resultado:")
            campos_briefing['especificos']['tom_voz'] = criar_campo_selecionavel("Tom de voz:", "selectbox", 
                                                                               ["Institucional", "Inspiracional", "Educativo", "Promocional"])
            campos_briefing['especificos']['direcionamento_arte'] = criar_campo_selecionavel("Direcionamento para a arte (KV):")
            campos_briefing['especificos']['palavras_chave'] = criar_campo_selecionavel("Palavras/conceitos-chave:")
            campos_briefing['especificos']['do_donts'] = criar_campo_selecionavel("Do's and Don'ts:")
            campos_briefing['especificos']['referencias'] = criar_campo_selecionavel("Referências:")
            campos_briefing['especificos']['materiais_extras'] = criar_campo_selecionavel("Materiais extras:")
            campos_briefing['especificos']['info_sensiveis'] = criar_campo_selecionavel("Informações sensíveis:")
            
            if st.checkbox("É sobre produtos?"):
                campos_briefing['especificos']['produtos_destaque'] = criar_campo_selecionavel("Produtos para destacar:")
        
        elif tipo_briefing == "Planejamento Mensal":
            campos_briefing['especificos']['eventos_mes'] = criar_campo_selecionavel("Eventos do mês:")
            campos_briefing['especificos']['datas_comemorativas'] = criar_campo_selecionavel("Datas/comemorações:")
            campos_briefing['especificos']['expectativa_mensal'] = criar_campo_selecionavel("Expectativa de resultados:")
            campos_briefing['especificos']['planejamento_conteudos'] = criar_campo_selecionavel("Conteúdos planejados:")
            campos_briefing['especificos']['produtos_temas'] = criar_campo_selecionavel("Produtos/temas técnicos:")
            campos_briefing['especificos']['planejamento_anual'] = criar_campo_selecionavel("Planejamento anual aprovado:", "file_uploader")
            campos_briefing['especificos']['manuais'] = criar_campo_selecionavel("Manuais de conteúdo disponíveis:")
        
        # ========== CRM ==========
        elif tipo_briefing == "Planejamento de CRM":
            campos_briefing['especificos']['escopo'] = criar_campo_selecionavel("Escopo contratado:")
            campos_briefing['especificos']['ferramenta_crm'] = criar_campo_selecionavel("Ferramenta de CRM utilizada:")
            campos_briefing['especificos']['maturidade'] = criar_campo_selecionavel("Maturidade de CRM:", "selectbox", 
                                                                                 ["Iniciante", "Intermediário", "Avançado"])
            campos_briefing['especificos']['objetivo_crm'] = criar_campo_selecionavel("Objetivo com CRM:")
            campos_briefing['especificos']['canais'] = criar_campo_selecionavel("Canais disponíveis:", "multiselect", 
                                                                              ["Email", "SMS", "WhatsApp", "Mídia Paga"])
            campos_briefing['especificos']['perfil_empresa'] = criar_campo_selecionavel("Perfil da empresa:", "selectbox", ["B2B", "B2C"])
            campos_briefing['especificos']['metas'] = criar_campo_selecionavel("Metas a serem alcançadas:")
            campos_briefing['especificos']['tamanho_base'] = criar_campo_selecionavel("Tamanho da base:")
            campos_briefing['especificos']['segmentacao'] = criar_campo_selecionavel("Segmentação/público-alvo:")
            campos_briefing['especificos']['tom_voz'] = criar_campo_selecionavel("Tom de voz:")
            campos_briefing['especificos']['fluxos'] = criar_campo_selecionavel("Fluxos/e-mails para trabalhar:")
            
            if st.checkbox("Geração de leads?"):
                campos_briefing['especificos']['sla'] = criar_campo_selecionavel("SLA entre marketing e vendas:")
        
        elif tipo_briefing == "Fluxo de Nutrição":
            campos_briefing['especificos']['gatilho'] = criar_campo_selecionavel("Gatilho de entrada:")
            campos_briefing['especificos']['asset_relacionado'] = criar_campo_selecionavel("Asset/evento relacionado:")
            campos_briefing['especificos']['etapa_funil'] = criar_campo_selecionavel("Etapa do funil:", "selectbox", 
                                                                                  ["Topo", "Meio", "Fundo"])
            campos_briefing['especificos']['canais_fluxo'] = criar_campo_selecionavel("Canais para o fluxo:", "multiselect", 
                                                                                   ["Email", "SMS", "WhatsApp", "Mídia Paga"])
            campos_briefing['especificos']['data_ativacao'] = criar_campo_selecionavel("Data de ativação esperada:", "date_input")
            campos_briefing['especificos']['objetivo_fluxo'] = criar_campo_selecionavel("Objetivo do fluxo:")
            campos_briefing['especificos']['resultado_esperado'] = criar_campo_selecionavel("Resultado final esperado:")

        elif tipo_briefing == "Email Marketing":
            campos_briefing['especificos']['publico_email'] = criar_campo_selecionavel("Público e segmentação:")
            campos_briefing['especificos']['data_disparo'] = criar_campo_selecionavel("Data de disparo:", "date_input")
            campos_briefing['especificos']['horario_preferencial'] = criar_campo_selecionavel("Horário preferencial:", "text_input")
            campos_briefing['especificos']['objetivo_email'] = criar_campo_selecionavel("Objetivo:")
            campos_briefing['especificos']['resultado_esperado'] = criar_campo_selecionavel("Resultado final esperado:")
            campos_briefing['especificos']['psd_figma'] = criar_campo_selecionavel("Arquivo PSD/Figma do email:", "file_uploader")
            campos_briefing['especificos']['google_doc'] = criar_campo_selecionavel("Link do Google Doc com conteúdo:", "text_input")
            campos_briefing['especificos']['links_videos'] = criar_campo_selecionavel("Links de vídeos:")
            campos_briefing['especificos']['ctas'] = criar_campo_selecionavel("CTAs:")

        elif tipo_briefing == "Campanha de Mídia":
            campos_briefing['especificos']['periodo_acao'] = criar_campo_selecionavel("Período da ação:", "text_input")
            campos_briefing['especificos']['orcamento'] = criar_campo_selecionavel("Orçamento (R$):", "number_input")
            campos_briefing['especificos']['mecanismo_promocional'] = criar_campo_selecionavel("Mecanismo promocional:")
            campos_briefing['especificos']['praca_especifica'] = criar_campo_selecionavel("Praça específica:")
            campos_briefing['especificos']['responsavel_criativo'] = criar_campo_selecionavel("Quem fará os criativos:", "selectbox", 
                                                                                           ["Macfor", "Cliente"])
            campos_briefing['especificos']['materiais'] = criar_campo_selecionavel("Materiais (copies e peças criativas):")
            campos_briefing['especificos']['objetivo_acao'] = criar_campo_selecionavel("Objetivo da ação:")
            campos_briefing['especificos']['meta'] = criar_campo_selecionavel("Meta:")
            campos_briefing['especificos']['plataformas'] = criar_campo_selecionavel("Plataformas:", "multiselect", 
                                                                                  ["Facebook", "Instagram", "Google Ads", "LinkedIn"])
            campos_briefing['especificos']['segmentacao'] = criar_campo_selecionavel("Segmentação:")
            campos_briefing['especificos']['link_destino'] = criar_campo_selecionavel("Link de destino:", "text_input")

        elif tipo_briefing == "Manutenção de Site":
            st.markdown("**Descreva a demanda usando 5W2H:**")
            campos_briefing['especificos']['what'] = criar_campo_selecionavel("O que precisa ser feito?")
            campos_briefing['especificos']['why'] = criar_campo_selecionavel("Por que é necessário?")
            campos_briefing['especificos']['where'] = criar_campo_selecionavel("Onde deve ser implementado?")
            campos_briefing['especificos']['when'] = criar_campo_selecionavel("Quando precisa estar pronto?")
            campos_briefing['especificos']['who'] = criar_campo_selecionavel("Quem será impactado?")
            campos_briefing['especificos']['how'] = criar_campo_selecionavel("Como deve funcionar?")
            campos_briefing['especificos']['how_much'] = criar_campo_selecionavel("Qual o esforço estimado?")
            campos_briefing['especificos']['descricao_alteracao'] = criar_campo_selecionavel("Descrição detalhada da alteração:")
            campos_briefing['especificos']['prints'] = criar_campo_selecionavel("Anexar prints (se aplicável):", "file_uploader")
            campos_briefing['especificos']['link_referencia'] = criar_campo_selecionavel("Link de referência:", "text_input")
            
            if st.checkbox("É cliente novo?"):
                campos_briefing['especificos']['acessos'] = criar_campo_selecionavel("Acessos (servidor, CMS, etc.):")

        elif tipo_briefing == "Construção de Site":
            campos_briefing['especificos']['acessos'] = criar_campo_selecionavel("Acessos (servidor, nuvens, repositórios, CMS):")
            campos_briefing['especificos']['dominio'] = criar_campo_selecionavel("Domínio:", "text_input")
            campos_briefing['especificos']['prototipo'] = criar_campo_selecionavel("Protótipo em Figma:", "file_uploader")
            campos_briefing['especificos']['conteudos'] = criar_campo_selecionavel("Conteúdos (textos, banners, vídeos):")
            campos_briefing['especificos']['plataforma'] = criar_campo_selecionavel("Plataforma:", "selectbox", 
                                                                                 ["WordPress", "React", "Vue.js", "Outra"])
            campos_briefing['especificos']['hierarquia'] = criar_campo_selecionavel("Hierarquia de páginas:")
            
            if st.checkbox("Incluir otimização SEO?"):
                campos_briefing['especificos']['seo'] = True
                campos_briefing['especificos']['palavras_chave'] = criar_campo_selecionavel("Palavras-chave principais:")
            else:
                campos_briefing['especificos']['seo'] = False

        elif tipo_briefing == "Landing Page":
            campos_briefing['especificos']['objetivo_lp'] = criar_campo_selecionavel("Objetivo da LP:")
            campos_briefing['especificos']['plataforma'] = criar_campo_selecionavel("Plataforma de desenvolvimento:", "text_input")
            campos_briefing['especificos']['integracao_site'] = criar_campo_selecionavel("Precisa integrar com site existente?", "selectbox", 
                                                                                      ["Sim", "Não"])
            campos_briefing['especificos']['dados_coletar'] = criar_campo_selecionavel("Dados a serem coletados no formulário:")
            campos_briefing['especificos']['destino_dados'] = criar_campo_selecionavel("Onde os dados serão gravados:")
            campos_briefing['especificos']['kv_referencia'] = criar_campo_selecionavel("KV de referência:", "file_uploader")
            campos_briefing['especificos']['conteudos_pagina'] = criar_campo_selecionavel("Conteúdos da página:")
            campos_briefing['especificos']['menu'] = criar_campo_selecionavel("Menu/barra de navegação:")
            campos_briefing['especificos']['header_footer'] = criar_campo_selecionavel("Header e Footer:")
            campos_briefing['especificos']['comunicar'] = criar_campo_selecionavel("O que deve ser comunicado:")
            campos_briefing['especificos']['nao_comunicar'] = criar_campo_selecionavel("O que não deve ser comunicado:")
            campos_briefing['especificos']['observacoes'] = criar_campo_selecionavel("Observações:")

        elif tipo_briefing == "Dashboards":
            st.markdown("**Acessos:**")
            campos_briefing['especificos']['google_access'] = st.checkbox("Solicitar acesso Google Analytics")
            campos_briefing['especificos']['meta_access'] = st.checkbox("Solicitar acesso Meta Ads")
            campos_briefing['especificos']['outros_acessos'] = criar_campo_selecionavel("Outros acessos necessários:")
            
            st.markdown("**Requisitos do Dashboard:**")
            campos_briefing['especificos']['okrs'] = criar_campo_selecionavel("OKRs e metas:")
            campos_briefing['especificos']['dados_necessarios'] = criar_campo_selecionavel("Dados que precisam ser exibidos:")
            campos_briefing['especificos']['tipos_graficos'] = criar_campo_selecionavel("Tipos de gráficos preferidos:", "multiselect", 
                                                                                      ["Barras", "Linhas", "Pizza", "Mapas", "Tabelas"])
            campos_briefing['especificos']['atualizacao'] = criar_campo_selecionavel("Frequência de atualização:", "selectbox", 
                                                                                  ["Tempo real", "Diária", "Semanal", "Mensal"])

        elif tipo_briefing == "Social (Design)":
            campos_briefing['especificos']['formato'] = criar_campo_selecionavel("Formato:", "selectbox", ["Estático", "Motion"])
            campos_briefing['especificos']['kv'] = criar_campo_selecionavel("KV a ser seguido:", "file_uploader")
            campos_briefing['especificos']['linha_criativa'] = criar_campo_selecionavel("Linha criativa:")
            campos_briefing['especificos']['usar_fotos'] = criar_campo_selecionavel("Usar fotos?", "selectbox", ["Sim", "Não"])
            campos_briefing['especificos']['referencias'] = criar_campo_selecionavel("Referências:")
            campos_briefing['especificos']['identidade_visual'] = criar_campo_selecionavel("Elementos de identidade visual:")
            campos_briefing['especificos']['texto_arte'] = criar_campo_selecionavel("Texto da arte:")

        elif tipo_briefing == "CRM (Design)":
            st.info("Layouts simples são mais eficientes para CRM!")
            campos_briefing['especificos']['referencias'] = criar_campo_selecionavel("Referências visuais:")
            campos_briefing['especificos']['tipografia'] = criar_campo_selecionavel("Tipografia preferencial:", "text_input")
            campos_briefing['especificos']['ferramenta_envio'] = criar_campo_selecionavel("Ferramenta de CRM que enviará a arte:", "text_input")
            campos_briefing['especificos']['formato_arte'] = criar_campo_selecionavel("Formato da arte:", "selectbox", ["Imagem", "HTML"])

        elif tipo_briefing == "Mídia (Design)":
            campos_briefing['especificos']['formato'] = criar_campo_selecionavel("Formato:", "selectbox", ["Horizontal", "Vertical", "Quadrado"])
            campos_briefing['especificos']['tipo_peca'] = criar_campo_selecionavel("Tipo de peça:", "selectbox", 
                                                                                 ["Arte estática", "Carrossel", "Motion"])
            campos_briefing['especificos']['direcionamento'] = criar_campo_selecionavel("Direcionamento de conteúdo:")
            campos_briefing['especificos']['num_pecas'] = criar_campo_selecionavel("Número de peças:", "number_input", padrao=1)
            campos_briefing['especificos']['publico'] = criar_campo_selecionavel("Público-alvo:")
            campos_briefing['especificos']['objetivo'] = criar_campo_selecionavel("Objetivo:")
            campos_briefing['especificos']['referencias_concorrentes'] = criar_campo_selecionavel("Referências de concorrentes:")

        elif tipo_briefing == "KV/Identidade Visual":
            campos_briefing['especificos']['info_negocio'] = criar_campo_selecionavel("Informações do negócio:")
            campos_briefing['especificos']['referencias'] = criar_campo_selecionavel("Referências:")
            campos_briefing['especificos']['restricoes'] = criar_campo_selecionavel("O que não fazer (cores, elementos proibidos):")
            campos_briefing['especificos']['manual_anterior'] = criar_campo_selecionavel("Manual de marca anterior:", "file_uploader")
            campos_briefing['especificos']['imagem_transmitir'] = criar_campo_selecionavel("Qual imagem queremos transmitir?")
            campos_briefing['especificos']['tema_campanha'] = criar_campo_selecionavel("Tema da campanha:")
            campos_briefing['especificos']['publico'] = criar_campo_selecionavel("Público-alvo:")
            campos_briefing['especificos']['tom_voz'] = criar_campo_selecionavel("Tom de voz:")
            campos_briefing['especificos']['banco_imagens'] = criar_campo_selecionavel("Tipo de imagens:", "selectbox", 
                                                                                    ["Banco de imagens", "Pessoas reais"])
            campos_briefing['especificos']['limitacoes'] = criar_campo_selecionavel("Limitações de uso:")

        elif tipo_briefing == "Email Marketing (Redação)":
            campos_briefing['especificos']['objetivo_email'] = criar_campo_selecionavel("Objetivo:")
            campos_briefing['especificos']['produtos'] = criar_campo_selecionavel("Produtos a serem divulgados:")
            campos_briefing['especificos']['estrutura'] = criar_campo_selecionavel("Estrutura desejada:")
            campos_briefing['especificos']['cta'] = criar_campo_selecionavel("CTA desejado:")
            campos_briefing['especificos']['link_cta'] = criar_campo_selecionavel("Link para o CTA:", "text_input")
            campos_briefing['especificos']['parte_campanha'] = criar_campo_selecionavel("Faz parte de campanha maior?", "selectbox", 
                                                                                      ["Sim", "Não"])

        elif tipo_briefing == "Site (Redação)":
            campos_briefing['especificos']['objetivo_site'] = criar_campo_selecionavel("Objetivo:")
            campos_briefing['especificos']['informacoes'] = criar_campo_selecionavel("Quais informações precisa ter:")
            campos_briefing['especificos']['links'] = criar_campo_selecionavel("Links necessários:")
            campos_briefing['especificos']['wireframe'] = criar_campo_selecionavel("Wireframe do site:", "file_uploader")
            campos_briefing['especificos']['tamanho_texto'] = criar_campo_selecionavel("Tamanho do texto:", "selectbox", 
                                                                                    ["Curto", "Médio", "Longo"])
            
            if st.checkbox("É site novo?"):
                campos_briefing['especificos']['insumos'] = criar_campo_selecionavel("Insumos sobre a empresa/projeto:")

        elif tipo_briefing == "Campanha de Mídias (Redação)":
            campos_briefing['especificos']['objetivo_campanha'] = criar_campo_selecionavel("Objetivo:")
            campos_briefing['especificos']['plataformas'] = criar_campo_selecionavel("Plataformas:", "multiselect", 
                                                                                   ["Facebook", "Instagram", "LinkedIn", "Google"])
            campos_briefing['especificos']['palavras_chave'] = criar_campo_selecionavel("Palavras-chave:")
            campos_briefing['especificos']['tom_voz'] = criar_campo_selecionavel("Tom de voz:")
            campos_briefing['especificos']['publico'] = criar_campo_selecionavel("Público-alvo:")
            campos_briefing['especificos']['cronograma'] = criar_campo_selecionavel("Cronograma:")

        elif tipo_briefing == "Relatórios":
            campos_briefing['especificos']['objetivo_relatorio'] = criar_campo_selecionavel("Objetivo:")
            campos_briefing['especificos']['periodo_analise'] = criar_campo_selecionavel("Período de análise:")
            campos_briefing['especificos']['granularidade'] = criar_campo_selecionavel("Granularidade:", "selectbox", 
                                                                                    ["Diária", "Semanal", "Mensal", "Trimestral"])
            campos_briefing['especificos']['metricas'] = criar_campo_selecionavel("Métricas a serem incluídas:")
            campos_briefing['especificos']['comparativos'] = criar_campo_selecionavel("Comparativos desejados:")

        elif tipo_briefing == "Estratégico":
            campos_briefing['especificos']['introducao'] = criar_campo_selecionavel("Introdução sobre a empresa:")
            campos_briefing['especificos']['orcamento'] = criar_campo_selecionavel("Orçamento (R$):", "number_input")
            campos_briefing['especificos']['publico'] = criar_campo_selecionavel("Público-alvo:")
            campos_briefing['especificos']['objetivo_mkt'] = criar_campo_selecionavel("Objetivo de marketing:")
            campos_briefing['especificos']['etapas_funil'] = criar_campo_selecionavel("Etapas do funil:", "multiselect", 
                                                                                    ["Topo", "Meio", "Fundo"])
            campos_briefing['especificos']['canais'] = criar_campo_selecionavel("Canais disponíveis:", "multiselect", 
                                                                              ["Social", "Email", "Site", "Mídia Paga", "SEO"])
            campos_briefing['especificos']['produtos'] = criar_campo_selecionavel("Produtos/portfólio:")
            campos_briefing['especificos']['metas'] = criar_campo_selecionavel("Metas e métricas:")
            campos_briefing['especificos']['concorrentes'] = criar_campo_selecionavel("Concorrentes:")
            campos_briefing['especificos']['acessos'] = criar_campo_selecionavel("Acessos (GA, Meta Ads, etc.):")
            campos_briefing['especificos']['expectativas'] = criar_campo_selecionavel("Expectativas de resultados:")
            campos_briefing['especificos']['materiais'] = criar_campo_selecionavel("Materiais de apoio:")

        elif tipo_briefing == "Concorrência":
            campos_briefing['especificos']['orcamento'] = criar_campo_selecionavel("Orçamento (R$):", "number_input")
            campos_briefing['especificos']['publico'] = criar_campo_selecionavel("Público-alvo:")
            campos_briefing['especificos']['objetivo'] = criar_campo_selecionavel("Objetivo:")
            campos_briefing['especificos']['etapas_funil'] = criar_campo_selecionavel("Etapas do funil:", "multiselect", 
                                                                                    ["Topo", "Meio", "Fundo"])
            campos_briefing['especificos']['produtos'] = criar_campo_selecionavel("Produtos/portfólio:")
            campos_briefing['especificos']['metas'] = criar_campo_selecionavel("Metas e métricas:")
            campos_briefing['especificos']['concorrentes'] = criar_campo_selecionavel("Concorrentes:")
            campos_briefing['especificos']['acessos'] = criar_campo_selecionavel("Acessos (GA, Meta Ads, etc.):")
            campos_briefing['especificos']['expectativas'] = criar_campo_selecionavel("Expectativas de resultados:")
        
        # Botão para gerar o briefing
        if st.button("🔄 Gerar Briefing Completo", type="primary"):
            with st.spinner('Construindo briefing profissional...'):
                try:
                    # Remove campos None (não selecionados)
                    campos_briefing['especificos'] = {k: v for k, v in campos_briefing['especificos'].items() if v is not None}
                    
                    # Construir o prompt com todas as informações coletadas
                    prompt_parts = [
                        f"# BRIEFING {tipo_briefing.upper()} - Positivo_Tecnologia",
                        f"**Projeto:** {campos_briefing['basicos']['nome_projeto']}",
                        f"**Responsável:** {campos_briefing['basicos']['responsavel']}",
                        f"**Data de Entrega:** {campos_briefing['basicos']['data_entrega']}",
                        "",
                        "## 1. INFORMAÇÕES BÁSICAS",
                        f"**Objetivo Geral:** {campos_briefing['basicos']['objetivo_geral']}",
                        "",
                        "## 2. INFORMAÇÕES ESPECÍFICAS"
                    ]
                    
                    # Adicionar campos específicos
                    for campo, valor in campos_briefing['especificos'].items():
                        if isinstance(valor, list):
                            valor = ", ".join(valor)
                        prompt_parts.append(f"**{campo.replace('_', ' ').title()}:** {valor}")
                    
                    prompt = "\n".join(prompt_parts)
                    resposta = modelo_texto.generate_content(prompt)
                    
                    # Salvar no MongoDB
                    briefing_data = {
                        "tipo": tipo_briefing,
                        "categoria": categoria,
                        "nome_projeto": campos_briefing['basicos']['nome_projeto'],
                        "responsavel": campos_briefing['basicos']['responsavel'],
                        "data_criacao": datetime.datetime.now(),
                        "data_entrega": campos_briefing['basicos']['data_entrega'],
                        "conteudo": resposta.text,
                        "campos_preenchidos": campos_briefing,
                        "obervacoes": obs,
                    }
                    collection_briefings.insert_one(briefing_data)
                    
                    st.subheader(f"Briefing {tipo_briefing} - {campos_briefing['basicos']['nome_projeto']}")
                    st.markdown(resposta.text)
                                
                    st.download_button(
                        label="📥 Download do Briefing",
                        data=resposta.text,
                        file_name=f"briefing_{tipo_briefing.lower().replace(' ', '_')}_{campos_briefing['basicos']['nome_projeto'].lower().replace(' ', '_')}.txt",
                        mime="text/plain"
                    )
                        
                except Exception as e:
                    st.error(f"Erro ao gerar briefing")

    with tab_saved:
        st.subheader("Briefings Salvos")
        
        # Conexão correta com a coleção (ajuste conforme sua configuração)
        # Se você já tem a conexão configurada em outro lugar, mantenha apenas a linha abaixo
        collection_briefings = client2.briefings_Positivo_Tecnologia.briefings  # Ajuste aqui
        
        # Filtros
        col_filtro1, col_filtro2 = st.columns(2)
        with col_filtro1:
            filtro_categoria = st.selectbox("Filtrar por categoria:", ["Todos"] + list(tipos_briefing.keys()))
        with col_filtro2:
            if filtro_categoria == "Todos":
                tipos_disponiveis = [item for sublist in tipos_briefing.values() for item in sublist]
                filtro_tipo = st.selectbox("Filtrar por tipo:", ["Todos"] + tipos_disponiveis)
            else:
                filtro_tipo = st.selectbox("Filtrar por tipo:", ["Todos"] + tipos_briefing[filtro_categoria])
        
        # Construir query para MongoDB
        query = {}
        if filtro_categoria != "Todos":
            query["categoria"] = filtro_categoria
        if filtro_tipo != "Todos":
            query["tipo"] = filtro_tipo
        
        # Buscar briefings - adicionei ordenação por data decrescente
        briefings_salvos = list(collection_briefings.find(query).sort("data_criacao", -1).limit(50))
        
        # Debug: mostra quantos documentos foram encontrados
        st.caption(f"Documentos encontrados: {len(briefings_salvos)}")
        
        if not briefings_salvos:
            st.info("Nenhum briefing encontrado com os filtros selecionados")
        else:
            for briefing in briefings_salvos:
                with st.expander(f"{briefing['tipo']} - {briefing['nome_projeto']} ({briefing['data_criacao'].strftime('%d/%m/%Y')})"):
                    st.markdown(briefing['conteudo'])
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.download_button(
                            label="📥 Download",
                            data=briefing['conteudo'],
                            file_name=f"briefing_{briefing['tipo'].lower().replace(' ', '_')}_{briefing['nome_projeto'].lower().replace(' ', '_')}.txt",
                            mime="text/plain",
                            key=f"dl_{briefing['_id']}"
                        )
                    with col2:
                        if st.button("🗑️", key=f"del_{briefing['_id']}"):
                            collection_briefings.delete_one({"_id": briefing['_id']})
                            st.rerun()
with tab_resumo:
    st.header("Resumo de Textos")
    st.caption("Resuma textos longos mantendo o alinhamento com as diretrizes da Positivo_Tecnologia")
    
    # Layout em colunas
    col_original, col_resumo = st.columns(2)
    
    with col_original:
        st.subheader("Texto Original")
        texto_original = st.text_area(
            "Cole o texto que deseja resumir:",
            height=400,
            placeholder="Insira aqui o texto completo que precisa ser resumido..."
        )
        
        # Configurações do resumo
        with st.expander("⚙️ Configurações do Resumo"):
            nivel_resumo = st.select_slider(
                "Nível de Resumo:",
                options=["Extenso", "Moderado", "Conciso"],
                value="Moderado"
            )
            
            incluir_pontos = st.checkbox(
                "Incluir pontos-chave em tópicos",
                value=True
            )
            
            manter_terminologia = st.checkbox(
                "Manter terminologia técnica",
                value=True
            )
    
    with col_resumo:
        st.subheader("Resumo Gerado")
        
        if st.button("Gerar Resumo", key="gerar_resumo"):
            if not texto_original.strip():
                st.warning("Por favor, insira um texto para resumir")
            else:
                with st.spinner("Processando resumo..."):
                    try:
                        # Configura o prompt de acordo com as opções selecionadas
                        config_resumo = {
                            "Extenso": "um resumo detalhado mantendo cerca de 50% do conteúdo original",
                            "Moderado": "um resumo conciso mantendo cerca de 30% do conteúdo original",
                            "Conciso": "um resumo muito breve com apenas os pontos essenciais (cerca de 10-15%)"
                        }[nivel_resumo]
                        
                        prompt = f"""
                        Crie um resumo profissional deste texto para a Positivo_Tecnologia Cooperativa Agroindustrial,
                        seguindo rigorosamente estas diretrizes da marca:
                        {conteudo}
                        
                        Requisitos:
                        - {config_resumo}
                        - {"Inclua os principais pontos em tópicos" if incluir_pontos else "Formato de texto contínuo"}
                        - {"Mantenha a terminologia técnica específica" if manter_terminologia else "Simplifique a linguagem"}
                        - Priorize informações relevantes para o agronegócio
                        - Mantenha o tom profissional da Positivo_Tecnologia
                        - Adapte para o público-alvo da cooperativa
                        
                        Texto para resumir:
                        {texto_original}
                        
                        Estrutura do resumo:
                        1. Título do resumo
                        2. {"Principais pontos em tópicos (se aplicável)" if incluir_pontos else "Resumo textual"}
                        3. Conclusão/Recomendações
                        """
                        
                        resposta = modelo_texto.generate_content(prompt)
                        
                        # Exibe o resultado
                        st.markdown(resposta.text)
                        
                        # Botão para copiar
                        st.download_button(
                            "📋 Copiar Resumo",
                            data=resposta.text,
                            file_name="resumo_Positivo_Tecnologia.txt",
                            mime="text/plain"
                        )
                        
                    except Exception as e:
                        st.error(f"Erro ao gerar resumo: {str(e)}")
    with tab_briefing_gerados:
        st.header("📚 Briefings Gerados - Positivo_Tecnologia")
        st.markdown("---")
        
        # Container principal com 2 colunas
        col_filtros, col_visualizacao = st.columns([1, 3])
        
        with col_filtros:
            st.subheader("Filtros")
            
            # Filtro por categoria
            categoria_selecionada = st.selectbox(
                "Categoria:",
                ["Todas"] + list(tipos_briefing.keys()),
                key="filtro_categoria_bg"
            )
            
            # Filtro por tipo (dinâmico baseado na categoria)
            if categoria_selecionada == "Todas":
                tipos_disponiveis = sorted({tipo for sublist in tipos_briefing.values() for tipo in sublist})
            else:
                tipos_disponiveis = tipos_briefing[categoria_selecionada]
            
            tipo_selecionado = st.selectbox(
                "Tipo de briefing:",
                ["Todos"] + tipos_disponiveis,
                key="filtro_tipo_bg"
            )
            
            # Filtro por período
            st.markdown("**Período de criação:**")
            col_data1, col_data2 = st.columns(2)
            with col_data1:
                data_inicio = st.date_input(
                    "De",
                    value=datetime.datetime.now() - datetime.timedelta(days=30),
                    key="data_inicio_bg"
                )
            with col_data2:
                data_fim = st.date_input(
                    "Até",
                    value=datetime.datetime.now(),
                    key="data_fim_bg"
                )
            
            # Filtro por responsável
            responsaveis = collection_briefings.distinct("responsavel")
            responsavel_selecionado = st.selectbox(
                "Responsável:",
                ["Todos"] + sorted(responsaveis),
                key="filtro_responsavel_bg"
            )
            
            st.markdown("---")
            st.markdown("**Ações em massa:**")
            if st.button("🔄 Atualizar Lista", use_container_width=True):
                st.rerun()
        
        with col_visualizacao:
            st.subheader("Visualização")
            
            # Construir query para MongoDB
            query = {
                "data_criacao": {
                    "$gte": datetime.datetime.combine(data_inicio, datetime.time.min),
                    "$lte": datetime.datetime.combine(data_fim, datetime.time.max)
                }
            }
            
            if categoria_selecionada != "Todas":
                query["categoria"] = categoria_selecionada
            
            if tipo_selecionado != "Todos":
                query["tipo"] = tipo_selecionado
            
            if responsavel_selecionado != "Todos":
                query["responsavel"] = responsavel_selecionado
            
            # Buscar briefings no MongoDB
            briefings = list(collection_briefings.find(query).sort("data_criacao", -1))
            
            if not briefings:
                st.info("Nenhum briefing encontrado com os filtros selecionados")
            else:
                # Selectbox para navegação rápida
                briefing_selecionado = st.selectbox(
                    "Selecione um briefing para visualizar:",
                    options=[f"{b['tipo']} - {b['nome_projeto']} ({b['data_criacao'].strftime('%d/%m/%Y')})" for b in briefings],
                    index=0,
                    key="selectbox_briefings"
                )
                
                # Encontrar o briefing correspondente
                selected_index = [f"{b['tipo']} - {b['nome_projeto']} ({b['data_criacao'].strftime('%d/%m/%Y')})" for b in briefings].index(briefing_selecionado)
                briefing = briefings[selected_index]
                
                # Exibir briefing
                with st.container(border=True):
                    col_header1, col_header2 = st.columns([3, 1])
                    with col_header1:
                        st.markdown(f"### {briefing['tipo']} - {briefing['nome_projeto']}")
                        st.caption(f"**Responsável:** {briefing['responsavel']} | **Data de criação:** {briefing['data_criacao'].strftime('%d/%m/%Y %H:%M')}")
                        st.caption(f"**Categoria:** {briefing['categoria']} | **Entrega prevista:** {briefing['data_entrega']}")
                    
                    with col_header2:
                        st.download_button(
                            label="📥 Exportar",
                            data=briefing['conteudo'],
                            file_name=f"briefing_{briefing['tipo'].replace(' ', '_')}_{briefing['nome_projeto'].replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    st.markdown("---")
                    
                    # Exibir conteúdo com tabs
                    tab_conteudo, tab_metadados = st.tabs(["📝 Conteúdo", "📊 Metadados"])
                    
                    with tab_conteudo:
                        st.markdown(briefing['conteudo'])
                    
                    with tab_metadados:
                        st.json({
                            "ID": str(briefing['_id']),
                            "Categoria": briefing['categoria'],
                            "Tipo": briefing['tipo'],
                            "Projeto": briefing['nome_projeto'],
                            "Responsável": briefing['responsavel'],
                            "Data de criação": briefing['data_criacao'].strftime('%Y-%m-%d %H:%M:%S'),
                            "Data de entrega": briefing['data_entrega'],
                            "Campos preenchidos": briefing['campos_preenchidos']
                        }, expanded=False)
                
                # Barra de ações
                st.markdown("---")
                col_acao1, col_acao2, col_acao3 = st.columns([1, 1, 2])
                
                with col_acao1:
                    if st.button("✏️ Editar Briefing", use_container_width=True):
                        st.session_state['editar_briefing_id'] = str(briefing['_id'])
                        st.switch_page("pages/editar_briefing.py")  # Substitua pelo seu fluxo de edição
                
                with col_acao2:
                    if st.button("🗑️ Excluir Briefing", type="secondary", use_container_width=True):
                        collection_briefings.delete_one({"_id": briefing['_id']})
                        st.success("Briefing excluído com sucesso!")
                        st.rerun()
                
                with col_acao3:
                    st.write("")  # Espaçamento
    
    # Estilo adicional
    st.markdown("""
    <style>
        div[data-testid="stExpander"] details {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div[data-testid="stVerticalBlock"] {
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
