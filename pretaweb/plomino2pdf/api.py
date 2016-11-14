from lxml import etree
from plone import api
from plone.subrequest import subrequest
from plone.transformchain.interfaces import ITransform
from StringIO import StringIO
from urllib import unquote
#from xhtml2pdf.document import pisaDocument
from zope.component import getAdapters
from zope.contenttype import guess_content_type, text_type
import re
import urlparse
import logging

logger = logging.getLogger('pretaweb.plomino2pdf.api')

from weasyprint import default_url_fetcher
from weasyprint import HTML


def sort_key(a, b):
    return cmp(a.order, b.order)


def my_fetcher(url):
    # Ignore certain resources
    if 'googleapis' in url:
        raise Exception('Not loading Google resources')

    if '++plone++production' in url:
        raise Exception('Not loading bundle resources')

    # Use the default URL fetcher for CSS files
    if url.endswith('.css'):
        return default_url_fetcher(url)

    uri = url
    # Otherwise fetch the data
    response = subrequest(unquote(uri))

    if response.status == 301:
        uri = response.headers['location']
        response = subrequest(unquote(uri))

    if response.status != 200:
        raise Exception("URI not found")

    content_type = response.getHeader('content-type')
    if not content_type:
        content_type = guess_content_type(uri)[0]
        if content_type and content_type.startswith('text/'):
            content_type = text_type(uri)

    data = response.getBody()
    return dict(string=data)
    # data = data.replace("\n", "")
    # if 'PDF-EXCLUDE' in data:
    #     return 'data:text/css;base64,'
    # data = data.encode('base64')
    # data_uri = 'data:{0};base64,{1}'.format(content_type, data)
    # return dict(string=data_uri)


def generate_pdf(url, context):
    """ Builds a PDF of the passed in url """
    request = getattr(context, "REQUEST", None)
    base_url = context.getParentDatabase().absolute_url()

    # Use subrequest to access the passed in url
    page = subrequest(url, root=context)

    # Transform the html
    # Have to set the content-type header to text/html before we can transform
    actual_header = request.response.getHeader('Content-Type')
    request.response.setHeader('Content-Type', 'text/html')
    html = transform_html(page.getBody(), request)
    request.response.setHeader('Content-Type', actual_header)

    pdf = HTML(string=html, base_url=base_url, url_fetcher=my_fetcher)

    output = StringIO()
    pdf.write_pdf(output)
    output.seek(0)
    return output


def transform_html(html, request):
    portal = api.portal.get()
    charset = portal.portal_properties.site_properties.getProperty(
        'default_charset', 'utf-8')
    new_html = None
    published = request.get('PUBLISHED', None)
    handlers = [v[1] for v in getAdapters((published, request,), ITransform)]
    handlers.sort(sort_key)
    if handlers:
        # The first handler is the diazo transform, the others are caching
        theme_handler = handlers[0]
        new_html = theme_handler.transformIterable([html], charset)
    # If the theme is not enabled, transform returns None
    if new_html is not None:
        new_html = etree.tostring(new_html.tree)
    else:
        new_html = html
    return new_html
