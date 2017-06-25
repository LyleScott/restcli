import json
from string import Template

import six
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.data import JsonLexer
from pygments.lexers.python import Python3Lexer
from pygments.lexers.textfmts import HttpLexer

from restcli.exceptions import (
    ParameterNotFoundError,
    GroupNotFoundError,
    RequestNotFoundError,
)
from restcli.reqmod import lexer, parser
from restcli.requestor import Requestor

__all__ = ['App']


class App(object):
    """High-level execution logic for restcli.

    Args:
        collection_file (str): Path to a Collection file.
        env_file (str): Path to an Environment file.

    Keyword Args:
        autosave (bool): Whether to automatically save changes to disk.
            Default: False
        style (str): Pygments colorscheme name. Default: 'fruity'

    Attributes:
        r: The Requestor object. Handles almost all I/O.
        autosave (bool): Same as above. Can be modified.
    """

    HTTP_TPL = Template('\n'.join((
        'HTTP/${http_version} ${status_code} ${reason}',
        '${headers}',
        '${body}',
    )))

    def __init__(self, collection_file, env_file, autosave=False,
                 style='fruity'):
        self.r = Requestor(collection_file, env_file)
        self.autosave = autosave

        self.http_lexer = HttpLexer()
        self.json_lexer = JsonLexer()
        self.python_lexer = Python3Lexer()
        self.formatter = Terminal256Formatter(style=style)

    def run(self, group_name, request_name, *env_args, save=False):
        """Run a Request.

        Args:
            group_name (str): A Group name in the Collection.
            request_name (str): A Request name in the Collection.
        """
        group = self.get_group(group_name, action='run')
        self.get_request(group, group_name, request_name, action='run')

        updater = self.parse_env(env_args)
        response = self.r.request(group_name, request_name, updater)

        if save or self.autosave:
            self.r.env.save()

        output = self.show_response(response)
        return output

    def view(self, group_name, request_name=None, param_name=None):
        """Inspect a Group, Request, or Request Parameter."""
        group = self.get_group(group_name, action='view')
        output_obj = group

        if request_name:
            request = self.get_request(group, group_name, request_name,
                                       action='view')
            output_obj = request

            if param_name:
                param = self.get_request_param(
                    request, group_name, request_name, param_name,
                    action='view')

                if param_name == 'script':
                    return highlight(param, self.python_lexer, self.formatter)

                if param_name == 'headers':
                    headers = dict(l.split(':')
                                   for l in param.strip().split('\n'))
                    output = self.key_value_pairs(headers)
                    return highlight(output, self.http_lexer, self.formatter)

                output_obj = param

        output = json.dumps(output_obj, indent=2)
        return highlight(output, self.json_lexer, self.formatter)

    def load_collection(self, source=None):
        """Reload the current Collection, changing it to `source` if given."""
        if source:
            self.r.collection.source = source
        self.r.collection.load()
        return ''

    def load_env(self, source=None):
        """Reload the current Environment, changing it to `source` if given."""
        if source:
            self.r.env.source = source
        self.r.env.load()
        return ''

    def save_env(self):
        """Save the current Environment to disk."""
        self.r.env.save()
        return ''

    @staticmethod
    def parse_env(args):
        """Parse some string args with Environment syntax."""
        lexemes = lexer.lex(args)
        return parser.parse(lexemes)

    def set_env(self, *args, save=False):
        """Set some new variables in the Environment."""
        set_env, del_env = self.parse_env(args)
        self.r.env.update_request(**set_env)
        self.r.env.remove(*del_env)

        output = ''
        if save or self.autosave:
            output += self.save_env()
        return output

    def get_group(self, group_name, action):
        """Retrieve a Group object."""
        try:
            return self.r.collection[group_name]
        except KeyError:
            raise GroupNotFoundError(
                file=self.r.collection.source,
                action=action,
                path=[group_name],
            )

    def get_request(self, group, group_name, request_name, action):
        """Retrieve a Request object."""
        try:
            return group[request_name]
        except KeyError:
            raise RequestNotFoundError(
                file=self.r.collection.source,
                action=action,
                path=[group_name, request_name]
            )

    def get_request_param(self, request, group_name, request_name, param_name,
                          action):
        """Retrieve a Request Parameter."""
        try:
            return request[param_name]
        except KeyError:
            raise ParameterNotFoundError(
                file=self.r.collection.source,
                action=action,
                path=[group_name, request_name, param_name]
            )

    def show_response(self, response):
        """Print an HTTP Response."""
        if response.headers.get('Content-Type', None) == 'application/json':
            try:
                body = json.dumps(response.json(), indent=2)
            except json.JSONDecodeError:
                body = response.text
        else:
            body = response.text

        http_txt = self.HTTP_TPL.substitute(
            http_version=str(float(response.raw.version) / 10),
            status_code=response.status_code,
            reason=response.reason,
            headers=self.key_value_pairs(response.headers),
            body=body,
        )
        return highlight(http_txt, self.http_lexer, self.formatter)

    def show_env(self):
        """Print the current Environment."""
        env = self.r.env
        if env:
            return highlight(json.dumps(env, indent=2), self.json_lexer,
                             self.formatter)
        else:
            return 'No Environment loaded.'

    @staticmethod
    def key_value_pairs(obj):
        """Format a dict-like object into lines of 'KEY: VALUE'."""
        return '\n'.join(['%s: %s' % (k, v) for k, v in six.iteritems(obj)])
