# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

from asyncio import subprocess
from psutil import process_iter
from pystemd.systemd1 import Unit
from time import sleep
from typing import List

from tezos_baking.wizard_structure import (
    get_key_address,
    proc_call,
    url_is_reachable,
)

import contextlib
import subprocess


@contextlib.contextmanager
def unit(service_name: str):
    unit = Unit(service_name.encode(), _autoload=True)
    unit.Unit.Start("replace")
    while unit.Unit.ActiveState == b"activating":
        sleep(1)
    if unit.Unit.ActiveState != b"active":
        raise Exception(f"{service_name} failed to start")
    # Some delay for changes to propagate
    sleep(5)
    try:
        yield unit
    finally:
        unit.Unit.Stop("replace")
        while unit.Unit.ActiveState not in [b"failed", b"inactive"]:
            sleep(1)
        # Some delay for changes to propagate
        sleep(5)


def check_running_process(process_name: str) -> bool:
    return process_name in [proc.name() for proc in process_iter()]


def check_active_service(service_name: str) -> bool:
    unit = Unit(service_name.encode(), _autoload=True)
    return unit.Unit.ActiveState == b"active"


def node_service_test(network: str):
    with unit(f"tezos-node-{network}.service") as _:
        # checking that service started 'tezos-node' process
        assert check_running_process("tezos-node")
        # checking that node is able to respond on RPC requests
        assert url_is_reachable("http://localhost:8732/config")


def baking_service_test(network: str, protocols: List[str]):
    # Generate baker key
    subprocess.run(
        ["sudo", "-u", "tezos", "tezos-client", "gen", "keys", "baker", "--force"]
    )
    with unit(f"tezos-baking-{network}.service") as _:
        assert check_active_service(f"tezos-node-{network}.service")
        assert check_running_process("tezos-node")
        for protocol in protocols:
            assert check_active_service(
                f"tezos-baker-{protocol.lower()}@{network}.service"
            )
            assert check_running_process(f"tezos-baker-{protocol}")


signer_backends = {
    "http": "http://localhost:8080",
    "tcp": "tcp://localhost:8000",
}


def signer_service_test(service_type: str):
    with unit(f"tezos-signer-{service_type}.service") as _:
        assert check_running_process(f"tezos-signer")
        proc_call(
            "sudo -u tezos tezos-signer -d /var/lib/tezos/signer gen keys remote --force"
        )
        remote_key = get_key_address("-d /var/lib/tezos/signer", "remote")[1]
        proc_call(
            f"tezos-client import secret key remote-signer {signer_backends[service_type]}/{remote_key} --force"
        )
        proc_call("tezos-client --mode mockup sign bytes 0x1234 for remote-signer")


def test_node_mainnet_service():
    node_service_test("mainnet")


def test_node_jakartanet_service():
    node_service_test("jakartanet")


def test_baking_jakartanet_service():
    baking_service_test("jakartanet", ["013-PtJakart"])


def test_baking_mainnet_service():
    baking_service_test("mainnet", ["013-PtJakart"])


def test_http_signer_service():
    signer_service_test("http")


def test_tcp_signer_service():
    signer_service_test("tcp")


def test_standalone_accuser_service():
    with unit(f"tezos-node-jakartanet.service") as _:
        with unit(f"tezos-accuser-013-ptjakart.service") as _:
            assert check_running_process(f"tezos-accuser-013-PtJakart")
