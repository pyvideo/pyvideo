#! /bin/bash

if [[ "${TRAVIS_PULL_REQUEST}" == "false" ]]; then
    make deploy;
fi

