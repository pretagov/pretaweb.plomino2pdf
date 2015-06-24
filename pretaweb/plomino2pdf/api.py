from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from lxml import etree
from plone import api
from plone.memoize import view
from plone.subrequest import subrequest
from plone.transformchain.interfaces import ITransform
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from StringIO import StringIO
from urllib import unquote
from xhtml2pdf.document import pisaDocument
from zope.component import getAdapters
from zope.contenttype import guess_content_type, text_type
import urlparse
import logging
logger=logging.getLogger('preteweb.plomino2pdf.api')

def sort_key(a, b):
    return cmp(a.order, b.order)

def email_form_as_pdf(form,recipient,subject=None,content=None):
    """ Builds a PDF of the submitted form and emails it to the recipient """
    # Get the html with values
    portal = api.portal.get()
    request = getattr(form,"REQUEST",None)

    # Use the custom view DisplayForm to render the form from the request
    displayform = subrequest('./DisplayForm')

    # Transform the html
    html=transform_html(displayform.getBody(),request)

    # Generate the pdf
    pdf = generate_pdf(html,form.absolute_url(),request)
    pdf_name=form.getId()

    # Create an email
    message = MIMEMultipart()
    if subject is None:
        subject='%s PDF Attached' % form.title
    message['Subject'] = subject
    message['From'] = '%s <%s>' % (portal.getProperty('email_from_name'),
                                   portal.getProperty('email_from_address'))
    message['To'] = recipient
    if content is None:
        content = 'Attached PDF %s.pdf' % pdf_name
    message_content = MIMEText('%s\n' % content)
    message.attach(message_content)

    # Attach the pdf
    pdf_mime = MIMEApplication(pdf)
    pdf_mime.add_header(
        'Content-Disposition','attachment',
        filename='%s.pdf' % pdf_name
    )
    message.attach(pdf_mime)

    # Send the email
    send_mime_message(message)

def send_mime_message(message):
    mh = api.portal.get_tool('MailHost')
    return mh.send(message, immediate=True)

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

def generate_pdf(html,path,request):

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
        data = data.encode("base64").replace("\n", "")
        data_uri = 'data:{0};base64,{1}'.format(ctype, data)
        return data_uri

    pdf = StringIO()

    pisadoc = pisaDocument(html,pdf, path=path,
                           raise_exception=True, link_callback=fetch_resources)
    # pisadoc = pisaDocument(html, pdf, raise_exception=True)
    assert pdf.len != 0, 'Pisa PDF generation returned empty PDF!'

    pdf_content = pdf.getvalue()
    pdf.close()
    return  pdf_content
