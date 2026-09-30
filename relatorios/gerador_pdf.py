"""
relatorios/gerador_pdf.py
=========================
Geração de relatórios PDF dos casos jurídicos.
"""

import os
from datetime import datetime
from fpdf import FPDF
from config import RELATORIOS_DIR

# ── Paleta de cores (RGB) ─────────────────────────────────────────────────────
COR_CABECALHO = (26, 60, 94)     # #1a3c5e  azul marinho (site)
COR_SECAO     = (26, 60, 94)     # #1a3c5e  mesmo azul marinho do site
COR_FUNDO_ALT = (232, 240, 248)  # azul claro suave
COR_TEXTO     = (26, 60, 94)     # azul marinho em vez de preto
COR_LABEL     = (100, 130, 160)  # azul acinzentado para labels
COR_BRANCO    = (255, 255, 255)

COR_PRIORIDADE = {
    'Prioridade 1': (231, 76, 60),   # vermelho
    'Prioridade 2': (230, 126, 34),  # laranja
    'Prioridade 3': (39, 174, 96),   # verde
}


# ── Classe PDF ────────────────────────────────────────────────────────────────

class PDFCaso(FPDF):

    def header(self):
        self.set_fill_color(*COR_CABECALHO)
        self.rect(0, 0, 210, 28, 'F')

        self.set_text_color(*COR_BRANCO)
        self.set_font('Helvetica', 'B', 15)
        self.set_xy(10, 7)
        self.cell(0, 7, 'ACESSUS Direito Popular', ln=True)

        self.set_font('Helvetica', '', 9)
        self.set_xy(10, 16)
        self.cell(0, 5, 'Sistema de Orientação Jurídica Popular', ln=True)

        self.set_y(36)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(*COR_LABEL)
        self.cell(
            0, 5,
            f'Uso interno  |  Não constitui assessoria jurídica  |  Página {self.page_no()}',
            align='C'
        )


# ── Funções auxiliares ────────────────────────────────────────────────────────

def _safe(s):
    """Remove caracteres fora do Latin-1 (ex: emojis, bullet •) para compatibilidade com Helvetica."""
    return str(s or '').encode('latin-1', errors='replace').decode('latin-1')


def _titulo_secao(pdf, texto):
    pdf.set_fill_color(*COR_SECAO)
    pdf.set_text_color(*COR_BRANCO)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 7, '  ' + _safe(texto), ln=True, fill=True)
    pdf.set_text_color(*COR_TEXTO)
    pdf.ln(2)


def _campo(pdf, label, valor, fundo=False):
    valor = _safe(valor).strip()
    if not valor or valor in ('None', '-'):
        return
    pdf.set_fill_color(*(COR_FUNDO_ALT if fundo else COR_BRANCO))
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(*COR_LABEL)
    pdf.cell(0, 5, _safe(label), ln=True, fill=True)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*COR_TEXTO)
    pdf.multi_cell(0, 6, valor, fill=True)
    pdf.ln(1)


def _formatar_data(data_cadastro):
    if not data_cadastro:
        return '—'
    try:
        dt = datetime.fromisoformat(str(data_cadastro)[:19])
        return dt.strftime('%d/%m/%Y  %H:%M')
    except Exception:
        return str(data_cadastro)[:16]


def _formatar_relato(relato):
    """
    Relatos do WhatsApp têm formato 'CAMPO: valor' gerado pelo questionário.
    Relatos da interface desktop são texto livre.
    Retorna lista de (label, valor) para renderizar no PDF.
    """
    if not relato:
        return [('Relato', '')]
    relato = relato.strip()
    if 'RELATO:' not in relato:
        return [('Relato', relato)]

    items = []
    for linha in relato.split('\n'):
        linha = linha.strip()
        if not linha or linha == '---':
            continue
        if ':' in linha:
            chave, _, valor = linha.partition(':')
            label = chave.strip().title().replace('_', ' ')
            items.append((label, valor.strip()))
    return items if items else [('Relato', relato)]


# ── Função principal ──────────────────────────────────────────────────────────

def gerar_pdf_caso(dados):
    """
    Gera o PDF de um caso e retorna o caminho do arquivo.

    dados: tuple retornada por buscar_caso_por_id —
           (id, nome_cliente, email, whatsapp, relato,
            tipo_caso, prioridade, anexos, data_cadastro)
    """
    (id_caso, nome, email, whatsapp,
     relato, tipo_caso, prioridade, anexos, data_cadastro) = dados

    pdf = PDFCaso()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Identificação do caso ─────────────────────────────────────────────
    _titulo_secao(pdf, 'IDENTIFICAÇÃO DO CASO')

    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(*COR_LABEL)
    pdf.cell(60, 5, 'Protocolo')
    pdf.cell(70, 5, 'Data de Cadastro')
    pdf.cell(0,  5, 'Prioridade', ln=True)

    r, g, b = COR_PRIORIDADE.get(str(prioridade), COR_TEXTO)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(*COR_CABECALHO)
    pdf.cell(60, 7, _safe(id_caso))

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(*COR_TEXTO)
    pdf.cell(70, 7, _safe(_formatar_data(data_cadastro)))

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 7, _safe(prioridade or '-'), ln=True)

    pdf.ln(2)
    _campo(pdf, 'Área Jurídica', tipo_caso, fundo=True)
    pdf.ln(3)

    # ── Dados do solicitante ──────────────────────────────────────────────
    _titulo_secao(pdf, 'DADOS DO SOLICITANTE')
    _campo(pdf, 'Nome',     nome,     fundo=False)
    _campo(pdf, 'E-mail',   email,    fundo=True)
    _campo(pdf, 'WhatsApp', whatsapp, fundo=False)
    pdf.ln(3)

    # ── Relato / Questionário ─────────────────────────────────────────────
    _titulo_secao(pdf, 'RELATO E INFORMAÇÕES DO CASO')
    for i, (label, valor) in enumerate(_formatar_relato(relato)):
        _campo(pdf, label, valor, fundo=(i % 2 == 1))
    pdf.ln(3)

    # ── Anexos ────────────────────────────────────────────────────────────
    if anexos and str(anexos).strip() not in ('', 'None'):
        _titulo_secao(pdf, 'ANEXOS')
        for path in str(anexos).split(','):
            path = path.strip()
            if path:
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(*COR_TEXTO)
                pdf.cell(0, 6, '  - ' + _safe(os.path.basename(path)), ln=True)
        pdf.ln(3)

    # ── Aviso legal ───────────────────────────────────────────────────────
    pdf.set_fill_color(*COR_FUNDO_ALT)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(*COR_LABEL)
    pdf.multi_cell(
        0, 5,
        'AVISO: Este relatório contém informações jurídicas de caráter geral com base '
        'na legislação brasileira. Não constitui assessoria jurídica, não substitui '
        'advogado e não deve ser utilizado como documento ou prova em qualquer processo.',
        fill=True
    )

    # ── Salva o arquivo ───────────────────────────────────────────────────
    os.makedirs(RELATORIOS_DIR, exist_ok=True)
    nome_arq = f"caso_{id_caso}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    caminho = os.path.join(RELATORIOS_DIR, nome_arq)
    pdf.output(caminho)
    return caminho
