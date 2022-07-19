# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

from psutil import process_iter
from pystemd.systemd1 import Unit, Manager
from time import sleep
from typing import List

from tezos_baking.wizard_structure import (
    get_key_address,
    proc_call,
    replace_in_service_config,
    url_is_reachable,
)

import contextlib
import re


@contextlib.contextmanager
def unit(service_name: str):
    unit = Unit(service_name.encode(), _autoload=True)
    unit.Unit.Start("replace")
    while unit.Unit.ActiveState == b"activating":
        sleep(1)
    try:
        yield unit
    finally:
        unit.Unit.Stop("replace")
        while unit.Unit.ActiveState not in [b"failed", b"inactive"]:
            sleep(1)


def replace_service_environment_variable(service_name: Unit, key: str, value: str):
    def find_service_filepath(service_name: str):
        with Manager(_autoload=True) as m:
            return m.Manager.ListUnitFilesByPatterns(
                ["enabled", "disabled"], [f"*{service_name}"]
            )[0][0]

    service_filepath = find_service_filepath(service_name)
    with open(service_filepath, "r") as f:
        config_contents = f.read()
    old = re.search(f'Environment="{key}=.*"', config_contents)
    if old is None:
        return None
    else:
        new = f'Environment="{key}={value}"'
        proc_call(f"sudo sed -i 's|{old.group(0)}|{new}|' {service_filepath.decode()}")
        with Manager(_autoload=True) as m:
            return m.Manager.Reload()

def retry(action, name: str, retry_count: int = 10) -> bool:
    if action(name):
        return True
    elif retry_count == 0:
        return False
    else:
        sleep(1)
        return retry(action, name, retry_count - 1)

def check_running_process(process_name: str) -> bool:
    return retry(lambda x: x in [proc.name() for proc in process_iter()], process_name)


def check_active_service(service_name: str) -> bool:
    return retry(lambda x: Unit(x.encode(), _autoload=True).Unit.ActiveState == b"active", service_name)


def node_service_test(network: str, rpc_endpoint="http://localhost:8732"):
    with unit(f"tezos-node-{network}.service") as _:
        # checking that service started 'tezos-node' process
        assert check_running_process("tezos-node")
        # checking that node is able to respond on RPC requests
        assert retry(url_is_reachable, f"{rpc_endpoint}/config")


def baking_service_test(network: str, protocols: List[str], baker_alias="baker"):
    # Generate baker key
    proc_call(f"sudo -u tezos tezos-client gen keys {baker_alias} --force")
    with unit(f"tezos-baking-{network}.service") as _:
        assert check_active_service(f"tezos-node-{network}.service")
        assert check_running_process("tezos-node")
        for protocol in protocols:
            assert check_active_service(
                f"tezos-baker-{protocol.lower()}@{network}.service"
            )
            assert check_running_process(f"tezos-baker-{protocol}")


signer_unix_socket = "/tmp/signer-socket"

signer_backends = {
    "http": "http://localhost:8080/",
    "tcp": "tcp://localhost:8000/",
    "unix": f"unix:{signer_unix_socket}?pkh=",
}


def signer_service_test(service_type: str):
    with unit(f"tezos-signer-{service_type}.service") as _:
        assert check_running_process(f"tezos-signer")
        proc_call(
            "sudo -u tezos tezos-signer -d /var/lib/tezos/signer gen keys remote --force"
        )
        remote_key = get_key_address("-d /var/lib/tezos/signer", "remote")[1]
        proc_call(
            f"tezos-client import secret key remote-signer {signer_backends[service_type]}{remote_key} --force"
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


def test_unix_signer_service():
    replace_service_environment_variable(
        "tezos-signer-unix.service", "SOCKET", signer_unix_socket
    )
    signer_service_test("unix")


def test_standalone_baker_service():
    replace_service_environment_variable(
        "tezos-baker-013-ptjakart.service",
        "NODE_DATA_DIR",
        "/var/lib/tezos/node-jakartanet",
    )
    with unit(f"tezos-node-jakartanet.service") as _:
        with unit(f"tezos-baker-013-ptjakart.service") as _:
            assert check_running_process(f"tezos-baker-013-PtJakart")


def test_nondefault_node_rpc_endpoint():
    rpc_addr = "127.0.0.1:8735"
    replace_service_environment_variable(
        "tezos-node-jakartanet.service", "NODE_RPC_ADDR", rpc_addr
    )
    try:
        node_service_test("jakartanet", f"http://{rpc_addr}")
    finally:
        replace_service_environment_variable(
            "tezos-node-jakartanet.service", "NODE_RPC_ADDR", "127.0.0.1:8732"
        )


def test_nondefault_baking_config():
    replace_in_service_config(
        "/etc/default/tezos-baking-jakartanet", "BAKER_ADDRESS_ALIAS", "another_baker"
    )
    replace_in_service_config(
        "/etc/default/tezos-baking-jakartanet", "LIQUIDITY_BAKING_TOGGLE_VOTE", "on"
    )
    baking_service_test("jakartanet", ["013-PtJakart"], "another_baker")
