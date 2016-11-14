from AccessControl import ModuleSecurityInfo
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('pretaweb.plomino2pdf')


def initialize(context):
    """Initializer called when used as a Zope 2 product."""

ModuleSecurityInfo('pretaweb.plomino2pdf.api').declarePublic('generate_pdf')
