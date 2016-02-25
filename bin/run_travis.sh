#! /bin/bash

if [[ "${TRAVIS_PULL_REQUEST}" == "false" ]]; then
    # Set correct permissions on deploy key
    chmod 600 .ssh/travis
    # Set global configs for author of repo
    git config --global user.email "code@logston.me"
    git config --global user.name "Paul Logston"
    # Set location of GIT_SSH key relative to inside output/
    export GIT_SSH=../bin/ssh-git.sh
    # Set location of deploy key relative to inside output/
    export DEPLOY_KEY=../.ssh/travis
    make content && make deploy
else
    make content && make html
fi

