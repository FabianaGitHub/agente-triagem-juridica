import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import shutil
import uuid

from config import (
    COR_FUNDO, COR_PRIMARIA, COR_SECUNDARIA,
    COR_URGENTE, COR_ALTA, COR_NORMAL,
    FONTE_TITULO, FONTE_LABEL, FONTE_BOTAO,
    ANEXOS_DIR
)
from banco.banco_dados import inserir_caso, buscar_caso_por_id, gerar_id_sequencial
from ia.classificador_casos import classificar_caso, treinar_modelo
from ia.prioridade_caso import calcular_prioridade, obter_cor_prioridade
from relatorios.gerador_pdf import gerar_pdf_caso

class InterfaceInsercao:
    def __init__(self, master: tk.Tk):
        self.master = master
        """self.master.title("Sistema de Triagem Jurídica com IA — Novo Caso")
        self.master.geometry("820x850")
        self.master.resizable(True, True)"""
        self.master.configure(background=COR_FUNDO)
        self._id_caso_var = tk.StringVar(value=gerar_id_sequencial())
        self._tipo_caso_atual = tk.StringVar(value="—")
        self._prioridade_atual = tk.StringVar(value="—")
        self._lista_anexos_originais = []
        self._lista_anexos_copiados = []

        self._construir_interface()
        self._pre_carregar_modelo()

    def _pre_carregar_modelo(self):
        def treinar():
            try:
                treinar_modelo()
            except Exception as e:
                print(f"[Interface] Aviso ao pré-carregar modelo: {e}")

        thread = threading.Thread(target=treinar, daemon=True)
        thread.start()

    def _construir_interface(self):
        frame_cabecalho = tk.Frame(self.master, bg=COR_PRIMARIA, pady=12)
        frame_cabecalho.pack(fill="x")

        tk.Label(
            frame_cabecalho,
            text="Sistema Inteligente de Triagem Jurídica com IA",
            font=FONTE_TITULO,
            bg=COR_PRIMARIA,
            fg="white",
        ).pack()

        canvas = tk.Canvas(self.master, bg=COR_FUNDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.master, orient="vertical", command=canvas.yview)
        self._frame_principal = tk.Frame(canvas, bg=COR_FUNDO, padx=20, pady=10)

        self._frame_principal.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._frame_principal, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame_form = tk.LabelFrame(
            self._frame_principal,
            text=" Dados do Cliente ",
            font=("Helvetica", 10, "bold"),
            bg=COR_FUNDO,
            fg=COR_PRIMARIA,
            padx=10, pady=8,
        )
        frame_form.pack(fill="x", pady=(0, 10))

        self._entry_nome = self._campo_texto(frame_form, "Nome Completo *", 0)
        self._entry_email = self._campo_texto(frame_form, "E-mail", 1)
        self._entry_whatsapp = self._campo_texto(frame_form, "WhatsApp", 2)

        frame_relato = tk.LabelFrame(
            self._frame_principal,
            text=" Relato do Caso *",
            font=("Helvetica", 10, "bold"),
            bg=COR_FUNDO,
            fg=COR_PRIMARIA,
            padx=10, pady=8,
        )
        frame_relato.pack(fill="x", pady=(0, 10))

        self._text_relato = tk.Text(
            frame_relato,
            height=7,
            font=("Helvetica", 10),
            wrap=tk.WORD,
            relief="solid",
            borderwidth=1,
        )
        self._text_relato.pack(fill="x", pady=(4, 0))

        frame_anexos = tk.LabelFrame(
            self._frame_principal,
            text=" Anexos / Evidências ",
            font=("Helvetica", 10, "bold"),
            bg=COR_FUNDO,
            fg=COR_PRIMARIA,
            padx=10, pady=8,
        )
        frame_anexos.pack(fill="x", pady=(0, 10))

        self._listbox_anexos = tk.Listbox(frame_anexos, height=3, font=("Helvetica", 9))
        self._listbox_anexos.pack(fill="x", expand=True, side="left", padx=(0, 10))

        frame_botoes_anexo = tk.Frame(frame_anexos, bg=COR_FUNDO)
        frame_botoes_anexo.pack(side="left")

        tk.Button(
            frame_botoes_anexo,
            text="Adicionar...",
            command=self._adicionar_anexo,
            font=("Helvetica", 9),
            bg=COR_SECUNDARIA,
            fg="white",
            relief="flat",
            padx=10
        ).pack(fill="x", pady=2)

        tk.Button(
            frame_botoes_anexo,
            text="Remover",
            command=self._remover_anexo,
            font=("Helvetica", 9),
            bg=COR_URGENTE,
            fg="white",
            relief="flat",
            padx=10
        ).pack(fill="x", pady=2)

        frame_botoes = tk.Frame(self._frame_principal, bg=COR_FUNDO)
        frame_botoes.pack(fill="x", pady=(0, 10))

        self._btn_analisar = tk.Button(
            frame_botoes,
            text="🔍  Analisar Caso",
            font=FONTE_BOTAO,
            bg=COR_SECUNDARIA,
            fg="black",
            activebackground="#1a6fa8",
            activeforeground="white",
            relief="flat",
            padx=16, pady=8,
            cursor="hand2",
            command=self._analisar_caso,
        )
        self._btn_analisar.pack(side="left", padx=(0, 8))

        self._btn_salvar = tk.Button(
            frame_botoes,
            text="💾  Salvar Caso",
            font=FONTE_BOTAO,
            bg="#27ae60",
            fg="black",
            activebackground="#1e8449",
            activeforeground="white",
            relief="flat",
            padx=16, pady=8,
            cursor="hand2",
            state="disabled",
            command=self._salvar_caso,
        )
        self._btn_salvar.pack(side="left", padx=(0, 8))

        self._btn_pdf = tk.Button(
            frame_botoes,
            text="📄  Gerar PDF",
            font=FONTE_BOTAO,
            bg="#8e44ad",
            fg="Black",
            activebackground="#6c3483",
            activeforeground="white",
            relief="flat",
            padx=16, pady=8,
            cursor="hand2",
            state="disabled",
            command=self._gerar_pdf,
        )
        self._btn_pdf.pack(side="left", padx=(0, 8))

        frame_resultado = tk.LabelFrame(
            self._frame_principal,
            text=" Resultado da Análise de IA ",
            font=("Helvetica", 10, "bold"),
            bg=COR_FUNDO,
            fg=COR_PRIMARIA,
            padx=10, pady=10,
        )
        frame_resultado.pack(fill="x", pady=(0, 10))

        frame_id = tk.Frame(frame_resultado, bg=COR_FUNDO)
        frame_id.pack(fill="x", pady=4)

        tk.Label(
            frame_id,
            text="ID do Caso:",
            font=("Helvetica", 10, "bold"),
            bg=COR_FUNDO,
            fg=COR_PRIMARIA,
            width=18,
            anchor="w",
        ).pack(side="left")

        tk.Label(
            frame_id,
            textvariable=self._id_caso_var,
            font=("Courier", 10),
            bg=COR_FUNDO,
            fg="#555",
        ).pack(side="left")

        frame_tipo = tk.Frame(frame_resultado, bg=COR_FUNDO)
        frame_tipo.pack(fill="x", pady=4)

        tk.Label(
            frame_tipo,
            text="Tipo de Caso:",
            font=("Helvetica", 10, "bold"),
            bg=COR_FUNDO,
            fg=COR_PRIMARIA,
            width=18,
            anchor="w",
        ).pack(side="left")

        self._lbl_tipo = tk.Label(
            frame_tipo,
            textvariable=self._tipo_caso_atual,
            font=("Helvetica", 11, "bold"),
            bg=COR_FUNDO,
            fg=COR_SECUNDARIA,
        )
        self._lbl_tipo.pack(side="left")

        frame_prio = tk.Frame(frame_resultado, bg=COR_FUNDO)
        frame_prio.pack(fill="x", pady=4)

        tk.Label(
            frame_prio,
            text="Prioridade:",
            font=("Helvetica", 10, "bold"),
            bg=COR_FUNDO,
            fg=COR_PRIMARIA,
            width=18,
            anchor="w",
        ).pack(side="left")

        self._lbl_prioridade = tk.Label(
            frame_prio,
            textvariable=self._prioridade_atual,
            font=("Helvetica", 11, "bold"),
            bg=COR_FUNDO,
            fg=COR_NORMAL,
        )
        self._lbl_prioridade.pack(side="left")

        self._lbl_status = tk.Label(
            self._frame_principal,
            text="",
            font=("Helvetica", 9, "italic"),
            bg=COR_FUNDO,
            fg="#121212",
        )
        self._lbl_status.pack()

    def _campo_texto(self, parent, label: str, linha: int) -> tk.Entry:
        frame = tk.Frame(parent, bg=COR_FUNDO)
        frame.pack(fill="x", pady=3)

        tk.Label(
            frame,
            text=label,
            font=FONTE_LABEL,
            bg=COR_FUNDO,
            fg=COR_PRIMARIA,
            width=18,
            anchor="w",
        ).pack(side="left")

        entry = tk.Entry(
            frame,
            font=("Helvetica", 10),
            relief="solid",
            borderwidth=1,
        )
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def _adicionar_anexo(self):
        filepaths = filedialog.askopenfilenames(
            title="Selecionar Anexos",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg"), ("Todos os arquivos", "*.*")]
        )
        if filepaths:
            for path in filepaths:
                if path not in self._lista_anexos_originais:
                    self._lista_anexos_originais.append(path)
                    self._listbox_anexos.insert(tk.END, os.path.basename(path))

    def _remover_anexo(self):
        selecionados = self._listbox_anexos.curselection()
        if selecionados:
            for index in reversed(selecionados):
                self._lista_anexos_originais.pop(index)
                self._listbox_anexos.delete(index)

    def _analisar_caso(self):
        relato = self._text_relato.get("1.0", tk.END).strip()
        if not relato:
            messagebox.showwarning("Aviso", "Por favor, descreva o relato do caso.")
            return

        self._lbl_status.config(text="Analisando...", fg=COR_SECUNDARIA)
        self.master.update()

        tipo = classificar_caso(relato)
        prioridade = calcular_prioridade(relato)
        cor = obter_cor_prioridade(prioridade)

        self._tipo_caso_atual.set(tipo)
        self._prioridade_atual.set(prioridade)
        self._lbl_prioridade.config(fg=cor)
        self._lbl_status.config(text="Análise concluída.", fg=COR_NORMAL)
        self._btn_salvar.config(state="normal")

    def _salvar_caso(self):
        nome = self._entry_nome.get().strip()
        email = self._entry_email.get().strip()
        whatsapp = self._entry_whatsapp.get().strip()
        relato = self._text_relato.get("1.0", tk.END).strip()
        tipo = self._tipo_caso_atual.get()
        prioridade = self._prioridade_atual.get()
        id_caso = self._id_caso_var.get()

        if not nome or not relato:
            messagebox.showwarning("Aviso", "Nome e Relato são obrigatórios.")
            return

        # Processar anexos: copiar para a pasta interna
        self._lista_anexos_copiados = []
        os.makedirs(ANEXOS_DIR, exist_ok=True)
        
        for path_origem in self._lista_anexos_originais:
            try:
                nome_arq = f"{id_caso[:8]}_{os.path.basename(path_origem)}"
                path_destino = os.path.join(ANEXOS_DIR, nome_arq)
                shutil.copy2(path_origem, path_destino)
                self._lista_anexos_copiados.append(path_destino)
            except Exception as e:
                print(f"Erro ao copiar anexo {path_origem}: {e}")

        anexos_str = ",".join(self._lista_anexos_copiados)

        try:
            inserir_caso(id_caso, nome, email, whatsapp, relato, tipo, prioridade, anexos_str)
            messagebox.showinfo("Sucesso", "Caso salvo com sucesso!")
            self._btn_pdf.config(state="normal")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def _gerar_pdf(self):
        id_caso = self._id_caso_var.get()
        dados = buscar_caso_por_id(id_caso)
        if dados:
            try:
                caminho = gerar_pdf_caso(dados)
                messagebox.showinfo("Sucesso", f"PDF gerado em:\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar PDF: {e}")
        else:
            messagebox.showerror("Erro", "Caso não encontrado no banco de dados.")
            
    def limpar_formulario(self):
        self._id_caso_var.set(gerar_id_sequencial())
        self._entry_nome.delete(0, tk.END)
        self._entry_email.delete(0, tk.END)
        self._entry_whatsapp.delete(0, tk.END)
        self._text_relato.delete("1.0", tk.END)
        self._listbox_anexos.delete(0, tk.END)
        self._lista_anexos_originais = []
        self._lista_anexos_copiados = []
        self._tipo_caso_atual.set("—")
        self._prioridade_atual.set("—")
        self._btn_salvar.config(state="disabled")
        self._btn_pdf.config(state="disabled")
        self._lbl_status.config(text="")
