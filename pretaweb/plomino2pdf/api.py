from lxml import etree
from plone import api
from plone.subrequest import subrequest
from plone.transformchain.interfaces import ITransform
from StringIO import StringIO
from urllib import unquote
from xhtml2pdf.document import pisaDocument
from zope.component import getAdapters
from zope.contenttype import guess_content_type, text_type
import re
import urlparse
import logging
logger=logging.getLogger('pretaweb.plomino2pdf.api')

def sort_key(a, b):
    return cmp(a.order, b.order)

def generate_pdf(url,context):
    """ Builds a PDF of the passed in url """
    # Get the html with values
    portal = api.portal.get()
    request = getattr(context,"REQUEST",None)

    # Use subrequest to access the passed in url
    page = subrequest(url,root=context)

    # Transform the html
    html = transform_html(page.getBody(),request)

    # Generate the pdf
    pdf = build_pdf(html,context.absolute_url(),request)

    # Return the generated pdf
    return pdf

def transform_html(html,request):
    portal = api.portal.get()
    charset = portal.portal_properties.site_properties.default_charset
    new_html = None
    published = request.get('PUBLISHED', None)
    handlers = [v[1] for v in getAdapters((published, request,), ITransform)]
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
    return new_html

def build_pdf(html,path,request):

    def fetch_resources(uri, rel):
        """
        Callback to allow pisa/reportlab to retrieve Images,Stylesheets, etc.
        `uri` is the href attribute from the html link element.
        `rel` gives a relative path, but it's not used here.
        """
        urltool = api.portal.get_tool("portal_url")
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
        data = data.replace("\n","")
        fontre = re.compile('.*format\(\'woff\'\).*')
        if fontre.match(data):
            return 'data:text/css;base64,'
        data = data.encode("base64")
        data_uri = 'data:{0};base64,{1}'.format(ctype, data)
        return data_uri

    pdf = StringIO()

    pisadoc = pisaDocument(html,pdf, path=path,
                           raise_exception=True, link_callback=fetch_resources)

    assert pdf.len != 0, 'Pisa PDF generation returned empty PDF!'

    pdf_content = pdf.getvalue()
    pdf.close()
    return  pdf_content
