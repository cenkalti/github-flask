GitHub-Flask
============

GitHub-Flask is an extension for authenticating Flask applications with GitHub.
It also provides support for various other requests to the GitHub API.


Installation
------------

GitHub-Flask is available on PyPI::

	pip install github-flask


Usage
-----

An example application is provided. Getting it up and running should be pretty
straightforward. Just run the sample application to see how it's working::

    $ python example.py


API Requests
------------

After authenticating, this extension also provides methods for doing
requests to the GitHub API as the authenticated user::

	github = GitHub()
	github.init_app(app)

	# returns the authenticated user resource as a dictionary
	github.get('user')
	
	# returns this repository
	github.get('repos/cenkalti/github-flask')
