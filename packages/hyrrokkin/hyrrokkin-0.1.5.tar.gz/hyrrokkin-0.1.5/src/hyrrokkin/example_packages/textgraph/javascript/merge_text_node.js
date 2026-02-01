//   Hyrrokkin - a library for building and running executable graphs
//
//   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd


var textgraph = textgraph || {};

textgraph.MergeTextNode = class {

    constructor(services) {
        this.services = services;
    }

    async run(inputs) {
        this.services.clear_status();
        if ("data_in" in inputs) {
            return {"data_out": inputs["data_in"].join(" ")};
        } else {
            this.services.set_status("{{no_data}}", "warning");
            return {};
        }
    }
}