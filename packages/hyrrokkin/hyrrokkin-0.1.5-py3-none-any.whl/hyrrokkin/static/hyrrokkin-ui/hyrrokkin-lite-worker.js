/*   Hyrrokkin - A visual modelling tool for constructing and executing directed graphs.

     Copyright (C) 2022-2025 Visual Topology Ltd

     Licensed under the MIT License
*/

/* src/js/local/local_worker.js */

var hyrrokkin = hyrrokkin || {};

hyrrokkin.LocalWorker = class {

    constructor() {
        this.driver = null;
    }

    async init(o) {
        o["imports"].forEach( name => {
            importScripts(name);
        });
    }

    async recv(msg) {
        // first message should be init
        let o = msg[0];
        if (o.action == "init") {
            await this.init(o);
            this.driver = new hyrrokkin_engine.ExecutionWorker(message_parts => this.send(message_parts));
        }
        if (this.driver) {
            this.driver.recv(msg);
        }
    }

    send(message_parts) {
        postMessage(message_parts);
    }
}

hyrrokkin.local_worker = new hyrrokkin.LocalWorker();

onmessage = async (e) => {
    await hyrrokkin.local_worker.recv(e.data);
}

