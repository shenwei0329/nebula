# coding=utf-8

from nebula.core import i18n


class NebulaFormTranslations(object):

    def __init__(self):
        self._translation = i18n.get_translations(domain='wtforms', translation_name='wtforms_translations')

    def gettext(self, string):
        return self._translation.gettext(string)

    def ngettext(self, singular, plural, n):
        return self._translation.udgettext(singular, plural, n)


class I18nMixin(object):

    def _get_translations(self):
        return NebulaFormTranslations()
