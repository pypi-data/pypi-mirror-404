#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software
#   and associated documentation files (the "Software"), to deal in the Software without
#   restriction, including without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#   BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from typing import Literal
import logging
import io

from hyrrokkin.utils.type_hints import JsonType
from hyrrokkin.interfaces.topology_api import TopologyApi
from hyrrokkin.interfaces.topology_listener_api import TopologyListenerAPI


class TopologyService(TopologyListenerAPI):

    def __init__(self, topology: TopologyApi, send_fn, design_metadata_update_callback=None, download_url="", base_path=""):
        self.topology = topology
        self.package_urls = []
        for package_id in self.topology.get_schema().get_packages().keys():
            self.package_urls.append(f"{base_path}/package/{package_id}")
        self.send_fn = send_fn
        self.logger = logging.getLogger("TopologyService")
        self.client_services = {}
        self.node_statuses = {}
        self.configuration_statuses = {}
        self.node_execution_states = {}
        self.design_metadata_update_callback = design_metadata_update_callback
        self.download_url = download_url
        self.topology.attach_listener(self)

    def open_session(self, session_id, directory_url=None, user_id=None):
        self.topology.open_session(session_id)
        init_msg = {
            "action": "init",
            "topology": self.topology.serialise(),
            "download_url": self.download_url,
            "is_paused": self.topology.is_paused(),
            "package_urls": self.package_urls
        }
        if directory_url is not None:
            init_msg["directory_url"] = directory_url
        self.send(init_msg, to_session_id=session_id)
        for msg in self.node_statuses.values():
            self.send(msg, to_session_id=session_id)
        for msg in self.configuration_statuses.values():
            self.send(msg, to_session_id=session_id)
        for msg in self.node_execution_states.values():
            self.send(msg, to_session_id=session_id)

    def close_session(self, session_id):
        self.topology.close_session(session_id)

    def send(self, *msg_parts, to_session_id=None, except_session_id=None):
        self.send_fn(*msg_parts, to_session_id=to_session_id, except_session_id=except_session_id)

    def handle_message(self, *msg_parts, from_session_id=None):
        msg = msg_parts[0]
        content = msg_parts[1:]
        action = msg["action"]
        match action:
            case "request_add_node":
                self.request_add_node(msg, *content)
            case "request_update_node_metadata":
                self.request_update_node_metadata(msg)
            case "request_add_link":
                self.request_add_link(msg)
            case "request_remove_node":
                self.request_remove_node(msg)
            case "request_remove_link":
                self.request_remove_link(msg)
            case "request_clear":
                self.request_clear(msg)
            case "request_update_design_metadata":
                self.request_update_design_metadata(msg)
            case "request_pause_execution":
                self.request_pause(msg)
            case "request_resume_execution":
                self.request_resume(msg)
            case "request_restart_execution":
                self.request_restart(msg)
            case "open_client":
                self.open_client(msg, from_session_id)
            case "close_client":
                self.close_client(msg, from_session_id)
            case "run_task":
                self.run_task(msg, content, from_session_id)
            case "upload_topology":
                self.load_from(content[0])
            case "client_message":
                client_id = msg["client_id"]
                target_type = msg["target_type"]
                target_id = msg["target_id"]
                key = (target_type, target_id, from_session_id, client_id)
                if key in self.client_services:
                    self.client_services[key].send_message(*content)
            case _:
                self.logger.warning(f"Unhandled action {action}")

    def load_from(self, from_bytes):
        f = io.BytesIO(from_bytes)
        self.topology.pause()
        (loaded_node_ids, loaded_link_ids, node_renamings) = self.topology.load(f)
        self.topology.resume()

    def request_add_node(self, msg, *content):
        node_id = msg.get("node_id", None)
        node_type = msg["node_type"]
        metadata = msg["metadata"]
        properties = msg.get("properties", {})
        data_keys = msg.get("data_keys", [])
        ref = msg.get("ref", None)
        data = {}
        for idx in range(len(data_keys)):
            data[data_keys[idx]] = content[idx]
        copy_from_node_id = msg["copy_from_node_id"]
        self.topology.add_node(node_id, node_type, metadata=metadata, properties=properties, data=data,
                               copy_from_node_id=copy_from_node_id, ref=ref)

    def request_update_node_metadata(self, msg):
        node_id = msg["node_id"]
        metadata = msg["metadata"]
        self.topology.update_node_metadata(node_id, metadata, ref=msg.get("ref", None))

    def request_add_link(self, msg):
        link_id = msg.get("link_id", None)
        from_node_id = msg["from_node_id"]
        from_port_name = msg["from_port_name"]
        to_node_id = msg["to_node_id"]
        to_port_name = msg["to_port_name"]
        self.topology.add_link(link_id, from_node_id, from_port_name, to_node_id, to_port_name,
                               ref=msg.get("ref", None))

    def request_remove_node(self, msg):

        node_id = msg["node_id"]

        # cascade to any links connected to the node to remove
        link_ids = self.topology.get_link_ids_for_node(node_id)
        for link_id in link_ids:
            self.request_remove_link({"link_id": link_id})

        self.topology.remove_node(node_id, ref=msg.get("ref", None))

    def request_remove_link(self, msg):
        link_id = msg["link_id"]
        self.topology.remove_link(link_id, ref=msg.get("ref", None))

    def request_clear(self, msg):
        self.topology.clear(ref=msg.get("ref", None))

    def request_pause(self, msg):
        self.topology.pause(ref=msg.get("ref", None))

    def request_resume(self, msg):
        self.topology.resume(ref=msg.get("ref", None))

    def request_restart(self, msg):
        self.topology.pause(ref=msg.get("ref", None))
        self.topology.restart(ref=msg.get("ref", None))

    def request_update_design_metadata(self, msg):
        metadata = msg["metadata"]
        self.topology.set_metadata(metadata, )

    def open_client(self, msg, from_session_id):
        client_id = msg["client_id"]
        target_type = msg["target_type"]
        target_id = msg["target_id"]
        client_options = msg["client_options"]
        key = (target_type, target_id, from_session_id, client_id)
        if target_type == "node":
            self.client_services[key] = self.open_node_client(target_id, from_session_id, client_id, client_options)
        elif target_type == "configuration":
            self.client_services[key] = self.open_configuration_client(target_id, from_session_id, client_id,
                                                                                  client_options)
        else:
            self.logger.warning(f"Unable to open client for target_type={target_type}")
            return True
        self.client_services[key].set_message_handler(
            lambda *msg: self.forward_message_to_client(msg, target_type, target_id, client_id, from_session_id))

    def open_node_client(self, node_id, from_session_id, client_id, client_options):
        return self.topology.attach_node_client(node_id, from_session_id, client_id, client_options)

    def open_configuration_client(self, package_id, from_session_id, client_id, client_options):
        return self.topology.attach_configuration_client(package_id, from_session_id, client_id, client_options)

    def forward_message_to_client(self, msg, target_type, target_id, client_id, session_id):
        header = {
            "action": "client_message",
            "client_id": client_id,
            "target_type": target_type,
            "target_id": target_id
        }
        msg_parts = [header] + list(msg)
        self.send(*msg_parts, to_session_id=session_id)

    def close_client(self, msg, from_session_id):
        client_id = msg["client_id"]
        target_type = msg["target_type"]
        target_id = msg["target_id"]
        if target_type == "node":
            self.close_node_client(target_id, from_session_id, client_id)
        else:
            self.close_configuration_client(target_id, from_session_id, client_id)

    def close_node_client(self, node_id, from_session_id, client_id):
        key = ("node", node_id, from_session_id, client_id)
        if key in self.client_services:
            self.client_services[key].close()
            del self.client_services[key]

    def close_configuration_client(self, package_id, from_session_id, client_id):
        key = ("configuration", package_id, from_session_id, client_id)
        if key in self.client_services:
            self.client_services[key].close()
            del self.client_services[key]

    def set_input_value(self, msg, content, from_session_id):
        node_id = msg["node_id"]
        input_port_name = msg["input_port_name"]
        input_value = content[0]
        self.topology.inject_input_value(node_id, input_port_name, input_value)

    def run_task(self, msg, content, from_session_id):
        ref = msg["ref"]
        input_ports = msg["input_ports"]
        task_name = msg["task_name"]
        input_port_values = {}
        for (name, descr) in input_ports.items():
            if "index" in descr:
                input_port_values[name] = content[descr["index"]]
            else:
                values = []
                for idx in range(descr["start_index"], descr["end_index"]):
                    values.append(content[idx])
                input_port_values[name] = values
        output_ports = msg["output_ports"]
        (output_values, failures) = self.topology.run_task(task_name, input_port_values, output_ports)
        self.ran_task(task_name, ref, output_values, failures, from_session_id)

    def ran_task(self, task_name, ref, output_values, failures, session_id):
        output_ports = []
        value_list = []
        for output_port in output_values:
            output_ports.append(output_port)
            value_list.append(output_values[output_port])

        header = {
            "action": "ran_task",
            "task_name": task_name,
            "output_ports": output_ports,
            "failures": failures
        }
        if ref:
            header["ref"] = ref
        msg_parts = [header] + value_list
        self.send(*msg_parts, to_session_id=session_id)

    def get_localisation_bundle_for_node(self, node_id, for_language=""):
        (package_id, _) = self.topology.get_type_for_node(node_id)
        return self.topology.get_localisation_bundle(package_id, for_language=for_language)

    def get_localisation_bundle_for_package(self, package_id, for_language=""):
        return self.topology.get_localisation_bundle(package_id, for_language=for_language)

    ####################################################################################################################
    # Listener API

    def status_event(self, target_type: Literal["node"] | Literal["configuration"],
                     target_id: str, msg: str,
                     status_code: Literal["error"] | Literal["warning"] | Literal["info"] | Literal["log"]):
        if target_type == "configuration":
            msg = {
                "action": "set_configuration_status",
                "package_id": target_id,
                "status_message": msg,
                "status_state": status_code
            }
            self.configuration_statuses[target_id] = msg
        elif target_type == "node":
            msg = {
                "action": "set_node_status",
                "node_id": target_id,
                "status_message": msg,
                "status_state": status_code
            }
            self.node_statuses[target_id] = msg
        else:
            raise ValueError(f"Invalid target_type={target_type}")
        self.send(msg)

    def execution_event(self, timestamp: float | None,
                        node_id: str,
                        state: Literal["pending"] | Literal["running"] | Literal["completed"] | Literal["failed"],
                        error: str | None, is_manual: bool) -> None:
        msg = {
            "action": "set_node_execution_state",
            "node_id": node_id,
            "execution_state": state
        }
        self.node_execution_states[node_id] = msg
        self.send(msg)

    def execution_completed(self) -> None:
        msg = {
            "action": "execution_complete"
        }
        self.send(msg)

    def request_open_client(self, origin_id: str, origin_type: Literal["node"] | Literal["configuration"],
                            session_id: str | None, client_name: str) -> None:
        msg = {
            "action": "open_client_request",
            "target_id": origin_id,
            "target_type": origin_type,
            "client_name": client_name
        }
        if session_id is None:
            self.send(msg)
        else:
            self.send(msg, to_session_id=session_id)

    def design_metadata_updated(self, metadata: dict[str, JsonType], ref: str | None):
        if self.design_metadata_update_callback:
            self.design_metadata_update_callback(metadata)
        msg = {
            "action": "design_metadata_updated",
            "metadata": metadata
        }
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def node_added(self, node_id: str, node_type: str, metadata: dict[str, JsonType], ref: str | None) -> None:
        msg = {
            "action": "node_added",
            "metadata": metadata,
            "node_type": node_type,
            "node_id": node_id
        }
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def node_metadata_updated(self, node_id: str, metadata: dict[str, JsonType], ref: str | None) -> None:
        msg = {
            "action": "node_metadata_updated",
            "node_id": node_id,
            "metadata": metadata
        }
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def node_reloaded(self, node_id: str, ref: str | None) -> None:
        msg = {
            "action": "node_reloaded",
            "node_id": node_id
        }
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def node_removed(self, node_id: str, ref: str | None = None) -> None:
        if node_id in self.node_statuses:
            del self.node_statuses[node_id]
        if node_id in self.node_execution_states:
            del self.node_execution_states[node_id]
        msg = {
            "action": "node_removed",
            "node_id": node_id
        }
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def link_added(self, link_id: str, link_type: str, from_node_id: str, from_port_name: str, to_node_id: str,
                   to_port_name: str, ref: str | None) -> None:
        msg = {
            "action": "link_added",
            "link_id": link_id,
            "link_type": link_type,
            "from_node_id": from_node_id,
            "from_port_name": from_port_name,
            "to_node_id": to_node_id,
            "to_port_name": to_port_name
        }
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def link_removed(self, link_id: str, ref: str | None = None) -> None:
        msg = {
            "action": "link_removed",
            "link_id": link_id
        }
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def clear(self, ref: str | None = None) -> None:
        msg = {"action": "note_cleared"}
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def started(self, ref: str | None = None):
        pass

    def paused(self, ref: str | None = None):
        msg = {"action": "note_paused"}
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def resumed(self, ref: str | None = None):
        msg = {"action": "note_resumed"}
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def restarting(self, ref: str | None = None) -> None:
        msg = {"action": "note_restarting"}
        if ref:
            msg["ref"] = ref
        self.send(msg)

    def restarted(self, ref: str | None = None) -> None:
        msg = {"action": "note_restarted"}
        if ref:
            msg["ref"] = ref
        self.send(msg)
