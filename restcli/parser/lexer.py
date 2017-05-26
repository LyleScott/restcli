import argparse
from collections import OrderedDict, namedtuple

import six

from restcli.utils import AttrSeq, split_quoted

ACTIONS = AttrSeq(
    'append',
    'assign',
    'delete',
)

lexer = argparse.ArgumentParser(prog='lexer', add_help=False)
lexer.add_argument('-d', '--{}'.format(ACTIONS.delete), action='append')
lexer.add_argument('-a', '--{}'.format(ACTIONS.append), action='append')

Node = namedtuple('Node', ['action', 'token'])


def lex(argument_str):
    """Lex a string into a sequence of (action, tokens) pairs."""
    argv = split_quoted(argument_str)
    opts, args = lexer.parse_known_args(argv)
    tokens = OrderedDict(
        Node(action=k, token=v)
        for k, v in vars(opts).items()
        if v is not None
    )
    if args:
        tokens[ACTIONS.assign] = split_quoted(' '.join(args))
    return tuple(six.iteritems(tokens))
