# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: LicenseRef-MIT-TQ

{ writeTextDir, runCommand, buildEnv, binaries, arm-binaries, commonMeta, replaceStrings }:
let
  release-binaries = import ./nix/build/release-binaries.nix;
  version = replaceStrings ["refs/tags/"] [""] commonMeta.branchName;
  release-notes = writeTextDir "release-notes.md" ''
    This release contains assets based on [${version} release](https://gitlab.com/tezos/tezos/tree/${version}).

    Binaries that target arm64 architecture has `-arm64` suffix in the name.
    Other binaries target x86_64.

    Descriptions for binaries included in this release:
    ${builtins.concatStringsSep "\n"
    (map ({ name, description, ... }: "- `${name}`: ${description}")
      release-binaries)}
  '';
  releaseNoTarball = buildEnv {
    name = "tezos-release-no-tarball";
    paths = [ "${binaries}" "${arm-binaries}" LICENSE release-notes ];
  };
  tarballName = "binaries-${commonMeta.version}-${commonMeta.release}.tar.gz";
  armTarballName = "binaries-${commonMeta.version}-${commonMeta.release}-arm64.tar.gz";
  binariesTarball = runCommand "binaries-tarball" { }
    "mkdir $out; tar --owner=serokell:1000 --mode='u+rwX' -czhf $out/${tarballName} -C ${binaries} .";
  armBinariesTarball = runCommand "binaries-tarball" { }
    "mkdir $out; tar --owner=serokell:1000 --mode='u+rwX' -czhf $out/${armTarballName} -C ${arm-binaries} .";
  LICENSE = writeTextDir "LICENSE" (builtins.readFile commonMeta.licenseFile);
in buildEnv {
  name = "tezos-release";
  paths = [ releaseNoTarball binariesTarball armBinariesTarball ];
}
