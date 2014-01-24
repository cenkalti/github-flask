import logging
import unittest

import requests
from mock import patch, Mock

from flask import Flask, request, redirect
from flask_github import GitHub


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
        app.config['GITHUB_CALLBACK_URL'] = 'http://localhost/github-callback'

        github = GitHub(app)

        @app.route('/login')
        def login():
            return github.authorize()

        @app.route('/github-callback')
        @github.authorized_handler
        def authorized(token):
            access_token.append(token)
            return ''

        # Mimics GitHub authorization URL
        # http://developer.github.com/v3/oauth/#web-application-flow
        @app.route('/oauth/authorize')
        def handle_auth():
            called_auth.append(1)
            assert request.args['client_id'] == '123'
            assert request.args['redirect_uri'] == 'http://localhost/github-callback'
            return redirect(request.args['redirect_uri'] + '?code=KODE')

        access_token = []
        called_auth = []

        client = app.test_client()
        client.get('/login', follow_redirects=True)

        assert called_auth
        assert access_token == ['asdf']


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
