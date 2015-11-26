import sys
import logging
import unittest

import requests
from mock import patch, Mock

from flask import Flask, request, redirect
from flask_github import GitHub, AccessControlError

logger = logging.getLogger(__name__)


class GitHubTestCase(unittest.TestCase):

    @patch.object(requests.Session, 'post')
    @patch.object(GitHub, 'BASE_AUTH_URL')
    def test_authorization(self, auth_url, post):
        def assert_params(*args, **kwargs):
            data = kwargs.pop('data')
            assert data['client_id'] == '123'
            assert data['client_secret'] == 'SEKRET'
            assert data['code'] == 'KODE'
            response = Mock()
            response.content = b'access_token=asdf&token_type=bearer'
            return response
        post.side_effect = assert_params
        auth_url.__get__ = Mock(return_value='http://localhost/oauth/')

        app = Flask(__name__)

        app.config['GITHUB_CLIENT_ID'] = '123'
        app.config['GITHUB_CLIENT_SECRET'] = 'SEKRET'

        github = GitHub(app)

        @app.route('/login')
        def login():
            return github.authorize(redirect_uri="http://localhost/callback")

        @app.route('/callback')
        @github.authorized_handler
        def authorized(token):
            access_token.append(token)
            return ''

        # Mimics GitHub authorization URL
        # http://developer.github.com/v3/oauth/#web-application-flow
        @app.route('/oauth/authorize')
        def handle_auth():
            logger.info("in /oauth/authorize")
            called_auth.append(1)
            assert request.args['client_id'] == '123'
            logger.debug("client_id OK")
            assert request.args['redirect_uri'] == 'http://localhost/callback'
            logger.debug("redirect_uri OK")
            return redirect(request.args['redirect_uri'] + '?code=KODE')

        access_token = []
        called_auth = []

        client = app.test_client()
        client.get('/login', follow_redirects=True)

        assert called_auth
        assert access_token == ['asdf'], access_token


class ConditionalRequestsTestCase(unittest.TestCase):

    def test_conditionals(self):
        # logger.info('testing etag...')

        app = Flask(__name__)
        app.config['GITHUB_CLIENT_ID'] = '123'
        app.config['GITHUB_CLIENT_SECRET'] = 'SEKRET'

        github = GitHub(app)

        @github.access_token_getter
        def access_token():
            return 'a8cf69512ab070ebae6563b735fdb9ca6e19073a'

        # no headers
        with self.assertRaises(AccessControlError):
            github.etag
        # logger.warn('exception thrown')

        # make normal request
        res = github.get('user')
        # logger.info('first res {}'.format(len(res)))
        assert len(res) > 0

        rate_limit = github.rate_limit
        # logger.info('rate limit {} {}'.format(type(rate_limit), rate_limit))
        assert rate_limit < 5000

        res = github.get('user', etag=github.etag)
        # logger.info('etag value {}'.format(github.etag))
        # logger.info('etag res {}'.format(type(res)))
        assert res is None

        # logger.info('rate limit {}'.format(github.rate_limit))
        assert github.rate_limit == rate_limit
        rate_limit = github.rate_limit

        res = github.get('user', last_modified=github.last_modified)
        # logger.info('lm value {}'.format(github.last_modified))
        # logger.info('lm res {}'.format(type(res)))
        assert res is None

        # logger.info('rate limit {}'.format(github.rate_limit))
        assert github.rate_limit == rate_limit


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
