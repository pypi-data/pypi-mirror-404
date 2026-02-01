/*   Hyrrokkin - A visual modelling tool for constructing and executing directed graphs.

     Copyright (C) 2022-2025 Visual Topology Ltd

     Licensed under the MIT License
*/

class TopologyDesigner {

    constructor(element_id) {
        this.element_id = element_id;
        this.is_handling_messages = false;
        this.message_queue = [];

        let path_components = window.location.pathname.split("/");
        let base_path = "";
        for(let idx=0; idx<path_components.length-1; idx++) {
            if (path_components[idx] !== "") {
                base_path += "/";
                base_path += path_components[idx];
            }
        }

        let url_params = new URLSearchParams(window.location.search);
        let connect_url = base_path +"/connect";
        if (url_params.has("topology_id")) {
            this.topology_id = url_params.get("topology_id");
            connect_url = base_path+"/topology/"+this.topology_id+"/connect";
        } else {
            this.topology_id = "topology";
        }

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

    async init(package_urls, directory_url) {

        let options = {
            "topology_id": this.topology_id,
            "package_urls": package_urls,
            "platform_extensions": [],
            "workspace_id": "workspace",
            "designer_title": "Topology Designer",
            "designer_splash": {
                "title": "Loading Topology Designer...",
                "image_url": "hyrrokkin-ui/images/hyrrokkin-ui.svg"
            }
        }

        if (directory_url) {
            options["directory_url"] = directory_url;
        }

        this.model = new hyrrokkin.RemoteModel(options, (...msg) => this.send(...msg), false);

        await hyrrokkin.start_designer(this.element_id, options, this.model);
    }

    async recv(msg) {
        let msg_parts = hyrrokkin_engine.MessageUtils.decode_message(msg);
        let payload = msg_parts[0];
        let action = payload["action"];
        if (action === "init") {
            await this.init(payload["package_urls"], payload["directory_url"]);
        }
        await this.model.handle(...msg_parts);
    }

    send(...msg_parts) {
        this.wsm.send(hyrrokkin_engine.MessageUtils.encode_message(...msg_parts));
    }

}