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

    # Email a form as a pdf
    from pretaweb.plomino2pdf.api import email_form_as_pdf
    email_form_as_pdf(plominoContext,'test@example.com')
