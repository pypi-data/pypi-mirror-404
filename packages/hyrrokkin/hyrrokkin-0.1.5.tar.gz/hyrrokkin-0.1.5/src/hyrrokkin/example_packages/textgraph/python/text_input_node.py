#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd

import asyncio

from hyrrokkin_engine.node_interface import NodeInterface


class TextInputNode(NodeInterface):

    def __init__(self, services):
        self.services = services
        self.clients = set()
        self.text = ""

    async def load(self):
        data = await self.services.get_data("value")
        if data is None:
            self.text = ""
        else:
            self.text = data.decode()

    async def open_client(self, client):
        self.clients.add(client)

        async def handle_message(value):
            if value != self.text:
                self.text = value
                await self.services.set_data("value", self.text.encode())
                for other_client in self.clients:
                    if other_client != client:
                        other_client.send_message(self.text)
                await self.services.request_run()

        client.set_message_handler(handle_message)
        client.send_message(self.text)

    async def close_client(self, client):
        self.clients.remove(client)

    async def run(self, inputs):
        self.services.clear_status()
        if self.text:
            return {"data_out": self.text}
        else:
            self.services.set_status("{{no_data}}", "warning")
            return {}
