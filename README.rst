pytube
######

|travis|

http://pytube.org is simply an index of Python-related media records. The raw
data being used here comes out of the `pyvideo-data`_ project.


.. |travis| image:: https://travis-ci.org/pytube/pytube.svg?branch=master
    :target: https://travis-ci.org/pytube/pytube

.. _`pyvideo-data`: https://github.com/pyvideo/pyvideo-data


Development setup
=================

Setting up a development environment is as simple as four easy steps.

1. Clone repo
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

  $ pip install -r requirements-dev.txt

Next, create the content directory. This is the directory that contains the reST
files that Pelican will render into the HTML site. From the root of the repo,
run the following command::

  $ make content

Finally, you'll be able to generate the HTML site. From the root of the repo,
run the following command::

  $ make html

To view the site, run the following command::

  $ make serve

This will start development server on port 8000. Goto browser and open
http://localhost:8000 to view your local version of pytube.org!


Want to help?
=============

We'd love the help! All feature ideas and bugs-to-be-fixed are listed in the
`issues <https://github.com/pytube/pytube/issues>`_ associated with this repo. Please check there for ideas on
how to contribute. Thanks!

If you want to contribute new media, please check the `pyvideo-data`_ project
and its `contribution docs`_.


Found an issue?
===============

If you've found an issue with the site or something that could be done better,
please open an issue_ on Github.

.. _`issue`: https://github.com/pytube/pytube/issues
.. _`contribution docs`: https://github.com/pyvideo/pyvideo-data/blob/master/CONTRIBUTING.rst
