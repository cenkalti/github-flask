# -*- coding: utf-8 -*-
"""
    GitHub-Flask
    ---------------

    Authenticate users in your Flask app with GitHub.

"""
from urllib import urlencode
from urlparse import parse_qs
from functools import wraps

import requests
from flask import redirect, request, json


class GitHubError(Exception):

    def __str__(self):
        response = self.args[0]
        try:
            message = response.json()['message']
        except Exception:
            message = None
        return "%s: %s" % (response.status_code, message)


class GitHub(object):
    """
    Provides decorators for authenticating users with GitHub within a Flask
    application. Helper methods are also provided interacting with GitHub API.

    """
    BASE_URL = 'https://api.github.com/'
    BASE_AUTH_URL = 'https://github.com/login/oauth/'

    def __init__(self, app=None):
        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def init_app(self, app):
        self.client_id = app.config['GITHUB_CLIENT_ID']
        self.client_secret = app.config['GITHUB_CLIENT_SECRET']
        self.callback_url = app.config['GITHUB_CALLBACK_URL']
        self.base_url = app.config.get('GITHUB_BASE_URL', self.BASE_URL)
        self.session = requests.session()

    def access_token_getter(self, f):
        """
        Registers a function as the access_token getter. Must return the
        access_token used to make requests to GitHub on the user's behalf.

        """
        self.get_access_token = f
        return f

    def get_access_token(self):
        raise NotImplementedError

    def authorize(self, scope=None):
        """
        Redirect to GitHub and request access to a user's data.

        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.callback_url,
        }
        if scope is not None:
            params['scope'] = scope

        url = self.BASE_AUTH_URL + 'authorize?' + urlencode(params)
        return redirect(url)

    def authorized_handler(self, f):
        """
        Decorator for the route that is used as the callback for authorizing
        with GitHub. This callback URL can be set in the settings for the app
        or passed in during authorization.

        """
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'code' in request.args:
                data = self.handle_response()
            else:
                data = self.handle_invalid_response()
            return f(*((data,) + args), **kwargs)
        return decorated

    def handle_response(self):
        """
        Handles response after the redirect to GitHub. This response
        determines if the user has allowed the this application access. If we
        were then we send a POST request for the access_key used to
        authenticate requests to GitHub.

        """
        params = {
            'code': request.args.get('code'),
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        url = self.BASE_AUTH_URL + 'access_token'
        response = self.session.post(url, params)
        data = parse_qs(response.content)
        for k, v in data.items():
            if len(v) == 1:
                data[k] = v[0]
        return data

    def handle_invalid_response(self):
        pass

    def raw_request(self, method, resource, params=None, **kwargs):
        """
        Makes a HTTP request and returns the raw response.

        """
        if params is None:
            params = {}

        if 'access_token' not in params:
            params['access_token'] = self.get_access_token()

        url = self.BASE_URL + resource
        return self.session.request(
            method, url, params=params, allow_redirects=True, **kwargs)

    def request(self, method, resource, **kwargs):
        response = self.raw_request(method, resource, **kwargs)

        status_code = str(response.status_code)

        if status_code.startswith('4'):
            raise GitHubError(response)

        assert status_code.startswith('2')

        if response.headers['Content-Type'].startswith('application/json'):
            return response.json()
        else:
            return response

    def get(self, resource, **kwargs):
        return self.request('GET', resource, **kwargs)

    def post(self, resource, data, **kwargs):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = json.dumps(data)
        return self.request('POST', resource, headers=headers,
                            data=data, **kwargs)

    def head(self, resource, **kwargs):
        return self.request('HEAD', resource, **kwargs)

    def patch(self, resource, **kwargs):
        raise NotImplementedError

    def put(self, resource, **kwargs):
        raise NotImplementedError

    def delete(self, resource, **kwargs):
        raise NotImplementedError
