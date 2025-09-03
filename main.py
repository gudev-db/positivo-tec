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
    page_title="Agente Macfor",
    page_icon="assets/page-icon.png"
)

# Sistema de autenticação
def check_login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.image('assets/macLogo.png', width=300)
        st.title("🔐 Login - Sistema Macfor")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image("assets/page-icon.png", width=100)
        with col2:
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            
            if st.button("Entrar"):
                if username == "admin" and password == "senha1234":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")
        st.stop()

# Verificar login
check_login()

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
st.image('assets/macLogo.png', width=300)
st.title("🤖 Sistema de Agentes Macfor")

# Botão de logout na sidebar
with st.sidebar:
    st.image("assets/page-icon.png", width=80)
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()
    
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

with tab_briefing:
    st.header("Gerador de Briefing")
    
    if not agente_selecionado:
        st.warning("Selecione um agente para usar esta funcionalidade")
    else:
        st.caption(f"Crie briefings completos para {agente_selecionado['nome']}")
        
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
                key = f"{rotulo}_{key_suffix}_{tipo}"
                
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
                        return st.file_uploader(rotulo, key=f"input_{key}")
                
                with col2:
                    incluir = st.checkbox("", value=True, key=f"incluir_{key}")
                    auto_preencher = st.button("🪄", key=f"auto_{key}", help="Preencher automaticamente com LLM")
                
                if auto_preencher:
                    prompt = f"Com base no seguinte contexto:\n{conteudo}\n\n E o objetivo do briefing {objetivo_geral} \n\nPreencha o campo '{rotulo}' para um briefing do tipo {tipo_briefing}. Retorne APENAS o valor para o campo, sem comentários ou formatação adicional."
                    
                    try:
                        resposta = modelo_texto.generate_content(prompt)
                        st.session_state[key] = resposta.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao gerar sugestão: {str(e)}")
                        st.session_state[key] = ""
                
                if valor is not None and valor != st.session_state[key]:
                    st.session_state[key] = valor
                
                return st.session_state[key] if incluir else None
            
            # ========== SOCIAL ==========
            if tipo_briefing == "Post único":
                campos_briefing['especificos']['fotos'] = criar_campo_selecionavel("Sugestão de Fotos necessárias:")
                campos_briefing['especificos']['texto'] = criar_campo_selecionavel("Sugestão de Texto do post:")
                campos_briefing['especificos']['expectativa'] = criar_campo_selecionavel("Sugestão de Expectativa de resultado:")
                campos_briefing['especificos']['tom_voz'] = criar_campo_selecionavel("Sugestão de Tom de voz:")
                campos_briefing['especificos']['direcionamento_arte'] = criar_campo_selecionavel("Sugestão de Direcionamento para a arte (KV):")
                campos_briefing['especificos']['palavras_chave'] = criar_campo_selecionavel("Sugestão de Palavras/conceitos-chave:")
                campos_briefing['especificos']['do_donts'] = criar_campo_selecionavel("Sugestão de Do's and Don'ts:")
                campos_briefing['especificos']['referencias'] = criar_campo_selecionavel("Sugestão de Referências:")
                campos_briefing['especificos']['materiais_extras'] = criar_campo_selecionavel("Sugestão de Materiais extras:")
                campos_briefing['especificos']['info_sensiveis'] = criar_campo_selecionavel("Sugestão de Informações sensíveis:")
                
                if st.checkbox("É sobre produtos?"):
                    campos_briefing['especificos']['produtos_destaque'] = criar_campo_selecionavel("Sugestão de Produtos para destacar:")
            
            elif tipo_briefing == "Planejamento Mensal":
                campos_briefing['especificos']['eventos_mes'] = criar_campo_selecionavel("Sugestão de Eventos do mês:")
                campos_briefing['especificos']['datas_comemorativas'] = criar_campo_selecionavel("Sugestão de Datas/comemorações:")
                campos_briefing['especificos']['expectativa_mensal'] = criar_campo_selecionavel("Sugestão de Expectativa de resultados:")
                campos_briefing['especificos']['planejamento_conteudos'] = criar_campo_selecionavel("Sugestão de Conteúdos planejados:")
                campos_briefing['especificos']['produtos_temas'] = criar_campo_selecionavel("Sugestão de Produtos/temas técnicos:")
                campos_briefing['especificos']['planejamento_anual'] = criar_campo_selecionavel("Sugestão de Planejamento anual aprovado:", "file_uploader")
                campos_briefing['especificos']['manuais'] = criar_campo_selecionavel("Sugestão de Manuais de conteúdo disponíveis:")
            
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
                campos_briefing['especificos']['canais_fluxo'] = criar_campo_selecionavel("Canais para divulgação")
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
                campos_briefing['especificos']['where'] = criar_campo_selecionavel("Onde deve ser implementedo?")
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
                            f"# BRIEFING {tipo_briefing.upper()} - {agente_selecionado['nome']}",
                            f"**Projeto:** {campos_briefing['basicos']['nome_projeto']}",
                            f"**Responsável:** {campos_briefing['basicos']['responsavel']}",
                            f"**Data de Entrega:** {campos_briefing['basicos']['data_entrega']}",
                            "",
                            "## 1. INFORMAÇÕES BÁSICAS",
                            f"**Objetivo Geral:** {campos_briefing['basicos']['objetivo_geral']}",
                            "",
                            "## 2. INFORMAÇÃO ESPECÍFICAS"
                        ]
                        
                        for campo, valor in campos_briefing['especificos'].items():
                            if isinstance(valor, list):
                                valor = ", ".join(valor)
                            prompt_parts.append(f"**{campo.replace('_', ' ').title()}:** {valor}")
                        
                        prompt = "\n".join(prompt_parts)
                        resposta = modelo_texto.generate_content(prompt)

                        prompt_design = f"""
                        Você é um designer que trabalha para a Macfor Marketing digital e deve gerar conteúdo criativo.

                        Crie um manual técnico para designers baseado em:
                        ###BEGIN BRIEFING###
                        {resposta.text}
                        ###END BRIEFING###
                        
                        ###BEGIN DIRETRIZES###
                        {conteudo}
                        ###END DIRETRIZES###

                        Inclua:
                        1. 🎨 Paleta de cores (códigos HEX/RGB) alinhada à marca
                        2. 🖼️ Diretrizes de fotografia/ilustração (estilo, composição)
                        3. ✏️ Tipografia hierárquica (títulos, corpo de texto)
                        4. 📐 Grid e proporções recomendadas
                        5. ⚠️ Restrições de uso (o que não fazer)
                        6. 🖌️ Descrição detalhada da imagem principal sugerida
                        7. 📱 Adaptações para diferentes formatos (stories, feed, etc.)
                        """
                        resposta_design = modelo_texto.generate_content(prompt_design)

                        prompt_copy = f"""
                        Crie textos para campanha considerando:
                        ###BEGIN BRIEFING###
                        {resposta.text}
                        ###END BRIEFING###
                        
                        ###BEGIN DIRETRIZES###
                        {conteudo}
                        ###END DIRETRIZES###

                        ###BEGIN DESIGN###
                        {resposta_design.text}
                        ###END DESIGN###
               
                        Entregar:
                        - 📝 Legenda principal (com emojis e quebras de linha)
                        - 🏷️ 10 hashtags relevantes (mix de marca, tema e trending)
                        - 🔗 Sugestão de link (se aplicável)
                        - 📢 CTA adequado ao objetivo
                        """
                        resposta_copy = modelo_texto.generate_content(prompt_copy)
                        
                        # Salvar no MongoDB
                        briefing_data = {
                            "agente_id": agente_selecionado["_id"],
                            "agente_nome": agente_selecionado["nome"],
                            "tipo": tipo_briefing,
                            "categoria": categoria,
                            "nome_projeto": campos_briefing['basicos']['nome_projeto'],
                            "responsavel": campos_briefing['basicos']['responsavel'],
                            "data_criacao": datetime.datetime.now(),
                            "data_entrega": campos_briefing['basicos']['data_entrega'],
                            "conteudo": resposta.text,
                            "design": resposta_design.text,
                            "copywriting": resposta_copy.text,
                            "campos_preenchidos": campos_briefing,
                            "observacoes": obs,
                        }
                        collection_briefings.insert_one(briefing_data)

                        resposta_design_apr = modelo_texto.generate_content(
                        f"""Revise este design conforme:
                        ###BEGIN DIRETRIZES###
                        {conteudo}
                        ###END DIRETRIZES###

                        ###BEGIN DESIGN###
                        {resposta_design.text}
                        ###END DESIGN###
                        
                        Formato requerido:
                        ### Design Ajustado
                        [versão reformulada]
                        
                        ### Alterações Realizadas
                        - [lista itemizada de modificações]
                        ### Justificativas
                        [explicação técnica das mudanças]"""
                    )

                        resposta_apr_copy = modelo_texto.generate_content(
                        f"""Revise este texto conforme:
                        ###BEGIN DIRETRIZES###
                        {conteudo}
                        ###END DIRETRIZES###

                        ###BEGIN TEXTO###
                        {resposta_copy.text}
                        ###END TEXTO###
                        
                        Formato requerido:
                        ### Texto Ajustado
                        [versão reformulada]
                        
                        ### Alterações Realizadas
                        - [lista itemizada de modificações]
                        ### Justificativas
                        [explicação técnica das mudanças]"""
                    )
                        
                        st.subheader(f"1. Briefing {tipo_briefing} - {campos_briefing['basicos']['nome_projeto']}")
                        st.markdown(resposta.text)
                        st.subheader("2. Ideação de design")
                        st.markdown(resposta_design.text)
                        st.subheader("3. Aprovação de Ideação de design")
                        st.markdown(resposta_design_apr.text)
                        st.subheader("4. Copywriting")
                        st.markdown(resposta_copy.text)
                        st.subheader("5. Aprovação de Copywriting")
                        st.markdown(resposta_apr_copy.text)
                                    
                        st.download_button(
                            label="📥 Download do Briefing",
                            data=resposta.text,
                            file_name=f"briefing_{tipo_briefing.lower().replace(' ', '_')}_{campos_briefing['basicos']['nome_projeto'].lower().replace(' ', '_')}.txt",
                            mime="text/plain"
                        )
                            
                    except Exception as e:
                        st.error(f"Erro ao gerar briefing: {str(e)}")

        with tab_saved:
            st.subheader("Briefings Salvos")
            
            # Filtros
            col_filtro1, col_filtro2 = st.columns(2)
            with col_filtro1:
                filtro_categoria = st.selectbox("Filtrar por categoria:", ["Todos"] + list(tipos_briefing.keys()), key="filtro_cat")
            with col_filtro2:
                if filtro_categoria == "Todos":
                    tipos_disponiveis = [item for sublist in tipos_briefing.values() for item in sublist]
                    filtro_tipo = st.selectbox("Filtrar por tipo:", ["Todos"] + tipos_disponiveis, key="filtro_tipo")
                else:
                    filtro_tipo = st.selectbox("Filtrar por tipo:", ["Todos"] + tipos_briefing[filtro_categoria], key="filtro_tipo")
            
            # Construir query
            query = {"agente_id": agente_selecionado["_id"]}
            if filtro_categoria != "Todos":
                query["categoria"] = filtro_categoria
            if filtro_tipo != "Todos":
                query["tipo"] = filtro_tipo
            
            # Buscar briefings
            briefings_salvos = list(collection_briefings.find(query).sort("data_criacao", -1).limit(50))
            
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
