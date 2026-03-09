#!/bin/bash

if [[ $# -ne 2 ]]; then
	echo "Usage: $0 hexdump_file output_file"
	exit 1
fi

if [[ ! -f "$1" ]]; then
	echo "$1 doesn't exist"
	exit 1
fi

if [[ -f "$2" ]]; then
	rm $2
fi

cat $1 | grep -oP '(?<= )[[:xdigit:]]{2}(?= )' | tr '\n' ' ' | xxd -r -p > $2
