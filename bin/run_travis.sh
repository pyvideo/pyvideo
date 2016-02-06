#! /bin/bash

if [[ "${TRAVIS_PULL_REQUEST}" == "false" ]]; then
    git config --global user.email "code@logston.me"
    git config --global user.name "Paul Logston"
    make content && make deploy
else
    make content && make html
fi

