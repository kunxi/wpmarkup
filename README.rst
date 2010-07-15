wpmarkup
********

An implementation of WordPress markup for Django, ported from ``wptexturize``.

Installation
============

The recommended way to install django-markupfield is with
`pip <http://pypi.python.org/pypi/pip>`_

It is not necessary to add ``'wpmarkup'`` to your ``INSTALLED_APPS``, it
merely needs to be on your ``PYTHONPATH``.

Usage
=====

from wpmarkup import Markup
rendered = Markup.render(raw)

Known bugs
==========

The markup only renders the raw text to HTML, none of special code in WordPress,
such as [more], [gallery] are supported yet.
