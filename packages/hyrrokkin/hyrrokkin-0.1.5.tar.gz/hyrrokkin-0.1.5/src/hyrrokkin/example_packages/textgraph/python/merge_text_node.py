#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd


from hyrrokkin_engine.node_interface import NodeInterface


class MergeTextNode(NodeInterface):

    def __init__(self, services):
        self.services = services

    async def run(self, inputs):
        self.services.clear_status()
        if ("data_in" in inputs):
            return {"data_out": " ".join(inputs["data_in"])}
        else:
            self.services.set_status("{{no_data}}", "warning")
            return {}
