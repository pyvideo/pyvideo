#!/bin/sh
if [ -z "$PKEY" ]; then
    # if PKEY is not specified, run ssh using default keyfile
    ssh "$@"
else
    ssh -i "$PKEY" "$@"
fi

