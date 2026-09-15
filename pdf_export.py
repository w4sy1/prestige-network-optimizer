"""Local PDF export, with embedded Unicode font and wrapped diagnostic fields."""
from pathlib import Path
import json
import sys
from xml.sax.saxutils import escape


def export_pdf(data,destination,title='Raport diagnostyczny'):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
    except ImportError:
        raise RuntimeError('Eksport PDF wymaga reportlab. Zainstaluj requirements-gui.txt lub użyj wydania EXE.') from None
    root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
    font=root/'assets/DejaVuSans.ttf'
    if not font.exists():raise FileNotFoundError('Brak fontu assets/DejaVuSans.ttf.')
    if 'PrestigeUnicode' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('PrestigeUnicode',str(font)))
    path=Path(destination)
    if path.exists():raise FileExistsError('Docelowy PDF już istnieje. Wybierz nową nazwę.')
    path.parent.mkdir(parents=True,exist_ok=True)
    text=ParagraphStyle('body',fontName='PrestigeUnicode',fontSize=9,leading=14,spaceAfter=8,wordWrap='CJK')
    label=ParagraphStyle('label',parent=text,textColor=colors.HexColor('#137766'),fontSize=10,spaceBefore=8,spaceAfter=3,keepWithNext=True)
    heading=ParagraphStyle('title',parent=text,fontSize=22,leading=28,textColor=colors.HexColor('#122b43'),spaceAfter=15)
    story=[Paragraph('PRESTIGE TECH',heading),Paragraph('by Dominik Wasilak',text),Spacer(1,12),Paragraph(escape(title),heading)]
    def add(value,key='',depth=0):
        if depth>20:raise ValueError('Zbyt głęboki raport.')
        if key:story.append(Paragraph(escape(str(key).replace('_',' ')),label))
        if isinstance(value,dict):
            if not value:story.append(Paragraph('Brak danych',text))
            for name,item in value.items():add(item,name,depth+1)
        elif isinstance(value,list):
            if not value:story.append(Paragraph('Brak pozycji',text))
            for index,item in enumerate(value):add(item,'Pozycja '+str(index+1),depth+1)
        else:
            content='Nieustalone' if value is None else str(value)
            # Small paragraphs allow long log lines to break across pages without an oversized cell.
            for start in range(0,max(1,len(content)),4000):
                story.append(Paragraph(escape(content[start:start+4000]).replace('\n','<br/>') or ' ',text))
    add(data)
    def page(canvas,document):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#2ac7a0'));canvas.line(40,42,A4[0]-40,42)
        canvas.setFont('PrestigeUnicode',8);canvas.setFillColor(colors.HexColor('#546477'))
        canvas.drawString(40,28,'Prestige Tech • Raport lokalny');canvas.drawRightString(A4[0]-40,28,str(document.page));canvas.restoreState()
    document=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=42,bottomMargin=56,title=title,author='Dominik Wasilak - Prestige Tech')
    try:document.build(story,onFirstPage=page,onLaterPages=page)
    except Exception:
        path.unlink(missing_ok=True);raise
    return str(path)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Lokalny eksport JSON do PDF')
    parser.add_argument('--input',required=True);parser.add_argument('--pdf',required=True)
    args=parser.parse_args();print(export_pdf(json.loads(Path(args.input).read_text(encoding='utf-8-sig')),args.pdf))
