//   Hyrrokkin - a library for building and running executable graphs
//
//   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd

var textgraph = textgraph || {};

textgraph.WordFrequencyNode = class {

    constructor(services) {
        this.services = services;
        this.clients = new Set();
        this.properties = null;
        let configuration_updated = async () => {
            await this.services.request_run();
        }
        this.update_listener = this.services.get_configuration().add_update_listener(configuration_updated);
    }

    async load() {
        this.properties = await this.services.get_properties();
        if (!("threshold" in this.properties)) {
            this.properties["threshold"] = 1;
        }
    }

    async open_client(client) {
        this.clients.add(client);
        client.set_message_handler(async (...msg) => await this.handle_message(client, ...msg));
        client.send_message(this.properties["threshold"]);
    }

    async close_client(client) {
        this.clients.delete(client);
    }

    async handle_message(from_client, value) {
        this.properties["threshold"] = value;
        await this.services.set_properties(this.properties);
        this.clients.forEach((other_client) => {
            if (other_client !== from_client) {
                other_client.send_message(value);
            }
        });
        this.services.request_run();
    }

    async run(inputs) {
        this.services.clear_status();
        if ("data_in" in inputs) {
            let input_text = inputs["data_in"];
            input_text = input_text.replaceAll("'","");
            let words = input_text.replace(/[^\w\s]/g," ").split(" ");
            let frequencies = {};
            let stop_words = this.services.get_configuration().get_stop_words();
            words.forEach((word) => {
                word = word.trim().toLowerCase();
                if (word && !stop_words.includes(word)) {
                   if (!(word in frequencies)) {
                       frequencies[word] = 0;
                   }
                   frequencies[word] += 1;
                }
            });
            let output = {};
            for (let word in frequencies) {
                if (word) {
                    if (frequencies[word] >= this.properties.threshold) {
                        output[word] = frequencies[word];
                    }
                }
            }

            return {"data_out": output};
        } else {
            this.services.set_status("{{no_data}}", "warning");
            return {};
        }
    }

    remove() {
        this.services.get_configuration().remove_update_listener(this.update_listener);
    }
}



