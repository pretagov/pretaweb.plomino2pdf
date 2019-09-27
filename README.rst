.. contents::

pretaweb.plomino2pdf
====================

Plone PDF library.

Introduction
============

This package contains a number of functions for generating PDF documents inside plone.

It's currently badly named. It has no dependency on Plomino.

Dependencies
============

You should install the dependencies required by weasyprint.

http://weasyprint.readthedocs.io/en/latest/install.html

On a Ubuntu system and when using Ubuntu you should install ``libcffi-dev``.

Installation
============

Include ``pretaweb.plomino2pdf`` in the ``eggs`` section of your buildout::

    eggs =
        ...
        pretaweb.plomino2pdf

Examples::

Generate a pdf:

    from pretaweb.plomino2pdf.api import generate_pdf
    pdf = generate_pdf('some_url',some_context)

This will generate a pdf using plone.subrequest. 'some_url' should be relative
to the url of some_context.

There is also a view that allows any url to be downloaded as a PDF:

    http://mysite/somepage/pdf_view

or

    http://mysite/somepage/pdf_view?filename=somepage.pdf

