from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
import re

# Configurações globais
styles = getSampleStyleSheet()
MARGEM = 1.8*cm
COR_PRIMARIA = "#2B3A4B"
COR_SECUNDARIA = "#4A6FA5"
COR_TEXTO = "#333333"

# ================= ESTILOS =================
estilo_nome = ParagraphStyle(
    name='Nome',
    parent=styles['Heading1'],
    fontSize=24,
    leading=28,
    alignment=TA_CENTER,
    spaceAfter=0.4*cm,
    fontName="Helvetica-Bold",
    textColor=colors.HexColor(COR_PRIMARIA)
)

estilo_contato = ParagraphStyle(
    name='Contato',
    parent=styles['Normal'],
    fontSize=9.5,
    leading=12,
    alignment=TA_CENTER,
    spaceAfter=0.6*cm,
    textColor=colors.HexColor("#555555")
)

estilo_titulo_secao = ParagraphStyle(
    name='TituloSecao',
    parent=styles['Heading2'],
    fontSize=12,
    leading=14,
    spaceBefore=0.7*cm,
    spaceAfter=0.3*cm,
    fontName="Helvetica-Bold",
    textColor=colors.white,
    backColor=colors.HexColor(COR_SECUNDARIA),
    borderPadding=(0.2*cm, 0.3*cm),
    alignment=TA_LEFT
)

estilo_item_lista = ParagraphStyle(
    name='ItemLista',
    parent=styles['Normal'],
    fontSize=10.5,
    leading=14,
    leftIndent=0.4*cm,
    bulletIndent=0.2*cm,
    spaceBefore=0.1*cm,
    spaceAfter=0.1*cm,
    bulletFontName="Helvetica-Bold",
    bulletFontSize=12,
    bulletColor=colors.HexColor(COR_SECUNDARIA),
    textColor=colors.HexColor(COR_TEXTO)
)

estilo_subtitulo = ParagraphStyle(
    name='Subtitulo',
    parent=styles['Normal'],
    fontSize=11,
    leading=13,
    spaceAfter=0.1*cm,
    fontName="Helvetica-Bold",
    textColor=colors.HexColor(COR_PRIMARIA)
)

estilo_detalhe = ParagraphStyle(
    name='Detalhe',
    parent=styles['Normal'],
    fontSize=10,
    leading=12,
    textColor=colors.HexColor("#666666"),
    spaceAfter=0.4*cm
)

divisor_secao = HRFlowable(
    width="100%",
    color=colors.HexColor("#E0E0E0"),
    thickness=0.8,
    spaceBefore=0.4*cm,
    spaceAfter=0.4*cm
)

# ================= FUNÇÕES AUXILIARES =================
def criar_tabela_contato(dados):
    return Table([dados],
               colWidths=[None]*len(dados),
               style=TableStyle([
                   ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                   ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                   ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#555555")),
                   ('FONTSIZE', (0,0), (-1,-1), 9.5),
                   ('LEADING', (0,0), (-1,-1), 11),
                   ('BOTTOMPADDING', (0,0), (-1,-1), 2)
               ]))

def processar_linha(linha, elementos, contexto):
    linha = linha.strip()
    if not linha:
        return contexto

    # Detecção de título de seção
    if re.match(r"^[A-Z][A-Z\s]+:$", linha):
        if elementos:
            elementos.append(Spacer(1, 0.3*cm))
        titulo = linha[:-1].strip()
        elementos.append(Paragraph(titulo, estilo_titulo_secao))
        return 'secao'

    # Detecção de subtítulo (cargo/formação)
    if contexto == 'secao' and '•' not in linha:
        elementos.append(Paragraph(linha, estilo_subtitulo))
        return 'subtitulo'

    # Detecção de detalhes (empresa/datas)
    if contexto in ['subtitulo', 'detalhe'] and '|' in linha:
        elementos.append(Paragraph(linha, estilo_detalhe))
        return 'detalhe'

    # Detecção de itens com bullet points
    if linha.startswith(('•', '-', '*')):
        texto = linha[1:].strip()
        elementos.append(Paragraph(texto, estilo_item_lista, bulletText='•'))
        return 'item'

    # Texto normal
    elementos.append(Paragraph(linha, estilo_detalhe))
    return 'texto'

# ================= FUNÇÃO PRINCIPAL =================
def criar_pdf_ats_formatado(texto_cv: str, nome_candidato: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGEM,
        leftMargin=MARGEM,
        topMargin=1.2*cm,
        bottomMargin=MARGEM,
        title=f"CV - {nome_candidato}",
        author="Gerador de CV ATS"
    )

    elementos = []
    linhas = texto_cv.split('\n')

    # Processar cabeçalho
    elementos.append(Paragraph(nome_candidato.upper(), estilo_nome))

    # Coletar informações de contato
    contatos = []
    for linha in linhas[1:]:
        if linha.strip() and not re.match(r"^[A-Z][A-Z\s]+:$", linha.strip()):
            contatos.append(linha.strip())
        else:
            break

    if contatos:
        elementos.append(criar_tabela_contato(contatos))
        elementos.append(divisor_secao)

    # Processar conteúdo principal
    contexto = 'inicio'
    for linha in linhas[len(contatos)+1:]:
        contexto = processar_linha(linha, elementos, contexto)

    try:
        doc.build(elementos)
    except Exception as e:
        raise RuntimeError(f"Erro na geração do PDF: {str(e)}")

    buffer.seek(0)
    return buffer
