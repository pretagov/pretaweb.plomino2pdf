from Acquisition import aq_parent
from DateTime import DateTime
from StringIO import StringIO
from urllib import unquote

from zope.component import getAdapters
from ZPublisher.HTTPResponse import HTTPResponse

from plone.memoize import view
from plone.subrequest import subrequest
from plone.transformchain.interfaces import ITransform
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from lxml import etree
from xhtml2pdf.document import pisaDocument

def sort_key(a, b):
    return cmp(a.order, b.order)

class PdfView(BrowserView):

    def __call__(self):
        return self.print_to_pdf()

    def print_to_pdf(self):
        pdf = StringIO()
        charset = self.context.portal_properties.site_properties.default_charset

        def fetch_resources(uri, rel):
            """
            Callback to allow pisa/reportlab to retrieve Images,Stylesheets, etc.
            `uri` is the href attribute from the html link element.
            `rel` gives a relative path, but it's not used here.
            """
            urltool = getToolByName(self.context, "portal_url")
            portal = urltool.getPortalObject()
            base = portal.absolute_url()
            if uri.startswith(base):
                response = subrequest(unquote(uri[len(base)+1:]))
                if response.status != 200:
                    return None
                try:
                    # stupid pisa doesn't let me send charset.
                    ctype,encoding = response.getHeader('content-type').split('charset=')
                    ctype = ctype.split(';')[0]
                    # pisa only likes ascii css
                    data = response.getBody().decode(encoding).encode('ascii',errors='ignore')
                except ValueError:
                    ctype = response.getHeader('content-type').split(';')[0]
                    data = response.getBody()
                data = data.encode("base64").replace("\n", "")
                data_uri = 'data:{0};base64,{1}'.format(ctype, data)
                return data_uri
            return uri

        published = self.request.get('PUBLISHED', None)
        handlers = [v[1] for v in getAdapters((published, self.request,), ITransform)]
        handlers.sort(sort_key)

        # The first handler is the diazo transform, the other 4 handlers are caching
        theme_handler = handlers[0]
        html = self.context.OpenDocument()
        new_html = theme_handler.transformIterable([html], charset)
        # If the theme is not enabled, transform returns None
        if new_html is not None:
            new_html = etree.tostring(new_html.tree)
        else:
            new_html = html
        pisadoc = pisaDocument(new_html, pdf, raise_exception=True, link_callback=fetch_resources)
        # pisadoc = pisaDocument(html, pdf, raise_exception=True)
        assert pdf.len != 0, 'Pisa PDF generation returned empty PDF!'
        #html.close()
        pdfcontent = pdf.getvalue()
        pdf.close()

        now = DateTime()
        # TODO: We need to get a proper filename from somewhere
        filename = 'certificate'
        nice_filename = '%s_%s' % (filename, now.strftime('%Y%m%d'))

        self.request.response.setHeader("Content-Disposition",
                                        "attachment; filename=%s.pdf" %
                                        nice_filename)
        self.request.response.setHeader("Content-Type", "application/pdf")
        self.request.response.setHeader("Content-Length", len(pdfcontent))
        self.request.response.setHeader('Last-Modified', DateTime.rfc822(DateTime()))
        self.request.response.setHeader("Cache-Control", "no-store")
        self.request.response.setHeader("Pragma", "no-cache")
        self.request.response.write(pdfcontent)
        return pdfcontent
