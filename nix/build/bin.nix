# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ runCommand, upx }:
pkg:
runCommand "${pkg.name}-bin" { } ''
  mkdir -p $out/bin
  shopt -s extglob
  cp ${pkg}/bin/!(*.sh) $out/bin
  chmod 700 -R $out
  ${upx}/bin/upx $out/bin/*
''
