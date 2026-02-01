#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd

import json

from hyrrokkin_engine.node_interface import NodeInterface


class TableDisplayNode(NodeInterface):

    def __init__(self, services):
        self.services = services
        self.clients = set()
        self.table = None

    async def reset_run(self):
        self.table = None
        for client in self.clients:
            client.send_message(self.table)

    async def run(self, inputs):
        self.table = None
        if "data_in" in inputs:
            input_value = inputs["data_in"]
            self.table = []
            for word in input_value:
                self.table.append([word, input_value[word]])
            self.table = sorted(self.table, key=lambda r: r[1], reverse=True)
            self.services.set_status(f"{len(self.table)} " + "{{rows}}", "info")
            self.services.request_open_client("results")
        else:
            self.services.set_status("{{no_data}}", "warning")
        for client in self.clients:
            client.send_message(self.table)

    async def open_client(self, client):
        self.clients.add(client)
        client.send_message(self.table)

    async def close_client(self, client):
        self.clients.remove(client)
