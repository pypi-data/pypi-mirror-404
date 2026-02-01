/*   Hyrrokkin - A visual modelling tool for constructing and executing directed graphs.

     Copyright (C) 2022-2025 Visual Topology Ltd

     Licensed under the MIT License
*/

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