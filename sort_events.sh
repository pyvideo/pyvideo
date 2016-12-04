#!/bin/bash
# This script generates a list of event directories in the order
# they were merged into the DATADIR. Thanks @Daniel-at-github!

DATADIR=data

cd $DATADIR
for EVENT_FILE in */"category.json"
do
  echo -n "$EVENT_FILE "
  git log --diff-filter=A --follow --format=%ai -1 -- "$EVENT_FILE"
done \
| sort -k2,2r -k1,1r \
| sed -e 's?/category.json??; s/ .*$//;'

