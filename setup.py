from setuptools import setup, find_packages
import os

version = open(os.path.join("pretaweb", "plomino2pdf", "version.txt")).read().strip()

setup(name='pretaweb.plomino2pdf',
      version=version,
      description="Plomino Plugin for rendering PDF documents",
      long_description=open(os.path.join("docs", "README.txt")).read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='',
      author='Michael Davis',
      author_email='m.r.davis@pretaweb.com',
      url='http://pypi.python.org/pypi/pretaweb.plomino2pdf',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['pretaweb'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
#          'xhtml2pdf',
          'weasyprint',
#          'pyPdf',
      ],
      extras_require = {
      'test': [
               'plone.app.testing',
               ]
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """
      )
