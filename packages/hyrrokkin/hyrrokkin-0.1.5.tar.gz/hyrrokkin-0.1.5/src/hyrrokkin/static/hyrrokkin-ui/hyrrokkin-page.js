/*   Hyrrokkin - A visual modelling tool for constructing and executing directed graphs.

     Copyright (C) 2022-2025 Visual Topology Ltd

     Licensed under the MIT License
*/

/* src/js/page/page.js */

var hyrrokkin = hyrrokkin || {};


class WebsocketMessageChannel {

    constructor(ws_url) {
        this.ws = null;
        this.message_handler = null;
        this.pending_messages_in = [];
        this.pending_messages_out = [];
        const ws = new WebSocket(ws_url);
        ws.binaryType = "arraybuffer";
        this.heartbeat = null;

        if (ws) {
            ws.onopen = (event) => {
                this.ws = ws;
                for (let idx = 0; idx < this.pending_messages_out.length; idx++) {
                    this.ws.send(this.pending_messages_out[idx]);
                }
                this.pending_messages_out = [];
                // this.start_heartbeat();
            }

            ws.onmessage = (msg) => {
                if (this.message_handler) {
                    this.message_handler(msg.data);
                } else {
                    this.pending_messages_in.push(msg.data);
                }
            }

            ws.onerror = (err) => {
                window.setTimeout(() => this.reconnect(),1000);
                this.stop_heartbeat();
            }

            ws.onclose = () => {
                window.setTimeout(() => this.reconnect(),1000);
                this.stop_heartbeat();
            }
        }
    }

    start_heartbeat() {
        // to keep the websocket from getting disconnected, it is helpful to send a heartbeat ""
        this.heartbeat = window.setInterval( () => {
            this.ws.send("");
        }, 10000);
    }

    stop_heartbeat() {
        if (this.heartbeat) {
            window.clearInterval(this.heartbeat);
            this.heartbeat = null;
        }
    }

    set_message_handler(message_handler) {
        this.message_handler = message_handler;
        for (let idx = 0; idx < this.pending_messages_in.length; idx++) {
            this.message_handler(this.pending_messages_in[idx]);
        }
        this.pending_messages_in = [];
    }

    reconnect() {
        alert("Connection to server lost, press OK to try to reconnect");
        location.reload();
    }

    send(msg) {
        if (this.ws) {
            this.ws.send(msg);
        } else {
            this.pending_messages_out.push(msg);
        }
    }
}

hyrrokkin.Page = class {

    constructor() {
        this.message_handler = null;
        this.pending_messages = [];
        let params = new URLSearchParams(window.location.search);
        if ((params.has("node_id") || params.has("package_id")) && params.has("page_id")) {
            this.parent_window = null;
            let url_comps = window.location.pathname.split("/");
            let url_base = "";
            for(let idx=0; idx < url_comps.length; idx += 1) {
                if (url_comps[idx] === "package") {
                    url_base = url_comps.slice(0,idx);
                    break;
                }
            }
            let ws_url = url_base;
            if (params.has("node_id")) {
                ws_url += "/node/"+params.get("node_id");
            } else {
                ws_url += "/configuration/"+params.get("package_id");
            }
            ws_url += "/"+params.get("page_id");
            if (params.has("language")) {
                ws_url += "/"+params.get("language");
            }
            ws_url += "/connect";
            this.ws = new WebsocketMessageChannel(ws_url);
            this.ws.set_message_handler((msg) => {
               let decoded_msg = hyrrokkin_engine.MessageUtils.decode_message(msg);
               this.handle_message(decoded_msg);
            });
        } else {
            this.ws = null;
            this.parent_window = window.opener || window.parent;
            this.parent_window.addEventListener("unload", (event) => {
                window.close();
            });

            window.addEventListener("message", (event) => hyrrokkin.page.handle_message(event.data));
        }
        this.connected = false;
        this.connection_handler = null;
        this.language = undefined;
        this.bundle = null;
    }

    set_connection_handler(handler) {
        this.connection_handler = handler;
        if (this.connected) {
            this.fire_connected();
        }
    }

    fire_connected() {
        if (this.connection_handler) {
            try {
                this.connection_handler();
            } catch (ex) {
            }
            this.connection_handler = null;
        }
    }

    set_message_handler(handler) {
        this.message_handler = handler;
        for(let idx=0; idx<this.pending_messages.length; idx++) {
            let msg = this.pending_messages[idx];
            this.message_handler(...msg);
        }
        this.pending_messages = [];
    }

    handle_message(msg) {
        let header = msg[0];
        let type = header["type"];
        switch (type) {
            case "page_init":
                this.language = header["language"];
                this.bundle = new hyrrokkin.L10NBundle(header["bundle"]);
                this.connected = true;
                this.fire_connected();
                break;
            case "page_message":
                let message_parts = msg[1];
                if (this.message_handler) {
                    this.message_handler(...message_parts);
                } else {
                    this.pending_messages.push(message_parts);
                }
                break;
            default:
                 console.warn("Unexpected msg received by page");
        }
    }

    localise_string(input) {
        if (this.connected) {
            return this.bundle.localise(input);
        } else {
            throw new Error("Cannot localise until page is connected. Set a connection handler to be notified")
        }
    }

    localise_body() {
        if (this.connected) {
            if (this.language === "") {
                /* no localisation available, nothing to do */
                return;
            }
            let localise = (node) => {
                if (node.nodeType === node.TEXT_NODE) {
                    let text = node.nodeValue;
                    if (text.includes("{{") && text.includes("}}")) {
                        node.nodeValue = this.bundle.localise(text);
                    }
                } else {
                    node.childNodes.forEach(node => localise(node));
                }
            }
            localise(document.body);
        } else {
            throw new Error("Cannot localise until page is connected. Set a connection handler to be notified")
        }
    }

    get_language() {
        return this.language;
    }

    send_to_network(msg) {
        if (this.parent_window) {
            this.parent_window.postMessage(msg, window.location.origin);
        } else {
            let enc_msg = hyrrokkin_engine.MessageUtils.encode_message(...msg);
            this.ws.send(enc_msg);
        }
    }

    send_message(...message_parts) {
        this.send_to_network([{"type":"page_message"},message_parts]);
    }
}

hyrrokkin.page = new hyrrokkin.Page();


/* ../engines/javascript/src/hyrrokkin_engine/message_utils.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.MessageUtils = class {

    static encode_message(...message_parts) {
        let encoded_components = [];
        let headers = [];
        let component_total_len = 0;
        message_parts.forEach(content => {
            let content_b = content;
            let header = {};
            if (content instanceof ArrayBuffer) {
                header["content_type"] = "binary";
                content_b = new Uint8Array(content);
            } else if (content === null || content === undefined) {
                header["content_type"] = "null";
                content_b = new ArrayBuffer(0);
            } else if (content instanceof String) {
                content_b = new TextEncoder().encode(content);
                header["content_type"] = "string";
            } else {
                content_b = new TextEncoder().encode(JSON.stringify(content));
                header["content_type"] = "json";
            }
            header["length"] = content_b.byteLength;
            headers.push(header);
            encoded_components.push(content_b);
            component_total_len += content_b.byteLength;
        });

        let header = { "components": headers }
        let header_s = JSON.stringify(header);
        let header_b = new TextEncoder().encode(header_s);
        let header_len = new ArrayBuffer(4);
        new DataView(header_len).setInt32(0,header_b.byteLength,false);

        let msg_buffer = new ArrayBuffer(4+header_b.byteLength+component_total_len);
        let dv = new Uint8Array(msg_buffer);
        dv.set(new Uint8Array(header_len),0);
        dv.set(header_b,4);
        let offset = 4+header_b.byteLength;
        for(let idx=0; idx<encoded_components.length; idx+=1) {
            dv.set(encoded_components[idx],offset);
            offset += headers[idx].length;
        }
        return msg_buffer;
    }

    static decode_message(msg_buffer) {
        let decoded = [];
        let view = new DataView(msg_buffer);
        let header_len = view.getInt32(0);
        let header_b = msg_buffer.slice(4, 4 + header_len);
        let header_s = new TextDecoder().decode(header_b);
        let header = JSON.parse(header_s);
        let offset = 4+header_len;
        header.components.forEach(component => {
            let content_b = msg_buffer.slice(offset,offset+component.length);
            let content = null;
            switch(component.content_type) {
                case "null":
                    content = null;
                    break;
                case "string":
                    content = (new TextDecoder()).decode(content_b);
                    break;
                case "binary":
                    content = content_b;
                    break;
                case "json":
                    content = JSON.parse((new TextDecoder()).decode(content_b));
                    break;
                default:
                    throw new Error("Corrupted message, cannot decode");
            }
            offset += component.length;
            decoded.push(content);
        });
        if (offset != msg_buffer.byteLength) {
            throw new Error("Corrupted message, not all message content was decoded");
        }

        return decoded;
    }
}

/* src/js/utils/l10n_bundle.js */

var hyrrokkin = hyrrokkin || {};

hyrrokkin.L10NBundle = class {

    debug = false;

    constructor(bundle_content) {
        this.bundle_content = bundle_content;
    }

    localise(input) {
        if (!input) {
            return "";
        }
        if (input in this.bundle_content) {
            let s = this.bundle_content[input];
            if (hyrrokkin.L10NBundle.debug) {
                return "*"+s+"*";
            } else {
                return s;
            }
        }
        // for empty bundles, localise returns the input
        if (Object.keys(this.bundle_content).length == 0) {
            return input;
        }
        // treat the input as possibly containing embedded keys, delimited by {{ and }},
        // for example "say {{hello}}" embeds they key hello
        // substitute any embedded keys and the surrounding delimiters with their values, if the key is present in the bundle
        let idx = 0;
        let s = "";
        while(idx<input.length) {
            if (input.slice(idx, idx+2) === "{{") {
                let startidx = idx+2;
                idx += 2;
                while(idx<input.length) {
                    if (input.slice(idx,idx+2) === "}}") {
                        let token = input.slice(startidx,idx);
                        if (token in this.bundle_content) {
                            token = this.bundle_content[token];
                            if (hyrrokkin.L10NBundle.debug) {
                                token = "*" + token + "*";
                            }
                        }
                        s += token;
                        idx += 2;
                        break;
                    } else {
                        idx += 1;
                    }
                }
            } else {
                s += input.charAt(idx);
                idx++;
            }
        }
        return s;
    }

    get_content() {
        return this.bundle_content;
    }
}



