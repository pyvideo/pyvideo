#! /bin/bash

if [[ "${TRAVIS_PULL_REQUEST}" == "false" ]]; then
    git config --global user.email "code@logston.me"
    git config --global user.name "Paul Logston"
    export GIT_SSH=bin/ssh-git.sh
    export PKEY=.travis.priv
    make content && make deploy
else
    make content && make html
fi

