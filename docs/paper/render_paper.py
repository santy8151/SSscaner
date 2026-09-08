"""Render the editable Markdown technical paper using the bundled PDF runtime."""
from pathlib import Path
import re
from html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, KeepTogether, Flowable

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'output/pdf/SSScanner-BTMGPA-paper-v0.4.pdf'
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('Segoe','C:/Windows/Fonts/segoeui.ttf'))
pdfmetrics.registerFont(TTFont('SegoeBold','C:/Windows/Fonts/segoeuib.ttf'))
pdfmetrics.registerFontFamily('Segoe',normal='Segoe',bold='SegoeBold',italic='Segoe',boldItalic='SegoeBold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle('PaperTitle',fontName='SegoeBold',fontSize=21,leading=27,textColor=colors.HexColor('#124d40'),spaceAfter=14))
styles.add(ParagraphStyle('PaperH2',fontName='SegoeBold',fontSize=13,leading=18,textColor=colors.HexColor('#124d40'),spaceBefore=15,spaceAfter=7,keepWithNext=True))
styles.add(ParagraphStyle('PaperH3',fontName='SegoeBold',fontSize=10.7,leading=15,spaceBefore=10,spaceAfter=5,keepWithNext=True))
styles.add(ParagraphStyle('PaperBody',fontName='Segoe',fontSize=10,leading=14.8,alignment=TA_JUSTIFY,spaceAfter=8,allowWidows=0,allowOrphans=0))
styles.add(ParagraphStyle('PaperRef',parent=styles['PaperBody'],fontSize=8.4,leading=12,alignment=0,spaceAfter=8))
styles.add(ParagraphStyle('Caption',fontName='Segoe',fontSize=8.6,leading=12,textColor=colors.HexColor('#4f645d'),spaceAfter=10))

def markup(text):
    text=escape(text)
    text=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',text)
    return re.sub(r'(https://[^\s]+)',lambda m:f'<link href="{m.group(1)}" color="#16654c">{m.group(1)}</link>',text)

class Architecture(Flowable):
    def __init__(self):
        super().__init__()
        self.width=480
        self.height=134
    def draw(self):
        c=self.canv
        boxes=[('BASE DE SERVICIO','Adaptación descrita',0),('ADQUISICIÓN','Sensores y protocolo',162),('SOFTWARE','Evidencia y modelos',324)]
        for title,subtitle,x in boxes:
            c.setFillColor(colors.HexColor('#edf5f1'));c.setStrokeColor(colors.HexColor('#47826c'));c.roundRect(x,52,150,67,7,fill=1)
            c.setFillColor(colors.HexColor('#194d3a'));c.setFont('SegoeBold',9);c.drawCentredString(x+75,94,title)
            c.setFont('Segoe',8);c.drawCentredString(x+75,76,subtitle)
        for x in [151,313]:
            c.line(x,85,x+10,85);c.line(x+6,88,x+10,85);c.line(x+6,82,x+10,85)
        c.setFont('Segoe',8.5);c.setFillColor(colors.HexColor('#4f645d'))
        c.drawString(0,31,'Salva memorias: alimentación auxiliar. Adaptador de datos: comunicación independiente.')
        c.drawString(0,14,'Tres paneles: presión / frecuencia / visión. Sin órdenes a actuadores en esta beta.')

def page(canvas,doc):
    w,h=A4
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#c9d9d1'));canvas.line(48,h-37,w-48,h-37)
    canvas.setFillColor(colors.HexColor('#406052'));canvas.setFont('Segoe',8)
    canvas.drawString(48,h-28,'SSSCANNER  /  BTMGPA  /  DOCUMENTO TÉCNICO DE TRABAJO')
    canvas.line(48,38,w-48,38);canvas.drawString(48,25,'v0.4 · 08/09/2026 · No revisado por pares · Validación de campo pendiente')
    canvas.drawRightString(w-48,25,str(doc.page));canvas.restoreState()

text=(Path(__file__).parent/'BTMGPA-paper.md').read_text(encoding='utf-8')
story=[];references=False
for block in text.split('\n\n'):
    block=block.strip()
    if not block:continue
    if block.startswith('# '):style='PaperTitle';block=block[2:]
    elif block.startswith('## '):style='PaperH2';block=block[3:];references=block=='Referencias'
    elif block.startswith('### '):style='PaperH3';block=block[4:]
    else:style='PaperRef' if references else 'PaperBody'
    if block=='Referencias':story.append(PageBreak())
    story.append(Paragraph(markup(block),styles[style]))
    if block=='2. Arquitectura y adaptación del hardware':
        story.append(KeepTogether([Architecture(),Paragraph('Figura 1. Arquitectura funcional propuesta. La figura no es un esquema de conexión física ni documenta un equipo comercial concreto.',styles['Caption'])]))

SimpleDocTemplate(str(OUTPUT),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=53,bottomMargin=53,title='BTMGPA: arquitectura modular para diagnóstico térmico y eléctrico',author='Proyecto Ssscaner · autoría formal pendiente',subject='Documento técnico de trabajo, sin resultados de campo').build(story,onFirstPage=page,onLaterPages=page)
print(OUTPUT)
