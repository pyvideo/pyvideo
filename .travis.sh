#! /bin/bash

# Set global configs for author of repo
git config --global user.email "paul.logston@gmail.com"
git config --global user.name "Paul Logston"
# Set location of GIT_SSH key relative to inside output/
export GIT_SSH=../.ssh/ssh-git.sh

if [[ "${TRAVIS_PULL_REQUEST}" == "false" ]]; then
    echo "Building and deploying to production";
    # Set correct permissions on deploy key
    chmod 600 keys/production
    # Set location of deploy key relative to inside output/
    export DEPLOY_KEY=../keys/production
    make deploy
else
    echo "Building PR ${TRAVIS_PULL_REQUEST}";
    # Set correct permissions on deploy key
    chmod 600 keys/preview
    # Set location of deploy key relative to inside output/
    export DEPLOY_KEY=../keys/preview
    make deploy-preview
fi

