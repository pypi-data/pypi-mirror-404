/*       
    Hyrrokkin - a library for building and running executable graphs

    MIT License - Copyright (C) 2022-2025  Visual Topology Ltd

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software
    and associated documentation files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or
    substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
    BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/
/* hyrrokkin_engine/client_interface.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

/**
 * a value that can be serialised to/from JSON
 *
 * @typedef {JSONSerialisable}
 */

/**
 * @callback ClientInterface~messageReceivedCallback
 *
 * @param @param {...(string|ArrayBuffer|JSONSerlialisable)} the message received, may be in multiple parts
 */

/**
 * Define an interface used by nodes to communicate with clients
 *
 * @interface
 *
 * @type {hyrrokkin_engine.ClientInterface}
 */
hyrrokkin_engine.ClientInterface = class {


    get_session_id() {
    }

    get_client_name() {
    }

    get_client_options() {
    }

    /**
     * set a function used to receive messages
     *
     * @param {ClientInterface~messageReceivedCallback} handler a function that will be called when a message from the client arrives
     */
    set_message_handler(handler) {
    }

    /**
     * send a message to the client
     *
     * @param {...*} message consists of zero or more components
     */
    send_message(...message) {
    }
}

/* hyrrokkin_engine/client.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.Client = class {

    constructor(session_id, client_id, client_options) {
        this.session_id = session_id;
        this.event_handlers = [];
        this.message_handler = null;
        this.send_fn = null;
        this.session_id = session_id;
        this.client_id = client_id;
        this.client_options = client_options;
        this.is_open = false;
    }

    get_session_id() {
        return this.session_id;
    }

    get_client_name() {
        return this.client_id.split("@")[0];
    }

    get_client_options() {
        return this.client_options;
    }

    get_id() {
        return this.session_id+":"+this.client_id;
    }

    open(send_fn) {
        this.send_fn = send_fn;
        this.is_open = true;
    }

    set_message_handler(handler) {
        this.message_handler = handler;
    }

    send_message(...message) {
        if (this.is_open) {
            this.send_fn(...message);
        } else {
            throw new Error("cannot send message, client is closed");
        }
    }

    async recv_message(...msg) {
        if (this.message_handler) {
            try {
                await this.message_handler(...msg);
            } catch(e) {
                console.error(e);
            }
        } else {
            console.warn("No message_handler");
        }
    }

     close() {
         this.is_open = false;
         this.send_fn = null;
     }
}

/* hyrrokkin_engine/message_utils.js */

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

/* hyrrokkin_engine/wrapper.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.Wrapper = class {

    constructor(target_id, target_type, data_store_utils, services,  send_message_cb) {
        this.target_id = target_id;
        this.target_type = target_type;
        this.data_store_utils = data_store_utils;
        this.services = services;
        this.clients = {};
        this.instance = null;
        this.services.wrapper = this;
        this.send_message_cb = send_message_cb;
        this.services.wrapper = this;
    }

    async set_instance(instance) {
        this.instance = instance;
        await this.load();
    }

    async load() {
        if (this.instance.load) {
            try {
                await this.instance.load();
            } catch(e) {
                console.error(e);
            }
        }
    }

    get_instance() {
        return this.instance;
    }

    async get_properties() {
        return await this.data_store_utils.get_properties();
    }

    async set_properties(properties) {
        await this.data_store_utils.set_properties(properties);
    }

    async get_data(key) {
        return await this.data_store_utils.get_data(key);
    }

    async set_data(key, data) {
        await this.data_store_utils.set_data(key, data);
    }

    async get_data_keys() {
        return await this.data_store_utils.get_data_keys();
    }

    get_services() {
        return this.services;
    }

    async open_client(session_id, client_id, client_options) {
        if (this.instance && this.instance.open_client) {
            try {
                let client = new hyrrokkin_engine.Client(session_id, client_id, client_options);
                client.open((...msg) => {
                    this.send_message_cb(session_id, client_id, ...msg);
                });
                await this.instance.open_client(client);
                this.clients[session_id+":"+client_id] = client;
            } catch(e) {
                console.error(e);
            }
        }
    }

    async recv_message(session_id, client_id, ...msg) {
        let client = this.clients[session_id+":"+client_id];
        if (client) {
            await client.recv_message(...msg);
        }
    }

    async close_client(session_id, client_id) {
        let client = this.clients[session_id+":"+client_id];
        if (this.instance && this.instance.close_client) {
            try {
                await this.instance.close_client(client);
            } catch(e) {
                console.error(e);
            }
        }
        client.close();
        delete this.clients[session_id+":"+client_id];
    }
}

/* hyrrokkin_engine/port_type.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.PortType = class {
  
  constructor(direction, is_input) {
    this.direction = direction;
    this.link_type = "";
    this.metadata = {};
    this.allow_multiple_connections = null;
    this.is_input = is_input;
  }

  deserialise(obj) {
    if (obj["link_type"]) {
      this.link_type = obj["link_type"];
    }
    if (obj["metadata"]) {
      this.metadata = obj["metadata"];
    }
    if ("allow_multiple_connections" in obj) {
      this.allow_multiple_connections = obj["allow_multiple_connections"];
    } else {
      this.allow_multiple_connections = false;
    }
  }

  get_link_type() {
    return this.link_type;
  }

  get_allow_multiple_connections() {
    return this.allow_multiple_connections;
  }

  get_metadata() {
      return this.metadata;
  }
}



/* hyrrokkin_engine/link_type.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.LinkType = class {
  
  constructor(link_type_id, package_type, schema) {
    this.metadata = schema["metadata"] || {};
    this.id = package_type.get_qualified_id(link_type_id);
    this.package_id = package_type.get_id();
  }

  get_metadata() {
      return this.metadata;
  }

  get_id() {
    return this.id;
  }

  get_package_id() {
    return this.package_id;
  }
}



/* hyrrokkin_engine/node_type.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.NodeType = class {

  constructor(node_type_id, package_type, schema) {
    this.id = package_type.get_qualified_id(node_type_id);
    this.package_type = package_type;
    this.schema = schema;
    this.package_id = package_type.get_id();
    this.metadata = schema["metadata"] || {};

    let input_ports = schema["input_ports"] || {};
    let output_ports = schema["output_ports"] || {};

    this.input_ports = {};
    this.output_ports = {};

    for (let key in input_ports) {
      let pt = new hyrrokkin_engine.PortType("input", true);
      pt.deserialise(input_ports[key]);
      this.input_ports[key] = pt;
    }

    for (let key in output_ports) {
      let pt = new hyrrokkin_engine.PortType("output", false);
      pt.deserialise(output_ports[key]);
      this.output_ports[key] = pt;
    }
  }

  get_metadata() {
      return this.metadata;
  }

  get_schema() {
    return this.schema;
  }

  allow_multiple_input_connections(input_port_name) {
    return this.input_ports[input_port_name].get_allow_multiple_connections();
  }

  allow_multiple_output_connections(output_port_name) {
    return this.output_ports[output_port_name].get_allow_multiple_connections();
  }

  get_input_link_type(input_port_name) {
    return this.input_ports[input_port_name].get_link_type();
  }

  get_output_link_type(output_port_name) {
    return this.output_ports[output_port_name].get_link_type();
  }

  get_id() {
    return this.id;
  }

  get_type() {
    return this.id;
  }

  get_package_id() {
    return this.package_id;
  }

  get_package_type() {
    return this.package_type;
  }
}




/* hyrrokkin_engine/package_type.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.PackageType = class {
  
  constructor(id, url, obj) {
    this.id = id;
    this.metadata = obj["metadata"];

    this.base_url = url;
    this.configuration = obj["configuration"] || {};
    this.sources = [];
    this.node_types = {};
    this.link_types = {};
    this.schema = obj;

    let node_types = obj["node_types"];
    for(let node_type_id in node_types) {
        this.node_types[node_type_id] = new hyrrokkin_engine.NodeType(node_type_id, this, node_types[node_type_id]);
    }

    let link_types = obj["link_types"];
    for(let link_type_id in link_types) {
        this.link_types[link_type_id] = new hyrrokkin_engine.LinkType(link_type_id, this, link_types[link_type_id]);
    }
  }

  async load_sources() {
    const sources_url = this.base_url + "/javascript.json";
    try {
      this.sources = await fetch(sources_url)
          .then(
              r => r.json()
          ).then(
              o => o["source_paths"]
          );
    } catch(e) {
      this.sources = [];
    }
  }

  get_sources() {
    return this.sources;
  }

  get_schema() {
    return this.schema;
  }

  get_id() {
    return this.id;
  }

  get_node_types() {
    return this.node_types;
  }

  get_node_type(node_type_id) {
    return this.node_types[node_type_id];
  }

  get_link_types() {
    return this.link_types;
  }

  get_metadata() {
    return this.metadata;
  }

  get_base_url() {
    return this.base_url;
  }

  get_resource_url(resource) {
    if (resource.startsWith("http")) {
      // resource is already an absolute URL
      return resource;
    }
    let resource_url =  this.base_url+"/"+resource;
    return String(resource_url);
  }

  get_qualified_id(id) {
    return this.id + ":" + id;
  }

  get_configuration() {
    return this.configuration;
  }
}

hyrrokkin_engine.PackageType.load = function(id, obj, url) {
  return new hyrrokkin_engine.PackageType(id, url, obj);
}



/* hyrrokkin_engine/configuration_service_interface.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

/**
 * An interface supplying services to a package configuration
 *
 * @interface
 * @type {hyrrokkin_engine.ConfigurationServiceInterface}
 */
hyrrokkin_engine.ConfigurationServiceInterface = class {

    /**
     * Get the version string for this package
     *
     * @returns {string} the package version or empty string if the package has no version metadata
     */
    get_package_version() {
    }

    /**
     * Get the properties associated with this configuration
     *
     * @returns {Object} the value of the properties
     */
    async get_properties() {
    }

    /**
     * Set the properties associated with this configuration
     *
     * @param {Object} properties the properties to set, must be an Object that is JSON serialisable
     */
    async set_properties(properties) {
    }

    /**
     * Retrieve data associated with a key or null if no data is associated with that key
     *
     * @param {string} key the key value
     *
     * @return {Promise<(ArrayBuffer|null)>}
     */
    async get_data(key) {
    }

    /**
     * Store data associated with a key
     *
     * @param {string} key the key value
     * @param {(ArrayBuffer|null)} data the data value (pass null to delete data associated with the key)
     *
     * @return {Promise<void>}
     */
    async set_data(key, data) {
    }

    /**
     * Sets a status message for this package
     *
     * @param {string} status_msg the status message
     * @param {string} level, one of "info", "warning", "error"
     */
    set_status(status_msg, level) {
    }

    /**
     * Clears the status message for this package
     */
    clear_status() {
    }

    /**
     * Resolve a relative resource path based on the location of the package schema
     *
     * @param resource_path
     */
    resolve_resource(resource_path) {
    }

    /**
     * Gets the configuration instance associated with a package.
     *
     * @param {string} package_id the id of the package
     *
     * @returns {(object|null)} the configuration instance or null if no configuration is defined for the package
     */
    get_configuration(package_id) {
    }

    /**
     * Called to request that a client of this configuration be opened
     *
     * @param {string} client_name: the type of client to load
     * @param {string|undefined} session_id: the session in which the client should be opened (if undefined, open in all sessions)
     */
    request_open_client(client_name, session_id) {
    }

}

/* hyrrokkin_engine/configuration_service.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.ConfigurationService = class extends hyrrokkin_engine.ConfigurationServiceInterface {

    constructor(package_id, package_version, base_url) {
        super();
        this.package_id = package_id;
        this.package_version = package_version;
        this.base_url = base_url;
        this.wrapper = null;
    }

    get_package_version() {
        return this.package_version;
    }

    async get_properties() {
        return await this.wrapper.get_properties();
    }

    async set_properties(properties) {
        await this.wrapper.set_properties(properties);
    }

    resolve_resource(resource_path) {
        return this.base_url + "/" + resource_path;
    }

    async get_data(key) {
        return await this.wrapper.get_data(key);
    }

    async set_data(key, data) {
        await this.wrapper.set_data(key, data);
    }

    async get_data_keys() {
        return await this.wrapper.get_data_keys();
    }

    set_status(status_msg, level) {
        this.wrapper.set_status(status_msg, level);
    }

    clear_status() {
        this.wrapper.set_status("", "");
    }

    get_configuration(package_id) {
        let configuration_wrapper = this.wrapper.get_configuration(package_id);
        if (configuration_wrapper) {
            return configuration_wrapper.get_instance();
        } else {
            return null;
        }
    }

    request_open_client(client_name) {
        this.wrapper.request_open_client(client_name);
    }
}


/* hyrrokkin_engine/configuration_wrapper.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.ConfigurationWrapper = class extends hyrrokkin_engine.Wrapper {

    constructor(executor, data_store_utils, package_id, services, send_message_cb) {
        super(package_id, "configuration", data_store_utils, services, send_message_cb);
        this.executor = executor;
        this.package_id = package_id;
    }

    get_configuration(package_id) {
        return this.executor.get_configuration_wrapper(package_id);
    }

    async create_node(node_type_id, service) {
        if (this.instance.create_node) {
            try {
                return await this.instance.create_node(node_type_id, service);
            } catch(ex) {
                console.error(ex);
            }
        }
    }

    set_status(status_msg, level) {
        this.executor.update_configuration_status(this.package_id, level, status_msg);
    }

    request_open_client(client_name, session_id) {
        this.executor.request_open_client(this.package_id, "configuration", session_id, client_name);
    }

    open_session(session_id) {
        if (this.instance.open_session) {
            try {
                this.instance.open_session(session_id);
            } catch(ex) {
                console.error(ex);
            }
        }
    }

    close_session(session_id) {
        if (this.instance.close_session) {
            try {
                this.instance.close_session(session_id);
            } catch(ex) {
                console.error(ex);
            }
        }
    }

    decode(encoded_bytes, link_type) {
        if (this.instance.constructor.decode) {
            try {
                return this.instance.constructor.decode(encoded_bytes, link_type);
            } catch (ex) {
                console.error(ex);
            }
        }
        return null;
    }

    encode(value, link_type) {
        if (this.instance.constructor.encode) {
            try {
                return this.instance.constructor.encode(value, link_type);
            } catch (ex) {
                console.error(ex);
            }
        }
        return null;
    }
}

/* hyrrokkin_engine/node_service_interface.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

/**
 * An interface supplying services to a node
 *
 * @interface
 * @type {hyrrokkin_engine.NodeServiceInterface}
 */
hyrrokkin_engine.NodeServiceInterface = class {

    /**
     * Get the unique ID of this node
     *
     * @returns {string} the node id
     */
    get_node_id() {
    }

    /**
     * Request that this node is re-run.  Typically called after a change to the node that would alter the output values
     * if there was no change to the inputs.
     */
    async request_run() {
    }

    /**
     * Get the set of properties associated with this node
     *
     * @returns {Object} the value of the properties
     */
    async get_properties() {
    }

    /**
     * Set the properties associated with this node
     *
     * @param {Object} properties the properties to set, must be an Object that is JSON serialisable
     */
    async set_properties(properties) {
    }

    /**
     * Retrieve data associated with a key or null if no data is associated with that key
     *
     * @param {string} key the key value
     *
     * @return {Promise<(ArrayBuffer|null)>}
     */
    async get_data(key) {
    }

    /**
     * Store data associated with a key
     *
     * @param {string} key the key value
     * @param {(ArrayBuffer|null)} data the data value (pass null to delete data associated with the key)
     *
     * @return {Promise<void>}
     */
    async set_data(key, data) {
    }

    /**
     * Sets a status message for this node
     *
     * @param {string} status_msg the status message
     * @param {string} level, one of "info", "warning", "error"
     */
    set_status(status_msg, level) {
    }

    /**
     * Clears the status message for this package
     */
    clear_status() {
    }

    /**
     * Take manual control of the running state
     *
     * @param {string} new_state one of "pending", "running", "completed", "failed"
     */
    set_running_state(new_state) {
    }

    /**
     * Resolve a relative resource path based on the location of the package schema
     *
     * @param resource_path
     */
    resolve_resource(resource_path) {
    }

    /**
     * Gets the configuration instance associated with a package.
     *
     * @param {string} [package_id] the id of the package, use the node's package id if not provided
     *
     * @returns {(object|null)} the configuration instance or null if no configuration is defined for the package
     */
    get_configuration(package_id) {
    }

    /**
     * Called to request that a client of this node be opened
     *
     * @param {string} client_name: the type of client to open
     * @param {string|undefined} session_id: the session in which the client should be opened (if undefined, open in all sessions)
     */
    request_open_client(client_name, session_id) {
    }

    /**
     * Gets the number of connections to/from this port
     *
     * @param {string} port_name: the name of the port to count connections to/from
     * @param {string} port_direction: specify whether the port is "input" or "output"
     */
    get_connection_count(port_name, port_direction) {
    }

}


/* hyrrokkin_engine/node_service.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.NodeService = class extends hyrrokkin_engine.NodeServiceInterface {

    constructor(node_id, base_url) {
        super();
        this.node_id = node_id;
        this.base_url = base_url;
        this.wrapper = null;
        this.active = true;
    }

    set_wrapper(wrapper) {
        this.wrapper = wrapper;
    }

    async get_properties() {
        return await this.wrapper.get_properties();
    }

    async set_properties(properties) {
        await this.wrapper.set_properties(properties);
    }

    resolve_resource(resource_path) {
        return this.base_url + "/" + resource_path;
    }

    async get_data(key) {
        if (this.active) {
            return await this.wrapper.get_data(key);
        }
    }

    async set_data(key, data) {
        if (this.active) {
            await this.wrapper.set_data(key, data);
        }
    }

    async get_data_keys() {
        if (this.active) {
            return await this.wrapper.get_data_keys();
        }
    }

    get_node_id() {
        return this.node_id;
    }

    get_configuration(package_id) {
        let configuration_wrapper = this.wrapper.get_configuration(package_id);
        if (configuration_wrapper) {
            return configuration_wrapper.get_instance();
        } else {
            return null;
        }
    }

    async request_run() {
        if (this.active) {
            await this.wrapper.request_run(this.node_id);
        }
    }

    set_status(status_msg, level) {
        if (!status_msg) {
            status_msg = "";
        }
        if (!level) {
            level = "info";
        }
        if (this.active) {
            this.wrapper.set_status(status_msg, level);
        }
    }

    clear_status() {
        this.wrapper.set_status("", "");
    }

    set_running_state(new_state) {
        if (this.active) {
            this.wrapper.set_running_state(new_state);
        }
    }

    request_open_client(client_name, session_id) {
        if (this.active) {
            this.wrapper.request_open_client(client_name, session_id);
        }
    }

    get_connection_count(port_name, port_direction) {
        if (this.active) {
            return this.wrapper.get_connection_count(port_name, port_direction);
        }
    }

    deactivate() {
        this.active = false;
    }
}


/* hyrrokkin_engine/node_wrapper.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.NodeWrapper = class extends hyrrokkin_engine.Wrapper {

    constructor(executor, data_store_utils, node_id, services, package_id, base_url, send_message_cb, get_connection_count_cb) {
        super(node_id, "node", data_store_utils, services, send_message_cb);
        this.executor = executor;
        this.package_id = package_id;
        this.base_url = base_url;
        this.node_id = node_id;
        this.get_connection_count_cb = get_connection_count_cb;
        this.active = true;
    }

    is_active() {
        return this.active;
    }

    reactivate() {
        this.active = true;
    }

    set_service(service) {
        this.services = service;
    }

    async reset_run() {
        if (this.instance && this.instance.reset_run) {
            try {
                await this.instance.reset_run();
            } catch(e) {
                console.error(e);
            }
        }
    }

    set_status(status_msg, level) {
        this.executor.update_node_status(this.node_id, level, status_msg);
    }

    set_running_state(new_state) {
        this.executor.update_running_state(this.node_id, new_state, true);
    }

    async execute(inputs) {
        if (this.active) {
            if (this.instance && this.instance.run) {
                try {
                    return await this.instance.run(inputs);
                } catch(e) {
                    throw e;
                }
            }
        }
        return {};
    }

    get_configuration(package_id) {
        return this.executor.get_configuration_wrapper(package_id || this.package_id);
    }

    async request_run() {
        await this.executor.request_run(this.node_id);
    }

    request_open_client(client_name, session_id) {
        this.executor.request_open_client(this.node_id, "node", session_id, client_name);
    }

    async remove() {
        if (this.instance && this.instance.remove) {
            try {
                await this.instance.remove();
            } catch(e) {
                console.error(e);
            }
        }
    }

    get_connection_count(port_name, port_direction) {
        return this.get_connection_count_cb(port_name, port_direction);
    }

    async stop_node() {
        this.active = false;
        this.services.deactivate();
        await this.reset_run();
        await this.remove();
    }
}

/* hyrrokkin_engine/graph_link.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.GraphLink = class {

    constructor(executor, from_node_id, from_port, to_node_id, to_port) {
        this.executor = executor;
        this.from_node_id = from_node_id;
        this.from_port = from_port;
        this.to_node_id = to_node_id;
        this.to_port = to_port;
    }

    has_value() {
        return this.from_port in (this.executor.node_outputs[this.from_node_id] || {});
    }

    get_value() {
        if (this.from_node_id in this.executor.node_outputs) {
            let outputs = this.executor.node_outputs[this.from_node_id];
            if (outputs && this.from_port in outputs) {
                return outputs[this.from_port];
            }
        }
        return null;
    }
}


/* hyrrokkin_engine/graph_executor.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.GraphExecutor = class {

    constructor(execution_monitor_callback,
                execution_state_callback, node_status_callback, configuration_status_callback,
                send_message_callback, output_notification_callback, request_open_client_callback, paused) {
        hyrrokkin_engine.graph_executor = this;

        this.injected_inputs = {};  // node-id => input-port => value
        this.output_listeners = {}; // node-id => output-port => true

        this.node_wrappers = {}; // node-id => node-wrapper
        this.links = {}; // link-id => GraphLink
        this.out_links = {}; // node-id => output-port => [GraphLink]
        this.in_links = {};  // node-id => input-port => [GraphLink]

        this.configuration_wrappers = {}; // package-id => configuration-wrapper
        this.base_urls = {}; // package-id => base_url

        this.dirty_nodes = {}; // node-id => True
        this.executing_nodes = {}; // node-id => True
        this.executed_nodes = {};  // node-id => True
        this.failed_nodes = {};    // node-id => Exception
        this.node_outputs = {}; // node-id => output-port => value

        this.target_queues = {"node": {}, "configuration": {}};
        this.target_is_handling = {"node": new Set(), "configuration": new Set()};

        this.paused = paused;
        this.execution_running = false;

        this.node_types = {};
        this.package_schemas = {};

        this.execution_monitor_callback = execution_monitor_callback;
        this.execution_state_callback = execution_state_callback;
        this.node_status_callback = node_status_callback;
        this.configuration_status_callback = configuration_status_callback;
        this.send_message_callback = send_message_callback;
        this.output_notification_callback = output_notification_callback;
        this.request_open_client_callback = request_open_client_callback;
    }

    queue_target(target_id, target_type, coro) {
        let target_queue = this.target_queues[target_type];
        if (!(target_id in target_queue)) {
            target_queue[target_id] = [];
        }
        target_queue[target_id].push(coro);

        if (!(target_id in this.target_is_handling[target_type])) {
            this.dispatch_target(target_id, target_type);
        }
    }

    dispatch_target(target_id, target_type) {
        let coro = this.target_queues[target_type][target_id][0];
        this.target_queues[target_type][target_id].splice(0, 1);
        this.target_is_handling[target_type].add(target_id)
        this.execute_target(target_id, target_type, coro).then(() => {
        });
    }

    async execute_target(target_id, target_type, coro) {
        await coro();
        this.target_is_handling[target_type].delete(target_id);
        if (this.target_queues[target_type][target_id].length > 0) {
            this.dispatch_target(target_id, target_type);
        }
    }

    decode_value(node_id, input_port_name, encoded_value) {
        let node_type_id = this.node_types[node_id];
        let package_id = node_type_id.split(":")[0];
        let node_type_name = node_type_id.split(":")[1];
        let node_type = this.package_schemas[package_id].get_node_type(node_type_name);
        let link_type_id = node_type.get_input_link_type(input_port_name);
        let link_package_id = link_type_id.split(":")[0];
        let link_type_name = link_type_id.split(":")[1];
        let configuration_wrapper = this.configuration_wrappers[link_package_id];
        return configuration_wrapper.decode(encoded_value, link_type_name);
    }

    encode_value(node_id, output_port_name, value) {
        let node_type_id = this.node_types[node_id];
        let package_id = node_type_id.split(":")[0];
        let node_type_name = node_type_id.split(":")[1];
        let node_type = this.package_schemas[package_id].get_node_type(node_type_name);
        let link_type_id = node_type.get_output_link_type(output_port_name);
        let link_package_id = link_type_id.split(":")[0];
        let link_type_name = link_type_id.split(":")[1];
        let configuration_wrapper = this.configuration_wrappers[link_package_id];
        return configuration_wrapper.encode(value, link_type_name);
    }

    async inject_input(node_id, input_port_name, values) {
        if (!(node_id in this.injected_inputs)) {
            this.injected_inputs[node_id] = {};
        }
        this.injected_inputs[node_id][input_port_name] = values;
        await this.mark_dirty(node_id);
    }

    async clear_injected_input(node_id, input_port_name) {
        if (node_id in this.injected_inputs) {
            if (input_port_name in this.injected_inputs[node_id]) {
                delete this.injected_inputs[node_id][input_port_name];
                await this.mark_dirty(node_id);
            }
        }
    }

    add_output_listener(node_id, output_port_name) {
        if (!(node_id in this.output_listeners)) {
            this.output_listeners[node_id] = {};
        }
        this.output_listeners[node_id][output_port_name] = true;
    }

    remove_output_listener(node_id, output_port_name) {
        if (node_id in this.output_listeners) {
            if (output_port_name in this.output_listeners[node_id]) {
                delete this.output_listeners[node_id][output_port_name];
            }
        }
    }

    get_output_value(node_id, port_name) {
        let node_outputs = this.node_outputs[node_id] || {};
        return node_outputs[port_name] || null;
    }

    get executing_node_count() {
        return Object.keys(this.executing_nodes).length;
    }

    count_failed() {
        return Object.keys(this.failed_nodes).length;
    }

    get_failures() {
        let failures = {};
        for(let node_id in this.failed_nodes) {
            failures[node_id] = String(this.failed_nodes[node_id]);
        }
        return failures;
    }

    async clear() {
        let node_ids = Object.keys(this.node_wrappers);
        for(let idx=0; idx<node_ids.length; idx++) {
            await this.remove_node(node_ids[idx]);
        }
        this.links = {};
        this.out_links = {};
        this.in_links = {};
    }

    valid_node(node_id) {
        return (node_id in this.node_wrappers);
    }

    async pause() {
        this.paused = true;
    }

    async resume() {
        this.paused = false;
        this.dispatch();
    }

    async mark_dirty(node_id) {
        if (node_id in this.dirty_nodes) {
            return;
        }

        this.dirty_nodes[node_id] = true;
        await this.reset_run(node_id);
        delete this.node_outputs[node_id];

        /* mark all downstream nodes as dirty */
        for (let out_port in this.out_links[node_id]) {
            let outgoing_links = this.out_links[node_id][out_port];
            for(let idx=0; idx<outgoing_links.length; idx++) {
                await this.mark_dirty(outgoing_links[idx].to_node_id);
            }
        }
    }

    async reset_run(node_id) {
        if (!(node_id in this.node_wrappers)) {
            return;
        }
        let wrapper = this.node_wrappers[node_id];
        this.update_running_state(node_id, "pending");
        delete this.failed_nodes[node_id];
        delete this.executed_nodes[node_id];
        await wrapper.reset_run();
    }

    dispatch() {
        if (this.paused) {
            return;
        }
        let launch_nodes = [];

        for (let node_id in this.dirty_nodes) {
            if (this.can_execute(node_id)) {
                launch_nodes.push(node_id);
            }
        }

        if (launch_nodes.length > 0 && this.executing_node_count === 0) {
            this.execution_started();
        }

        if (launch_nodes.length === 0 && this.executing_node_count === 0) {
            this.execution_complete();
        }

        for (let idx = 0; idx < launch_nodes.length; idx++) {
            let node_id = launch_nodes[idx];
            this.execute(node_id).then(() => {});
        }
    }

    can_execute(node_id) {
        if (node_id in this.executing_nodes) {
            // cannot execute a node that is already executing
            return false;
        }
        let node_wrapper = this.node_wrappers[node_id];
        if (!node_wrapper.is_active()) {
            return false;
        }
        for (let in_port in this.in_links[node_id]) {
            let in_links = this.in_links[node_id][in_port];
            for (let idx in in_links) {
                let in_link = in_links[idx];
                let pred_node_id = in_link.from_node_id;
                if (!(pred_node_id in this.executed_nodes)) {
                    return false;
                }
            }
        }
        return true;
    }

    pre_execute(node_id) {
        let inputs = {};
        let node_type_id = this.node_types[node_id];
        let package_id = node_type_id.split(":")[0];
        let node_type_name = node_type_id.split(":")[1];
        let node_type = this.package_schemas[package_id].get_node_type(node_type_name);
        let in_links = this.in_links[node_id] || {};
        for (let input_port_name in in_links) {
            if (in_links[input_port_name].length > 0) {
                let allow_multiple_connections = node_type.allow_multiple_input_connections(input_port_name);
                if (allow_multiple_connections) {
                    inputs[input_port_name] = [];
                    for (let idx in in_links[input_port_name]) {
                        let in_link = in_links[input_port_name][idx];
                        if (in_link.has_value()) {
                            inputs[input_port_name].push(in_link.get_value());
                        }
                    }
                } else {
                    if (in_links[input_port_name][0].has_value()) {
                        inputs[input_port_name] = in_links[input_port_name][0].get_value();
                    }
                }
            }
        }

        // add in any injected input values
        if (node_id in this.injected_inputs) {
            for (let injected_input_port_name in this.injected_inputs[node_id]) {
                let allow_multiple_connections = node_type.allow_multiple_input_connections(injected_input_port_name);
                let injected_values = this.injected_inputs[node_id][injected_input_port_name];
                if (allow_multiple_connections) {
                    if (!(injected_input_port_name in inputs)) {
                        inputs[injected_input_port_name] = [];
                    }
                    inputs[injected_input_port_name] = injected_values;
                } else {
                    inputs[injected_input_port_name] = injected_values[0];
                }
            }
        }

        return inputs;
    }

    async execute(node_id) {
        if (!(node_id in this.node_wrappers)) {
            return;
        }
        delete this.dirty_nodes[node_id];
        this.executing_nodes[node_id] = true;
        let node = this.node_wrappers[node_id];

        let inputs = this.pre_execute(node_id);
        this.update_running_state(node_id, "running");

        try {
            let outputs = await node.execute(inputs);
            this.update_running_state(node_id, "completed");
            await this.post_execute(node_id, outputs);
        } catch(ex) {
            this.update_running_state(node_id, "failed");
            await this.post_execute(node_id, null, ex);
        }

        this.dispatch();
    }

    async post_execute(node_id, outputs, reject_reason) {
        if (!this.valid_node(node_id)) {
            return; // node has been deleted since it started executing
        }
        delete this.executing_nodes[node_id];
        delete this.node_outputs[node_id];
        if (reject_reason) {
            if (reject_reason.stack) {
                // console.error(reject_reason.stack);
            }
            this.failed_nodes[node_id] = reject_reason;
        } else {
            this.node_outputs[node_id] = outputs;
            this.executed_nodes[node_id] = true;
        }

        let node_type_id = this.node_types[node_id];
        let package_id = node_type_id.split(":")[0];
        let node_type_name = node_type_id.split(":")[1];
        let node_type = this.package_schemas[package_id].get_node_type(node_type_name);

        if (node_id in this.output_listeners && this.output_notification_callback) {
            for (let port_name in outputs) {
                if (port_name in this.output_listeners[node_id]) {
                    await this.output_notification_callback(node_id, port_name,outputs[port_name]);
                }
            }
        }
    }

    async create_configuration_service(package_id, package_version, base_url, persistence) {
        let service = new hyrrokkin_engine.ConfigurationService(package_id, package_version, base_url);
        let wrapper = new hyrrokkin_engine.ConfigurationWrapper(this, persistence, package_id, service,
            (session_id, client_id,...msg) => this.send_message_callback(package_id, "configuration", session_id, client_id, ...msg));
        this.configuration_wrappers[package_id] = wrapper;
        return service;
    }

    async add_package(package_id, schema, base_url, configuration_instance) {
        await this.configuration_wrappers[package_id].set_instance(configuration_instance);
        this.package_schemas[package_id] = hyrrokkin_engine.PackageType.load(package_id, schema, base_url);
        this.base_urls[package_id] = base_url;
    }

    get_configuration_wrapper(package_id) {
        return this.configuration_wrappers[package_id];
    }

    async create_node_service(node_id, package_id, node_type_id, persistence) {
        let service = new hyrrokkin_engine.NodeService(node_id, this.base_urls[package_id]);
        this.node_types[node_id] = package_id+":"+node_type_id;
        let base_url = this.base_urls[package_id];
        let wrapper = new hyrrokkin_engine.NodeWrapper(this, persistence, node_id, service, package_id, base_url,
            (session_id, client_id,...msg) => this.send_message_callback(node_id, "node", session_id, client_id, ...msg),
            (port_name, port_direction) => this.get_connection_count(node_id,port_name,port_direction));
        this.node_wrappers[node_id] = wrapper;
        return service;
    }

    async add_node(node_id, package_id, node_type_id, persistence, copy_from_node_id) {
        let services = await this.create_node_service(node_id, package_id, node_type_id, persistence);
        let configuration_wrapper = this.get_configuration_wrapper(package_id);
        this.in_links[node_id] = {};
        this.out_links[node_id] = {};
        this.node_outputs[node_id] = {};
        let instance = await configuration_wrapper.create_node(node_type_id,services);
        if (copy_from_node_id) {
            await this.copy_node(copy_from_node_id, node_id);
        }
        await this.node_wrappers[node_id].set_instance(instance);
        await this.mark_dirty(node_id);
        this.dispatch();
        return instance;
    }

    async copy_node(source_node_id, dest_node_id) {
        let source_wrapper = this.node_wrappers[source_node_id];
        let dest_wrapper = this.node_wrappers[dest_node_id];
        let source_properties = await source_wrapper.get_properties();
        await dest_wrapper.set_properties(source_properties);
        let source_data_keys = await source_wrapper.get_data_keys();
        for (let idx = 0; idx < source_data_keys.length; idx++) {
            let data = await source_wrapper.get_data(source_data_keys[idx]);
            await dest_wrapper.set_data(source_data_keys[idx], data);
        }
    }

    async stop_node(node_id) {
        let wrapper = this.node_wrappers[node_id];
        await wrapper.stop_node();
    }

    async restart_node(node_id) {
        console.log("HERE");
        // restarting this node involves re-using the wrapper, but creating a new node instance and service
        let wrapper = this.node_wrappers[node_id];
        let node_type_id = this.node_types[node_id];
        let package_id = node_type_id.split(":")[0];
        let node_type_name = node_type_id.split(":")[1];

        let package_configuration = this.configuration_wrappers[package_id];
        let service = new hyrrokkin_engine.NodeService(node_id, this.base_urls[package_id]);
        wrapper.set_service(service);
        wrapper.reactivate();
        service.set_wrapper(wrapper);
        let new_instance = await package_configuration.create_node(node_type_name, service);
        await wrapper.set_instance(new_instance);
        await this.mark_dirty(node_id);
        this.dispatch();
    }

    async reset_node(node_id) {
        let wrapper = this.node_wrappers[node_id];
        await wrapper.set_properties({});
        let data_keys = await wrapper.get_data_keys();
        for (let idx = 0; idx < data_keys.length; idx++) {
            await wrapper.set_data(data_keys[idx], null);
        }
        await wrapper.load();
    }

    async add_link(link_id, from_node_id, from_port, to_node_id, to_port) {

        let link = new hyrrokkin_engine.GraphLink(this, from_node_id, from_port, to_node_id, to_port);
        this.links[link_id] = link;

        if (!(from_port in this.out_links[from_node_id])) {
            this.out_links[from_node_id][from_port] = [];
        }

        if (!(to_port in this.in_links[to_node_id])) {
            this.in_links[to_node_id][to_port] = [];
        }

        this.out_links[from_node_id][from_port].push(link);
        this.in_links[to_node_id][to_port].push(link);

        await this.mark_dirty(to_node_id);

        this.dispatch();
    }

    async remove_link(link_id) {
        let link = this.links[link_id];
        delete this.links[link_id];

        let arr_out = this.out_links[link.from_node_id][link.from_port];
        arr_out.splice(arr_out.indexOf(link), 1);

        let arr_in = this.in_links[link.to_node_id][link.to_port];
        arr_in.splice(arr_in.indexOf(link), 1);

        await this.mark_dirty(link.to_node_id);

        this.dispatch();
    }

    get_connection_count(node_id, port_name, port_direction) {
        switch(port_direction) {
            case "output":
                return ((this.out_links[node_id] || {})[port_name] || []).length;
            case "input":
                return ((this.in_links[node_id] || {})[port_name] || []).length;
        }
    }

    async remove_node(node_id) {
        // at this point any links into and out of this node should have been removed
        if (node_id in this.node_wrappers) {
            await this.node_wrappers[node_id].remove();
            delete this.node_wrappers[node_id];
        }
        if (node_id in this.executing_nodes) {
            delete this.executing_nodes[node_id];
        }
        if (node_id in this.failed_nodes) {
            delete this.failed_nodes[node_id];
        }
        if (node_id in this.executed_nodes) {
            delete this.executed_nodes[node_id];
        }
        if (node_id in this.dirty_nodes) {
            delete this.dirty_nodes[node_id];
        }
        if (node_id in this.node_outputs) {
            delete this.node_outputs[node_id];
        }
        if (node_id in this.node_types) {
            delete this.node_types[node_id];
        }
        if (node_id in this.injected_inputs) {
            delete this.injected_inputs[node_id];
        }
    }

    get_node(node_id) {
        return this.node_wrappers[node_id];
    }

    async request_run(node_id) {
        await this.mark_dirty(node_id);
        this.dispatch();
    }

    request_open_client(target_id, target_type, session_id, client_name) {
        if (this.request_open_client_callback) {
            this.request_open_client_callback(target_id, target_type, session_id, client_name);
        }
    }

    execution_started() {
        if (!this.execution_running) {
            this.execution_running = true;
            if (this.execution_monitor_callback) {
                this.execution_monitor_callback(false);
            }
        }
    }

    execution_complete() {
        if (this.execution_running) {
            this.execution_running = false;
            if (this.execution_monitor_callback) {
                this.execution_monitor_callback(true);
            }
        }
    }

    update_running_state(node_id, execution_state, is_manual) {
        if (this.execution_state_callback) {
            this.execution_state_callback(node_id, execution_state, is_manual !== undefined ? is_manual : false);
        }
    }

    update_node_status(node_id, level, msg) {
        if (this.node_status_callback) {
            this.node_status_callback(node_id, level, msg);
        }
    }

    update_configuration_status(package_id, level, msg) {
        if (this.configuration_status_callback) {
            this.configuration_status_callback(package_id, level, msg);
        }
    }

    open_session(session_id) {
        for(let package_id in this.configuration_wrappers) {
            this.configuration_wrappers[package_id].open_session(session_id);
        }
    }

    close_session(session_id) {
        for(let package_id in this.configuration_wrappers) {
            this.configuration_wrappers[package_id].close_session(session_id);
        }
    }

    async open_client(target_id, target_type, session_id, client_id, client_options) {
        this.queue_target(target_id, target_type, async () => {
            let wrapper = null;
            if (target_type === "node") {
                wrapper = this.node_wrappers[target_id];
            } else if (target_type === "configuration") {
                wrapper = this.configuration_wrappers[target_id];
            }
            if (wrapper) {
                await wrapper.open_client(session_id, client_id, client_options);
            }
        });
    }

    async recv_message(target_id, target_type, session_id, client_id, ...msg) {
        this.queue_target(target_id, target_type, async () => {
            let wrapper = null;
            if (target_type === "node") {
                wrapper = this.node_wrappers[target_id];
            } else if (target_type === "configuration") {
                wrapper = this.configuration_wrappers[target_id];
            }

            if (wrapper) {
                await wrapper.recv_message(session_id, client_id, ...msg);
            }
        });
    }

    async close_client(target_id, target_type, session_id, client_id) {
        this.queue_target(target_id, target_type, async () => {
            let wrapper = null;

            if (target_type === "node") {
                wrapper = this.node_wrappers[target_id];
            } else if (target_type === "configuration") {
                wrapper = this.configuration_wrappers[target_id];
            }
            if (wrapper) {
                await wrapper.close_client(session_id, client_id);
            }
        });
    }

    close() {
    }
}

/* hyrrokkin_engine_utils/expression_checker.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.ExpressionChecker = class {

    constructor() {
        this.unary_operator_typemaps = {};
        this.binary_operator_typemaps = {};
        this.function_typemaps = {};
        this.literal_typemapper = null;
    }

    add_unary_operator_types(name,output_type,input_type) {
        if (!(name in this.unary_operator_typemaps)) {
            this.unary_operator_typemaps[name] = [];
        }
        this.unary_operator_typemaps[name].push([output_type,input_type]);
    }

    add_binary_operator_types(name,output_type, input_type1, input_type2) {
        if (!(name in this.binary_operator_typemaps)) {
            this.binary_operator_typemaps[name] = [];
        }
        this.binary_operator_typemaps[name].push([output_type,input_type1,input_type2]);
    }

    add_function_types(name,output_type,...input_types) {
        if (!(name in this.function_typemaps)) {
            this.function_typemaps[name] = [];
        }
        this.function_typemaps[name].push([output_type].concat(input_types));
    }

    add_literal_typemapper(mapper_fn) {
        this.literal_typemapper = mapper_fn;
    }

    typematch(candidate_types, typemap_types) {
        if (candidate_types.length !== typemap_types.length) {
            return false;
        }
        for(let idx=0; idx<candidate_types.length; idx++) {
            if (candidate_types[idx] !== typemap_types[idx]) {
                if (typemap_types[idx] !== "*") {
                    return false;
                }
            }
        }
        return true;
    }

    check_expression(parsed_expression, name_typemap) {
        if (parsed_expression.name) {
            if (!(parsed_expression.name in name_typemap)) {
                return {"error_type":"invalid_name", "name":parsed_expression.name, "context": parsed_expression};
            } else {
                parsed_expression.type = name_typemap[parsed_expression.name];
                return null;
            }
        }

        if (parsed_expression.literal) {
            let typename = this.literal_typemapper(parsed_expression.literal);
            if (!typename) {
                return {"error_type":"literal_type_error", "literal":parsed_expression.literal, "context": parsed_expression};
            } else {
                parsed_expression.type = typename;
                 return null;
            }
        }

        if (parsed_expression.operator || parsed_expression.function) {
            for(let idx=0; idx<parsed_expression.args.length; idx++) {
                let error = this.check_expression(parsed_expression.args[idx], name_typemap);
                if (error !== null) {
                    return error;
                }
            }

            let types = [];
            parsed_expression.args.forEach(arg => {
                types.push(arg.type);
            });
            let typemap = null;

            if (parsed_expression.operator) {
                if (parsed_expression.args.length === 1) {
                    typemap = this.unary_operator_typemaps[parsed_expression.operator];
                } else {
                    typemap = this.binary_operator_typemaps[parsed_expression.operator];
                }
            } else {
                typemap = this.function_typemaps[parsed_expression.function];
            }

            if (typemap === undefined) {
                // operator or function name lookup failed
                if (parsed_expression.operator) {
                    return {
                        "error_type": "operator_type_missing",
                        "operator": parsed_expression.operator,
                        "context": parsed_expression
                    };
                } else {
                    return {
                        "error_type": "function_type_missing",
                        "function": parsed_expression.function,
                        "context": parsed_expression
                    };
                }
            }
            for(let idx=0; idx<typemap.length; idx++) {
                if (this.typematch(types,typemap[idx].slice(1))) {
                    parsed_expression.type = typemap[idx][0];
                    return null;
                }
            }
            // no type match
            if (parsed_expression.operator) {
                    return {
                        "error_type": "operator_type_error",
                        "operator": parsed_expression.operator,
                        "types": types,
                        "context": parsed_expression
                    };
            } else {
                return {
                    "error_type": "function_type_error",
                    "function": parsed_expression.function,
                    "types": types,
                    "context": parsed_expression
                };
            }
        }
    }
}

/* hyrrokkin_engine_utils/expression_parser.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.ExpressionParser = class {

    constructor() {
        this.input = undefined;
        this.unary_operators = {};
        this.binary_operators = {};
        this.reset();
    }

    reset() {
        // lexer state
        this.index = 0;
        this.tokens = [];
        this.current_token_type = undefined; // s_string, d_string, string, name, operator, number, open_parenthesis, close_parenthesis, comma
        this.current_token_start = 0;
        this.current_token = undefined;
    }

    add_unary_operator(name) {
        this.unary_operators[name] = true;
    }

    add_binary_operator(name,precedence) {
        this.binary_operators[name] = precedence;
    }

    is_alphanum(c) {
        return (this.is_alpha(c) || (c >= "0" && c <= "9"));
    }

    is_alpha(c) {
        return ((c >= "a" && c <= "z") || (c >= "A" && c <= "Z"));
    }

    flush_token() {
        if (this.current_token_type !== undefined) {
            if (this.current_token_type === "name") {
                // convert to name => operator if the name matches known operators
                if (this.current_token in this.binary_operators || this.current_token in this.unary_operators) {
                    this.current_token_type = "operator";
                }
            }
            this.tokens.push([this.current_token_type, this.current_token, this.current_token_start]);
        }
        this.current_token = "";
        this.current_token_type = undefined;
        this.current_token_start = undefined;
    }

    read_whitespace(c) {
        switch(this.current_token_type) {
            case "s_string":
            case "d_string":
                this.current_token += c;
                break;
            case "name":
            case "operator":
            case "number":
                this.flush_token();
                break;
        }
    }

    read_doublequote() {
        switch(this.current_token_type) {
            case "d_string":
                this.flush_token();
                break;
            case "s_string":
                this.current_token += '"';
                break;
            default:
                this.flush_token();
                this.current_token_type = "d_string";
                this.current_token_start = this.index;
                break;
        }
    }

    read_singlequote() {
        switch(this.current_token_type) {
            case "s_string":
                this.flush_token();
                break;
            case "d_string":
                this.current_token += "'";
                break;
            default:
                this.flush_token();
                this.current_token_type = "s_string";
                this.current_token_start = this.index;
                break;
        }
    }

    read_digit(c) {
        switch(this.current_token_type) {
            case "operator":
                this.flush_token();
            case undefined:
                this.current_token_type = "number";
                this.current_token_start = this.index;
                this.current_token = c;
                break;
            case "d_string":
            case "s_string":
            case "name":
            case "number":
                this.current_token += c;
                break;
        }
    }

    read_e(c) {
        switch(this.current_token_type) {
            case "number":
                // detect exponential notation E or e
                this.current_token += c;
                // special case, handle negative exponent eg 123e-10
                if (this.input[this.index+1] === "-") {
                    this.current_token += "-";
                    this.index += 1;
                }
                break;

            default:
                this.read_default(c);
                break;
        }
    }

    read_parenthesis(c) {
        switch(this.current_token_type) {
            case "s_string":
            case "d_string":
                this.current_token += c;
                break;
            default:
                this.flush_token();
                this.tokens.push([(c === "(") ? "open_parenthesis" : "close_parenthesis",c, this.index]);
                break;
        }
    }

    read_comma(c) {
        switch(this.current_token_type) {
            case "d_string":
            case "s_string":
                this.current_token += c;
                break;
            default:
                this.flush_token();
                this.tokens.push(["comma",c, this.index]);
                break;
        }
    }

    read_default(c) {
        switch(this.current_token_type) {
            case "d_string":
            case "s_string":
                this.current_token += c;
                break;
            case "name":
                if (this.is_alphanum(c) || c === "_" || c === ".") {
                    this.current_token += c;
                } else {
                    this.flush_token();
                    this.current_token_type = "operator";
                    this.current_token_start = this.index;
                    this.current_token = c;
                }
                break;
            case "number":
                this.flush_token();
                // todo handle exponential notation eg 1.23e10
                if (this.is_alphanum(c)) {
                    throw {"error":"invalid_number","error_pos":this.index,"error_content":c};
                } else {
                    this.flush_token();
                    this.current_token_type = "operator";
                    this.current_token_start = this.index;
                    this.current_token = c;
                }
                break;
            case "operator":
                if (this.is_alphanum(c)) {
                    this.flush_token();
                    this.current_token_type = "name";
                    this.current_token_start = this.index;
                    this.current_token = c;
                } else {
                    if (this.current_token in this.unary_operators || this.current_token in this.binary_operators) {
                        this.flush_token();
                        this.current_token_type = "operator";
                        this.current_token_start = this.index;
                    }
                    this.current_token += c;
                }
                break;
            case undefined:
                this.current_token = c;
                if (this.is_alpha(c)) {
                    this.current_token_type = "name";
                } else {
                    this.current_token_type = "operator";
                }
                this.current_token_start = this.index;
                break;
            default:
                throw {"error":"internal_error","error_pos":this.index};
        }
    }

    read_eos() {
        switch(this.current_token_type) {
            case "d_string":
            case "s_string":
                throw {"error":"unterminated_string","error_pos":this.input.length};
            default:
                this.flush_token();
        }
    }

    merge_string_tokens() {
        let merged_tokens = [];
        let buff = "";
        let buff_pos = -1;
        for(let idx=0; idx<this.tokens.length;idx++) {
            let t = this.tokens[idx];
            let ttype = t[0];
            let tcontent = t[1];
            let tstart = t[2];
            if (ttype === "s_string" || ttype === "d_string") {
                buff += tcontent;
                buff_pos = (buff_pos < 0) ? tstart : buff_pos;
            } else {
                if (buff_pos >= 0) {
                    merged_tokens.push(["string",buff,buff_pos]);
                    buff = "";
                    buff_pos = -1;
                }
                merged_tokens.push(t);
            }
        }
        if (buff_pos >= 0) {
            merged_tokens.push(["string", buff, buff_pos]);
        }
        this.tokens = merged_tokens;
    }

    lex() {
        this.reset();
        this.index = 0;
        while(this.index < this.input.length) {
            let c = this.input.charAt(this.index);
            switch(c) {
                case " ":
                case "\t":
                case "\n":
                    this.read_whitespace(c);
                    break;
                case "\"":
                    this.read_doublequote();
                    break;
                case "'":
                    this.read_singlequote();
                    break;
                case "(":
                case ")":
                    this.read_parenthesis(c);
                    break;
                case ",":
                    this.read_comma(c);
                    break;
                case "0":
                case "1":
                case "2":
                case "3":
                case "4":
                case "5":
                case "6":
                case "7":
                case "8":
                case "9":
                case ".":
                    this.read_digit(c);
                    break;
                case "e":
                case "E":
                    this.read_e(c);
                    break;
                default:
                    this.read_default(c);
                    break;
            }
            this.index += 1;
        }
        this.read_eos();
        this.merge_string_tokens();
        return this.tokens;
    }

    get_ascending_precedence() {
        let prec_list = [];
        for(let op in this.binary_operators) {
            prec_list.push(this.binary_operators[op]);
        }

        prec_list = [...new Set(prec_list)];

        prec_list = prec_list.sort();

        return prec_list;
    }

    parse(s) {
        this.input = s;
        try {
            this.lex();
            this.token_index = 0;
            let parsed = this.parse_expr();
            this.strip_debug(parsed);
            return parsed;
        } catch(ex) {
            return ex;
        }
    }

    get_parser_context() {
        return {
            "type": this.tokens[this.token_index][0],
            "content": this.tokens[this.token_index][1],
            "pos": this.tokens[this.token_index][2],
            "next_type": (this.token_index < this.tokens.length - 1) ? this.tokens[this.token_index+1][0] : null,
            "last_type": (this.token_index > 0) ? this.tokens[this.token_index-1][0] : null
        }
    }

    parse_function_call(name) {
        let ctx = this.get_parser_context();
        let result = {
            "function": name,
            "args": [],
            "pos": ctx.pos
        }
        // skip over function name and open parenthesis
        this.token_index += 2;

        // special case - no arguments
        ctx = this.get_parser_context();
        if (ctx.type === "close_parenthesis") {
            return result;
        }

        while(this.token_index < this.tokens.length) {
            ctx = this.get_parser_context();
            if (ctx.last_type === "close_parenthesis") {
                return result;
            } else {
                if (ctx.type === "comma") {
                    throw {"error": "comma_unexpected", "error_pos": ctx.pos};
                }
                // read an expression and a following comma or close parenthesis
                result.args.push(this.parse_expr());
            }
        }
        return result;
    }

    parse_expr() {
        let args = [];
        while(this.token_index < this.tokens.length) {
            let ctx = this.get_parser_context();
            switch(ctx.type) {
                case "name":
                    if (ctx.next_type === "open_parenthesis") {
                        args.push(this.parse_function_call(ctx.content));
                    } else {
                        this.token_index += 1;
                        args.push({"name":ctx.content,"pos":ctx.pos});
                    }
                    break;
                case "string":
                    args.push({"literal":ctx.content,"pos":ctx.pos});
                    this.token_index += 1;
                    break;
                case "number":
                    args.push({"literal":Number.parseFloat(ctx.content),"pos":ctx.pos});
                    this.token_index += 1;
                    break;
                case "open_parenthesis":
                    this.token_index += 1;
                    args.push(this.parse_expr());
                    break;
                case "close_parenthesis":
                case "comma":
                    this.token_index += 1;
                    return this.refine_expr(args,this.token_index-1);
                case "operator":
                    args.push({"operator":ctx.content,"pos":ctx.pos});
                    this.token_index += 1;
                    break;
            }
        }
        return this.refine_expr(args,this.token_index);
    }

    refine_binary(args) {
        let precedences = this.get_ascending_precedence();
        for(let precedence_idx=0; precedence_idx < precedences.length; precedence_idx++) {
            let precedence = precedences[precedence_idx];
            for(let idx=args.length-2; idx>=0; idx-=2) {
                let subexpr = args[idx];
                if (subexpr.operator && this.binary_operators[subexpr.operator] === precedence) {
                    let lhs = args.slice(0,idx);
                    let rhs = args.slice(idx+1,args.length);
                    return {"operator":subexpr.operator,"pos":subexpr.pos,"args":[this.refine_binary(lhs),this.refine_binary(rhs)]};
                }
            }
        }
        return args[0];
    }

    refine_expr(args,end_pos) {
        if (args.length === 0) {
            throw {"error": "expression_expected", "pos": end_pos};
        }
        // first deal with unary operators
        for(let i=args.length-1; i>=0; i--) {
            // unary operators
            let arg = args[i];
            let prev_arg = (i>0) ? args[i-1] : undefined;
            let next_arg = (i<args.length-1) ? args[i+1] : undefined;
            if (arg.operator && (arg.operator in this.unary_operators)) {
                if (prev_arg === undefined || prev_arg.operator) {
                    if (next_arg !== undefined) {
                        // special case, convert unary - followed by a number literal to a negative number literal
                        if (arg.operator === "-" && typeof next_arg.literal === "number") {
                            args = args.slice(0, i).concat([{
                                "literal": -1*next_arg.literal,
                                "pos": arg.pos
                            }]).concat(args.slice(i + 2, args.length));
                        } else {
                            args = args.slice(0, i).concat([{
                                "operator": arg.operator,
                                "pos": arg.pos,
                                "args": [next_arg]
                            }]).concat(args.slice(i + 2, args.length));
                        }
                    }
                }
            }
        }

        // check that args are correctly formed, with operators in every second location, ie "e op e op e" and all operators
        // are binary operators with no arguments already assigned
        for(let i=0; i<args.length; i+=1) {
            let arg = args[i];
            if (i % 2 === 1) {
                if (!arg.operator || "args" in arg) {
                    throw {"error": "operator_expected", "error_pos": arg.pos };
                } else {
                    if (!(arg.operator in this.binary_operators)) {
                        throw {"error": "binary_operator_expected", "error_pos": arg.pos};
                    }
                }
            }
            if (i % 2 === 0 || i === args.length-1) {
                if (arg.operator && !("args" in arg)) {
                    throw {"error": "operator_unexpected", "error_pos": arg.pos};
                }
            }
        }

        return this.refine_binary(args);
    }

    strip_debug(expr) {
        if ("pos" in expr) {
            delete expr.pos;
        }
        if ("args" in expr) {
            expr.args.forEach(e => this.strip_debug(e));
        }
    }

}


/* hyrrokkin_engine_utils/value_stream.js */

/**
 * Hyrrokkin Engine Namespace
 * @namespace
*/
var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.AsyncLock = class {

  /**
   * Implement a simple asynchronous mutex-like lock.  Call acquire() to obtain the lock and release() to release it.
   */
  constructor () {
    this.releases = [];
    this.locked = false;
  }

  dispatch() {
     if (this.releases.length > 0 && this.locked === false) {
         this.releases.shift()();
         this.locked = true;
     }
  }

  /**
   * Release this lock so that another may acquire it
   */
  release() {
      this.locked = false;
      this.dispatch();
  }

  /**
   *  Acquire this lock, blocking others from acquiring it
   *
   *  @return {Promise<unknown>}
   */
  acquire() {
    return new Promise(resolve => {
        this.releases.push(resolve);
        this.dispatch();
    });
  }
}

/**
 * A callback that is invoked for a subscriber when a value is received from a stream
 *
 * @callback hyrrokkin_engine.ValueStream~subscriberCallback
 *
 * @param {*} value the value received from the stream
 *
 * @return {Promise<undefined>}
 */

/**
 * A callback that is invoked for a subscriber when a stream is closed
 *
 * @callback hyrrokkin_engine.ValueStream~closeCallback
 *
 * @param {boolean} was_cancelled set to true if the stream was interrupted due to an error
 *
 * @return {Promise<undefined>} a transformed value
 */

/**
 * Class representing a Value Stream
 *
 * @typedef hyrrokkin_engine.ValueStream
 */
hyrrokkin_engine.ValueStream = class {

    /**
     * Create a value stream base class.  Do not call this directly, use the static methods create_from_streams
     * or create_source to construct an appropriate subclass
     *
     * @param {int} activation_threshold if supplied, block publishing onto this stream until this many subscribers are active
     */
    constructor(activation_threshold) {
        // map from subscriber_id to an async function that receives published values
        this.subscribers = {};
        // map from subscriber_id to an async function that is called when the stream closes
        this.close_fns = {};
        // count of subscriptions issued on this stream
        this.subscriber_count = 0;

        // block publication on this stream until this many subscribers are attached
        this.activation_threshold = activation_threshold;
        this.active = false;

        this.is_closed = false;
        this.was_cancelled = false

        this.publication_lock = new hyrrokkin_engine.AsyncLock();
        this.completion_lock = new hyrrokkin_engine.AsyncLock();
    }

    async prepare() {
        if (this.activation_threshold) {
            await this.publication_lock.acquire();
        } else {
            this.active = true;
        }
        await this.completion_lock.acquire();
    }

    /**
     * Create a value stream based on 1 or more other value streams.  The resulting stream will publish events received on
     * any of the input streams.
     *
     * @param {hyrrokkin_engine.ValueStream[]} input_streams a list of input streams.
     * @param {(transformFunction|asyncTransformFunction)=} transform_function an optional function to transform values received on the input streams.  May be async or non-async.
     * @param {int=} activation_threshold if supplied, block publishing onto this stream until this many subscribers are subscribed
     *
     * @return {Promise<hyrrokkin_engine.ValueStream>}
     */
    static
    async create_from_streams(input_streams, transform_function, activation_threshold) {
        let stream = new hyrrokkin_engine.TransformStream(activation_threshold, input_streams, transform_function);
        await stream.prepare();
        return stream;
    }

    /**
     * Create a value source stream.  Call the publish method to publish values to this stream.
     *
     * @param {int=} activation_threshold if supplied, block publishing onto this stream until this many subscribers are active
     * @return {Promise<hyrrokkin_engine.ValueStream>}
     */
    static
    async create_source(activation_threshold) {
        let stream = new hyrrokkin_engine.SourceStream(activation_threshold);
        await stream.prepare()
        return stream;
    }

    /**
     * Activate this stream, unblocking the publish method.
     *
     * This is not usually called directly, but automatically once enough subscribers are subscribed.
     */
    activate() {
        if (this.active === false) {
            this.active = true;
            this.publication_lock.release();
        }
    }

    /**
     * Check that values can be published to this stream
     *
     * @return {boolean} true iff a caller can use the publish method without being blocked or raising an exception
     *
     * @throws {Error} if this stream does not allow the publish method to be called
     */
    can_publish() {
        return (this.active && !this.is_closed);
    }

    /**
     * Subscribe to values in this stream, passing in two callback functions
     *
     * @param {hyrrokkin_engine.ValueStream~subscriberCallback=} subscriber an async function that is invoked with a value published on the stream
     * @param {hyrrokkin_engine.ValueStream~closeCallback=} close_fn an optional function that is called when th stream is closed
     *
     * @return {string} a subscriber-id that is unique to this stream.  Pass this to the unsubscribe method to unsubscribe these functions from further values published on the stream
     */
    subscribe(subscriber, close_fn) {
        let subscriber_id = "s" + this.subscriber_count;
        this.subscriber_count += 1;
        this.subscribers[subscriber_id] = subscriber;
        if (close_fn) {
            this.close_fns[subscriber_id] = close_fn;
        }
        if (this.active === false && (this.activation_threshold > 0) &&
                (Object.keys(this.subscribers).length >= this.activation_threshold)) {
            this.activate();
        }
        return subscriber_id;
    }

    /**
     * Unsubscribe from further values published on this stream
     *
     * @param {string} subscriber_id a subscriber id returned from a call to the subscribe method
     */
    unsubscribe(subscriber_id) {
        if (subscriber_id in this.subscribers) {
            delete this.subscribers[subscriber_id];
        }
        if (subscriber_id in this.close_fns) {
            delete this.close_fns[subscriber_id];
        }
    }

    /**
     * Publish a value onto the stream.  This call will block until the stream becomes active.
     *
     * @param {*} value the value to be published
     * @return {Promise<boolean>} true if the value was published, false if the stream was closed
     *
     * @throws {Error} if this stream does not allow the publish method to be called
     */
    async publish(value) {
        if (this.is_closed) {
            return false;
        }

        await this.publication_lock.acquire();

        try {
            let promises = [];
            for (let subscriber_id in this.subscribers) {
                let subscriber = this.subscribers[subscriber_id];
                promises.push(subscriber(value));
            }
            await Promise.all(promises);
        } finally {
            this.publication_lock.release();
        }
        return true;
    }

    /**
     * Close this stream.  Closing will prevent further values from being published to subscribers.  Subscribers will be
     * notified if they registered a callback for the close_fn parameter when they called the subscribe method
     *
     * @param {boolean} was_cancelled True iff this stream is being closed abnormally (due to an error)
     *
     * @return {Promise<void>}
     */
    async close(was_cancelled) {
        if (!this.is_closed) {
            this.is_closed = true;
            this.was_cancelled = was_cancelled;
            this.completion_lock.release();
            for (let subscrber_id in this.close_fns) {
                let close_fn = this.close_fns[subscrber_id];
                await close_fn(was_cancelled);
            }
        }
    }

    /**
     *  Block until the stream has closed
     *
     * @return {Promise<boolean>} return True if the stream was closed abnormally, False if the stream was closed normally.
     */
    async waitfor_close() {
        await this.completion_lock.acquire();
        this.completion_lock.release();
        return this.was_cancelled;
    }
}

hyrrokkin_engine.TransformStream = class extends hyrrokkin_engine.ValueStream {

    constructor(activation_threshold, input_streams, transform_fn) {
        super(activation_threshold);
        this.input_streams = [];
        this.closed_count = 0;
        this.cancelled_count = 0;
        this.input_stream_count = 0;
        this.subscriber_ids = [];
        input_streams.forEach(input_stream => {
            this.attach_to(input_stream, transform_fn);
        });
    }

    /**
     * Attach an input stream and optionally, a transform function which will transform values received from that stream
     *
     * @param {hyrrokkin_engine.ValueStream} input_stream an input stream
     * @param {transformFunction|asyncTransformFunction} transform_fn an optional function to transform values received on the input streams.  May be async or non-async.
     * @return {string} the subscriber id used to subscribe to the input stream
     */
    attach_to(input_stream, transform_fn) {

        let subscriber_fn = async (value) => {
            if (transform_fn) {
                value = await transform_fn(value);
            }
            await super.publish(value);
        }

        let close_fn = async (was_cancelled) => {
            this.closed_count += 1
            if (was_cancelled) {
                this.cancelled_count += 1;
            }
            if (this.closed_count === this.input_stream_count) {
                await this.close(was_cancelled = (this.cancelled_count > 0));
            }
        }
        let subscriber_id = input_stream.subscribe(subscriber_fn, close_fn);
        this.subscriber_ids.push(subscriber_id);
        this.input_streams.push(input_stream);
        this.input_stream_count += 1;
        return subscriber_id;
    }

    /**
     * Detach from all input streams.
     */
    detach() {
        for (let idx = 0; idx < this.input_stream_count; idx++) {
            this.input_streams[idx].unsubscribe(this.subscriber_ids[idx]);
        }
        this.input_streams = [];
        this.subscriber_ids = [];
        this.input_stream_count = 0;
    }

    /**
     * Check that values can be published to this stream
     *
     * @throws {Error} Always throws an Error - this kind of stream does not allow values to be published to it
     */
    can_publish() {
        throw new Error("Cannot publish directly to this kind of stream");
    }

    /**
     * Publish a value to this stream
     *
     * @throws {Error} Always throws an Error - this kind of stream does not allow values to be published to it
     */
    async publish(value) {
        throw new Error("Cannot publish directly to this kind of stream");
    }
}

hyrrokkin_engine.SourceStream = class extends hyrrokkin_engine.ValueStream {

    /**
     * Create a value stream which enables the caller to then publish values
     *
     * @param {int=} activation_threshold if supplied, block publishing onto this stream until this many subscribers are active
     */
    constructor(activation_threshold) {
        super(activation_threshold);
    }
}










/* hyrrokkin_engine_utils/value_collection.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

/**
 * values stored in a collection can be of any type
 *
 * @typedef AnyValue
 */

/**
 * A function which transforms a value
 *
 * @callback transformFunction
 *
 * @param {AnyValue} value the value to be transformed
 *
 * @return {AnyValue} a transformed value
 */

/**
 * An async  function which transforms a value
 *
 * @callback asyncTransformFunction
 *
 * @param {AnyValue} value the value to be transformed
 *
 * @return {Promise<AnyValue>} a transformed value
 */


hyrrokkin_engine.ValueCollectionIterator = class {

    constructor(collection) {
        this.collection = collection;
        this.position = 0;
    }

    async next() {
        if (this.position < this.collection.size()) {
            let value = await this.collection.get(this.position);
            this.position += 1;
            return {"value": value};
        }
        return {"done":true};
    }

}

/**
 * Implement a collection of values.
 *
 * Call hyrrokkin_engine.ValueCollection.create_from_collections or hyrrokkin_engine.ValueCollection.create_source
 * static methods to create an appropriate instance of this class.
 *
 * @type {hyrrokkin_engine.ValueCollection}
 *
 */
hyrrokkin_engine.ValueCollection = class {


    constructor() {
        this.is_closed = false;
    }

    /**
     * Create a collection by concatenating one or more collections
     *
     * @param {hyrrokkin_engine.ValueCollection[]} source_collections the collections to concatenate
     * @param {transformFunction|asyncTransformFunction} transform_fn an optional function to transform values from the source collections into this collection
     *
     * @return {hyrrokkin_engine.ValueCollection}
     */
    static
    create_from_collections(source_collections, transform_fn) {
        return new hyrrokkin_engine.TransformCollection(source_collections, transform_fn);
    }

    /**
     * Create a collection based on a value store
     *
     * @param {hyrrokkin_engine.ValueStore} value_store an object implementing the ValueStore interface which is used to store values held in the collection
     *
     * @return {hyrrokkin_engine.ValueCollection} A new ValueCollection instance
     */
    static
    create_from_store(value_store) {
        return new hyrrokkin_engine.StoreCollection(value_store);
    }

    /**
     * Open an async iterator over this collection
     *
     * @return {hyrrokkin_engine.ValueCollectionIterator} an async iterator
     *
     * @throws {hrrokkin_engine.ValueCollectionClosedError} if the collection has been closed
     */
    [Symbol.asyncIterator]() {
        if (this.is_closed) {
            throw new hyrrokkin_engine.hyrrokkin_engine.ValueCollectionClosedError();
        } else {
            return new hyrrokkin_engine.ValueCollectionIterator(this);
        }
    }

    /**
     * Get the size of this collection
     *
     * @return {int} the number of items in the collection
     *
     * @throws {hrrokkin_engine.ValueCollectionClosedError} if the collection has been closed
     */
    size() {
    }

    /**
     * Retrieve a value from the collection
     *
     * @param {int} index the index into the collection
     * @return {Promise<*>} a promise that resolves to the returned value
     *
     * @throws {hrrokkin_engine.ValueCollectionClosedError} if the collection has been closed
     * @throws {hrrokkin_engine.IndexError} if the index is out of range
     */
    async get(index) {
    }

    /**
     * Close the collection, freeing up any resources.
     *
     * @throws {hrrokkin_engine.ValueCollectionClosedError} if the collection has already been closed
     */
    close() {
        if (this.is_closed) {
            throw new hyrrokkin_engine.hyrrokkin_engine.ValueCollectionClosedError();
        }
        this.is_closed = true;
    }
}

/**
 * An exception that is thrown when attempting to access a collection that has been closed
 *
 * @type {hyrrokkin_engine.ValueCollectionClosedError}
 */
hyrrokkin_engine.ValueCollectionClosedError = class extends Error {

    constructor() {
        super("Attempting to access a value from a ValueCollection that has been closed")
    }
}

/**
 * An exception that is thrown when attempting to access an item from a collection with an index that is out of range
 *
 * @type {hyrrokkin_engine.IndexError}
 */
hyrrokkin_engine.IndexError = class extends Error {

    constructor(index, limit) {
        super(`Index ${index} is out of range 0..${limit}`)
    }
}


hyrrokkin_engine.ValueStore = class {

    /**
     * Retrieve a value from the store at a particular index
     *
     * @param index an index into the store
     * @return {Promise<*>} a promise that resolves to the returned value
     *
     * @throws {hyrrokkin_engine.IndexError} if the index is out of range
     */
    async get(index) {
    }

    /**
     * Gets the number of values held in this store
     *
     * @return {int} the number of values
     */
    get length() {
    }

    /**
     * Close this store, freeing any resources
     */
    close() {
    }
}

hyrrokkin_engine.InMemoryValueStore = class extends hyrrokkin_engine.ValueStore {

    /**
     * A simple implementation of the ValueStore interface using an in-memory array of values
     *
     * @param {AnyValue[]} values an array of values
     */
    constructor(values) {
        super();
        this.values = values;
    }

    async get(index) {
        if (index >= 0 && index < this.length) {
            return this.values[index];
        }
        throw new hyrrokkin_engine.IndexError(index, this.length);
    }

    get length() {
        return this.values.length;
    }

    close() {
        this.values = [];
    }
}


hyrrokkin_engine.StoreCollection = class extends hyrrokkin_engine.ValueCollection {

    constructor(value_store) {
        super();
        this.value_store = value_store;
    }

    size() {
        if (this.is_closed) {
            throw new hyrrokkin_engine.hyrrokkin_engine.ValueCollectionClosedError();
        }
        return this.value_store.length;
    }

    async get(pos) {
        if (this.is_closed) {
            throw new hyrrokkin_engine.hyrrokkin_engine.ValueCollectionClosedError();
        }
        return await this.value_store.get(pos);
    }

    close() {
        super.close();
        this.value_store.close();
    }

}

hyrrokkin_engine.TransformCollection = class extends hyrrokkin_engine.ValueCollection {

    constructor(source_collections, transform_fn) {
        super();
        this.source_collections = source_collections;
        this.transform_fn = transform_fn;
    }

    size() {
        let total_sz = 0;
        for(let idx=0; idx<this.source_collections.length; idx++) {
            total_sz += this.source_collections[idx].size();
        }
        return total_sz;
    }

    async get(pos) {
        let index = pos;
        if (this.is_closed) {
            throw new hyrrokkin_engine.hyrrokkin_engine.ValueCollectionClosedError();
        }
        for(let idx=0; idx<this.source_collections.length; idx++) {
            let collection = this.source_collections[idx];
            let sz = collection.size();
            if (pos < sz) {
                let value = await collection.get(pos);
                if (this.transform_fn) {
                    value = await this.transform_fn(value);
                }
                return value;
            } else {
                pos -= sz;
            }
        }
        throw new hyrrokkin_engine.IndexError(index, this.size());
    }
}



/* hyrrokkin_engine_utils/value_iterable.js */
var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.IteratorCombiner = class {

    constructor(input_iterators) {
        this.promises = {}; // map from iterator index to a promise returning the next value from that iterator
        this.input_iterators = input_iterators;
        for(let idx=0; idx<this.input_iterators.length; idx++) {
            this.promises[idx] = this.create_promise(idx);
        }
    }

    create_promise(index) {
        return new Promise((resolve, reject) => {
            this.input_iterators[index].next().then(
                value => {
                    value.index = index;
                    resolve(value);
                }
            );
        }, index);
    }

    async next() {
        while(Object.keys(this.promises).length > 0) {
            let current = await Promise.race(Object.values(this.promises));
            if (current.done) {
                delete this.promises[current.index];
            } else {
                this.promises[current.index] = this.create_promise(current.index);
                return current;
            }
        }
        return {"done":true}
    }
}

hyrrokkin_engine.ValueIteratorCombined = class {

    constructor(parent_iterable, input_iterators, lockstep_threshold) {
        this.parent_iterable = parent_iterable;
        this.subscriber_locks = {};
        this.value = null;
        this.value_available = false;
        this.fetch_required = true;
        this.lockstep_threshold = lockstep_threshold;
        this.subscriber_count = 0;
        this.fetched_count = 0;
        this.input_exhausted = false;
        this.exn = null;

        if (input_iterators.length > 1) {
            this.input_iterator = new hyrrokkin_engine.IteratorCombiner(input_iterators);
        } else {
            this.input_iterator = input_iterators[0];
        }
    }

    async subscribe() {
        this.subscriber_count += 1;
        let subscriber_id = "s" + this.subscriber_count;
        let lock = new hyrrokkin_engine.AsyncLock();
        if (!this.value_available) {
            await lock.acquire();
            if (this.value_available) {
                lock.release();
            }
        }
        this.subscriber_locks[subscriber_id] = lock;
        return subscriber_id;
    }

    unsubscribe(subscriber_id) {
        this.lockstep_threshold -= 1;
        this.subscriber_locks[subscriber_id].release();
        delete this.subscriber_locks[subscriber_id];
        if (this.fetched_count === this.lockstep_threshold) {
            this.fetch_required = true;
        }
    }

    async fetch(subscriber_id) {

        if (this.fetch_required) {
            this.fetch_required = false;
            try {
                let v = await this.input_iterator.next();
                if (!v.done) {
                    this.value = await this.parent_iterable.transform(v.value);
                    this.value_available = true;
                    this.fetched_count = 0;
                } else {
                    this.input_exhausted = true;
                }
            } catch (ex) {
                console.log(ex);
                this.input_exhausted = true;
                this.exn = ex;
            }

            Object.values(this.subscriber_locks).map(lock => lock.release());

        }
        await this.subscriber_locks[subscriber_id].acquire();
        if (this.input_exhausted) {
            return {"done": true};
        }
        if (this.exn !== null) {
            throw this.exn;
        }
        this.fetched_count += 1;
        if (this.fetched_count >= this.lockstep_threshold) {
            this.fetch_required = true;
        }
        return {"value":this.value}
    }
}

hyrrokkin_engine.ValueIterator = class {

    constructor() {
    }
}

hyrrokkin_engine.SyncValueIterator = class extends hyrrokkin_engine.ValueIterator {

    constructor(combined_iterator) {
        super();
        this.combined_iterator = combined_iterator;
        this.subscriber_id = null;
    }

    async next() {
        if (this.subscriber_id === null) {
            this.subscriber_id = await this.combined_iterator.subscribe();
        }
        return await this.combined_iterator.fetch(this.subscriber_id);
    }

    close() {
        this.combined_iterator.unsubscribe(this.subscriber_id);
    }
}

/**
 * Implement an async iterable of values with some added functionality.
 *
 * Call hyrrokkin_engine.ValueIterable.create_from_iterables to create an instance of this type.
 *
 * @implements {AsyncIterable}
 *
 * @type {hyrrokkin_engine.ValueIterable}
 *
 */
hyrrokkin_engine.ValueIterable = class {

    constructor(input_iterables, transform_fn, lockstep_threshold) {
        this.input_iterables = input_iterables;
        this.lockstep_threshold = lockstep_threshold;

        this.combined_iterator = new hyrrokkin_engine.ValueIteratorCombined(this,
            this.input_iterables.map(iterable => iterable[Symbol.asyncIterator]()),
            this.lockstep_threshold);

        this.iterator_count = 0;
        this.transform_fn = transform_fn;
    }

    async transform(value) {
        if (this.transform_fn === null) {
            return value;
        }
        return await this.transform_fn(value);
    }

    /**
     * Return an async iterable based on a set of input iterables.
     *
     * @param {AsyncIterable[]} input_iterables a list of one or more async iterables that provide input values
     * @param {(transformFunction|asyncTransformFunction)=} transform_fn a function to transform values from the input iterables
     * @param {int=} lockstep_threshold Specify that this many iterators opened over this iterable will be optimised to share a
     *                               single set of iterators obtained from the input iterables.
     *                               However, note that these iterators will yield values in lock-step.
     *                               If more than this many iterators are opened, each subsequent iterator will
     *                               open new input iterators.
     * @return {hyrrokkin_engine.ValueIterable} An async iterable
     */
    static create_from_iterables(input_iterables, transform_fn, lockstep_threshold) {
        return new hyrrokkin_engine.ValueIterable(input_iterables, transform_fn, lockstep_threshold);
    }

    [Symbol.asyncIterator]() {
        this.iterator_count += 1;
        return new hyrrokkin_engine.SyncValueIterator(this.combined_iterator);
    }
}




/* hyrrokkin_engine/node_interface.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

/**
 * An interface describing methods that nodes should implement
 *
 * @interface
 * @type {hyrrokkin_engine.NodeInterface}
 */
hyrrokkin_engine.NodeInterface = class {

    /**
     * Construct an instance of this node
     *
     * @param {hyrrokkin_engine.NodeServiceInterface} services a service object supplying useful functionality to the node
     */
    constructor(services) {
    }

    /**
     * Called after construction.  Load any resources associated with this Node
     *
     * @return {Promise<void>}
     */
    async load() {
    }

    /**
     * Implement this to be notified when a call to the run method is pending.
     */
    async reset_run() {
    }

    /**
     * Called to run the node, reading inputs and returning outputs
     *
     * @param {object} inputs an object containing input values where the key is an input port name and the value is an array of values presented by nodes connected to the port
     *
     * @return {Promise<object>} an object containing output values where the key is an output port name
     */
    async run(inputs) {
    }

    /**
     * Called when a client is opened
     *
     * @param {hyrrokkin_engine.ClientInterface} client an instance providing methods to send and receive messages
     */
    async open_client(client) {
    }

    /**
     * Called when a client is closed
     *
     * @param {hyrrokkin_engine.ClientInterface} client an instance providing methods to send and receive messages
     */
    async close_client(client) {
    }

    /**
     * Called when the node is removed
     */
    async remove() {
    }
}


/* hyrrokkin_engine/configuration_interface.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

/**
 * Defines an interface that package configuration classes should implement
 *
 * @interface
 * @type {hyrrokkin_engine.ConfigurationInterface}
 */
hyrrokkin_engine.ConfigurationInterface = class {

    /**
     * The configuration constructor is passed a configuration service instance
     *
     * @param {hyrrokkin_engine.ConfigurationServiceInterface} configuration_service
     */
    constructor(configuration_service) {
    }

    /**
     * Called after construction.  Load any resources associated with this Configuration
     *
     * @return {Promise<void>}
     */
    async load() {
    }

    /**
     *  Create a node which is defined within this package
     *
     * @param node_type_id {string} the id of the node type (a valid key in the schema's node_types dictionary)
     * @param service {hyrrokkin_engine.NodeServiceInterface} a service instance which will provide services to the node
     *
     * @return {Promise<*>}
     */
    async create_node(node_type_id, service) {
    }

    /**
     * Called when a session is opened
     *
     * @param session_id {string} identify the session being opened
     */
    open_session(session_id) {
    }

    /**
     * Called when a session is closed
     *
     * @param session_id {string} identify the session being closed
     */
    close_session(session_id) {
    }

    /**
     * Decode binary data into a value valid for a particular link type
     *
     * @param encoded_bytes {ArrayBuffer} binary data to decode
     * @param link_type {string} the link type associated with the value
     *
     * @return {*}
     */
    async decode(encoded_bytes, link_type) {
    }

    /**
     * Encode a value associated with a link type to binary data
     *
     * @param value {*} the value to encode
     * @param link_type {string} the link type associated with the value
     *
     * @return {ArrayBuffer}
     */
    async encode(value, link_type) {
    }

    /**
     * Called when a client is opened
     *
     * @param {hyrrokkin_engine.ClientInterface} client an instance providing methods to send and receive messages
     */
    async open_client(client) {
    }

    /**
     * Called when a client is closed
     *
     * @param {hyrrokkin_engine.ClientInterface} client an instance providing methods to send and receive messages
     */
    async close_client(client) {
    }

}


/* hyrrokkin_engine/persistence_interface.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

/**
 * An interface defining a persistence API used to store properties and data for a node or configuration
 *
 * @interface
 * @type {hyrrokkin_engine.PersistenceInterface}
 */
hyrrokkin_engine.PersistenceInterface = class {

    /**
     * Construct a instance
     */
    constructor() {
    }

    /**
     * Get the set of properties associated with this node/configuration
     *
     * @returns {Object} the value of the properties
     */
    async get_properties() {
    }

    /**
     * Set the properties associated with this node
     *
     * @param {Object} properties the properties to set, must be an Object that is JSON serialisable
     */
    async set_properties(properties) {
    }

    /**
     * Retrieve data associated with a key or null if no data is associated with that key
     *
     * @param {string} key the key value
     *
     * @return {Promise<(ArrayBuffer|null)>}
     */
    async get_data(key) {
    }

    /**
     * Store data associated with a key
     *
     * @param {string} key the key value
     * @param {(ArrayBuffer|null)} data the data value (pass null to delete data associated with the key)
     *
     * @return {Promise<void>}
     */
    async set_data(key, data) {
    }

    /**
     * Get an array containing the keys of all data items
     *
     * @return {Promise<string[]>}
     */
    async get_data_keys() {
    }

}


/* hyrrokkin_engine_drivers/common/persistence.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.Persistence = class extends hyrrokkin_engine.PersistenceInterface {

    constructor() {
        super();
        this.target_id = null;
        this.target_type = null;
        this.property_update_listeners = [];
        this.data_update_listeners = [];
        this.callbacks_enabled = true;
    }

    configure(target_id, target_type) {
        this.target_id = target_id;
        this.target_type = target_type;
    }

    static check_valid_data_key(key) {
        if (!key.match(/^[0-9a-zA-Z_]+$/)) {
            throw new Error("data key can only contain alphanumeric characters and underscores");
        }
    }

    static check_valid_data_value(data) {
        if (data instanceof ArrayBuffer) {
            return;
        } else if (data === null) {
            return;
        }
        throw new Error("data value can only be null or ArrayBuffer")
    }

    add_properties_update_listener(listener) {
        this.property_update_listeners.push(listener);
    }

    add_data_update_listener(listener) {
        this.data_update_listeners.push(listener);
        return listener;
    }

    properties_updated(properties) {
        if (this.callbacks_enabled) {
            for (let idx = 0; idx < this.property_update_listeners.length; idx++) {
                this.property_update_listeners[idx](this.target_id, this.target_type, properties);
            }
        }
    }

    data_updated(key, value) {
        if (this.callbacks_enabled) {
            for (let idx = 0; idx < this.data_update_listeners.length; idx++) {
                this.data_update_listeners[idx](this.target_id, this.target_type, key, value);
            }
        }
    }

    enable_callbacks() {
        this.callbacks_enabled = true;
    }

    disable_callbacks() {
        this.callbacks_enabled = false;
    }
}

/* hyrrokkin_engine_drivers/common/persistence_memory.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.PersistenceMemory = class extends hyrrokkin_engine.Persistence {

    constructor() {
        super();
        this.properties = {};
        this.data = {};
    }

    static check_valid_data_key(key) {
        if (!key.match(/^[0-9a-zA-Z_]+$/)) {
            throw new Error("data key can only contain alphanumeric characters and underscores");
        }
    }

    static check_valid_data_value(data) {
        if (data instanceof ArrayBuffer) {
            return;
        } else if (data === null) {
            return;
        }
        throw new Error("data value can only be null or ArrayBuffer")
    }

    get_properties() {
        return this.properties;
    }

    async set_properties(properties) {
        this.properties = JSON.parse(JSON.stringify(properties));
        this.properties_updated(properties);
    }

    async get_data(key) {
        hyrrokkin_engine.Persistence.check_valid_data_key(key);
        if (key in this.data) {
            return this.data[key];
        }
        return null;
    }

    async set_data(key, data) {
        hyrrokkin_engine.Persistence.check_valid_data_key(key);
        hyrrokkin_engine.Persistence.check_valid_data_value(data);
        if (key === null) {
            if (key in this.data) {
                delete this.data[key];
            }
        } else {
            this.data[key] = data;
        }
        this.data_updated(key, data);
    }

    async get_data_keys() {
        return Object.keys(this.data);
    }
}

/* hyrrokkin_engine_drivers/execution_worker.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.ExecutionWorker = class {

    constructor(send_fn, verbose) {
        this.verbose = verbose;
        this.graph_executor = null;
        this.packages = {};
        this.message_queue = [];
        this.handling = false;
        this.clients = {};
        this.send_fn = send_fn;
        this.injected_inputs = {};
        this.output_listeners = {};
        this.persistence= {};
        this.read_only = false;
        this.topology_id = undefined;
        this.workspace_id = undefined;
        this.persistence_mode = "";
        this.execution_folder = undefined;
        this.running_task = null;
        this.running_task_name = null;
    }

    async init(o) {
        this.read_only = o["read_only"];
        let paused = o["paused"];
        this.persistence_mode = o["persistence_mode"] || "memory";
        this.workspace_id = o["workspace_id"]; // set only when running in-client
        this.topology_id = o["topology_id"];   // set only when running in-client
        this.execution_folder = o["execution_folder"]; // set when running in server

        this.graph_executor = new hyrrokkin_engine.GraphExecutor(
            (is_complete) => {
                this.execution_monitor(is_complete);
            },
            (node_id,execution_state,is_manual) => {
                this.send({"action":"update_execution_state","node_id":node_id, "execution_state":execution_state, "is_manual": is_manual});
            },
            (node_id, level, msg) => {
                this.send({"action":"update_status", "status":level, "message":msg, "origin_type":"node", "origin_id":node_id});
            },
            (package_id,level,msg) => {
                this.send({"action":"update_status", "status":level, "message":msg, "origin_type":"configuration", "origin_id":package_id});
            },
            (origin_id, origin_type, session_id, client_id, ...msg) => {
                this.send({"action":"client_message", "origin_id":origin_id, "origin_type":origin_type, "session_id":session_id, "client_id":client_id}, ...msg);
            },
            async (node_id, output_port_name, value) => {
                let encoded_bytes = this.graph_executor.encode_value(node_id, output_port_name, value);
                this.send({"action":"output_notification", "node_id":node_id, "output_port_name":output_port_name}, encoded_bytes);
            },
            (origin_id, origin_type, session_id, client_name) => {
                this.send({"action":"request_open_client", "origin_id":origin_id, "origin_type":origin_type, "session_id":session_id, "client_name":client_name});
            }, paused);

    }

    get_persistence(target_id, target_type) {
        let key = target_id + ":" + target_type;
        if (key in this.persistence) {
            return this.persistence[key];
        }
        let persistence = null;
        if (this.persistence_mode === "filesystem") {
            persistence = new hyrrokkin_engine.PersistenceDenoFilesystem(this.execution_folder, this.read_only);
        } else if (this.persistence_mode === "client") {
            persistence = new hyrrokkin_engine.PersistenceClient(this.workspace_id, this.topology_id, this.read_only);
        } else {
            persistence = new hyrrokkin_engine.PersistenceMemory();
        }
        persistence.configure(target_id, target_type)
        this.persistence[key] = persistence
        return persistence;
    }

    track_persistence_changes(target_id, target_type) {
        if (this.read_only) {
            return;
        }
        if (this.persistence_mode === "shared_filesystem" || this.persistence_mode === "client") {
            return;
        }
        let key = target_id + ":" + target_type;
        let persistence = this.persistence[key];
        persistence.add_properties_update_listener(
            (target_id, target_type, properties) => {
                this.properties_updated(target_id, target_type, properties)
            });
        persistence.add_data_update_listener(
            (target_id, target_type, key, value) => {
                this.data_updated(target_id, target_type, key, value)
            });
    }

    remove_persistence(target_id, target_type) {
        let key = target_id + ":" + target_type;
        if (key in this.persistence) {
            delete this.persistence[key];
        }
    }

    properties_updated(target_id, target_type, properties) {
        this.send({
            "action": "set_properties",
            "target_id": target_id,
            "target_type": target_type,
            "properties": properties
        });
    }

    data_updated(target_id, target_type, key, value) {
        this.send({
            "action": "set_data",
            "target_id": target_id,
            "target_type": target_type,
            "key": key
        }, value);
    }

    async add_package(o) {
        let package_id = o["package_id"];
        let schema = o["schema"];
        let base_url = o["folder"];
        let package_version = (schema["metadata"] || {})["version"] || "";
        let persistence = this.get_persistence(package_id,"configuration");
         this.track_persistence_changes(package_id, "configuration");
        let services = await this.graph_executor.create_configuration_service(package_id, package_version, base_url, persistence);
        let instance = hyrrokkin_engine.registry.create_configuration(package_id, services);
        await this.graph_executor.add_package(package_id, schema, base_url, instance, services);
    }

    async add_node(o) {
        let node_id = o["node_id"];
        let node_type_id = o["node_type_id"];
        let copy_from_node_id = o["copy_from_node_id"] || "";
        let package_id = node_type_id.split(":")[0];
        node_type_id = node_type_id.split(":")[1];
        let persistence = this.get_persistence(node_id,"node");
        this.track_persistence_changes(node_id, "node");
        await this.graph_executor.add_node(node_id, package_id, node_type_id, persistence, copy_from_node_id);
    }

    async set_properties(o) {
        let target_id = o["target_id"];
        let target_type = o["target_type"];
        let properties = o["properties"];
        let persistence = this.get_persistence(target_id, target_type);
        persistence.disable_callbacks();
        await persistence.set_properties(properties);
        persistence.enable_callbacks();
    }

    async set_data(o, data_value) {
        let target_id = o["target_id"];
        let target_type = o["target_type"];
        let key = o["key"]
        let persistence = this.get_persistence(target_id, target_type);
        persistence.disable_callbacks();
        await persistence.set_data(key, data_value);
        persistence.enable_callbacks();
    }

    async remove_node(o) {
        await this.graph_executor.remove_node(o["node_id"]);
        this.remove_persistence(o["node_id"],"node");
    }

    async inject_input(o, ...encoded_bytes) {
        let decoded_values = [];
        for(let idx=0; idx<encoded_bytes.length; idx++) {
            decoded_values.push(this.graph_executor.decode_value(o["node_id"], o["input_port_name"], encoded_bytes[idx]));
        }
        await this.graph_executor.inject_input(o["node_id"], o["input_port_name"], decoded_values);
    }

    async clear_injected_input(o) {
        await this.graph_executor.clear_injected_input(o["node_id"], o["input_port_name"]);
    }

    add_output_listener(o) {
        this.graph_executor.add_output_listener(o["node_id"], o["output_port_name"]);
    }

    remove_output_listener(o) {
        this.graph_executor.remove_output_listener(o["node_id"], o["output_port_name"]);
    }

    async add_link(o) {
        await this.graph_executor.add_link(o["link_id"], o["from_node_id"], o["from_port"], o["to_node_id"],o["to_port"]);
    }

    async remove_link(o) {
        await this.graph_executor.remove_link(o["link_id"]);
    }

    async clear(o) {
        await this.graph_executor.clear();
    }

    open_session(o) {
        let session_id = o["session_id"];
        this.graph_executor.open_session(session_id);
    }

    close_session(o) {
        let session_id = o["session_id"];
        this.graph_executor.close_session(session_id);
    }

    async open_client(o) {
        let target_id = o["target_id"];
        let target_type = o["target_type"];
        let client_id = o["client_id"];
        let session_id = o["session_id"];
        let client_options = o["client_options"];
        await this.graph_executor.open_client(target_id, target_type, session_id, client_id, client_options);
    }

    async client_message(o,...msg) {
        let target_id = o["target_id"];
        let target_type = o["target_type"];
        let client_id = o["client_id"];
        let session_id = o["session_id"];
        await this.graph_executor.recv_message(target_id, target_type, session_id, client_id, ...msg);
    }

    async close_client(o) {
        let target_id = o["target_id"];
        let target_type = o["target_type"];
        let client_id = o["client_id"];
        let session_id = o["session_id"];
        await this.graph_executor.close_client(target_id, target_type, session_id, client_id);
    }

    async pause(o) {
        await this.graph_executor.pause();
        this.send({"action":"note_paused"});
    }

    async resume(o) {
        await this.graph_executor.resume();
        this.send({"action":"note_resumed"});
    }

    async close() {
        this.graph_executor.close();
    }

    async recv(msg) {
        if (this.handling) {
            this.message_queue.push(msg);
        } else {
            this.handling = true;
            try {
                await this.handle(msg);
            } finally {
                while(true) {
                    let msg = this.message_queue.shift();
                    if (msg) {
                        try {
                            await this.handle(msg);
                        } catch(ex) {
                        }
                    } else {
                        break;
                    }
                }
                this.handling = false;
            }
        }
    }

    async handle(msg) {
        let o = msg[0];
        if (this.verbose) {
            console.log("Worker <- " + o.action);
        }
        switch(o.action) {
            case "init":
                await this.init(o);
                break;
            case "add_package":
                await this.add_package(o);
                break;
            case "packages_added":
                this.send({"action":"init_complete"});
                break;
            case "add_node":
                await this.add_node(o);
                break;
            case "remove_node":
                await this.remove_node(o);
                break;
            case "inject_input":
                await this.inject_input(o, ...msg.slice(1));
                break;
            case "clear_injected_input":
                await this.inject_input(o);
                break;
            case "add_output_listener":
                this.add_output_listener(o);
                break;
            case "remove_output_listener":
                this.remove_output_listener(o);
                break;
            case "add_link":
                await this.add_link(o);
                break;
            case "set_properties":
                await this.set_properties(o);
                break;
            case "set_data":
                await this.set_data(o,...msg.slice(1));
                break;
            case "remove_link":
                await this.remove_link(o);
                break;
            case "open_session":
                this.open_session(o);
                break;
            case "close_session":
                this.close_session(o);
                break;
            case "open_client":
                await this.open_client(o);
                break;
            case "client_message":
                await this.client_message(o, ...msg.slice(1));
                break;
            case "close_client":
                await this.close_client(o);
                break;
            case "pause":
                await this.pause(o);
                break;
            case "resume":
                await this.resume(o);
                break;
            case "run_task":
                await this.run_task(o, ...msg.slice(1));
                break;
            case "stop_node":
                console.log("stop_node");
                await this.graph_executor.stop_node(o["node_id"]);
                this.send({"action":"node_stopped", "node_id": o["node_id"]});
                break;
            case "restart_node":
                console.log("restart_node");
                await this.graph_executor.restart_node(o["node_id"]);
                break;
            case "clear":
                await this.clear(o);
                break;
            case "close":
                await this.close();
                return false;
        }
        return true;
    }

    async run_task(control_packet, ...extras) {
        let input_ports = control_packet["input_ports"];
        let output_port_names = control_packet["output_ports"];
        let task_name = control_packet["task_name"];
        console.log("Running task: "+task_name);
        await this.graph_executor.pause();
        for (let name in input_ports) {
            let values = [];
            let idx = input_ports[name].start_index;
            let comps = name.split(":");
            let node_id = comps[0];
            let input_port_name = comps[1];
            while(idx < input_ports[name].end_index) {
                values.push(this.graph_executor.decode_value(node_id, input_port_name, extras[idx]));
                idx += 1;
            }
            await this.graph_executor.inject_input(node_id, input_port_name, values);
        }
        this.running_task = output_port_names;
        this.running_task_name = task_name;
        await this.graph_executor.resume()
    }

    execution_monitor(is_complete) {
        if (is_complete) {
            this.send({
                "action": "execution_complete",
                "count_failed": this.graph_executor.count_failed(),
                "failures": this.graph_executor.get_failures()
            });
            if (this.running_task !== null) {
                let output_port_ids = this.running_task;
                let output_port_values = [];
                output_port_ids.forEach(output_port_id => {
                    let comps = output_port_id.split(":");
                    let node_id = comps[0];
                    let output_port_name = comps[1];
                    let value = this.graph_executor.get_output_value(node_id, output_port_name);
                    let encoded_value = this.graph_executor.encode_value(node_id, output_port_name, value);
                    output_port_values.push(encoded_value);
                });
                this.send({"action": "task_complete", "task_name": this.running_task_name,
                        "failures": this.graph_executor.get_failures(),
                        "output_ports": output_port_ids
                    },
                    ...output_port_values)
                this.running_task = null;
                this.running_task_name = null;
            }
        } else {
            // this.send({"action":"execution_started"});
        }
    }

    send(control_packet,...extra) {
        if (this.verbose) {
            console.log("-> " + JSON.stringify(control_packet));
        }
        let message_parts = [control_packet];
        extra.forEach(o => {
            message_parts.push(o);
        })
        this.send_fn(message_parts);
    }
}


/* hyrrokkin_engine/registry.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.Registry = class {

    constructor() {
        this.configuration_factories = {};
        this.node_factories = {};
    }

    register_configuration_factory(package_id, configuration_factory) {
        this.configuration_factories[package_id] = configuration_factory;
    }

    register_node_factory = function(node_type_id,node_factory) {
        this.node_factories[node_type_id] = node_factory;
    }

    defines_configuration(package_id) {
        return (package_id in this.configuration_factories);
    }

    create_configuration(package_id, configuration_services) {
        return this.configuration_factories[package_id](configuration_services);
    }

    create_node(node_type_id, node_services) {
        return this.node_factories[node_type_id](node_services);
    }
}

hyrrokkin_engine.registry = new hyrrokkin_engine.Registry();

/* hyrrokkin_engine_drivers/client/index_db.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.IndexDB = class {

    constructor(name) {
        this.name = "topology-"+name;
    }

    async init() {
        this.db = await this.open();
    }

    async open() {
        return await new Promise((resolve,reject) => {
            const request = indexedDB.open(this.name, 1);
            request.onsuccess = (evt) => {
                resolve(evt.target.result);
            }
            request.onerror = (evt) => {
                resolve(null);
            }
            request.onupgradeneeded = (evt) => {
                // Save the IDBDatabase interface
                let db = evt.target.result;
                db.createObjectStore("data", {});
            }
        });
    }


    async get(key) {
        return await new Promise((resolve,reject) => {
            const transaction = this.db.transaction(["data"], "readonly");
            const request = transaction.objectStore("data").get(key);
            request.onsuccess = (evt) => {
                resolve(evt.target.result);
            }
            request.onerror = (evt) => {
                resolve(undefined);
            }
        });
    }

    async put(key, value) {
        return await new Promise((resolve,reject) => {
            const transaction = this.db.transaction(["data"], "readwrite");
            const request = transaction.objectStore("data").put(value,key);
            request.onsuccess = (evt) => {
                resolve(true);
            }
            request.onerror = (evt) => {
                resolve(true);
            }
        });
    }

    async delete(key) {
        return await new Promise((resolve,reject) => {
            const transaction = this.db.transaction(["data"], "readwrite");
            const request = transaction.objectStore("data").delete(key);
            request.onsuccess = (evt) => {
                resolve(evt.target.result);
            }
            request.onerror = (evt) => {
                resolve(undefined);
            }
        });
    }

    async get_keys() {
        return await new Promise((resolve,reject) => {
            const transaction = this.db.transaction(["data"], "readonly");
            const request = transaction.objectStore("data").getAllKeys();
            request.onsuccess = (evt) => {
                resolve(evt.target.result);
            }
            request.onerror = (evt) => {
                resolve(undefined);
            }
        });
    }

    close() {
        this.db.close();
        this.db = null;
    }
}

hyrrokkin_engine.IndexDB.create = async function(name) {
    let db = new hyrrokkin_engine.IndexDB(name);
    await db.init();
    return db;
}

hyrrokkin_engine.IndexDB.remove = async function(name) {
    return await new Promise((resolve,reject) => {
        const request = indexedDB.deleteDatabase("topology-"+name);
        request.onsuccess = (evt) => {
            resolve(true);
        }
        request.onerror = (evt) => {
            resolve(false);
        }
    });
}

/* hyrrokkin_engine_drivers/client/client_storage.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.ClientStorage = class {

    constructor(db_name) {
        this.db_name = db_name;
        this.db = null;
    }

    static check_valid_data_key(key) {
        if (!key.match(/^[0-9a-zA-Z_]+$/)) {
            throw new Error("data key can only contain alphanumeric characters and underscores");
        }
    }

    static check_valid_data_value(data) {
        if (data instanceof ArrayBuffer) {
            return;
        } else if (data === null) {
            return;
        }
        throw new Error("data value can only be null or ArrayBuffer")
    }

    async open() {
        this.db = await hyrrokkin_engine.IndexDB.create(this.db_name);
    }

    close() {
        if (this.db !== null) {
            this.db.close();
            this.db = null;
        }
    }

    async get_item(key) {
        if (!this.db) {
            await this.open();
        }
        let result = await this.db.get(key);
        if (result === undefined) {
            result = null;
        }
        return result;
    }

    async set_item(key, value) {
        if (!this.db) {
            await this.open();
        }
        await this.db.put(key, value);
    }

    async remove_item(key) {
        if (!this.db) {
            await this.open();
        }
        await this.db.delete(key);
    }

    async remove() {
        this.close();
        await hyrrokkin_engine.IndexDB.remove(this.db_name);
    }

    async get_keys() {
        if (!this.db) {
            await this.open();
        }
        return await this.db.get_keys();
    }

    async clear() {
        // clear the database by removing and re-opening
        await this.remove();
        await this.open();
    }

    async copy_to(to_db_name) {
        await this.open();
        let other = await new hyrrokkin_engine.ClientStorage(to_db_name);
        await other.open();
        await other.clear();
        let keys = await this.get_keys();
        for(let idx in keys) {
            let key = keys[idx];
            let value = await this.get_item(key);
            await other.set_item(key, value);
        }
        other.close();
    }
}

/* hyrrokkin_engine_drivers/client/persistence_client.js */

var hyrrokkin_engine = hyrrokkin_engine || {};

hyrrokkin_engine.PersistenceClient = class extends hyrrokkin_engine.Persistence {

    constructor(workspace_id, topology_id, read_only) {
        super();
        this.workspace_id = workspace_id;
        this.topology_id = topology_id;
        this.properties = null;
        this.data_cache = {};
        this.read_only = read_only;
    }

    get_workspace_path(path) {
        return "workspace."+this.workspace_id+"."+path;
    }

    get_topology_path(path) {
        return "workspace."+this.workspace_id+".topology."+path
    }

    async get_properties() {
        if (this.properties !== null) {
            return this.properties;
        }
        let db = new hyrrokkin_engine.ClientStorage(this.get_topology_path(this.topology_id));
        try {
            let path = this.target_type + "/" + this.target_id + "/properties.json";
            let properties = await db.get_item(path);
            this.properties = properties !== null ? JSON.parse(properties) : {};
            return this.properties;
        } finally {
            db.close();
        }
    }

    async set_properties(properties) {
        if (!this.read_only) {
            this.properties = JSON.parse(JSON.stringify(properties));
            let db = new hyrrokkin_engine.ClientStorage(this.get_topology_path(this.topology_id));
            try {
                let path = this.target_type + "/" + this.target_id + "/properties.json";
                await db.set_item(path, JSON.stringify(this.properties));
            } finally {
                db.close();
            }
            this.properties_updated(this.properties);
        }
    }

    async get_data(key) {
        hyrrokkin_engine.ClientStorage.check_valid_data_key(key);
        if (key in this.data_cache) {
            return this.data_cache[key];
        } else {
            let db = new hyrrokkin_engine.ClientStorage(this.get_topology_path(this.topology_id));
            try {
                let path = this.target_type + "/" + this.target_id + "/data/" + key;
                return await db.get_item(path);
            } finally {
                db.close();
            }
        }
    }

    async set_data(key, data) {
        hyrrokkin_engine.ClientStorage.check_valid_data_key(key);
        hyrrokkin_engine.ClientStorage.check_valid_data_value(data);
        if (this.read_only) {
            if (data === null) {
                if (key in this.data_cache) {
                    delete this.data_cache[key];
                }
            } else {
                this.data_cache[key] = data;
            }
        } else {
            let db = new hyrrokkin_engine.ClientStorage(this.get_topology_path(this.topology_id));
            try {
                let path = this.target_type + "/" + this.target_id + "/data/" + key;
                if (data === null) {
                    await db.remove_item(path);
                } else {
                    await db.set_item(path, data);
                }
            } finally {
                db.close();
            }
            this.data_updated(key, data);
        }
    }

    async get_data_keys() {
        let db = new hyrrokkin_engine.ClientStorage(this.get_topology_path(this.topology_id));
        try {
            let prefix = this.target_type + "/" + this.target_id + "/data/";
            let all_keys = await db.get_keys();
            let data_keys = [];
            for(let idx=0; idx<all_keys.length; idx++) {
                let key = all_keys[idx];
                if (key.startsWith(prefix)) {
                    data_keys.push(key.slice(prefix.length));
                }
            }
            return data_keys;
        } finally {
            db.close();
        }
    }
}

