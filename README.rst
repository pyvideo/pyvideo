pytube
######

.. image:: https://badges.gitter.im/pyvideo/pyvideo.svg
   :alt: Join the chat at https://gitter.im/pyvideo/pyvideo
   :target: https://gitter.im/pyvideo/pyvideo?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

.. image:: https://badges.gitter.im/pytube/pytube.svg
   :alt: Join the chat at https://gitter.im/pytube/pytube
   :target: https://gitter.im/pytube/pytube?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

.. image:: https://travis-ci.org/pytube/pytube.svg?branch=master
    :target: https://travis-ci.org/pytube/pytube

.. image:: https://zenodo.org/badge/23288/pytube/pytube.svg
   :target: https://zenodo.org/badge/latestdoi/23288/pytube/pytube

http://pytube.org is simply an index of Python-related media records. The raw
data being used here comes out of the `pytube/data`_ repo.

.. _`pytube/data`: https://github.com/pytube/data

Before opening a PR, please check out our `Development Philosophy`_.

.. _`Development Philosophy`: https://github.com/pytube/pytube/wiki/Development-Philosophy

Development setup
=================

Setting up a development environment is as simple as four easy steps.

1. Clone repo (recursively; it contains submodules)
2. Install dependencies
3. Build reST files from JSON files
4. Build HTML files from reST files

All of these steps are explained in detail below.

First, pull down this repo's code::

  $ git clone --recursive https://github.com/pytube/pytube.git

Then, install the dependencies for building this site. It is recommended to
install all the requirements inside virtualenv_, use virtualenvwrapper_ to
manage virtualenvs. **Building pytube.org requires Python 3.5**

.. _virtualenv: https://virtualenv.pypa.io/en/latest/
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.org/en/latest/

First of all, create a virtual environment to install all the dependencies
into either using virtualenvwrapper::

  $ mkvirtualenv -p python3 pytube

\... or using pyvenv::

  $ pyvenv .env && source .env/bin/activate

From the root of the repo, run the following command::

  $ pip install -r requirements/dev.txt

Finally, you'll be able to generate the HTML site. From the root of the repo,
run the following command::

  $ make html

To view the site, run the following command::

  $ make serve

This will start development server on port 8000. Goto browser and open
http://localhost:8000 to view your local version of pytube.org!

Debugging
=========

If you're trying to debug unexpected build results, you can pass one of two
variables to the make process to influence to logging level::

  # Show Pelican warnings
  $ make VERBOSE=1 html

  # Show even more output
  $ make DEBUG=1 html


Accessibility tests
===================

There are automated tests to ensure that none of the pages have significant
accessibility problems; to run them:

1. Download `chromedriver <https://sites.google.com/a/chromium.org/chromedriver/downloads>`_
   and add it to your PATH environment variable (copy to ``/usr/local/bin``, etc.)
2. Run ``make test``

Want to help?
=============

We'd love the help! All feature ideas and bugs-to-be-fixed are listed in the
`issues <https://github.com/pytube/pytube/issues>`_ associated with this repo. Please check there for ideas on
how to contribute. Thanks!

If you want to contribute new media, please check the `pytube/data`_ repo
and its `contribution docs`_.


Found an issue?
===============

If you've found an issue with the site or something that could be done better,
please open an issue_ on Github.

.. _`issue`: https://github.com/pytube/pytube/issues
.. _`contribution docs`: https://github.com/pytube/data/blob/master/CONTRIBUTING.rst

Want our Google Analytics info?
===============================

PyTube tries to be as open source as possible. 
We share the data that Google Analytics collects on request. 
Please feel free to send an email to pytube.org@gmail.com 
with the header "Google Analytics Access Request" if you would like access
to this data. Please note that it may take a few weeks to be granted this 
access.

PyTube or Pyvideo
=================

Due to some migration pains, this site has gone through a name change.
Although the website is named pyvideo.org, this code base contains many
references to the old website name pytube.org. This will be fixed in the
future.


