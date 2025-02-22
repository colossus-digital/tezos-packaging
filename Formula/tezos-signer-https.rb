# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosSignerHttps < Formula
  url "file:///dev/null"
  version "v14.0-1"

  depends_on "tezos-signer"

  desc "Meta formula that provides backround tezos-signer service that runs over https"

  def install
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      signer="/usr/local/bin/tezos-signer"

      if [[ -n $PIDFILE ]]; then
        pid_file_args=("--pid-file" "$PIDFILE")
      else
        pid_file_args=()
      fi

      if [[ -n $MAGIC_BYTES ]]; then
        magic_bytes_args=("--magic-bytes" "$MAGIC_BYTES")
      else
        magic_bytes_args=()
      fi

      if [[ -n $CHECK_HIGH_WATERMARK ]]; then
        check_high_watermark_args=("--check-high-watermark")
      else
        check_high_watermark_args=()
      fi

      "$signer" -d "$DATA_DIR" launch https signer "$CERT_PATH" "$KEY_PATH" --address "$ADDRESS" --port "$PORT" \
        ${pid_file_args[@]+"${pid_file_args[@]}"} ${magic_bytes_args[@]+"${magic_bytes_args[@]}"} \
        ${check_high_watermark_args[@]+"${check_high_watermark_args[@]}"} "$@"
    EOS
    File.write("tezos-signer-https-start", startup_contents)
    bin.install "tezos-signer-https-start"
  end
  def plist
    <<~EOS
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
      "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
      <plist version="1.0">
        <dict>
          <key>Label</key>
          <string>#{plist_name}</string>
          <key>Program</key>
          <string>#{opt_bin}/tezos-signer-https-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>ADDRESS</key>
              <string>127.0.0.1</string>
              <key>PORT</key>
              <string>8080</string>
              <key>CERT_PATH</key>
              <string></string>
              <key>KEY_PATH</key>
              <string></string>
              <key>DATA_DIR</key>
              <string>#{var}/lib/tezos/signer-https</string>
              <key>PIDFILE</key>
              <string></string>
              <key>MAGIC_BYTES</key>
              <string></string>
              <key>CHECK_HIGH_WATERMARK</key>
              <string></string>
          </dict>
          <key>RunAtLoad</key><true/>
          <key>StandardOutPath</key>
          <string>#{var}/log/#{name}.log</string>
          <key>StandardErrorPath</key>
          <string>#{var}/log/#{name}.log</string>
        </dict>
      </plist>
    EOS
  end
  def post_install
    mkdir "#{var}/lib/tezos/signer-https"
  end
end
