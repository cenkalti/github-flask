# -*- coding: utf-8 -*-
"""
    GitHub-Flask
    ============

    Authenticate users in your Flask app with GitHub.

"""
import logging
try:
    from urllib.parse import urlencode, parse_qs
except ImportError:
    from urllib import urlencode
    from urlparse import parse_qs
from functools import wraps

import requests
from flask import redirect, request, json

__version__ = '3.1.2'

_logger = logging.getLogger(__name__)
# Add NullHandler to prevent logging warnings on startup
null_handler = logging.NullHandler()
_logger.addHandler(null_handler)


def is_valid_response(response):
    """Returns ``True`` if response ``status_code`` is not an error type,
    returns ``False`` otherwise.

    :param response: :class:~`requests.Response` object to check
    :type response: :class:~`requests.Response`
    :returns: ``True`` if response ``status_code`` is not an error type,
              ``False`` otherwise.
    :rtype bool:
    """
    return 200 <= response.status_code <= 299


def is_json_response(response):
    """Returns ``True`` if response ``Content-Type`` is JSON.

    :param response: :class:~`requests.Response` object to check
    :type response: :class:~`requests.Response`
    :returns: ``True`` if ``response`` is JSON, ``False`` otherwise
    :rtype bool:
    """
    content_type = response.headers.get('Content-Type', '')
    return content_type == 'application/json' or content_type.startswith('application/json;')


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
        self.base_url = app.config.get('GITHUB_BASE_URL', self.BASE_URL)
        self.auth_url = app.config.get('GITHUB_AUTH_URL', self.BASE_AUTH_URL)
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

    def authorize(self, scope=None, redirect_uri=None, state=None):
        """
        Redirect to GitHub and request access to a user's data.

        :param scope: List of `Scopes`_ for which to request access, formatted
                      as a string or comma delimited list of scopes as a
                      string. Defaults to ``None``, resulting in granting
                      read-only access to public information (includes public
                      user profile info, public repository info, and gists).
                      For more information on this, see the examples in
                      presented in the GitHub API `Scopes`_ documentation, or
                      see the examples provided below.
        :type scope: str
        :param redirect_uri: `Redirect URL`_ to which to redirect the user
                             after authentication. Defaults to ``None``,
                             resulting in using the default redirect URL for
                             the OAuth application as defined in GitHub.  This
                             URL can differ from the callback URL defined in
                             your GitHub application, however it must be a
                             subdirectory of the specified callback URL,
                             otherwise raises a :class:`GitHubError`.  For more
                             information on this, see the examples in presented
                             in the GitHub API `Redirect URL`_ documentation,
                             or see the example provided below.
        :type redirect_uri: str
        :param state: An unguessable random string. It is used to protect
                      against cross-site request forgery attacks.
        :type state: str

        For example, if we wanted to use this method to get read/write access
        to user profile information, in addition to read-write access to code,
        commit status, etc., we would need to use the `Scopes`_ ``user`` and
        ``repo`` when calling this method.

        .. code-block:: python

            github.authorize(scope="user,repo")

        Additionally, if we wanted to specify a different redirect URL
        following authorization.

        .. code-block:: python

            # Our application's callback URL is "http://example.com/callback"
            redirect_uri="http://example.com/callback/my/path"

            github.authorize(scope="user,repo", redirect_uri=redirect_uri)


        .. _Scopes: https://developer.github.com/v3/oauth/#scopes
        .. _Redirect URL: https://developer.github.com/v3/oauth/#redirect-urls

        """
        _logger.debug("Called authorize()")
        params = {'client_id': self.client_id}
        if scope:
            params['scope'] = scope
        if redirect_uri:
            params['redirect_uri'] = redirect_uri
        if state:
            params['state'] = state

        url = self.auth_url + 'authorize?' + urlencode(params)
        _logger.debug("Redirecting to %s", url)
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
        _logger.debug("Handling response from GitHub")
        params = {
            'code': request.args.get('code'),
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        url = self.auth_url + 'access_token'
        _logger.debug("POSTing to %s", url)
        _logger.debug(params)
        response = self.session.post(url, data=params)
        data = parse_qs(response.content)
        _logger.debug("response.content = %s", data)
        for k, v in data.items():
            if len(v) == 1:
                data[k] = v[0]
        token = data.get(b'access_token', None)
        if token is not None:
            token = token.decode('ascii')
        return token

    def _handle_invalid_response(self):
        pass

    def raw_request(self, method, resource, access_token=None, **kwargs):
        """
        Makes a HTTP request and returns the raw
        :class:`~requests.Response` object.

        """
        # Set ``Authorization`` header
        kwargs.setdefault('headers', {})
        if access_token is None:
            access_token = self.get_access_token()
        kwargs['headers'].setdefault('Authorization', 'token %s' % access_token)

        if resource.startswith(("http://", "https://")):
            url = resource
        else:
            url = self.base_url + resource
        return self.session.request(method, url, allow_redirects=True, **kwargs)

    def request(self, method, resource, all_pages=False, **kwargs):
        """
        Makes a request to the given endpoint.
        Keyword arguments are passed to the :meth:`~requests.request` method.
        If the content type of the response is JSON, it will be decoded
        automatically and a dictionary will be returned.
        Otherwise the :class:`~requests.Response` object is returned.

        """
        response = self.raw_request(method, resource, **kwargs)

        if not is_valid_response(response):
            raise GitHubError(response)

        if is_json_response(response):
            result = response.json()
            while all_pages and response.links.get('next'):
                url = response.links['next']['url']
                response = self.raw_request(method, url, **kwargs)
                if not is_valid_response(response) or \
                        not is_json_response(response):
                    raise GitHubError(response)
                body = response.json()
                if isinstance(body, list):
                    result += body
                elif isinstance(body, dict) and 'items' in body:
                    result['items'] += body['items']
                else:
                    raise GitHubError(response)
            return result
        else:
            return response

    def get(self, resource, **kwargs):
        """Shortcut for ``request('GET', resource)``."""
        return self.request('GET', resource, **kwargs)

    def post(self, resource, data, **kwargs):
        """Shortcut for ``request('POST', resource)``.
        Use this to make POST request since it will also encode ``data`` to
        'application/json' format."""
        headers = kwargs.pop('headers', {})
        headers.setdefault('Content-Type', 'application/json')
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
