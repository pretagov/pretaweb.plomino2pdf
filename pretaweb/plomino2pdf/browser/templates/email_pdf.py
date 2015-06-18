from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from plone import api
from plone.directives import form
from plone.supermodel import model
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from pretaweb.plomino2pdf import _
from zope import schema
from z3c.form import field, button

class IEmailPdf(model.Schema):
    email = schema.TextLine(
        title = _(u'Email Address')
    )

class EmailPdf(form.SchemaForm):

    schema = IEmailPdf
    ignoreContext=True
    template = ViewPageTemplateFile('email_pdf.pt')

    def update(self):
        self.sent=False
        if self.request.get('sent') and self.request.get('sent') == 'true':
            self.sent=True
        super(EmailPdf, self).update()

    @button.buttonAndHandler(_(u'Email PDF'),name='email_pdf')
    def email_pdf(self,action):
        data,errors = self.extractData()
        if not errors:
            self.sendPDF(data['email'])
            api.portal.show_message(
                'PDF has been emailed to: %s' % data['email'],
                request=self.request
            )
            self.request.response.redirect('%s/email_pdf?sent=true' \
                % self.context.absolute_url())
        else:
            self.status = self.formErrorsMessage

    def attach_pdf_from_context(self):
        pdf_api = self.context.restrictedTraverse('plomino_pdf_api')
        pdf_mime = MIMEApplication(pdf_api.generate_pdf())
        pdf_mime.add_header(
            'Content-Disposition','attachment',
            filename='plomino.pdf'
        )
        return pdf_mime

    def sendPDF(self,recipient):
        message = MIMEMultipart()
        message['Subject'] = 'Plomino PDF'
        message['From'] = 'support@pretagov.co.uk'
        message['To'] = recipient
        message_content = MIMEText('Your PDF is attached.\n\n')
        message.attach(message_content)
        message.attach(self.attach_pdf_from_context())
        mh = api.portal.get_tool('MailHost')
        return mh.send(message, immediate=True)
