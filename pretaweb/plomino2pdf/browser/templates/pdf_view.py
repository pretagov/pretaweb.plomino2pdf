from DateTime import DateTime
from zope.interface import implementer
from plone.memoize import view
from Products.Five import BrowserView
from pretaweb.plomino2pdf import api as pdf_api
from zope.publisher.interfaces import IPublishTraverse

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
        content_url = '%s?%s' %('/'.join(self.request.URL.split('/')[:-1]),self.request["QUERY_STRING"])
        pdfcontent = pdf_api.generate_pdf(content_url,self.context)
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
        self.request.response.setHeader("Content-Length", len(pdfcontent.getvalue()))
        self.request.response.setHeader('Last-Modified', DateTime.rfc822(DateTime()))
        self.request.response.setHeader("Cache-Control", "no-store")
        self.request.response.setHeader("Pragma", "no-cache")
        self.request.response.write(pdfcontent.getvalue())
        return pdfcontent
