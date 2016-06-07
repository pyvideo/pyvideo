PY?=python3
PELICAN?=pelican
PELICANOPTS=

BASEDIR=$(CURDIR)
INPUTDIR=$(BASEDIR)/content
OUTPUTDIR=$(BASEDIR)/output
DATADIR=$(BASEDIR)/data
CONFFILE=$(BASEDIR)/pelicanconf.py
PUBLISHCONF=$(BASEDIR)/publishconf.py

GITHUB_PAGES_REPO=git@github.com:pytube/pytube.github.io.git
PREVIEW_GITHUB_PAGES_REPO=git@github.com:pytube-preview/pytube-preview.github.io.git

DEBUG ?= 0
ifeq ($(DEBUG), 1)
	PELICANOPTS += -D
endif

RELATIVE ?= 0
ifeq ($(RELATIVE), 1)
	PELICANOPTS += --relative-urls
endif

CHROMEDRIVER := $(shell which chromedriver)

help:
	@echo 'Makefile for a pelican Web site                                           '
	@echo '                                                                          '
	@echo 'Usage:                                                                    '
	@echo '   make html                           (re)generate the web site          '
	@echo '   make clean                          remove the generated files         '
	@echo '   make regenerate                     regenerate files upon modification '
	@echo '   make publish                        generate using production settings '
	@echo '   make serve [PORT=8000]              serve site at http://localhost:8000'
	@echo '   make devserver [PORT=8000]          start/restart develop_server.sh    '
	@echo '   make stopserver                     stop local server                  '
	@echo '   make github                         upload the web site via gh-pages   '
	@echo '   make deploy                         upload the web site to production  '
	@echo '   make test                           run the accessibility tests        '
	@echo '                                                                          '
	@echo 'Set the DEBUG variable to 1 to enable debugging, e.g. make DEBUG=1 html   '
	@echo 'Set the RELATIVE variable to 1 to enable relative urls                    '
	@echo '                                                                          '

link-data:
	ln -Ffsn $(DATADIR) $(INPUTDIR)/conferences

html: link-data
	$(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)

publish: link-data
	$(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(PUBLISHCONF) $(PELICANOPTS)

production_push:
	cd $(OUTPUTDIR) && git init && git add .
	cd $(OUTPUTDIR) && git commit -m "Initial commit"
	cd $(OUTPUTDIR) && git remote add origin $(GITHUB_PAGES_REPO)
	cd $(OUTPUTDIR) && git push origin master --force
	echo "Upload complete"

deploy: publish production_push

preview_push:
	cd $(OUTPUTDIR) && echo "preview.pytube.org" > CNAME
	cd $(OUTPUTDIR) && git init && git add .
	cd $(OUTPUTDIR) && git commit -m "Initial commit"
	cd $(OUTPUTDIR) && git remote add origin $(PREVIEW_GITHUB_PAGES_REPO)
	cd $(OUTPUTDIR) && git push origin master --force
	echo "Upload complete"

deploy-preview: html preview_push

clean:
	[ ! -d $(OUTPUTDIR) ] || rm -rf $(OUTPUTDIR)

regenerate: link-data
	$(PELICAN) -r $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)

serve:
ifdef PORT
	cd $(OUTPUTDIR) && $(PY) -m pelican.server $(PORT)
else
	cd $(OUTPUTDIR) && $(PY) -m pelican.server
endif

devserver: link-data
ifdef PORT
	$(BASEDIR)/develop_server.sh restart $(PORT)
else
	$(BASEDIR)/develop_server.sh restart
endif

stopserver:
	$(BASEDIR)/develop_server.sh stop
	@echo 'Stopped Pelican and SimpleHTTPServer processes running in background.'

test:
ifndef CHROMEDRIVER
	$(error "Could not find chromedriver, download from https://sites.google.com/a/chromium.org/chromedriver/downloads and add it to a directory in your PATH")
endif
	pip install -r requirements/tests.txt
	cd $(BASEDIR) && SELENIUM_BROWSER=chrome py.test tests/test_a11y.py

.PHONY: html help clean purge deploy production_push preview_push deploy-preview regenerate serve devserver publish github

