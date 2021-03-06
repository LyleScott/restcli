import abc
import json
import re
import string

import six
from restcli.exceptions import ReqModSyntaxError, ReqModValueError
from restcli.params import VALID_URL_CHARS
from restcli.utils import AttrMap, AttrSeq, classproperty, is_ascii

PARAM_TYPES = AttrSeq(
    'json_field',
    'str_field',
    'header',
    'url_param',
)


def parse_mod(mod_str):
    """Attempt to parse a str into a Mod."""
    error = None
    for mod_cls in MODS.values():
        try:
            mod = mod_cls.match(mod_str)
        except ReqModSyntaxError as err:
            error = err
            continue
        return mod
    raise error


class Mod(six.with_metaclass(abc.ABCMeta, object)):

    param_type = NotImplemented
    param = NotImplemented
    delimiter = NotImplemented

    _types = None
    _pattern = None

    split_re_tpl = string.Template(r'(?<=[^\\])${delimiter}')

    def __init__(self, key, value):
        self.raw_key = key
        self.raw_value = value
        self.key = None
        self.value = None
        self.validated = False

    def __str__(self):
        if self.validated:
            attrs = ['key', 'value']
        else:
            attrs = ['raw_key', 'raw_value']
        attrs.append('validated')
        attr_kwargs = (
            '%s=%r' % (attr, getattr(self, attr))
            for attr in attrs
        )
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join(attr_kwargs),
        )

    @classmethod
    @abc.abstractmethod
    def clean_params(cls, key, value):
        """Validate and format the Mod's key and/or value."""

    @classmethod
    def match(cls, mod_str):
        parts = cls.pattern.split(mod_str)
        if len(parts) != 2:
            raise ReqModSyntaxError(value=mod_str)
        key, value = parts
        return cls(key=key, value=value)

    def clean(self):
        self.key, self.value = self.clean_params(self.raw_key, self.raw_value)
        self.validated = True

    @classproperty
    def pattern(cls):
        if not cls._pattern:
            re_str = cls.split_re_tpl.substitute(
                delimiter=re.escape(cls.delimiter))
            cls._pattern = re.compile(re_str)
        return cls._pattern


class JsonFieldMod(Mod):

    param_type = PARAM_TYPES.json_field
    param = 'body'
    delimiter = ':='

    @classmethod
    def clean_params(cls, key, value):
        try:
            json_value = json.loads(value)
        except json.JSONDecodeError as err:
            # TODO: implement error handling
            raise ReqModValueError(value=value, msg='invalid JSON - %s' % err)
        return key, json_value


class StrFieldMod(Mod):

    param_type = PARAM_TYPES.str_field
    param = 'body'
    delimiter = '='

    @classmethod
    def clean_params(cls, key, value):
        return key, value


class HeaderMod(Mod):

    param_type = PARAM_TYPES.header
    param = 'headers'
    delimiter = ':'

    @classmethod
    def clean_params(cls, key, value):
        # TODO: legit error messages
        msg = "non-ASCII character(s) found in header"
        if not is_ascii(str(key)):
            raise ReqModValueError(value=key, msg=msg)
        if not is_ascii(str(value)):
            raise ReqModValueError(value=value, msg=msg)
        return key, value


class UrlParamMod(Mod):

    param_type = PARAM_TYPES.url_param
    param = 'query'
    delimiter = '=='

    @classmethod
    def clean_params(cls, key, value):
        if not all(char in VALID_URL_CHARS for char in key + value):
            raise ReqModValueError(
                value=cls.delimiter.join((key, value)),
                msg='Invalid char(s) found in URL parameter.'
                    ' Accepted chars are: %s' % (VALID_URL_CHARS,)
            )
        return key, value


# Tuple of Mod classes, in order of specificity of delimiters
MODS = AttrMap(*(
    (mod_cls.delimiter, mod_cls) for mod_cls in (
        JsonFieldMod,
        UrlParamMod,
        HeaderMod,
        StrFieldMod,
    )
))
