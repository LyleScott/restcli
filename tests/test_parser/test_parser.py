import random
import string
from collections import OrderedDict

import pytest
import pytest_mock

from restcli import yaml_utils as yaml
from restcli.parser import parser
from restcli.parser.lexer import ACTIONS

from ..helpers import contents_equal

odict = OrderedDict


@pytest.fixture
def request():
    """Generate a semi-random request object."""
    req = odict()
    req['method'] = random.choice(('get', 'post', 'put', 'delete'))
    req['url'] = '%s.org' % ''.join(random.sample(string.ascii_lowercase, 10))
    req['headers'] = odict((
        ('Content-Type', 'application/json'),
        ('Accept', 'application/json')
    ))

    # Add body if method supports writes
    if req['method'] in ('post', 'put'):
        name = 'Fr%snken Fr%snkenfrank' % (
            'a' * random.randint(1, 6),
            'a' * random.randint(1, 6),
        )
        req['body'] = yaml.dump(odict((
            ('name', name),
            ('age', random.randint(10, 20)),
            ('color', random.choice(('red', 'yellow', 'blue'))),
            ('warranty', random.choice((True, False))),
            ('insurance', None),
        )))

    return req


class TestParse:

    @staticmethod
    def mktokens(*tokens):
        default_tokens = OrderedDict((
            (ACTIONS.assign, None),
            (ACTIONS.append, None),
            (ACTIONS.delete, None),
        ))
        default_tokens.update(tokens)
        return tuple(default_tokens.items())

    def test_assign(self, request, mocker):
        tokens = self.mktokens((ACTIONS.assign, [
            "Authorization:JWT abc123.foo",
        ]))
        result = parser.parse(tokens, request)
        expected = odict((
            ('Content-Type', 'application/json'),
            ('Accept', 'application/json'),
            ('Authorization', 'JWT abc123.foo'),
        ))
        assert contents_equal(result['headers'], expected)


