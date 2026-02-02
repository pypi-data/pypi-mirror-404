import json
import os
from pathlib import Path
import requests

from typing import Optional, cast

from .exceptions import AgentBootstrapError

from zscams.agent.src.support.configuration import (
    CONFIG_PATH,
    ROOT_PATH,
    get_config,
    override_config,
)
from zscams.agent.src.support.yaml import resolve_placeholders, assert_no_placeholders_left
from zscams.agent.src.support.mac import get_mac_address
from zscams.agent.src.support.filesystem import resolve_path, ensure_dir, is_file_exists
from zscams.agent.src.support.network import get_local_hostname, get_local_ip_address
from zscams.agent.src.support.openssl import (
    generate_csr_from_private_key,
    generate_private_key,
)
from zscams.agent.src.support.logger import get_logger


class BackendClient:
    """Client to interact with the backend service."""

    MACHINE_INFO_FILE_NAME = "machine_info.json"

    def __init__(self):
        config = get_config()
        self.services_config = config.get("services", [])
        self.backend_config = config.get("backend", {})
        self.bootstrap_info = config.get("bootstrap_info", {})
        self.remote_config = config.get("remote", {})
        self.url = self.backend_config.get("base_url")
        self.session = requests.session()
        self.agent_id = get_mac_address()
        self.logger = get_logger("backend_client")

        self.__machine_cache_path = Path(
            os.path.join(
                ROOT_PATH.parent,
                self.backend_config.get("cache_dir"),
                self.MACHINE_INFO_FILE_NAME,
            )
        )

    def bootstrap(self, equipment_name: str, enforced_id: Optional[str] = None):
        """Bootstrap the agent with the backend."""

        if not self.is_authenticated():
            self.logger.error("Couldn't authenticate")
            raise AgentBootstrapError(
                "Client is not authenticated to bootstrap. Please login first."
            )

        self.logger.info("bootstrapping agent ID %s", self.agent_id)

        csr_info = self.bootstrap_info.get("csr", {})
        remote_configs = get_config().get("remote", {})

        private_key_path = cast(
            str,
            resolve_path(
                remote_configs.get("client_key"), os.path.dirname(CONFIG_PATH)
            ),
        )

        self.logger.info("Generating the private key...")
        private_key_content = generate_private_key(private_key_path)

        self.logger.info("Generated the private key at %s", private_key_path)

        common_name = (
            f"{equipment_name}.orangecyberdefense.com"
            if equipment_name
            else csr_info.get("default_common_name")
        )

        ip = get_local_ip_address()
        csr = generate_csr_from_private_key(
            private_key_content,
            csr_info.get("country"),
            csr_info.get("state"),
            csr_info.get("locality"),
            csr_info.get("organization"),
            common_name,
        )

        payload = {
            "private_ip": ip,
            "lan_ip": ip,
            "hostname": get_local_hostname(),
            "equipment_name": equipment_name,
            "csr": csr,
            "enforced_id": enforced_id,
            "services": [service.get("name") for service in self.services_config if service.get("custom_port_name", None)],
            "blacklist_ports": self.bootstrap_info.get("blacklist_ports", []),
            "cert_issuer": self.bootstrap_info.get("cert_issuer", None),
        }

        self.logger.debug(
            "bootstrapping the agent with payload %s", json.dumps(payload, indent=2)
        )

        res = self._post(f"agent-bootstrap/{self.agent_id}", payload)
        res_json = res.json()

        if not res.ok or res_json.get("success") is False:
            message = (
                res_json.get("message", None)
                or res_json.get("error", None)
                or res_json.get("errors", None)
                or "Unknown error"
            )
            raise AgentBootstrapError(
                f"Bootstrapping failed on backend request: {message}"
            )

        self.logger.info("Signed the cert")
        self.logger.debug("Signed cert response: %s", json.dumps(res_json, indent=2))

        customer_machine = res_json.get("response", {})
        ca_chain: list[str] = customer_machine.get("ca_chain", [])
        signed_cert: str = customer_machine.get("signed_certificate", [])
        self._write_certificates(ca_chain, signed_cert)

        # To cache the machine info
        self.get_machine_info(ignore_cache=True)

        self.__override_config_services_ports(customer_machine.get("services", []))

        return customer_machine

    def get_machine_info(self, ignore_cache: bool = False):
        """Get machine information from the backend."""

        if not ignore_cache and is_file_exists(self.__machine_cache_path, self.logger):
            return self.__load_machine_info_from_cache()

        res = self._get(f"customers-machines/machine-id/{self.agent_id}")
        res.raise_for_status()

        machine_info = res.json().get("response", {})
        self.logger.debug(
            "Fetched machine info: %s", json.dumps(machine_info, indent=2)
        )
        self.__cache_machine_info(machine_info)
        return machine_info

    def __load_machine_info_from_cache(self):
        """Cache machine information to a local file."""

        self.logger.info(
            "Loading machine info from cache at %s", self.__machine_cache_path
        )
        with open(self.__machine_cache_path, "r", encoding="utf-8") as cache_file:
            return json.load(cache_file)

    def __cache_machine_info(self, machine_info: dict):
        """Cache machine information to a local file."""

        ensure_dir(str(self.__machine_cache_path.parent.absolute()))
        self.logger.info("Caching machine info to %s", self.__machine_cache_path)
        with open(self.__machine_cache_path, "w", encoding="utf-8") as cache_file:
            json.dump(machine_info, cache_file, indent=2)

    def _write_certificates(self, ca_chain: list[str], cert: str):
        if cert:
            cert_path = os.path.join(ROOT_PATH, self.remote_config.get("client_cert"))

            self.logger.info("Writing signed certificate to %s", cert_path)
            with open(cert_path, "w", encoding="utf-8") as cert_file:
                cert_file.write(cert)

        if ca_chain:
            ca_chain_path = os.path.join(ROOT_PATH, self.remote_config.get("ca_chain"))

            self.logger.info("Writing CA chain to %s", ca_chain_path)
            with open(ca_chain_path, "w", encoding="utf-8") as ca_chain_file:
                ca_chain_file.write("\n\n".join(ca_chain))

    def is_bootstrapped(self) -> bool:
        """Check if the agent is bootstrapped."""

        is_bootstrapped_res = self._get(
            f"agent-bootstrap/{self.agent_id}/is-bootstrapped"
        )
        is_bootstrapped_res.raise_for_status()

        return (
            is_bootstrapped_res.json().get("response", {}).get("is-bootstrapped", False)
        )

    def _get(self, path: str):
        """Perform a GET request to the backend."""

        return self.session.get(self.__prepare_path(path))

    def _post(self, path: str, body: dict):
        """Perform a POST request to the backend."""

        return self.session.post(self.__prepare_path(path), json=body)

    def _put(self, path: str, body: dict):
        """Perform a PUT request to the backend."""

        return self.session.put(self.__prepare_path(path), json=body)

    def _delete(self, path: str):
        """Perform a DELETE request to the backend."""

        return self.session.delete(self.__prepare_path(path))

    def login(self, username: str, totp: str):
        """Perform login to the backend using username and TOTP."""

        payload = {
            "username": username,
            "totp": totp,
            "client_id": "orchestrator-client",
            "grant_type": "password",
        }

        self.logger.info("Logging in to backend as %s", username)

        response = self.session.post(
            self.__prepare_path("authentication/temp/login"), json=payload
        )
        if not response.ok:
            self.logger.error(
                "Login failed with status code %d: %s",
                response.status_code,
                response.text,
            )
            response.raise_for_status()

        token = response.json().get("access_token")
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

        self.logger.info("Login successful")

        return response.json()

    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self.session.headers.get("Authorization") is not None

    def __prepare_path(self, path):
        return f"{self.url}/{path.lstrip('/')}"
            
    def __override_config_services_ports(self, cm_services: list[dict]):
        self.logger.debug("Overriding configuration services ports...")

        config = get_config()
        custom_ports = {}
        for cm_service in cm_services:
            for cfg_service_idx, cfg_service in enumerate(config.get("services", [])):
                if cm_service.get("name") == cfg_service.get("name"):

                    if not config["services"][cfg_service_idx]["params"]:
                        config["services"][cfg_service_idx]["params"] = {}

                    port_field_name = cfg_service.get("custom_port_name", None)
                    if port_field_name:
                        custom_ports[port_field_name] = cm_service.get("port")
                        config["services"][cfg_service_idx]["params"][port_field_name] = (
                            cm_service.get("port")
                        )
        resolve_placeholders(config, custom_ports)
        assert_no_placeholders_left(config)
        self.logger.debug("Done overriding the configurations")

        return override_config(config)


backend_client = BackendClient()
