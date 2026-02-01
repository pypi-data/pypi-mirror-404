/*   Hyrrokkin - A visual modelling tool for constructing and executing directed graphs.

     Copyright (C) 2022-2025 Visual Topology Ltd

     Licensed under the MIT License
*/

class TopologyApplication {

    constructor(element_id) {
        this.element_id = element_id;
        this.is_handling_messages = false;
        this.message_queue = [];

        let url_params = new URLSearchParams(window.location.search);

        if (url_params.has("application_id")) {
            this.application_id = url_params.get("application_id");
        }

        this.load().then(() => {
        });
    }

    async load() {
        let details = await fetch("/application/"+this.application_id+"/application.json")
        this.application_details = await details.json();
        this.topology_id = this.application_details["topology_id"];
        let connect_url = "/topology/"+this.topology_id+"/connect";
        this.wsm = new WebsocketMessageChannel(connect_url);

        this.wsm.set_message_handler((msg) => {
            this.message_queue.push(msg);
            if (!this.is_handling_messages) {
                this.handle_messages();
            }
        });
    }

    handle_messages() {
        if (this.message_queue.length>0) {
            this.is_handling_messages = true;
            this.recv(this.message_queue.shift()).then(() => this.handle_messages());
        } else {
            this.is_handling_messages = false;
        }
    }

    async init(package_urls) {

        this.options = {
            "topology_id": this.topology_id,
            "package_urls": package_urls,
            "platform_extensions": [],
            "workspace_id": "workspace",
            "directory_url": "/topology-directory.html"
        }

        this.model = new hyrrokkin.RemoteModel(this.options, (...msg) => this.send(...msg), false);

        this.application = await hyrrokkin.start_application(this.application_id, this.element_id, this.application_details, this.options, this.model);
    }

    async recv(msg) {
        let msg_parts = hyrrokkin_engine.MessageUtils.decode_message(msg);
        let payload = msg_parts[0];
        let action = payload["action"];
        if (action === "init") {
            await this.init(payload["package_urls"]);
        }
        await this.model.handle(...msg_parts);
        if (action === "init") {
            this.application.open();
        }
    }

    send(...msg_parts) {
        this.wsm.send(hyrrokkin_engine.MessageUtils.encode_message(...msg_parts));
    }

}