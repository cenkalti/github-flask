# -*- coding: utf-8 -*-
"""
    GitHub-Flask
    ============

    Authenticate users in your Flask app with GitHub.

"""
import logging
from urllib import urlencode
from urlparse import parse_qs
from functools import wraps

import requests
from flask import redirect, request, json

__version__ = '0.3.4'

logger = logging.getLogger(__name__)


class GitHubError(Exception):
    """Raised if a request fails to the GitHub API."""

    def __str__(self):
        try:
            message = self.response.json()['message']
        except Exception:
            message = None
        return "%s: %s" % (self.response.status_code, message)

    @property
    def response(self):
        """The :class:`~requests.Response` object for the request."""
        return self.args[0]


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
        logger.debug("Called authorize()")
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.callback_url,
        }
        if scope is not None:
            params['scope'] = scope

        url = self.BASE_AUTH_URL + 'authorize?' + urlencode(params)
        logger.debug("Redirecting to %s", url)
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
                data = self._handle_response()
            else:
                data = self._handle_invalid_response()
            return f(*((data,) + args), **kwargs)
        return decorated

    def _handle_response(self):
        """
        Handles response after the redirect to GitHub. This response
        determines if the user has allowed the this application access. If we
        were then we send a POST request for the access_key used to
        authenticate requests to GitHub.

        """
        logger.debug("Handling response from GitHub")
        params = {
            'code': request.args.get('code'),
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        url = self.BASE_AUTH_URL + 'access_token'
        logger.debug("POSTing to %s", url)
        logger.debug(params)
        response = self.session.post(url, data=params)
        data = parse_qs(response.content)
        logger.debug("response.content = %s", data)
        for k, v in data.items():
            if len(v) == 1:
                data[k] = v[0]
        return data.get('access_token', None)

    def _handle_invalid_response(self):
        pass

    def raw_request(self, method, resource, params=None, **kwargs):
        """
        Makes a HTTP request and returns the raw
        :class:`~requests.Response` object.

        """
        if params is None:
            params = {}

        if 'access_token' not in params:
            params['access_token'] = self.get_access_token()

        url = self.BASE_URL + resource
        return self.session.request(
            method, url, params=params, allow_redirects=True, **kwargs)

    def request(self, method, resource, **kwargs):
        """
        Makes a request to the given endpoint.
        Keyword arguments are passed to the :meth:`~requests.request` method.
        If the content type of the response is JSON, it will be decoded
        automatically and a dictionary will be returned.
        Otherwise the :class:`~requests.Response` object is returned.

        """
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
        """Shortcut for ``request('GET', resource)``."""
        return self.request('GET', resource, **kwargs)

    def post(self, resource, data, **kwargs):
        """Shortcut for ``request('POST', resource)``.
        Use this to make POST request since it will also encode ``data`` to
        'application/x-www-form-urlencoded' format."""
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = json.dumps(data)
        return self.request('POST', resource, headers=headers,
                            data=data, **kwargs)

    def head(self, resource, **kwargs):
        return self.request('HEAD', resource, **kwargs)

    def patch(self, resource, **kwargs):
        return self.request('PATCH', resource, **kwargs)

    def put(self, resource, **kwargs):
        return self.request('PUT', resource, **kwargs)

    def delete(self, resource, **kwargs):
        return self.request('DELETE', resource, **kwargs)
