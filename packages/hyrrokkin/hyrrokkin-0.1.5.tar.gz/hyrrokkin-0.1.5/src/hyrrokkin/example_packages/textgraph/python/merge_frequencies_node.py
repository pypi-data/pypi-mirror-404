#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd


from hyrrokkin_engine.node_interface import NodeInterface


class MergeFrequenciesNode(NodeInterface):

    def __init__(self, services):
        self.services = services
        self.clients = set()
        self.properties = None

    async def load(self):
        self.properties = await self.services.get_properties()
        if "mode" not in self.properties:
            self.properties["mode"] = "add"

    async def open_client(self, client):
        self.clients.add(client)

        async def handle_message(value):
            self.properties["mode"] = value
            await self.services.set_properties(self.properties)
            for other_client in self.clients:
                if other_client != client:
                    other_client.send_message(value)
            await self.services.request_run()

        client.set_message_handler(handle_message)
        client.send_message(self.properties["mode"])

    async def close_client(self, client):
        self.clients.remove(client)

    async def run(self, inputs):
        self.services.clear_status()
        if ("data_in0" in inputs or "data_in1" in inputs):
            input_0 = inputs.get("data_in0", {})
            input_1 = inputs.get("data_in1", {})
            output = {}
            mode = self.properties["mode"]
            for word in input_0:
                output[word] = input_0[word]

            for word in input_1:
                if mode == "add":
                    output[word] = output.get(word, 0) + input_1[word]
                else:
                    output[word] = output.get(word, 0) - input_1[word]

            return {"data_out": output}
        else:
            self.services.set_status("{{no_data}}", "warning")
            return {}
