#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd


import re

from hyrrokkin_engine.node_interface import NodeInterface


class WordFrequencyNode(NodeInterface):

    def __init__(self, services):
        self.services = services
        self.clients = set()
        self.properties = None

        async def configuration_updated():
            await self.services.request_run()

        self.update_listener = self.services.get_configuration().add_update_listener(configuration_updated)

    async def load(self):
        self.properties = await self.services.get_properties()
        if "threshold" not in self.properties:
            self.properties["threshold"] = 1

    async def open_client(self, client):
        self.clients.add(client)

        async def handle_message(value):
            self.properties["threshold"] = value
            await self.services.set_properties(self.properties)
            for other_client in self.clients:
                if other_client != client:
                    other_client.send_message(value)
            await self.services.request_run()

        client.set_message_handler(handle_message)
        client.send_message(self.properties["threshold"])

    async def close_client(self, client):
        self.clients.remove(client)

    async def run(self, inputs):
        self.services.clear_status()
        if "data_in" in inputs:
            input_text = inputs["data_in"]
            input_text = input_text.replace("'", "")
            frequencies = {}
            stop_words = self.services.get_configuration().get_stop_words()
            words = re.sub(r'[^\w\s]', ' ', input_text).split(' ')

            for word in words:
                word = word.strip().lower()
                if word and word not in stop_words:
                    if word not in frequencies:
                        frequencies[word] = 0
                    frequencies[word] += 1

            output = {}
            for word in frequencies:
                if frequencies[word] >= self.properties["threshold"]:
                    output[word] = frequencies[word]

            return {"data_out": output}
        else:
            self.services.set_status("{{no_data}}", "warning")
            return {}

    def remove(self):
        self.services.get_configuration().remove_update_listener(self.update_listener)
