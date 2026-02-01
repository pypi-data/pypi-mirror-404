//   Hyrrokkin - a library for building and running executable graphs
//
//   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd

var textgraph = textgraph || {};

textgraph.TableDisplayNode = class {

    constructor(services) {
        this.services = services;
        this.clients = new Set();
        this.table = null;
    }

    async reset_run() {
        this.table = null;
        this.services.set_status("","info");
        this.clients.forEach((client) => {
            client.send_message(this.table);
        });
    }

    async run(inputs) {
        this.services.clear_status();
        this.table = null;
        if ("data_in" in inputs) {
            let input_value = inputs["data_in"];
            this.table = [];
            for(let word in input_value) {
                this.table.push([word,input_value[word]]);
            }
            this.table.sort(function(r1, r2) {
                return r2[1] - r1[1];
            });

            this.services.set_status(`${this.table.length} {{rows}}`, "info");
            this.services.request_open_client("results");
        } else {
            this.services.set_status("{{no_data}}", "warning");
        }
        this.clients.forEach((client) => {
            client.send_message(this.table);
        });
    }

    open_client(client) {
        this.clients.add(client);
        client.send_message(this.table);
    }

    close_client(client) {
        this.clients.delete(client);
    }
}
