.. contents::

pretaweb.plomino2pdf
====================

Plomino PDF library.

Introduction
============

This package contains a number of functions for generating PDF documents from
plomino.

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
