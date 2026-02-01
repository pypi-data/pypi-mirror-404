//   Hyrrokkin - a library for building and running executable graphs
//
//   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd


var textgraph = textgraph || {};

textgraph.MergeFrequenciesNode = class {

    constructor(services) {
        this.services = services;
        this.clients = new Set();
        this.properties = null;
    }

    async load() {
        this.properties = await this.services.get_properties();
        if (!("mode" in this.properties)) {
            this.properties["mode"] = "add";
        }
    }

    async open_client(client) {
        this.clients.add(client);

        let handle_message = async (value) => {
            this.properties["mode"] = value;
            await this.services.set_properties(this.properties);
            this.clients.forEach((other_client) => {
                if (other_client !== client) {
                    other_client.send_message(value);
                }
            });
            await this.services.request_run();
        }

        client.set_message_handler(handle_message);
        client.send_message(this.properties["mode"]);
    }

    async close_client(client) {
        this.clients.delete(client);
    }

    async run(inputs) {
        this.services.clear_status();
        if ("data_in0" in inputs || "data_in1" in inputs) {
            let input_0 = inputs["data_in0"] || {};
            let input_1 = inputs["data_in1"] || {};

            let output = {};
            let mode = this.properties["mode"];
            for(let word in input_0) {
                output[word] = input_0[word];
            }
            for(let word in input_1) {
                if (mode === "add") {
                    output[word] = (output[word] || 0) + input_1[word];
                } else {
                    output[word] = (output[word] || 0) - input_1[word];
                }
            }

            return {"data_out": output};
        } else {
            this.services.set_status("{{no_data}}", "warning");
            return {};
        }
    }
}