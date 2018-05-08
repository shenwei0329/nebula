# coding=utf-8

import os

import flask_babel
from flask import _request_ctx_stack
from babel import support, Locale
try:
    from pytz.gae import pytz
except ImportError:
    from pytz import timezone, UTC
else:
    timezone = pytz.timezone
    UTC = pytz.UTC

from . import constants


def load_translations(domain=None):
    dirname = os.path.join(constants.LOCALE_PATH)
    return support.Translations.load(dirname, [get_locale()], domain)


def get_translations(domain=None, translation_name='babel_translations'):
    """Returns the correct gettext translations that should be used for
    this request.  This will never fail and return a dummy translation
    object if used outside of the request or if a translation cannot be
    found.
    """
    ctx = _request_ctx_stack.top
    translations = ctx and getattr(ctx, translation_name, None) or None
    if translations is None:
        translations = load_translations(domain=domain)
        if ctx is not None:
            setattr(ctx, translation_name, translations)
    return translations

flask_babel.get_translations = get_translations


def get_locale():
    """Returns the locale that should be used for this request as
    `babel.Locale` object.  This returns `None` if used outside of
    a request.
    """
    ctx = _request_ctx_stack.top
    locale = ctx and getattr(ctx, 'babel_locale', None) or None
    if locale is None:
        if ctx is None:
            locale = Locale.parse(constants.DEFAULT_LOCALE)
        else:
            babel = ctx.app.extensions['babel']
            if babel.locale_selector_func is None:
                locale = babel.default_locale
            else:
                rv = babel.locale_selector_func()
                if rv is None:
                    locale = babel.default_locale
                else:
                    locale = Locale.parse(rv)
            ctx.babel_locale = locale
    return locale

flask_babel.get_locale = get_locale


def get_timezone():
    """Returns the timezone that should be used for this request as
    `pytz.timezone` object.  This returns `None` if used outside of
    a request.
    """
    ctx = _request_ctx_stack.top
    # tzinfo = getattr(ctx, 'babel_tzinfo', None)
    tzinfo = ctx and getattr(ctx, 'babel_tzinfo', None) or None
    if tzinfo is None:
        if ctx is None:
            tzinfo = timezone(constants.DEFAULT_TIMEZONE)
        else:
            babel = ctx.app.extensions['babel']
            if babel.timezone_selector_func is None:
                tzinfo = babel.default_timezone
            else:
                rv = babel.timezone_selector_func()
                if rv is None:
                    tzinfo = babel.default_timezone
                else:
                    if isinstance(rv, basestring):
                        tzinfo = timezone(rv)
                    else:
                        tzinfo = rv
            ctx.babel_tzinfo = tzinfo
    return tzinfo

flask_babel.get_timezone = get_timezone


def gettext(string, **variables):
    """Translates a string with the current locale and passes in the
    given keyword arguments as mapping to a string formatting string.

    ::

        gettext(u'Hello World!')
        gettext(u'Hello %(name)s!', name='World')
    """
    t = get_translations()
    if t is None:
        return string % variables
    return variables and t.ugettext(string) % variables or t.ugettext(string)
_ = gettext


def ngettext(singular, plural, num, **variables):
    """Translates a string with the current locale and passes in the
    given keyword arguments as mapping to a string formatting string.
    The `num` parameter is used to dispatch between singular and various
    plural forms of the message.  It is available in the format string
    as ``%(num)d`` or ``%(num)s``.  The source language should be
    English or a similar language which only has one plural form.

    ::

        ngettext(u'%(num)d Apple', u'%(num)d Apples', num=len(apples))
    """
    variables.setdefault('num', num)
    t = get_translations()
    if t is None:
        return (singular if num == 1 else plural) % variables
    return t.ungettext(singular, plural, num) % variables


def pgettext(context, string, **variables):
    """Like :func:`gettext` but with a context.

    .. versionadded:: 0.7
    """
    t = get_translations()
    if t is None:
        return string % variables
    return t.upgettext(context, string) % variables


def npgettext(context, singular, plural, num, **variables):
    """Like :func:`ngettext` but with a context.

    .. versionadded:: 0.7
    """
    variables.setdefault('num', num)
    t = get_translations()
    if t is None:
        return (singular if num == 1 else plural) % variables
    return t.unpgettext(context, singular, plural, num) % variables


def lazy_gettext(string, **variables):
    """Like :func:`gettext` but the string returned is lazy which means
    it will be translated when it is used as an actual string.

    Example::

        hello = lazy_gettext(u'Hello World')

        @app.route('/')
        def index():
            return unicode(hello)
    """
    from speaklater import make_lazy_string
    return make_lazy_string(gettext, string, **variables)


def lazy_pgettext(context, string, **variables):
    """Like :func:`pgettext` but the string returned is lazy which means
    it will be translated when it is used as an actual string.

    .. versionadded:: 0.7
    """
    from speaklater import make_lazy_string
    return make_lazy_string(pgettext, context, string, **variables)
