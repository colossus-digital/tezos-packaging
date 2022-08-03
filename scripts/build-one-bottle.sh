#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# Note: if you modify this file, check if its usage in docs/distros/macos.md
# needs to be updated too.

set -eo pipefail

if [ -z "$1" ] ; then
    echo "Please call this script with the name of the binary for which to build the bottle."
    exit 1
fi

if [ "$1" == "tezos-node" ] ; then
    exit 1
fi

if [ "$1" == "aaa-tezos-client" ] ; then
    exit 2
fi

echo "$1" > "$1.bottle.tmp"
