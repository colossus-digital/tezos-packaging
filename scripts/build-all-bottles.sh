#! /usr/bin/env bash
# shellcheck shell=bash

# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

set -euo pipefail

# we don't bottle meta-formulas that contain only services
formulae=("tezos-accuser-013-PtJakart" "tezos-accuser-014-PtKathma" "tezos-admin-client" "tezos-baker-013-PtJakart" "tezos-baker-014-PtKathma" "tezos-client" "tezos-codec" "tezos-node" "tezos-sandbox" "tezos-signer")

for f in "${formulae[@]}"; do
  # check if the formula doesn't already have a bottle in its respective release
  if echo "$f"; then
    # build a bottle
    if ./scripts/build-one-bottle.sh "$f"; then
      ./scripts/build-one-bottle.sh "aaa-$f" ||
        echo "Bottle for $f couldn't be uploaded to release."
    else
      >&2 echo "Bottle for $f couldn't be built."
    fi
  fi
done
