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

from hyrrokkin.interfaces.topology_listener_api import TopologyListenerAPI
from hyrrokkin.utils.type_hints import JsonType


class TopologyListener(TopologyListenerAPI):

    def status_event(self, target_type: Literal["node", "configuration"], target_id: str, msg: str,
                     status_code: Literal["error", "warning", "info", "log"]):
        pass

    def execution_event(self, timestamp: float | None, node_id: str,
                        state: Literal["pending", "running", "completed", "failed"],
                        error: str | None, is_manual: bool) -> None:
        pass

    def execution_completed(self) -> None:
        pass

    def design_metadata_updated(self, metadata: dict[str, JsonType], ref: str | None) -> None:
        pass

    def node_added(self, node_id: str, node_type: str, metadata: dict[str, JsonType], ref: str | None) -> None:
        pass

    def node_metadata_updated(self, node_id: str, metadata: dict[str, JsonType], ref: str | None) -> None:
        pass

    def node_removed(self, node_id: str, ref: str | None) -> None:
        pass

    def node_reloaded(self, node_id: str, ref: str | None) -> None:
        pass

    def link_added(self, link_id: str, link_type: str, from_node_id: str, from_port_name: str, to_node_id: str,
                   to_port_name: str, ref: str | None) -> None:
        pass

    def link_removed(self, link_id: str, ref: str | None) -> None:
        pass

    def clear(self, ref: str | None) -> None:
        pass

    def started(self, ref: str | None) -> None:
        pass

    def paused(self, ref: str | None) -> None:
        pass

    def resumed(self, ref: str | None) -> None:
        pass

    def restarting(self, ref: str | None) -> None:
        pass

    def restarted(self, ref: str | None) -> None:
        pass

    def request_open_client(self, origin_id: str, origin_type: Literal["node", "configuration"],
                            session_id: str | None, client_name: str) -> None:
        pass
