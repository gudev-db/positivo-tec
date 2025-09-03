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
    page_title="Agente Personalizado",
    page_icon="🤖"
)

# Conexão com MongoDB
client = MongoClient("mongodb+srv://gustavoromao3345:RqWFPNOJQfInAW1N@cluster0.5iilj.mongodb.net/auto_doc?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true")
db = client['agentes_personalizados']
collection_agentes = db['agentes']
collection_briefings = db['briefings']

# Configuração da API Gemini
gemini_api_key = os.getenv("GEM_API_KEY")
genai.configure(api_key=gemini_api_key)
modelo_vision = genai.GenerativeModel("gemini-2.0-flash", generation_config={"temperature": 0.1})
modelo_texto = genai.GenerativeModel("gemini-1.5-flash")

# Funções para gerenciar agentes
def criar_agente(nome, system_prompt, base_conhecimento):
    """Cria um novo agente no banco de dados"""
    agente = {
        "nome": nome,
        "system_prompt": system_prompt,
        "base_conhecimento": base_conhecimento,
        "data_criacao": datetime.datetime.now(),
        "ativo": True
    }
    return collection_agentes.insert_one(agente).inserted_id

def listar_agentes():
    """Lista todos os agentes disponíveis"""
    return list(collection_agentes.find({"ativo": True}).sort("nome", 1))

def obter_agente(agente_id):
    """Obtém um agente específico pelo ID"""
    return collection_agentes.find_one({"_id": agente_id})

def atualizar_agente(agente_id, nome, system_prompt, base_conhecimento):
    """Atualiza um agente existente"""
    return collection_agentes.update_one(
        {"_id": agente_id},
        {"$set": {
            "nome": nome,
            "system_prompt": system_prompt,
            "base_conhecimento": base_conhecimento,
            "data_atualizacao": datetime.datetime.now()
        }}
    )

def desativar_agente(agente_id):
    """Desativa um agente (soft delete)"""
    return collection_agentes.update_one(
        {"_id": agente_id},
        {"$set": {"ativo": False}}
    )

# Interface principal
st.title("🤖 Interface de Agentes Personalizados")

# Sidebar para gerenciamento de agentes
with st.sidebar:
    st.header("🔧 Gerenciamento de Agentes")
    
    # Selecionar agente atual
    agentes = listar_agentes()
    if agentes:
        agente_options = {f"{ag['nome']} (ID: {str(ag['_id'])[:8]})": ag for ag in agentes}
        agente_selecionado_key = st.selectbox(
            "Selecione o Agente:",
            options=list(agente_options.keys())
        )
        agente_selecionado = agente_options[agente_selecionado_key]
        conteudo = agente_selecionado["base_conhecimento"]
        system_prompt = agente_selecionado["system_prompt"]
        st.success(f"Agente: {agente_selecionado['nome']}")
    else:
        st.warning("Nenhum agente criado ainda.")
        conteudo = ""
        system_prompt = "Você é um assistente virtual útil."
        agente_selecionado = None
    
    # Formulário para criar/editar agentes
    with st.expander("➕ Criar/Editar Agente", expanded=False):
        with st.form("form_agente"):
            novo_nome = st.text_input("Nome do Agente:", value=agente_selecionado["nome"] if agente_selecionado else "")
            novo_system_prompt = st.text_area("System Prompt:", 
                                            value=agente_selecionado["system_prompt"] if agente_selecionado else "Você é um assistente virtual especializado. Baseie todas as suas respostas na base de conhecimento fornecida.")
            nova_base = st.text_area("Base de Conhecimento:", height=200,
                                   value=agente_selecionado["base_conhecimento"] if agente_selecionado else "",
                                   placeholder="Cole aqui toda a base de conhecimento para este agente...")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Salvar Agente"):
                    if novo_nome and nova_base:
                        if agente_selecionado:
                            # Atualizar agente existente
                            atualizar_agente(agente_selecionado["_id"], novo_nome, novo_system_prompt, nova_base)
                            st.success("Agente atualizado com sucesso!")
                        else:
                            # Criar novo agente
                            criar_agente(novo_nome, novo_system_prompt, nova_base)
                            st.success("Agente criado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Nome e base de conhecimento são obrigatórios.")
            
            with col2:
                if agente_selecionado and st.form_submit_button("🗑️ Desativar Agente"):
                    desativar_agente(agente_selecionado["_id"])
                    st.success("Agente desativado!")
                    st.rerun()

# Tipos de briefing disponíveis organizados por categoria
tipos_briefing = {
    "Social": ["Post único", "Planejamento Mensal"],
    "CRM": ["Planejamento de CRM", "Fluxo de Nutrição", "Email Marketing"],
    "Mídias": ["Campanha de Mídia"],
    "Tech": ["Manutenção de Site", "Construção de Site", "Landing Page"],
    "Analytics": ["Dashboards"],
    "Design": ["Social", "CRM", "Mídia", "KV/Identidade Visual"],
    "Redação": ["Email Marketing", "Site", "Campanha de Mídias"],
    "Planejamento": ["Relatórios", "Estratégico", "Concorrência"]
}

# Abas principais
tab_chatbot, tab_aprovacao, tab_geracao, tab_briefing, tab_briefing_gerados, tab_resumo = st.tabs([
    "💬 Chatbot", 
    "✅ Aprovação de Conteúdo", 
    "✨ Geração de Conteúdo",
    "📋 Geração de Briefing",  
    "📋 Briefings Gerados",
    "📝 Resumo de Textos",
])

with tab_chatbot:  
    st.header(f"Chat Virtual - {agente_selecionado['nome'] if agente_selecionado else 'Selecione um agente'}")
    st.caption("Pergunte qualquer coisa sobre a base de conhecimento do agente")
    
    if not agente_selecionado:
        st.warning("Por favor, selecione ou crie um agente na sidebar para começar.")
    else:
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
            
            # Prepara o contexto com as diretrizes do agente
            contexto = f"""
            {system_prompt}
            
            Base de conhecimento do {agente_selecionado['nome']}:
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

with tab_aprovacao:
    st.header("Validação de Materiais")
    
    if not agente_selecionado:
        st.warning("Selecione um agente para usar esta funcionalidade")
    else:
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
    
    if not agente_selecionado:
        st.warning("Selecione um agente para usar esta funcionalidade")
    else:
        campanha_brief = st.text_area("Briefing criativo:", help="Descreva objetivos, tom de voz e especificações", height=150)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Diretrizes Visuais")

            if st.button("Gerar Especificações", key="gen_visual"):
                with st.spinner('Criando guia de estilo...'):
                    prompt = f"""
                    Você é um designer que trabalha para criar conteúdo alinhado com as diretrizes da marca.

                    Crie um manual técnico para designers baseado em:
                    Brief: {campanha_brief}
                    Diretrizes: {conteudo}

                    Inclua:
                    1. 🎨 Paleta de cores (códigos HEX/RGB) alinhada à marca
                    2. 🖼️ Diretrizes de fotografia/ilustração (estilo, composição)
                    3. ✏️ Tipografia hierárquica (títulos, corpo de texto)
                    4. 📐 Grid e proporções recomendadas
                    5. ⚠️ Restrições de uso (o que não fazer)
                    6. 🖌️ Descrição detalhada da imagem principal sugerida
                    7. 📱 Adaptações para diferentes formatos (stories, feed, etc.)
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
                    - 📝 Legenda principal (com emojis e quebras de linha)
                    - 🏷️ 10 hashtags relevantes (mix de marca, tema e trending)
                    - 🔗 Sugestão de link (se aplicável)
                    - 📢 CTA adequado ao objetivo
                    """
                    resposta = modelo_texto.generate_content(prompt)
                    st.markdown(resposta.text)



with tab_briefing_gerados:
    st.header("📚 Briefings Gerados")
    
    if not agente_selecionado:
        st.warning("Selecione um agente para usar esta funcionalidade")
    else:
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
            
            # Filtro por tipo
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
            responsaveis = collection_briefings.distinct("responsavel", {"agente_id": agente_selecionado["_id"]})
            responsavel_selecionado = st.selectbox(
                "Responsável:",
                ["Todos"] + sorted(responsaveis),
                key="filtro_responsavel_bg"
            )
        
        with col_visualizacao:
            st.subheader("Visualização")
            
            # Construir query
            query = {
                "agente_id": agente_selecionado["_id"],
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
            
            # Buscar briefings
            briefings = list(collection_briefings.find(query).sort("data_criacao", -1))
            
            if not briefings:
                st.info("Nenhum briefing encontrado com os filtros selecionados")
            else:
                # Selectbox para navegação
                briefing_selecionado = st.selectbox(
                    "Selecione um briefing para visualizar:",
                    options=[f"{b['tipo']} - {b['nome_projeto']} ({b['data_criacao'].strftime('%d/%m/%Y')})" for b in briefings],
                    index=0,
                    key="selectbox_briefings"
                )
                
                # Encontrar briefing correspondente
                selected_index = [f"{b['tipo']} - {b['nome_projeto']} ({b['data_criacao'].strftime('%d/%m/%Y')})" for b in briefings].index(briefing_selecionado)
                briefing = briefings[selected_index]
                
                # Exibir briefing
                with st.container(border=True):
                    col_header1, col_header2 = st.columns([3, 1])
                    with col_header1:
                        st.markdown(f"### {briefing['tipo']} - {briefing['nome_projeto']}")
                        st.caption(f"**Responsável:** {briefing['responsavel']} | **Data:** {briefing['data_criacao'].strftime('%d/%m/%Y %H:%M')}")
                        st.caption(f"**Categoria:** {briefing['categoria']} | **Entrega:** {briefing['data_entrega']}")
                    
                    with col_header2:
                        st.download_button(
                            label="📥 Exportar",
                            data=briefing['conteudo'],
                            file_name=f"briefing_{briefing['tipo'].replace(' ', '_')}_{briefing['nome_projeto'].replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    st.markdown("---")
                    
                    # Tabs de conteúdo
                    tab_conteudo, tab_design, tab_copy, tab_metadados = st.tabs(["📝 Conteúdo", "🎨 Design", "📝 Copy", "📊 Metadados"])
                    
                    with tab_conteudo:
                        st.markdown(briefing['conteudo'])
                    
                    with tab_design:
                        st.markdown(briefing.get('design', 'Nenhum conteúdo de design disponível'))
                    
                    with tab_copy:
                        st.markdown(briefing.get('copywriting', 'Nenhum conteúdo de copy disponível'))
                    
                    with tab_metadados:
                        st.json({
                            "ID": str(briefing['_id']),
                            "Agente": briefing['agente_nome'],
                            "Categoria": briefing['categoria'],
                            "Tipo": briefing['tipo'],
                            "Projeto": briefing['nome_projeto'],
                            "Responsável": briefing['responsavel'],
                            "Data criação": briefing['data_criacao'].strftime('%Y-%m-%d %H:%M:%S'),
                            "Data entrega": briefing['data_entrega']
                        }, expanded=False)

with tab_resumo:
    st.header("Resumo de Textos")
    
    if not agente_selecionado:
        st.warning("Selecione um agente para usar esta funcionalidade")
    else:
        st.caption("Resuma textos longos mantendo o alinhamento com a base de conhecimento do agente")
        
        # Layout em colunas
        col_original, col_resumo = st.columns(2)
        
        with col_original:
            st.subheader("Texto Original")
            texto_original = st.text_area(
                "Cole o texto que deseja resumir:",
                height=400,
                placeholder="Insira aqui o texto completo que precisa ser resumido...",
                key="texto_resumo"
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
                            # Configura o prompt
                            config_resumo = {
                                "Extenso": "um resumo detalhado mantendo cerca de 50% do conteúdo original",
                                "Moderado": "um resumo conciso mantendo cerca de 30% do conteúdo original",
                                "Conciso": "um resumo muito breve com apenas os pontos essenciais (cerca de 10-15%)"
                            }[nivel_resumo]
                            
                            prompt = f"""
                            Crie um resumo profissional deste texto para {agente_selecionado['nome']},
                            seguindo rigorosamente esta base de conhecimento:
                            {conteudo}
                            
                            Requisitos:
                            - {config_resumo}
                            - {"Inclua os principais pontos em tópicos" if incluir_pontos else "Formato de texto contínuo"}
                            - {"Mantenha a terminologia técnica específica" if manter_terminologia else "Simplifique a linguagem"}
                            - Mantenha o tom profissional
                            - Adapte para o público-alvo
                            
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
                                file_name=f"resumo_{agente_selecionado['nome'].replace(' ', '_')}.txt",
                                mime="text/plain"
                            )
                            
                        except Exception as e:
                            st.error(f"Erro ao gerar resumo: {str(e)}")

# Estilização adicional
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
