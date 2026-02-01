/*   Hyrrokkin - A visual modelling tool for constructing and executing directed graphs.

     Copyright (C) 2022-2025 Visual Topology Ltd

     Licensed under the MIT License
*/

class TopologyDirectory {

    constructor(element_id) {
        this.store = null;
        this.element_id = element_id;
        this.is_handling_messages = false;
        this.message_queue = [];

        this.wsm = new WebsocketMessageChannel("connect");

        this.wsm.set_message_handler((msg) => {
            this.message_queue.push(msg);
            if (!this.is_handling_messages) {
                this.handle_messages();
            }
        });

        this.hyrrokkin_directory_api = null;
    }

    handle_messages() {
        if (this.message_queue.length>0) {
            this.is_handling_messages = true;
            this.recv(this.message_queue.shift()).then(() => this.handle_messages());
        } else {
            this.is_handling_messages = false;
        }
    }

    send(msg) {
        let enc_msg = hyrrokkin_engine.MessageUtils.encode_message(msg);
        this.wsm.send(enc_msg);
    }

    async init(payload) {
        let topologies = payload["topologies"];
        let applications = payload["applications"];
        let package_urls = payload["package_urls"];

        this.base_path = payload["base_path"];

        let options = {
            "package_urls": package_urls,
            "applications": applications,
            "directory_title": "Topology Directory",
            "templates": {},
            "show_status": true,
            "directory_splash": {
                "title": "Loading Topology Directory...",
                "image_url": "hyrrokkin-ui/images/hyrrokkin-ui.svg"
            },
            "application_url": "topology-application.html"
        }

        this.store = new hyrrokkin.RemoteStore((msg) => this.send(msg),topologies);

        options["directory_refresh_interval"] = 0;

        this.hyrrokkin_directory_api = await hyrrokkin.start_directory(this.element_id, options, this.store);

        this.hyrrokkin_directory_api.set_open_topology_in_designer_handler((topology_id) => {
            let target_url = this.base_path+"/topology-designer.html?topology_id="+topology_id;
            window.open(target_url,"_self");
        });
    }

    async recv(msg) {
        let msg_parts = hyrrokkin_engine.MessageUtils.decode_message(msg);
        let payload = msg_parts[0];
        let action = payload["action"];
        switch(action) {
            case "init":
                await this.init(payload);
                break;
            default:
                await this.store.recv(payload);
        }
    }
}



