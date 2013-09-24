from Acquisition import aq_parent
from DateTime import DateTime
from StringIO import StringIO
from urllib import unquote
import urlparse

from zope.component import getAdapters
from zope.interface import implements
from zope.interface import implementer
from ZPublisher.HTTPResponse import HTTPResponse

from plone.memoize import view
from plone.subrequest import subrequest
from plone.transformchain.interfaces import ITransform
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from lxml import etree
from xhtml2pdf.document import pisaDocument
from zope.publisher.interfaces import IPublishTraverse
from zope.contenttype import guess_content_type, text_type

def sort_key(a, b):
    return cmp(a.order, b.order)

@implementer(IPublishTraverse)
class PdfView(BrowserView):

    filename = None

    def __init__(self, context, request):
        """ Once we get to __call__, the path is lost so we
        capture it here on initialization
        """
        super(PdfView, self).__init__(context, request)
        #self.filename = request.path[-1]
        # subpath seems to screw up pisa
        self.filename = self.request.get('filename', None)

    def __call__(self):
        return self.print_to_pdf()

    def publishTraverse(self, request, name):

        self.traverse_subpath = self.request['TraversalRequestNameStack'] + [name]
        self.request['TraversalRequestNameStack'] = []
        return self

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
            uri = urlparse.urljoin(rel, uri)
            if uri.startswith(base):
                uri = uri[len(base)+1:]
            response = subrequest(unquote(uri))
            if response.status == 301:
                new_uri = response.headers['location']
                response = subrequest(unquote(new_uri))
            if response.status != 200:
                return None

            content_type = response.getHeader('content-type')
            if content_type:
                try:
                    # stupid pisa doesn't let me send charset.
                    ctype, encoding = response.getHeader('content-type').split('charset=')
                    ctype = ctype.split(';')[0]
                except ValueError:
                    ctype = response.getHeader('content-type').split(';')[0]
                    encoding = 'utf8'
            else:
                # content-type in headers could be empty,
                # we need to use guess_content_type and text_type
                # to guess the content-type
                ctype, encoding = guess_content_type(uri)
                if ctype and ctype.startswith('text/'):
                    ctype = text_type(uri)

            if ctype == 'text/css':
                # pisa only likes ascii css
                # in order to backward compatible old version, don't put keywords
                # encode in version 2.7: Support for keyword arguments added
                data = response.getBody().decode(encoding).encode('ascii', 'ignore')
            else:
                data = response.getBody()
            data = data.encode("base64").replace("\n", "")
            data_uri = 'data:{0};base64,{1}'.format(ctype, data)
            return data_uri

        meta_type = self.context.meta_type
        if meta_type == 'PlominoView':
            html = self.context.checkBeforeOpenView()
        elif meta_type == 'PlominoDocument':
            html = self.context.checkBeforeOpenDocument()
        elif meta_type == 'PlominoForm':
            html = self.context.OpenForm(searchresults=[])
        else:
            html = getattr(self.context, self.context.default_view)()
        new_html = None
        published = self.request.get('PUBLISHED', None)
        handlers = [v[1] for v in getAdapters((published, self.request,), ITransform)]
        handlers.sort(sort_key)
        if handlers:
            # The first handler is the diazo transform, the other 4 handlers are caching
            theme_handler = handlers[0]
            new_html = theme_handler.transformIterable([html], charset)
        # If the theme is not enabled, transform returns None
        if new_html is not None:
            new_html = etree.tostring(new_html.tree)
        else:
            new_html = html
        pisadoc = pisaDocument(new_html, pdf, path=self.context.absolute_url(),
                               raise_exception=True, link_callback=fetch_resources)
        # pisadoc = pisaDocument(html, pdf, raise_exception=True)
        assert pdf.len != 0, 'Pisa PDF generation returned empty PDF!'
        #html.close()
        pdfcontent = pdf.getvalue()
        pdf.close()

        now = DateTime()
        # TODO: We need to get a proper filename from somewhere
        if not self.filename:
            filename = 'printed'
            nice_filename = '%s_%s.pdf' % (filename, now.strftime('%Y%m%d'))
        else:
            nice_filename = self.filename
            if nice_filename[-4:] != '.pdf':
                nice_filename += '.pdf'

        self.request.response.setHeader("Content-Disposition",
                                        "attachment; filename=%s" %
                                        nice_filename)
        self.request.response.setHeader("Content-Type", "application/pdf")
        self.request.response.setHeader("Content-Length", len(pdfcontent))
        self.request.response.setHeader('Last-Modified', DateTime.rfc822(DateTime()))
        self.request.response.setHeader("Cache-Control", "no-store")
        self.request.response.setHeader("Pragma", "no-cache")
        self.request.response.write(pdfcontent)
        return pdfcontent
