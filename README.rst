wpmarkup
********

An implementation of WordPress <http://wordpress.org>_ markup for Django, ported from ``wptexturize``.

Installation
============

The recommended way to install django-markupfield is with
`pip <http://pypi.python.org/pypi/pip>`_ ::

    pip install -e git://github.com/kunxi/wpmarkup.git#egg=wpmarkup

It is not necessary to add ``'wpmarkup'`` to your ``INSTALLED_APPS``, it
merely needs to be on your ``PYTHONPATH``.

Usage
=====

Render the raw text to HTML using WordPress style:::

    from wpmarkup import Markup
    rendered = Markup.render(raw)

Known bugs
==========

The markup only renders the raw text to HTML, none of special code in WordPress,
such as [more], [gallery] are supported yet.
