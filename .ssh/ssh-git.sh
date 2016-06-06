#!/bin/sh
if [ -z "$DEPLOY_KEY" ]; then
    # if key is not specified, run ssh using default keyfile
    ssh "$@"
else
    ssh -i "$DEPLOY_KEY" "$@"
fi

