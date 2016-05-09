import cStringIO as StringIO
from django.template.loader import get_template
from xhtml2pdf import pisa


def render_to_pdf(template_path, context):
    template = get_template(template_path)
    html = template.render({'data': context})
    pdf_result = StringIO.StringIO()
    pisa.pisaDocument(StringIO.StringIO(html.encode("ISO-8859-1")), pdf_result)
    return pdf_result
