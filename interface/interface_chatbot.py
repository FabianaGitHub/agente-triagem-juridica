import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime

# Importações do seu projeto
from config import COR_FUNDO, COR_PRIMARIA, COR_SECUNDARIA, FONTE_LABEL, FONTE_BOTAO
from ia.motor_decisao import agente_decisao
from ia.base_conhecimento import obter_orientacao_legal
from banco.banco_dados import gerar_id_sequencial, inserir_caso

class InterfaceChatbot:
    def __init__(self, master):
        self.master = master
        self.master.configure(background=COR_FUNDO)
        
        # Estado da conversa
        self.nome_usuario = ""
        self.relato_usuario = ""
        self.etapa = "NOME" # NOME -> RELATO -> CONFIRMACAO -> FINALIZADO
        
        self._construir_interface()
        self._boas_vindas()

    def _construir_interface(self):
        """Cria os elementos visuais do Chatbot."""
        # Área de exibição do chat (Histórico)
        self.chat_frame = tk.Frame(self.master, bg="white", bd=1, relief="solid")
        self.chat_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        
        self.chat_text = tk.Text(
            self.chat_frame, 
            state="disabled", 
            bg="white", 
            font=("Helvetica", 10),
            wrap="word",
            padx=10, pady=10
        )
        self.chat_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.chat_frame, command=self.chat_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        
        # Área de entrada de mensagem (Input)
        input_frame = tk.Frame(self.master, bg=COR_FUNDO)
        input_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.entry_msg = tk.Entry(input_frame, font=("Helvetica", 11), relief="solid", bd=1)
        self.entry_msg.pack(side="left", fill="x", expand=True, ipady=8)
        self.entry_msg.bind("<Return>", lambda e: self._enviar_mensagem())
        
        self.btn_enviar = tk.Button(
            input_frame, 
            text="Enviar", 
            command=self._enviar_mensagem,
            bg=COR_SECUNDARIA, 
            fg="white", 
            font=FONTE_BOTAO,
            relief="flat",
            padx=15,
            cursor="hand2"
        )
        self.btn_enviar.pack(side="right", padx=(10, 0))

    def _adicionar_mensagem(self, remetente, texto):
        """Adiciona uma bolha de texto ao chat."""
        self.chat_text.config(state="normal")
        
        # Formatação do remetente
        if remetente == "Você":
            cor = COR_PRIMARIA
            prefixo = f"\n[{datetime.now().strftime('%H:%M')}] Você: "
        else:
            cor = "#2c3e50"
            prefixo = f"\n[{datetime.now().strftime('%H:%M')}] Agente IA: "
            
        self.chat_text.insert(tk.END, prefixo, ("bold", remetente))
        self.chat_text.insert(tk.END, f"{texto}\n")
        
        # Configuração de cores e estilos
        self.chat_text.tag_config(remetente, foreground=cor)
        self.chat_text.tag_config("bold", font=("Helvetica", 10, "bold"))
        
        self.chat_text.see(tk.END)
        self.chat_text.config(state="disabled")

    def _boas_vindas(self):
        """Mensagem inicial do Agente."""
        msg = "Olá! Sou o Assistente de Triagem Jurídica IA. Estou aqui para realizar seu atendimento inicial e tirar dúvidas sobre a legislação brasileira.\n\nPara começarmos, como posso te chamar?"
        self._adicionar_mensagem("Agente", msg)

    def _enviar_mensagem(self):
        """Captura a mensagem do usuário e inicia o processamento."""
        msg = self.entry_msg.get().strip()
        if not msg:
            return
        
        self.entry_msg.delete(0, tk.END)
        self._adicionar_mensagem("Você", msg)
        
        # Processamento em background para não travar a interface gráfica
        threading.Thread(target=self._processar_resposta, args=(msg,), daemon=True).start()

    def _processar_resposta(self, msg):
        """Lógica do fluxo de conversa (Máquina de Estados)."""
        time.sleep(0.6) # Simula o tempo de 'leitura' da IA
        
        if self.etapa == "NOME":
            self.nome_usuario = msg
            self.etapa = "RELATO"
            resp = f"Prazer em te conhecer, {self.nome_usuario}! Agora, por favor, me conte o que aconteceu. Tente descrever o problema com o máximo de detalhes (ex: datas, valores, nomes envolvidos)."
            self._adicionar_mensagem("Agente", resp)
            
        elif self.etapa == "RELATO":
            self.relato_usuario = msg
            self._analisar_relato()
            
        elif self.etapa == "CONFIRMACAO":
            confirmacoes = ["sim", "s", "pode", "quero", "com certeza", "ok", "por favor"]
            if any(palavra in msg.lower() for palavra in confirmacoes):
                self._registrar_caso()
            else:
                self.etapa = "RELATO"
                resp = "Entendido. Se quiser me contar mais detalhes ou descrever outro problema, estou ouvindo. Caso contrário, posso te ajudar em algo mais?"
                self._adicionar_mensagem("Agente", resp)

    def _analisar_relato(self):
        """Usa o Motor de Decisão e a Base de Conhecimento para responder."""
        # 1. O Agente identifica a área e a ação
        decisao = agente_decisao.analisar(self.relato_usuario)
        area = decisao["area"]
        acao = decisao["acao_sugerida"]
        
        # 2. Busca o fundamento legal correspondente
        orientacao = obter_orientacao_legal(area)
        
        # 3. Constrói a resposta fundamentada
        resp = f"Analisando seu relato sob a ótica da legislação brasileira, identifiquei que seu caso se enquadra em **{area}**.\n\n"
        resp += f"⚖️ **Fundamento Legal:** {orientacao['fundamento']}\n"
        resp += f"📖 **O que a lei diz:** {orientacao['explicacao']}\n\n"
        resp += f"💡 **Minha Recomendação:** {acao}\n\n"
        resp += "Deseja que eu registre este atendimento no sistema para que um advogado analise seu caso formalmente? (Responda Sim ou Não)"
        
        self.etapa = "CONFIRMACAO"
        self._adicionar_mensagem("Agente", resp)

    def _registrar_caso(self):
        """Salva o caso no banco de dados SQLite de forma automática."""
        try:
            # Gera o ID sequencial sincronizado (ex: 001_2026)
            id_caso = gerar_id_sequencial()
            
            # Re-analisa para garantir os dados finais
            decisao = agente_decisao.analisar(self.relato_usuario)
            
            # Insere no banco de dados (mesma função do cadastro manual)
            inserir_caso(
                id_caso, 
                self.nome_usuario, 
                "Atendimento via Chatbot", # Email padrão
                "Não informado",           # WhatsApp padrão
                self.relato_usuario, 
                decisao["area"], 
                f"Prioridade {decisao['prioridade']}", 
                "" # Sem anexos via chat
            )
            
            self.etapa = "FINALIZADO"
            resp = f"✅ **Sucesso!** Seu atendimento foi registrado com o protocolo **{id_caso}**.\n\nNossa equipe jurídica já recebeu seu relato. Você pode consultar o status na aba 'Consultar Casos'.\n\nPosso ajudar em algo mais?"
            self._adicionar_mensagem("Agente", resp)
            
        except Exception as e:
            self._adicionar_mensagem("Agente", f"⚠️ Desculpe, ocorreu um erro técnico ao registrar seu caso: {e}")
