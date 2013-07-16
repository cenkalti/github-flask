GitHub-Flask
============

.. module:: flask_github

GitHub-Flask is an extension to `Flask`_ that allows you authenticate your
users via GitHub using `OAuth`_ protocol and call `GitHub API`_ methods.

GitHub-Flask depends on the `requests`_ library.

.. _Flask: http://flask.pocoo.org/
.. _OAuth: http://oauth.net/
.. _GitHub API: http://developer.github.com/v3/
.. _requests: http://python-requests.org/


Installation
------------

Install the extension with the following command:

.. code-block:: bash

    $ pip install GitHub-Flask


Configuration
-------------

Here’s an example of how GitHub-Flask is typically initialized and configured:

.. code-block:: python

    from flask import Flask
    from flask.ext.github import GitHub

    app = Flask(__name__)
    app.config['GITHUB_CLIENT_ID'] = 'XXX'
    app.config['GITHUB_CLIENT_SECRET'] = 'YYY'
    app.config['GITHUB_CALLBACK_URL'] = 'http://example.com/github-callback'

    github = GitHub(app)

The following configuration settings exist for GitHub-Flask:

=================================== ==========================================
`GITHUB_CLIENT_ID`                  Your GitHub application's client id. Go to
                                    https://github.com/settings/applications
                                    to register new application.

`GITHUB_CLIENT_SECRET`              Your GitHub application's client secret.

`GITHUB_CALLBACK_URL`               This is the URL that GitHub redirects the
                                    user after authorization.
                                    It must the same URL entered on your
                                    application settings page.
                                    You can enter something like
                                    http://localhost:5000/github-callback
                                    on both places during development.
=================================== ==========================================


Authenticating / Authorizing Users
----------------------------------

To authenticate your users with GitHub simply call
:meth:`~flask_github.GitHub.authorize` at your login handler:

.. code-block:: python

    @app.route('/login')
    def login():
        return github.authorize()


It will redirect the user to GitHub. If the user accepts the authorization
request GitHub will redirect the user to your callback URL with the
OAuth ``code`` parameter. Then the extension will make another request to
GitHub to obtain access token and call your
:meth:`~flask_github.GitHub.authorized_handler` function with that token.
If the authorization fails ``oauth_token`` parameter will be ``None``:

.. code-block:: python

    @app.route('/github-callback')
    @github.authorized_handler
    def authorized(oauth_token):
        next_url = request.args.get('next') or url_for('index')
        if oauth_token is None:
            flash("Authorization failed.")
            return redirect(next_url)

        user = User.query.filter_by(github_access_token=oauth_token).first()
        if user is None:
            user = User(token)
            db_session.add(user)

        user.github_access_token = oauth_token
        db_session.commit()
        return redirect(next_url)

Store this token somewhere securely. It is needed later to make requests on
behalf of the user.


Invoking Remote Methods
-----------------------

We need to register a function as a token getter for Github-Flask extension.
It will be called automatically by the extension to get the access token of
the user. It should return the access token or ``None``:

.. code-block:: python

    @github.access_token_getter
    def token_getter():
        user = g.user
        if user is not None:
            return user.github_access_token

After setting up you can use the
:meth:`~flask_github.GitHub.get`,  :meth:`~flask_github.GitHub.post`
or other verb methods of the :class:`~flask_github.GitHub` object.
They will return a dictionary representation of the given API endpoint.

.. code-block:: python

    @app.route('/repo')
    def repo():
        repo_dict = github.get('repos/cenkalti/github-flask')
        return str(repo_dict)


Full Example
------------

A full example can be found in `example.py`_ file.
Install the required `Flask-SQLAlchemy`_ package first.
Then edit the file and change
``GITHUB_CLIENT_ID`` and ``GITHUB_CLIENT_SECRET`` settings.
Then you can run it as a python script:

.. code-block:: bash

    $ pip install Flask-SQLAlchemy
    $ python example.py

.. _example.py: https://github.com/cenkalti/github-flask/blob/master/example.py
.. _Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/

API Reference
-------------

.. autoclass:: GitHub
   :members:

.. autoclass:: GitHubError
   :members:
