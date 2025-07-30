from typing import Optional
import logging
from contextvars import ContextVar
from collections import defaultdict
from enum import Enum

import gettext

from discord.app_commands import Translator, locale_str
from discord.enums import Locale


logger = logging.getLogger(__name__)


SOURCE_LOCALE = 'en_US'
ctx_locale: ContextVar[str] = ContextVar('locale', default=SOURCE_LOCALE)
ctx_translator: ContextVar['LeoBabel'] = ContextVar('translator', default=None)  # type: ignore

null = gettext.NullTranslations()


class LeoBabel(Translator):
    def __init__(self):
        self.supported_locales = set()  # Will be loaded from config
        self.supported_domains = {}
        self.translators = defaultdict(dict)  # locale -> domain -> GNUTranslator

    def read_supported(self):
        """
        Load supported localisations and domains from the config.
        """
        from meta import conf

        locales = conf.babel.get('locales', '')
        stripped = (loc.strip(', ') for loc in locales.split(','))
        self.supported_locales = {loc for loc in stripped if loc}
        self.supported_locales.add(SOURCE_LOCALE)

        domains = conf.babel.get('domains', '')
        stripped = (dom.strip(', ') for dom in domains.split(','))
        self.supported_domains = {dom for dom in stripped if dom}

    async def load(self):
        self._load()

    def _load(self):
        """
        Initialise the gettext translators for the supported_locales.
        """
        self.read_supported()
        missing = []
        loaded = []
        for locale in self.supported_locales:
            for domain in self.supported_domains:
                if locale == SOURCE_LOCALE:
                    continue
                try:
                    translator = gettext.translation(domain, "locales/", languages=[locale])
                    loaded.append(f"Loaded translator for <locale: {locale}> <domain: {domain}>")
                except OSError:
                    # Presume translation does not exist
                    missing.append(f"Could not load translator for supported <locale: {locale}> <domain: {domain}>")
                    translator = null

                self.translators[locale][domain] = translator
        if missing:
            logger.warning('\n'.join(("Missing Translators:", *missing)))
        if loaded:
            logger.debug('\n'.join(("Loaded Translators:", *loaded)))

    async def unload(self):
        self.translators.clear()

    def get_translator(self, locale: Optional[str], domain):
        locale = locale or SOURCE_LOCALE
        locale = locale.replace('-', '_') if locale else None
        if locale == SOURCE_LOCALE:
            translator = null
        elif locale in self.supported_locales and domain in self.supported_domains:
            translator = self.translators[locale].get(domain, None)
            if translator is None:
                # This should never really happen because we already loaded the supported translators
                logger.warning(
                    f"Translator missing for supported <locale: {locale}> "
                    "and <domain: {domain}>. Setting NullTranslator."
                )
                translator = self.translators[locale][domain] = null
        else:
            # Unsupported
            translator = null
        return translator

    def t(self, lazystr, locale=None):
        domain = lazystr.domain
        translator = self.get_translator(locale or lazystr.locale or ctx_locale.get(), domain)
        return lazystr._translate_with(translator)

    async def translate(self, string: locale_str, locale: Locale, context):
        loc = locale.value.replace('-', '_')
        if loc in self.supported_locales:
            domain = string.extras.get('domain', None)
            if domain is None and isinstance(string, LazyStr):
                logger.debug(
                    f"LeoBabel cannot translate a locale_str with no domain set. Context: {context}, String: {string}"
                )
                return None

            translator = self.get_translator(loc, domain)
            if not isinstance(string, LazyStr):
                lazy = LazyStr(Method.GETTEXT, string.message)
            else:
                lazy = string
            return lazy._translate_with(translator)


class Method(Enum):
    GETTEXT = 'gettext'
    NGETTEXT = 'ngettext'
    PGETTEXT = 'pgettext'
    NPGETTEXT = 'npgettext'


class LocalBabel:
    def __init__(self, domain):
        self.domain = domain

    @property
    def methods(self):
        return (self._, self._n, self._p, self._np)

    def _(self, message):
        return LazyStr(Method.GETTEXT, message, domain=self.domain)

    def _n(self, singular, plural, n):
        return LazyStr(Method.NGETTEXT, singular, plural, n, domain=self.domain)

    def _p(self, context, message):
        return LazyStr(Method.PGETTEXT, context, message, domain=self.domain)

    def _np(self, context, singular, plural, n):
        return LazyStr(Method.NPGETTEXT, context, singular, plural, n, domain=self.domain)


class LazyStr(locale_str):
    __slots__ = ('method', 'args', 'domain', 'locale')

    def __init__(self, method, *args, locale=None, domain=None):
        self.method = method
        self.args = args
        self.domain = domain
        self.locale = locale

    @property
    def message(self):
        return self._translate_with(null)

    @property
    def extras(self):
        return {'locale': self.locale, 'domain': self.domain}

    def __str__(self):
        return self.message

    def _translate_with(self, translator: gettext.GNUTranslations):
        method = getattr(translator, self.method.value)
        return method(*self.args)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.method}, {self.args!r}, locale={self.locale}, domain={self.domain})'

    def __eq__(self, obj: object) -> bool:
        return isinstance(obj, locale_str) and self.message == obj.message

    def __hash__(self) -> int:
        return hash(self.args)
