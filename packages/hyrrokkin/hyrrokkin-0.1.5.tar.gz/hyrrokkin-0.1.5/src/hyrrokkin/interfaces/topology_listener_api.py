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

from abc import ABC, abstractmethod
from typing import Literal
from hyrrokkin.utils.type_hints import JsonType


class TopologyListenerAPI(ABC):

    @abstractmethod
    def status_event(self, target_type: Literal["node", "configuration"],
                     target_id: str, msg: str,
                     status_code: Literal["error", "warning", "info", "log"]):
        """
        Called when a status event is issued by a node or package configuration

        Args:
            target_type: whether the event is from a node or package configuration
            target_id: the node_id (if target_type=node) or package_id (if target_type=configuration)
            msg: the contents of the status message
            status_code: classifies the message as error, warning, info or log
        """

    @abstractmethod
    def execution_event(self, timestamp: float | None,
                        node_id: str,
                        state: Literal["pending", "running", "completed", "failed"],
                        error: str | None, is_manual: bool) -> None:
        """
        Called when a node execution event occurs

        Args:
            timestamp: the time at which the event occurred, in seconds since epoch
            node_id: the id of the node to which the event relates
            state: the new state of the node
            exception: if the state is failed, a string describing the error
            is_manual: whether the event was manually issued by the node
        """

    @abstractmethod
    def execution_completed(self) -> None:
        """
        Called when no nodes are running or scheduled to run
        """

    @abstractmethod
    def design_metadata_updated(self, metadata: dict[str, JsonType], ref: str | None) -> None:
        """
        Called when the design's metadata is updated

        Args:
            metadata:  the updated metadata
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def node_added(self, node_id: str, node_type: str, metadata: dict[str, JsonType], ref: str | None) -> None:
        """
        Called when a node is added to the topology

        Args:
            node_id: the id of the node
            node_type: in the form <package_id>:<node_type_id>
            metadata: metadata describing the added node
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def node_metadata_updated(self, node_id: str, metadata: dict[str, JsonType], ref: str | None) -> None:
        """
        Called when a node's metadata is updated

        Args:
            node_id: the id of the node being updated
            metadata: the new metadata
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def node_removed(self, node_id: str, ref: str | None) -> None:
        """
        Called when a node is removed

        Args:
            node_id: the id of the node being removed
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def node_reloaded(self, node_id: str, ref: str | None) -> None:
        """
        Called when a node is reloaded

        Args:
            node_id: the id of the node being reloaded
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def link_added(self, link_id: str, link_type: str, from_node_id: str, from_port_name: str, to_node_id: str,
                   to_port_name: str, ref: str | None) -> None:
        """
        Called when a link is added to the topology

        Args:
            link_id: the id of the link being added
            link_type: the link type in the form <package_id>:<link_type_id>
            from_node_id: the id of the source node
            from_port_name: the port name of the source port
            to_node_id: the id of the destination node
            to_port_name: the port name of the destination port
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def link_removed(self, link_id: str, ref: str | None) -> None:
        """
        Called when a link is removed from the topology

        Args:
            link_id: the id of the link being removed
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def clear(self, ref: str | None) -> None:
        """
        Called when the topology is cleared, removing all nodes and links

        Args:
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def started(self, ref: str | None) -> None:
        """
        Called when the topology is started

        Args:
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def paused(self, ref: str | None) -> None:
        """
        Called when the topology is paused

        Args:
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def resumed(self, ref: str | None) -> None:
        """
        Called when the topology is resumed

        Args:
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def restarting(self, ref: str | None) -> None:
        """
        Called when the topology is about to restart

        Args:
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def restarted(self, ref: str | None) -> None:
        """
        Called when the topology is restarted

        Args:
            ref: an optional reference identifier provided in the originating request
        """

    @abstractmethod
    def request_open_client(self, origin_id: str, origin_type: Literal["node", "configuration"],
                            session_id: str | None, client_name: str) -> None:
        """
        Called to request that a client be opened

        Args:
            origin_id: the id of the originating node or package configuration
            origin_type: the origin type (node or configuration)
            session_id: the name of the session to open the client in (or None to request opening in all sessions)
            client_name: the name of the client to open
        """
