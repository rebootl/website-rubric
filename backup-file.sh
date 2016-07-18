#!/bin/bash
#
# make a backup copy of file $1, inplace
#
# file --> file_YYYY-MM-DD_HH:MM.<suffix $2>

FILE="$1"

shift

if [ -z "$1" ]; then
    _SUFF=""
else
    _SUFF=."$1"
fi

DATE=$(date "+%F_%R")

cp "$FILE" "${FILE}_${DATE}${_SUFF}"
