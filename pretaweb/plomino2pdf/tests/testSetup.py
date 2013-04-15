import time
import unittest2 as unittest
from zExceptions import BadRequest

from zope.component import getSiteManager
from zope.component import getUtility

from plone.browserlayer.utils import registered_layers

from Products.CMFCore.utils import getToolByName

from base import PROJECTNAME
from base import INTEGRATION_TESTING

class TestInstallation(unittest.TestCase):
    """Ensure product is properly installed"""
    layer = INTEGRATION_TESTING
    
    def setUp(self):
        self.portal = self.layer['portal']
    
    def testBrowserLayerRegistered(self):
        sm = getSiteManager(self.portal)
        layers = [o.__name__ for o in registered_layers()]
        assert 'IPlomino2Pdf' in layers

class TestReinstall(unittest.TestCase):
    """Ensure product can be reinstalled safely"""
    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def testReinstall(self):
        portal_setup = getToolByName(self.portal, 'portal_setup')
        try:
            portal_setup.runAllImportStepsFromProfile('profile-%s:default' % PROJECTNAME)
        except BadRequest:
            # if tests run too fast, duplicate profile import id makes test fail
            time.sleep(0.5)
            portal_setup.runAllImportStepsFromProfile('profile-%s:default' % PROJECTNAME)
