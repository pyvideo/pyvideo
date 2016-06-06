#! /bin/bash

# Set global configs for author of repo
git config --global user.email "code@logston.me"
git config --global user.name "Paul Logston"
# Set location of GIT_SSH key relative to inside output/
export GIT_SSH=../.ssh/ssh-git.sh

# Set correct permissions on deploy key
chmod 600 .ssh/travis
# Set location of deploy key relative to inside output/
export DEPLOY_KEY=../.ssh/travis

if [[ "${TRAVIS_PULL_REQUEST}" == "false" ]]; then
    echo "Building and deploying to production";
    # Set correct permissions on deploy key
    chmod 600 .ssh/travis
    # Set location of deploy key relative to inside output/
    export DEPLOY_KEY=../.ssh/travis
    make deploy
else
    echo "Building PR ${TRAVIS_PULL_REQUEST}";
    # Set correct permissions on deploy key
    chmod 600 .ssh/preview
    # Set location of deploy key relative to inside output/
    export DEPLOY_KEY=../.ssh/preview
    make deploy-preview
fi

