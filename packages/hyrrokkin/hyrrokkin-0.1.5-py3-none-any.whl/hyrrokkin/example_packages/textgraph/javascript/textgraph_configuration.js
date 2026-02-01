//   Hyrrokkin - a library for building and running executable graphs
//
//   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd

var textgraph = textgraph || {};

textgraph.TextgraphConfiguration = class {

    // https://gist.github.com/sebleier/554280 with modifications
    static DEFAULT_STOP_WORDS = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will", "just", "dont", "should", "now"]

    constructor(services) {
        this.services = services;
        this.clients = new Set();
        this.update_listeners = new Set();
    }

    async load() {
        let keys = await this.services.get_data_keys();
        if (keys.includes("stop_words")) {
            this.stop_words = JSON.parse((new TextDecoder()).decode(await this.services.get_data("stop_words")));
        } else {
            this.stop_words = textgraph.TextgraphConfiguration.DEFAULT_STOP_WORDS;
        }
    }

    get_stop_words() {
        return this.stop_words;
    }

    add_update_listener(listener) {
        this.update_listeners.add(listener);
        return listener;
    }

    remove_update_listener(listener) {
        this.update_listeners.delete(listener);
    }

    async notify_update_listeners() {
        const arr = Array.from(this.update_listeners);
        for(let idx=0; idx<arr.length; idx++) {
            await arr[idx]();
        }
    }

    async create_node(node_type_id, node_services) {
        switch (node_type_id) {
            case "text_input_node": return new textgraph.TextInputNode(node_services);
            case "word_frequency_node": return new textgraph.WordFrequencyNode(node_services);
            case "merge_frequencies_node": return new textgraph.MergeFrequenciesNode(node_services);
            case "merge_text_node": return new textgraph.MergeTextNode(node_services);
            case "table_display_node": return new textgraph.TableDisplayNode(node_services);
            default: return null;
        }
    }

    async open_client(client) {
        this.clients.add(client);
        let handle_message = async (stop_words) => {
            this.stop_words = stop_words;
            await this.services.set_data("stop_words", (new TextEncoder()).encode(JSON.stringify(this.stop_words)).buffer);
            this.clients.forEach((other_client) => {
                if (other_client !== client) {
                    other_client.send_message(stop_words);
                }
            });
            await this.notify_update_listeners();
        }
        client.set_message_handler(handle_message);
        client.send_message(this.stop_words);
    }

    static
    encode(value, link_type) {
        console.log("encode "+value+" "+link_type);
        if (value !== null) {
            if (link_type === "text") {
                return (new TextEncoder()).encode(value).buffer;
            } else if (link_type === "frequency_table") {
                return (new TextEncoder()).encode(JSON.stringify(value)).buffer;
            }
        }
        return null;
    }

    static
    decode(encoded_bytes, link_type) {
        if (encoded_bytes !== null) {
            let txt = (new TextDecoder()).decode(encoded_bytes);
            if (link_type === "text") {
                return txt;
            } else if (link_type === "frequency_table") {
                return JSON.parse(txt);
            }
        }
        return null;
    }

    async close_client(client) {
        this.clients.delete(client);
    }
}

hyrrokkin_engine.registry.register_configuration_factory("textgraph",(configuration_services) => new textgraph.TextgraphConfiguration(configuration_services));







