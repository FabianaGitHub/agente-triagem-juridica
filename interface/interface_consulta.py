"""
interface/interface_consulta.py
================================
Interface Gráfica de Consulta de Casos — Tkinter

Este módulo implementa a tela de consulta e visualização dos casos jurídicos
cadastrados no sistema. Permite ao usuário visualizar todos os casos em uma
tabela interativa, pesquisar por nome ou tipo de caso, visualizar os detalhes
completos de um caso selecionado e gerar o PDF do caso.

Classe principal:
    - InterfaceConsulta: janela Tkinter de consulta de casos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COR_FUNDO, COR_PRIMARIA, COR_SECUNDARIA, FONTE_TITULO, FONTE_LABEL
from banco.banco_dados import listar_casos, buscar_caso_por_id
from relatorios.gerador_pdf import gerar_pdf_caso
from ia.prioridade_caso import obter_cor_prioridade


class InterfaceConsulta:
    """
    Janela de consulta e visualização de casos jurídicos cadastrados.

    Exibe uma tabela com todos os casos e permite visualizar detalhes
    e gerar relatórios PDF de casos selecionados.
    """
    def __init__(self, master):
        self.master = master
    
        """
        Inicializa a interface de consulta.

        Parâmetros:
            master (tk.Toplevel): Janela secundária do Tkinter.
        """
        self.master = master
        """self.master.title("Sistema de Triagem Jurídica — Consulta de Casos")
        self.master.geometry("1000x620")
        self.master.resizable(True, True)"""

        self.master.configure(background=COR_FUNDO)
        self._construir_interface()
        self._carregar_casos()

    def _construir_interface(self):
        """Constrói todos os widgets da interface de consulta."""

        # ── Cabeçalho ────────────────────────────────────────────────────
        frame_cabecalho = tk.Frame(self.master, bg=COR_PRIMARIA, pady=10)
        frame_cabecalho.pack(fill="x")

        tk.Label(
            frame_cabecalho,
            text="Consulta de Casos Jurídicos",
            font=FONTE_TITULO,
            bg=COR_PRIMARIA,
            fg="white",
        ).pack()

        # ── Barra de pesquisa ─────────────────────────────────────────────
        frame_pesquisa = tk.Frame(self.master, bg=COR_FUNDO, padx=15, pady=8)
        frame_pesquisa.pack(fill="x")

        tk.Label(
            frame_pesquisa,
            text="Pesquisar:",
            font=FONTE_LABEL,
            bg=COR_FUNDO,
            fg=COR_PRIMARIA,
        ).pack(side="left")

        self._entry_pesquisa = tk.Entry(
            frame_pesquisa,
            font=("Helvetica", 10),
            relief="solid",
            borderwidth=1,
            width=35,
        )
        self._entry_pesquisa.pack(side="left", padx=6)
        self._entry_pesquisa.bind("<KeyRelease>", self._filtrar_casos)

        tk.Button(
            frame_pesquisa,
            text="Atualizar",
            font=("Helvetica", 9, "bold"),
            bg=COR_SECUNDARIA,
            fg="white",
            relief="flat",
            padx=10, pady=4,
            cursor="hand2",
            command=self._carregar_casos,
        ).pack(side="left", padx=4)

        # ── Tabela de casos ───────────────────────────────────────────────
        frame_tabela = tk.Frame(self.master, bg=COR_FUNDO, padx=15)
        frame_tabela.pack(fill="both", expand=True)

        colunas = ("ID", "Nome", "Tipo de Caso", "Prioridade", "Data")
        self._tabela = ttk.Treeview(
            frame_tabela,
            columns=colunas,
            show="headings",
            selectmode="browse",
            height=15,
        )

        # Configuração das colunas
        larguras = {"ID": 60, "Nome": 200, "Tipo de Caso": 200, "Prioridade": 180, "Data": 150}
        for col in colunas:
            self._tabela.heading(col, text=col, command=lambda c=col: self._ordenar(c))
            self._tabela.column(col, width=larguras.get(col, 120), anchor="center")

        # Scrollbars
        scroll_v = ttk.Scrollbar(frame_tabela, orient="vertical", command=self._tabela.yview)
        scroll_h = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self._tabela.xview)
        self._tabela.configure(yscrollcommand=scroll_v.set, xscrollcommand=scroll_h.set)

        self._tabela.pack(side="left", fill="both", expand=True)
        scroll_v.pack(side="right", fill="y")
        scroll_h.pack(side="bottom", fill="x")

        # Evento de seleção
        self._tabela.bind("<<TreeviewSelect>>", self._ao_selecionar)
        self._tabela.bind("<Double-1>", lambda e: self._ver_detalhes())

        # ── Botões de ação ────────────────────────────────────────────────
        frame_acoes = tk.Frame(self.master, bg=COR_FUNDO, padx=15, pady=8)
        frame_acoes.pack(fill="x")

        self._btn_detalhes = tk.Button(
            frame_acoes,
            text="🔎  Ver Detalhes",
            font=("Helvetica", 9, "bold"),
            bg=COR_SECUNDARIA,
            fg="white",
            relief="flat",
            padx=12, pady=6,
            cursor="hand2",
            state="disabled",
            command=self._ver_detalhes,
        )
        self._btn_detalhes.pack(side="left", padx=(0, 8))

        self._btn_pdf = tk.Button(
            frame_acoes,
            text="📄  Gerar PDF",
            font=("Helvetica", 9, "bold"),
            bg="#8e44ad",
            fg="white",
            relief="flat",
            padx=12, pady=6,
            cursor="hand2",
            state="disabled",
            command=self._gerar_pdf,
        )
        self._btn_pdf.pack(side="left")

        # Contador de registros
        self._lbl_total = tk.Label(
            frame_acoes,
            text="",
            font=("Helvetica", 9, "italic"),
            bg=COR_FUNDO,
            fg="#777",
        )
        self._lbl_total.pack(side="right")

        # Armazena todos os casos para filtragem
        self._todos_casos = []

    def _carregar_casos(self):
        """Carrega todos os casos do banco e preenche a tabela."""
        try:
            self._todos_casos = listar_casos()
            self._preencher_tabela(self._todos_casos)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar os casos:\n{e}")

    def _preencher_tabela(self, casos: list):
        """Preenche a tabela com a lista de casos fornecida."""
        # Limpa a tabela
        for item in self._tabela.get_children():
            self._tabela.delete(item)

        # Cores de fundo alternadas por prioridade
        self._tabela.tag_configure("urgente", background="#fde8e8")
        self._tabela.tag_configure("alta", background="#fef3e2")
        self._tabela.tag_configure("normal", background="#eafaf1")
        self._tabela.tag_configure("par", background="#f8f9fa")

        for i, caso in enumerate(casos):
            caso_id, nome, email, whatsapp, relato, tipo, prioridade, anexos, data = caso

            # Define a tag de cor baseada na prioridade
            if prioridade and "1" in str(prioridade):
                tag = "urgente"
            elif prioridade and "2" in str(prioridade):
                tag = "alta"
            elif prioridade and "3" in str(prioridade):
                tag = "normal"
            else:
                tag = "par" if i % 2 == 0 else ""

            self._tabela.insert(
                "",
                "end",
                iid=str(caso_id),
                values=(f"#{caso_id:04d}", nome, tipo, prioridade, data),
                tags=(tag,),
            )

        self._lbl_total.config(text=f"Total: {len(casos)} caso(s)")

    def _filtrar_casos(self, event=None):
        """Filtra os casos exibidos com base no texto de pesquisa."""
        termo = self._entry_pesquisa.get().strip().lower()
        if not termo:
            self._preencher_tabela(self._todos_casos)
            return

        filtrados = [
            caso for caso in self._todos_casos
            if termo in str(caso[1]).lower()   # Nome
            or termo in str(caso[5]).lower()   # Tipo de caso
            or termo in str(caso[6]).lower()   # Prioridade
        ]
        self._preencher_tabela(filtrados)

    def _ao_selecionar(self, event=None):
        """Habilita os botões quando um caso é selecionado."""
        selecionado = self._tabela.selection()
        estado = "normal" if selecionado else "disabled"
        self._btn_detalhes.config(state=estado)
        self._btn_pdf.config(state=estado)

    def _ver_detalhes(self):
        """Abre uma janela com os detalhes completos do caso selecionado."""
        selecionado = self._tabela.selection()
        if not selecionado:
            return

        caso_id = int(selecionado[0])
        dados = buscar_caso_por_id(caso_id)
        if not dados:
            messagebox.showerror("Erro", "Caso não encontrado.")
            return

        # Janela de detalhes
        janela = tk.Toplevel(self.master)
        janela.title(f"Detalhes do Caso #{caso_id:04d}")
        janela.geometry("600x500")
        janela.configure(bg=COR_FUNDO)

        caso_id, nome, email, whatsapp, relato, tipo, prioridade, data = dados
        cor_prio = obter_cor_prioridade(str(prioridade))

        # Cabeçalho
        tk.Frame(janela, bg=COR_PRIMARIA, height=4).pack(fill="x")
        frame_titulo = tk.Frame(janela, bg=COR_PRIMARIA, pady=8)
        frame_titulo.pack(fill="x")
        tk.Label(
            frame_titulo,
            text=f"Caso #{caso_id:04d} — {nome}",
            font=("Helvetica", 12, "bold"),
            bg=COR_PRIMARIA,
            fg="white",
        ).pack()

        # Conteúdo
        frame_conteudo = tk.Frame(janela, bg=COR_FUNDO, padx=20, pady=15)
        frame_conteudo.pack(fill="both", expand=True)

        campos = [
            ("Data de Cadastro:", data),
            ("Nome:", nome),
            ("E-mail:", email or "Não informado"),
            ("WhatsApp:", whatsapp or "Não informado"),
            ("Tipo de Caso:", tipo),
        ]

        for label, valor in campos:
            frame_linha = tk.Frame(frame_conteudo, bg=COR_FUNDO)
            frame_linha.pack(fill="x", pady=2)
            tk.Label(frame_linha, text=label, font=("Helvetica", 9, "bold"),
                     bg=COR_FUNDO, fg=COR_PRIMARIA, width=18, anchor="w").pack(side="left")
            tk.Label(frame_linha, text=str(valor), font=("Helvetica", 9),
                     bg=COR_FUNDO, fg="#333").pack(side="left")

        # Prioridade com cor
        frame_prio = tk.Frame(frame_conteudo, bg=COR_FUNDO)
        frame_prio.pack(fill="x", pady=2)
        tk.Label(frame_prio, text="Prioridade:", font=("Helvetica", 9, "bold"),
                 bg=COR_FUNDO, fg=COR_PRIMARIA, width=18, anchor="w").pack(side="left")
        tk.Label(frame_prio, text=str(prioridade), font=("Helvetica", 9, "bold"),
                 bg=COR_FUNDO, fg=cor_prio).pack(side="left")

        # Relato
        tk.Label(frame_conteudo, text="Relato:", font=("Helvetica", 9, "bold"),
                 bg=COR_FUNDO, fg=COR_PRIMARIA, anchor="w").pack(fill="x", pady=(8, 2))

        from tkinter import scrolledtext
        text_relato = scrolledtext.ScrolledText(
            frame_conteudo, height=8, font=("Helvetica", 9),
            wrap=tk.WORD, relief="solid", borderwidth=1,
        )
        text_relato.insert("1.0", str(relato))
        text_relato.config(state="disabled")
        text_relato.pack(fill="both", expand=True)

    def _gerar_pdf(self):
        """Gera o PDF do caso selecionado na tabela."""
        selecionado = self._tabela.selection()
        if not selecionado:
            return

        caso_id = int(selecionado[0])
        dados = buscar_caso_por_id(caso_id)
        if not dados:
            messagebox.showerror("Erro", "Caso não encontrado.")
            return

        try:
            caminho = gerar_pdf_caso(dados)
            messagebox.showinfo(
                "PDF gerado",
                f"Relatório gerado com sucesso!\n\nArquivo:\n{caminho}",
            )
        except Exception as e:
            messagebox.showerror("Erro ao gerar PDF", f"Não foi possível gerar o PDF:\n{e}")

    def _ordenar(self, coluna: str):
        """Ordena a tabela pela coluna clicada."""
        dados = [
            (self._tabela.set(item, coluna), item)
            for item in self._tabela.get_children("")
        ]
        dados.sort(reverse=False)
        for index, (_, item) in enumerate(dados):
            self._tabela.move(item, "", index)
