//   Hyrrokkin - a library for building and running executable graphs
//
//   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd

var textgraph = textgraph || {};

textgraph.TextInputNode = class {

    constructor(services) {
        this.services = services;
        this.clients = new Set();
        this.text = "";
    }

    async load() {
        let data = await this.services.get_data("value");
        if (data === null) {
            this.text = "";
        } else {
            this.text = (new TextDecoder()).decode(data);
        }
    }

    async open_client(client) {
        this.clients.add(client);
        client.set_message_handler(async (...msg) => await this.handle_message(client, ...msg));
        client.send_message(this.text);
    }

    async close_client(client) {
        this.clients.delete(client);
    }

    async handle_message(from_client, value) {
        if (value !== this.text) {
            this.text = value;
            await this.services.set_data("value", (new TextEncoder()).encode(this.text).buffer);
            await this.services.request_run();
            this.clients.forEach((other_client) => {
                if (other_client !== from_client) {
                    other_client.send_message(this.text);
                }
            });
        }
    }

    async run(inputs) {
        this.services.clear_status();
        if (this.text) {
            return {"data_out": this.text}
        } else {
            this.services.set_status("{{no_data}}", "warning");
            return {};
        }
    }
}
