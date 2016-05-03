pytube
######

|travis|

A repository of Python relate media. http://PyTube.org

.. |travis| image:: https://travis-ci.org/pytube/pytube.svg?branch=master
    :target: https://travis-ci.org/pytube/pytube


Setup
------

It is recommended to install all the requirements inside virtualenv_, use virtualenvwrapper_ to manage virtualenvs.

.. _virtualenv: https://virtualenv.pypa.io/en/latest/
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.org/en/latest/

.. code:: sh

          pip install -r requirements-dev.txt
          make serve

This will start development server on port 8000. Goto browser and open http://localhost:8000 to view development server.



TODO
----

- Ability to mark media as draft (private)
- Ability to mark media as approved (JS trigger PR for change in data)
- Ability to post title slide before video is up (draft mode)
- Tweet URLs automatically once video goes live

- Style site
- Convert all "summary" values in JSON data to be rST parsible
- Implement search (google search is fine)
- Link checker (script to check that all links in site are 200 OK)
- TravisCI integration (build site on push to master or merger of PR)
- A sweet 404 page
