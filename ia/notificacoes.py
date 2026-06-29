import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, HtmlContent

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
EMAIL_REMETENTE  = os.environ.get('EMAIL_REMETENTE', '')
ADVOGADO_EMAIL   = os.environ.get('ADVOGADO_EMAIL', '')
PAINEL_URL       = os.environ.get('PAINEL_URL', 'https://agente-triagem-juridica.onrender.com/advogados')


def _montar_html(protocolo, area, prioridade, whatsapp_cliente, relato, urgente):
    campos_html = ''
    if relato:
        for linha in relato.split('\n'):
            linha = linha.strip()
            if not linha or linha == '---':
                continue
            if ':' in linha:
                chave, _, valor = linha.partition(':')
                chave = chave.strip().title().replace('_', ' ')
                valor = valor.strip()
                campos_html += (
                    f'<tr>'
                    f'<td style="padding:8px 12px;color:#666;font-size:14px;'
                    f'white-space:nowrap;width:180px;vertical-align:top;">{chave}</td>'
                    f'<td style="padding:8px 12px;font-size:14px;">{valor}</td>'
                    f'</tr>'
                )

    num = str(prioridade)
    cor_prio = '#dc3545' if '1' in num else ('#fd7e14' if '2' in num else '#28a745')

    alerta = (
        '<div style="background:#dc3545;color:white;padding:12px 16px;'
        'border-radius:6px;margin-bottom:20px;font-weight:bold;">'
        '⚠️ CASO URGENTE — Requer atenção imediata</div>'
    ) if urgente else ''

    link_caso = f'{PAINEL_URL}/caso/{protocolo}'

    return f"""
<div style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;">
  <div style="background:#1a3c5e;padding:20px 24px;border-radius:8px 8px 0 0;">
    <h1 style="color:white;margin:0;font-size:22px;">ACESSUS Direito Popular</h1>
    <p style="color:#a8c4e0;margin:4px 0 0;font-size:14px;">Sistema de Orientação Jurídica Popular</p>
  </div>
  <div style="background:#f8f9fa;padding:20px 24px;border:1px solid #dee2e6;
              border-top:none;border-radius:0 0 8px 8px;">
    {alerta}
    <h2 style="color:#1a3c5e;margin:0 0 16px;font-size:18px;">Novo caso encaminhado para você</h2>

    <table style="width:100%;border-collapse:collapse;background:white;
                  border-radius:6px;overflow:hidden;border:1px solid #dee2e6;margin-bottom:16px;">
      <tr style="background:#1a3c5e;color:white;">
        <td colspan="2" style="padding:10px 12px;font-size:14px;font-weight:bold;">Resumo do Caso</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;color:#666;font-size:14px;width:180px;">Protocolo</td>
        <td style="padding:8px 12px;font-size:14px;font-weight:bold;">{protocolo}</td>
      </tr>
      <tr style="background:#f8f9fa;">
        <td style="padding:8px 12px;color:#666;font-size:14px;">Área Jurídica</td>
        <td style="padding:8px 12px;font-size:14px;">{area}</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;color:#666;font-size:14px;">Prioridade</td>
        <td style="padding:8px 12px;font-size:14px;">
          <span style="background:{cor_prio};color:white;padding:2px 10px;
                       border-radius:20px;font-size:13px;">{prioridade}</span>
        </td>
      </tr>
      <tr style="background:#f8f9fa;">
        <td style="padding:8px 12px;color:#666;font-size:14px;">WhatsApp do cliente</td>
        <td style="padding:8px 12px;font-size:14px;">{whatsapp_cliente or 'Não informado'}</td>
      </tr>
    </table>

    <table style="width:100%;border-collapse:collapse;background:white;
                  border-radius:6px;overflow:hidden;border:1px solid #dee2e6;margin-bottom:20px;">
      <tr style="background:#1a3c5e;color:white;">
        <td colspan="2" style="padding:10px 12px;font-size:14px;font-weight:bold;">Informações do Caso</td>
      </tr>
      {campos_html}
    </table>

    <div style="text-align:center;margin:20px 0;">
      <a href="{link_caso}"
         style="background:#1a3c5e;color:white;padding:12px 28px;border-radius:6px;
                text-decoration:none;font-size:15px;font-weight:bold;display:inline-block;">
        Ver caso completo no painel
      </a>
    </div>

    <p style="color:#999;font-size:12px;text-align:center;margin-top:20px;
              border-top:1px solid #dee2e6;padding-top:12px;">
      ACESSUS Direito Popular — Sistema de Triagem Jurídica<br>
      E-mail gerado automaticamente. Não responda a esta mensagem.
    </p>
  </div>
</div>
"""


def enviar_email_advogado(protocolo, area, prioridade, whatsapp_cliente, relato,
                          urgente=False, email_destino=None):
    """Notifica o advogado por e-mail quando um caso é encaminhado. Retorna True se enviado."""
    destinatario = email_destino or ADVOGADO_EMAIL
    if not SENDGRID_API_KEY or not EMAIL_REMETENTE or not destinatario:
        logger.warning('[SendGrid] Variáveis não configuradas — e-mail ignorado.')
        return False

    prefixo = '[URGENTE] ' if urgente else ''
    assunto = f'{prefixo}Novo caso encaminhado — Protocolo {protocolo} | {area}'
    html    = _montar_html(protocolo, area, prioridade, whatsapp_cliente, relato, urgente)

    mensagem = Mail(
        from_email=EMAIL_REMETENTE,
        to_emails=destinatario,
        subject=assunto,
        html_content=HtmlContent(html)
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        resp = sg.send(mensagem)
        logger.info(f'[SendGrid] Enviado para {destinatario} — HTTP {resp.status_code}')
        return True
    except Exception as e:
        logger.error(f'[SendGrid] Falha ao enviar: {e}')
        return False
