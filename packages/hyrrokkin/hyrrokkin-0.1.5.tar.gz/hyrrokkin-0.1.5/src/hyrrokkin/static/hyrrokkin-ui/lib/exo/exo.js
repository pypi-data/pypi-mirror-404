/* js/exo-common.js */

/* MIT License

Copyright (c) 2021-2023 Visual Topology

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

let colors = ["red","orange","blue","green","purple","brown","gray","pink","yellow"];
let dark_colors = colors.map((name) => "dark-"+name);
let light_colors = colors.map((name) => "light-"+name);

let all_colors = ["black","white"]+colors+dark_colors+light_colors;

let sizes = ["no","tiny","small","medium","large","huge"];

class ExoUtils {

    static createElement(tag, attrs) {
        let elt = document.createElement(tag);
        for(let name in attrs) {
            elt.setAttribute(name,attrs[name]);
        }
        return elt;
    }

    static addClasses(element, classnames) {
        classnames.forEach(classname => ExoUtils.addClass(element, classname));
    }

    static addClass(element, classname) {
        var classes = (element.getAttribute("class") || "").split(" ");
        var classnames = classname.split(" ");
        for(let idx=0; idx<classnames.length; idx++) {
            let cls = classnames[idx];
            if (classes.findIndex(name => name == cls) == -1) {
                classes.push(cls);
            }
        }
        var new_classes = classes.join(" ")
        element.setAttribute("class", new_classes);
    }

    static getClasses(element) {
        return (element.getAttribute("class") || "").split(" ").filter(name => name != "");
    }

    static removeClass(element, classname) {
        var classes = ExoUtils.getClasses(element);
        classes = classes.filter(name => name != classname);
        element.setAttribute("class", classes.join(" "));
    }

    static removeClasses(element, pattern) {
        var classes = ExoUtils.getClasses(element);
        classes.forEach(cls => {
            let resolved = cls.match(pattern);
            if (resolved != null) {
                this.removeClass(element, cls);
            }
        });
    }

    static removeClassesFromList(element, classname_list) {
        var classes = ExoUtils.getClasses(element);
        classes.forEach(cls => {
            if (classname_list.includes(cls)) {
                this.removeClass(element, cls);
            }
        });
    }

    static addStyle(element, name, value) {
        var style = element.getAttribute("style") || "";
        style = style + name + ": " + value + ";";
        element.setAttribute("style", style);
    }

    static setAttributes(element,attr_value_pairs) {
        attr_value_pairs.forEach(pair => { element.setAttribute(pair[0],pair[1])});
    }

    static moveChildNodes(from_element,to_element) {
        var to_move = [];
        for(var idx=0; idx<from_element.childNodes.length; idx++) {
            var node = from_element.childNodes[idx];
            to_move.push(node);
        }
        for(var idx=0; idx<to_move.length; idx++) {
            var node = to_move[idx];
            if (node != to_element) {
                from_element.removeChild(node);
                to_element.appendChild(node);
            }
        }
    }

    static replaceNode(old_node,new_node) {
        var parent = old_node.parentNode;
        if (!parent) {
            alert("problem here");
        }
        parent.replaceChild(new_node,old_node);
    }

    static removeAllChildren(elt) {
        while (elt.firstChild) {
            elt.removeChild(elt.firstChild);
        }
    }

    static applyColor(elt, name, value) {
        let to_remove = colors.map((color_name) => "exo-"+color_name+"-"+name);
        ExoUtils.removeClassesFromList(elt, to_remove);
        ExoUtils.addClass(elt,"exo-"+value+"-"+name);
    }

    static applySizedDimension(elt, name,value) {
        if (value == undefined) {
            return;
        }
        if (value == "") {
            value = "medium";
        }
        let to_remove = sizes.map((size_name) => "exo-"+size_name+"-"+name);
        ExoUtils.removeClassesFromList(elt, to_remove);
        if (value) {
            switch (value) {
                case "no":
                case "tiny":
                case "small":
                case "medium":
                case "large":
                case "huge":
                    ExoUtils.addClass(elt, "exo-" + value + "-" + name);
                    break;
                default:
                    console.log("Exo: Invalid " + name + " value: " + value + ", valid values are no,tiny,small,medium,large,huge");
            }
        }
    }
}

var exo_counter = 0;

class CustomExoControl extends HTMLElement {

    constructor() {
        super();
        this.value = undefined;
        this.exo_label = null;
        this.exo_tooltip_div = null;
        this.exo_tooltip_content = null;
        this.exo_br = null;
        this.exo_output = null;
        this.exo_id = "s"+exo_counter;
        this.value = undefined;
        exo_counter += 1;
        this.exo_built = false;
    }

    exoGetId() {
        return this.exo_id;
    }

    connectedCallback() {
       let parameters = this.exoGetParameters(this);
       this.exoBuild(parameters);
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (this.exo_built) {
            this.exoUpdate(name, newValue);
        }
    }

    static get observedAttributes() {
        return ["fg-color", "bg-color", "border-color", "border","margin","padding","rounded",
            "vmargin","hmargin","label","tooltip","disabled","class","aria-label", "visible", "invalid"];
    }

    exoBuildCommon(tag, parameters) {

        this.exo_element = document.createElement(tag);

        if (parameters["full_width"]) {
            ExoUtils.addClass(this.exoGetInputElement(),"exo-full-width");
        }

        this.exo_root_element = document.createElement("div");
        // this.exo_root_element.setAttribute("style","width:fit-content;height:fit-content;");

        this.exo_root_element.appendChild(this.exo_element);

        this.exo_built = true;
    }

    exoBuildComplete(parameters) {
        for(var parameter_name in parameters) {
            this.exoUpdate(parameter_name,parameters[parameter_name]);
        }
        this.appendChild(this.exoGetRootElement());
    }

    exoGetParameters() {
        let parameters = {};
        this.getAttributeNames().forEach(name => parameters[name] = this.getAttribute(name));
        return parameters;
    }

    exoUpdateParameters(parameters) {
        for(var name in parameters) {
            this.exoUpdate(name, parameters[name]);
        }
    }

    exoUpdate(name,value) {
        if (!this.exo_built) {
            return;
        }
        switch(name) {
            case "value":
                this.exoSetControlValue(value);
                break;
            case "fg-color":
                this.applyColor("fgr",value);
                break;
            case "bg-color":
                this.applyColor("bg",value);
                break;
            case "border-color":
                this.applyColor("border",value);
                break;
            case "border":
            case "margin":
            case "padding":
            case "rounded":
            case "vmargin":
            case "hmargin":
                this.applySizedDimension(name,value);
                break;
            case "bg-image":
                if (value) {
                    ExoUtils.addStyle(this.exoGetInputElement(),"background-image","url('"+value+"');");
                }
                break;
            case "full-width":
                ExoUtils.addClass(this.exoGetInputElement(),"exo-full-width");
                break;
            case "label":
                this.exoUpdateLabel(value);
                break;
            case "tooltip":
                this.exoUpdateTooltip(value);
                break;
            case "id":
                // ignore
                break;
            case "invalid":
                this.exoGetInputElement().setCustomValidity(value);
                this.exoGetInputElement().reportValidity();
                break;
            case "class":
                ExoUtils.addClass(this.exoGetInputElement(),value);
                break;
            case "disabled":
                switch(value) {
                    case "true":
                        this.exoGetInputElement().setAttribute("disabled", "disabled");
                        break;
                    case "false":
                        this.exoGetInputElement().removeAttribute("disabled");
                        break;
                }
                break;
            case "visible":
                switch(value) {
                    case "true":
                        ExoUtils.addStyle(this.exoGetRootElement(),"visibility", "visible");
                        break;
                    case "false":
                        ExoUtils.addStyle(this.exoGetRootElement(),"visibility", "hidden");
                        break;
                }
                break;
            case "aria-label":
                this.exoGetInputElement().setAttribute(name,value);
                break;
            default:
                console.log("Unrecognized exoUpdate: "+name+","+value);
        }
    }

    exoGetInputElement() {
        return this.exo_element;
    }

    applySizedDimension(name,value) {
        ExoUtils.applySizedDimension(this.exoGetInputElement(),name,value);
    }

    applyColor(name,value) {
        ExoUtils.applyColor(this.exoGetInputElement(),name,value);
    }

    exoDefineOutput() {
        if (!this.exo_br) {
            this.exoAddBr();
        }
        this.exo_output = document.createElement("output");
        this.exo_output.setAttribute("for",this.exoGetId());
        this.exoGetInputElement().parentElement.insertBefore(this.exo_output, this.exo_br);
    }

    exoSetOutputValue(value) {
        if (!this.exo_output) {
            this.exoDefineOutput();
        }
        ExoUtils.removeAllChildren(this.exo_output);
        this.exo_output.appendChild(document.createTextNode(value));
    }

    exoSetControlValue(value) {
        this.value = value;
    }

    exoGetControlValue() {
        return this.value;
    }

    exoGetRootElement() {
        return this.exo_root_element;
    }

    exoUpdateLabel(text) {
        if (!text) {
            if (this.exo_label) {
                this.exo_root_element.removeChild(this.exo_label);
                this.exo_label = null;
            }
            if (!this.exo_tooltip_div && !this.exo_label && !this.exo_output) {
                this.exoRemoveBr();
            }
        } else {
            this.exoAddBr();
            if (!this.exo_label) {
                this.exo_label = document.createElement("label");
                this.exo_label.setAttribute("for", this.exoGetId());
                this.exo_label.setAttribute("style", "display:inline; margin-right:5px;");
                if (this.exo_root_element.firstChild) {
                    this.exo_root_element.insertBefore(this.exo_label, this.exo_root_element.firstChild);
                } else {
                    this.exo_root_element.appendChild(this.exo_label);
                }
            }

            ExoUtils.removeAllChildren(this.exo_label);
            this.exo_label.appendChild(document.createTextNode(text ? text : "\u00A0"));
        }
    }

    exoUpdateTooltip(text) {
        if (!text) {
            if (this.exo_tooltip_div) {
                this.exo_root_element.removeChild(this.exo_tooltip_div);
                this.exo_tooltip_div = null;
                this.exo_tooltip_content = null;
            }
            if (!this.exo_tooltip_div && !this.exo_label && !this.exo_output) {
                this.exoRemoveBr();
            }
        } else {
            this.exoAddBr();
            if (!this.exo_tooltip_div) {
                this.exo_tooltip_div = document.createElement("div");
                this.exo_tooltip_div.setAttribute("tabindex", "0");
                this.exo_tooltip_div.setAttribute("class", "exo-icon exo-icon-help exo-icon-inline exo-help-tooltip");
                this.exo_tooltip_content = document.createElement("div");
                this.exo_tooltip_content.setAttribute("class", "exo-help-content exo-white-bg exo-border");
                this.exo_tooltip_div.appendChild(this.exo_tooltip_content);
                if (this.exo_output) {
                    this.exo_root_element.insertBefore(this.exo_tooltip_div, this.exo_output);
                } else {
                    this.exo_root_element.insertBefore(this.exo_tooltip_div, this.exo_br);
                }
            }
            ExoUtils.removeAllChildren(this.exo_tooltip_content);
            this.exo_tooltip_content.appendChild(document.createTextNode(text));
        }

    }

    exoAddBr() {
        if (!this.exo_br) {
            this.exo_br = document.createElement("br");
            if (this.exo_root_element.firstChild) {
                this.exo_root_element.insertBefore(this.exo_br,this.exo_root_element.firstChild);
            } else {
                this.exo_root_element.appendChild(this.exo_br);
            }
        }
    }

    exoRemoveBr() {
        if (this.exo_br) {
            this.exo_root_element.removeChild(this.exo_br);
            this.exo_br = null;
        }
    }
}





/* js/controls/exo-checkbox.js */


class CustomExoCheckbox extends CustomExoControl {
    constructor() {
        super();
    }

    exoBuild(parameters) {
        super.exoBuildCommon("input", parameters);

        this.exoGetInputElement().setAttribute("type","checkbox");
        this.exoGetInputElement().addEventListener("change", evt => {
            let v = evt.target.checked;
            this.exoSetControlValue(v?"true":"false");
            this.checked = v;
            this.dispatchEvent(new CustomEvent("change"));
            evt.stopPropagation();
        });

        super.exoBuildComplete(parameters);
    }

    exoUpdate(name,value) {
        switch(name) {
            case "value":
                const bvalue = (value == "true") ? true : false;
                this.exoGetInputElement().checked = bvalue;
                this.exoSetControlValue(value);
                this.checked = bvalue;
                break;
            default:
                super.exoUpdate(name,value);
        }
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value');
        return attrs;
    }
}

customElements.define("exo-checkbox", CustomExoCheckbox);


/* js/controls/exo-date.js */


class CustomExoDateTimeBase extends CustomExoControl {

    constructor() {
        super();
    }

    exoBuild(parameters,input_type) {
        super.exoBuildCommon("input", parameters);

        this.exoGetInputElement().setAttribute("type",input_type);

        super.exoBuildComplete(parameters);
    }

    exoUpdate(name,value) {
        switch(name) {
            case "value":
                this.exoGetInputElement().value = value;
                this.exoSetControlValue(value);
                break;
            case "min":
                this.exoGetInputElement().setAttribute("min", value);
                break;
            case "max":
                this.exoGetInputElement().setAttribute("max", value);
                break;
            default:
                super.exoUpdate(name,value);
        }
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value','min','max');
        return attrs;
    }
}

class CustomExoDate extends CustomExoDateTimeBase {

    constructor() {
        super();
    }

    exoBuild(parameters, type) {
        super.exoBuild(parameters,"date");
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value','min','max');
        return attrs;
    }
}

class CustomExoTime extends CustomExoDateTimeBase {

    constructor() {
        super();
    }

    exoBuild(parameters) {
        super.exoBuild(parameters, "time");
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value','min','max');
        return attrs;
    }
}

class CustomExoDateTimeLocal extends CustomExoDateTimeBase {

    constructor() {
        super();
    }

    exoBuild(parameters) {
        super.exoBuild(parameters, "datetime-local");
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value','min','max');
        return attrs;
    }
}

customElements.define("exo-date", CustomExoDate);
customElements.define("exo-time", CustomExoTime);
customElements.define("exo-datetime-local", CustomExoDateTimeLocal);




/* js/controls/exo-file.js */


class CustomExoFile extends CustomExoControl {

    constructor() {
        super();
        this.filename_span = null;
    }

    exoBuild(parameters) {
        super.exoBuildCommon("input", parameters);
        this.exoGetInputElement().setAttribute("type","file");
        this.exoGetInputElement().setAttribute("id","file_test");

        ExoUtils.addStyle(this.exoGetInputElement(),"display","none");
        this.label = document.createElement("label");
        this.label.setAttribute("class","exo-button");
        this.label.setAttribute("for","file_test");

        this.filename_span = document.createElement("span");
        this.filename_span.setAttribute("style","margin-left:10px;")
        this.filename_span.appendChild(document.createTextNode("filename.txt"));

        this.exoGetRootElement().appendChild(this.label);
        this.exoGetRootElement().appendChild(this.filename_span);

        var that = this;

        this.exoGetInputElement().oninput = function (evt) {
            const filelist = that.exoGetInputElement().files;
            var files = {};
            for(var idx=0; idx<filelist.length;idx++) {
                var file = filelist[idx];
                files[file.name] = file;
                ExoUtils.removeAllChildren(that.filename_span);
                that.filename_span.appendChild(document.createTextNode(file.name));
            }
            that.dispatchEvent(new CustomEvent("exo-file-changed",{detail:files}));
        }
        super.exoBuildComplete(parameters);
    }

    exoUpdate(name,value) {
        switch(name) {
            case "button-text":
                 ExoUtils.removeAllChildren(this.label);
                 this.label.appendChild(document.createTextNode(value));
                 break;
            case "filename":
                ExoUtils.removeAllChildren(this.filename_span);
                this.filename_span.appendChild(document.createTextNode(value));
                break;
            default:
                super.exoUpdate(name,value);
        }
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push("filename","button-text");
        return attrs;
    }
/*
    async upload(filelist, callback) {
        var uploaded = {};
        for (var idx = 0; idx < filelist.length; idx++) {
            await this.upload_file(filelist[idx], uploaded);
        }
        callback(uploaded);
    }

    async upload_file(file, uploaded) {
        var that = this;
        var ab = await file.arrayBuffer();
        var dec = new TextDecoder();
        uploaded[file.name] = dec.decode(ab);
    }
*/
}

customElements.define("exo-file", CustomExoFile);


/* js/controls/exo-number.js */


class CustomExoNumber extends CustomExoControl {

    constructor() {
        super();
    }

    exoBuild(parameters) {
        super.exoBuildCommon("input", parameters);

        this.exoGetInputElement().setAttribute("type","number");

         this.exoGetInputElement().addEventListener("change", evt => {
            let v = evt.target.value;
            this.exoSetControlValue(v);
            this.dispatchEvent(new CustomEvent("change"));
            evt.stopPropagation();
        });

        super.exoBuildComplete(parameters);
    }

    exoUpdate(name,value) {
        switch(name) {
            case "min":
                this.exoGetInputElement().setAttribute("min", value);
                break;
            case "max":
                this.exoGetInputElement().setAttribute("max", value);
                break;
            case "step":
                this.exoGetInputElement().setAttribute("step", value);
                break;
            case "value":
                this.exoGetInputElement().value = value;
                this.exoSetControlValue(value);
                break;
            default:
                super.exoUpdate(name,value);
        }
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value','min','max','step');
        return attrs;
    }
}

customElements.define("exo-number", CustomExoNumber);


/* js/controls/exo-radio.js */


class CustomExoRadio extends CustomExoControl {
    constructor() {
        super();
        this.exo_button_count = 0;
        this.exo_button_map = {};
        this.exo_radio_name = "";
    }

    exoBuild(parameters) {
        super.exoBuildCommon("div", parameters);
        this.exo_radio_name = this.exoGetId()+"_rbg";
        this.appendChild(this.exoGetRootElement());
        super.exoBuildComplete(parameters);
    }

    exoUpdate(name, value) {
        switch (name) {
            case "value":
                this.exoSetControlValue(value);
                this.exoSetButtonStates();
                this.exoGetInputElement().value = value;
                break;
            case "options":
                let options = JSON.parse(value);
                this.exoClearRadioButtons();
                options.map((item) => this.exoAddRadioButton(item[0],item[1]));
                this.exoSetButtonStates(); // update the buttons
                break;
            default:
                super.exoUpdate(name, value);
        }
    }

    exoSetButtonStates() {
        var value = this.exoGetControlValue();
        for(var v in this.exo_button_map) {
            var btn = this.exo_button_map[v];
            if (value == v) {
                btn.checked = true;
            } else {
                btn.checked = false;
            }
        }
    }


    exoClearRadioButtons() {
        ExoUtils.removeAllChildren(this.exoGetInputElement());
        this.exo_button_map = {};
        this.exo_button_count = 0;
    }

    exoAddRadioButton(value,label_text) {

        var btn_id = this.exoGetId()+"_b"+this.exo_button_count;
        this.exo_button_count += 1;

        var label = document.createElement("label");
        ExoUtils.addStyle(label,"display","inline-block");
        label.setAttribute("for",btn_id);
        var span = document.createElement("span");
        ExoUtils.addClass(span,"label-body");
        span.appendChild(document.createTextNode(label_text));
        label.appendChild(span);
        var input = document.createElement("input");
        input.setAttribute("id",btn_id);
        input.setAttribute("type","radio");
        input.setAttribute("name", this.exo_radio_name);
        input.setAttribute("value",value);

        this.exo_button_map[value] = input;

        this.exoGetInputElement().appendChild(label);
        this.exoGetInputElement().appendChild(input);

        input.addEventListener("input", evt => {
            this.exoSetControlValue(value);
            evt.stopPropagation();
        });
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('options','value');
        return attrs;
    }


}

customElements.define("exo-radio", CustomExoRadio);

/* js/controls/exo-range.js */




class CustomExoRange extends CustomExoControl {

    constructor() {
        super();
    }

    exoBuild(parameters) {
        super.exoBuildCommon("input", parameters);

        this.exoGetInputElement().setAttribute("type","range");
        this.exoGetInputElement().setAttribute("style","display:inline;");

        this.exoGetInputElement().setAttribute("min", parameters["min"]);
        this.exoGetInputElement().setAttribute("max", parameters["max"]);

        if ("step" in parameters) {
            this.exoGetInputElement().setAttribute("step", parameters["step"]);
        }
        this.exoGetInputElement().value = parameters["value"];

        this.exoGetInputElement().addEventListener("change", evt => {
            let v = evt.target.value;
            this.exoSetControlValue(v);
            this.exoSetOutputValue(v);
            this.dispatchEvent(new CustomEvent("change"));
            evt.stopPropagation();
        });

        let elt = this.exoGetInputElement();
        elt.parentNode.insertBefore(document.createTextNode(parameters["min"]),elt);
        elt.parentNode.insertBefore(document.createTextNode(parameters["max"]),elt.nextSibling);

        this.exoSetOutputValue(parameters["value"]);

        super.exoBuildComplete(parameters);
    }

    exoUpdate(name,value) {
        switch(name) {
            case "value":
                this.exoGetInputElement().value = value;
                this.exoSetControlValue(value);
                this.exoSetOutputValue(value);
                break;
            case "min":
                this.exoGetInputElement().setAttribute("min", value);
                break;
            case "max":
                this.exoGetInputElement().setAttribute("max", value);
                break;
            case "step":
                this.exoGetInputElement().setAttribute("step", value);
                break;
            default:
                super.exoUpdate(name,value);
        }
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value','min','max','step');
        return attrs;
    }
}

customElements.define("exo-range", CustomExoRange);


/* js/controls/exo-select.js */



class CustomExoSelect extends CustomExoControl {

    constructor() {
        super();
        this.exo_value_label_map = {};
        this.exo_is_multiple = false;
    }

    exoBuild(parameters) {

        super.exoBuildCommon("select", parameters);
        this.exoGetInputElement().setAttribute("class", "select");

        this.exoGetInputElement().addEventListener("change", evt => {
            let v = undefined;
            if (this.exo_is_multiple) {
                var selected_values = [];
                var options = this.exoGetInputElement().querySelectorAll("option");
                for (var i=0; i<options.length; i++) {
                    let opt = options[i];
                    if (opt.selected) {
                        selected_values.push(opt.value);
                    }
                }
                v = JSON.stringify(selected_values);
            } else {
                v = this.exoGetInputElement().value;
            }
            this.exoSetControlValue(v);
            this.dispatchEvent(new CustomEvent("change"));
            evt.stopPropagation();
        });
        this.appendChild(this.exoGetRootElement());

        if ("multiple" in parameters) {
            this.exo_is_multiple = true;
            delete parameters["multiple"];
            this.exoGetInputElement().setAttribute("multiple","multiple");
        }
        if ("options" in parameters) {
            this.exoSetOptions(parameters["options"]);
            delete parameters["options"];
        }
        super.exoBuildComplete(parameters);
    }

    exoUpdate(name, value) {
        switch (name) {
            case "value":
                if (this.exo_is_multiple) {
                    let value_arr = [];
                    if (value) {
                        value_arr = JSON.parse(value);
                    }
                    let options = this.exoGetInputElement().querySelectorAll("option");
                    for (var i=0; i<options.length; i++) {
                        let opt = options[i];
                        if (value_arr.includes(opt.value)) {
                            opt.selected = true;
                        } else {
                            opt.selected = false;
                        }
                    }
                    this.exoSetControlValue(value);
                } else {
                    this.exoGetInputElement().value = value;
                    this.exoSetControlValue(value);
                }
                break;
            case "size":
                this.exoGetInputElement().setAttribute("size",value);
                break;
            case "options":
                this.exoSetOptions(value);
                break;
            default:
                super.exoUpdate(name, value);
        }
    }

    exoSetOptions(value) {
        let options = JSON.parse(value);
        let current_value = this.exoGetControlValue();
        this.exoClearOptions();
        options.map((item) => this.exoAddOption(item[0],item[1]));
        let updated_value = undefined;
        if (!this.exo_is_multiple) {
            if (current_value in this.exo_value_label_map) {
                updated_value = current_value;
            }
        } else {
            if (current_value) {
                let current_values = JSON.parse(current_value);
                let updated_values = [];
                current_values.forEach(value => {
                    if (value in this.exo_value_label_map) {
                        updated_values.push(value);
                    }
                });
                updated_value = JSON.stringify(updated_values);
            }
        }
        this.exoUpdate("value",updated_value);
    }

    exoClearOptions() {
        if (this.exoGetInputElement()) {
            ExoUtils.removeAllChildren(this.exoGetInputElement());
        }
        this.exo_value_label_map = {};
    }

    exoAddOption(value,label,disabled) {
        var option = document.createElement("option");
        option.appendChild(document.createTextNode(label));
        option.setAttribute("value", value);
        if (disabled) {
            option.setAttribute("disabled", "disabled");
        } else {
            this.exo_value_label_map[value] = label;
        }
        this.exoGetInputElement().appendChild(option);
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('options','multiple','value');
        return attrs;
    }

}

CustomExoSelect.INVALID_ERROR = "Invalid";

customElements.define("exo-select", CustomExoSelect);

/* js/controls/exo-text.js */


class CustomExoText extends CustomExoControl {

    constructor() {
        super();
    }

    exoBuild(parameters) {
        super.exoBuildCommon("input", parameters);

        this.exoGetInputElement().setAttribute("type","text");
        this.exoGetInputElement().value = parameters["value"] || "";

        this.exoGetInputElement().addEventListener("change", evt => {
            let v = evt.target.value;
            this.exoSetControlValue(v);
            this.dispatchEvent(new CustomEvent("change"));
            evt.stopPropagation();
        });

        super.exoBuildComplete(parameters);
    }

    exoUpdate(name,value) {
        switch(name) {
            case "value":
                this.exoGetInputElement().value = value;
                this.exoSetControlValue(value);
                break;
            default:
                super.exoUpdate(name,value);
        }
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value');
        return attrs;
    }
}

customElements.define("exo-text", CustomExoText);


/* js/controls/exo-textarea.js */


class CustomExoTextArea extends CustomExoControl {

    constructor() {
        super();
    }

    exoBuild(parameters) {
        super.exoBuildCommon("textarea", parameters);

        var that = this;

        this.exoGetInputElement().addEventListener("change", evt => {
            let v = evt.target.value;
            this.exoSetControlValue(v);
            this.dispatchEvent(new CustomEvent("change"));
            evt.stopPropagation();
        });

        super.exoBuildComplete(parameters);
    }

    exoUpdate(name,value) {
        switch(name) {
            case "value":
                this.exoGetInputElement().value = value;
                this.exoSetControlValue(value);
                break;
            case "rows":
            case "cols":
                this.exoGetInputElement().setAttribute(name,value);
                break;
            default:
                super.exoUpdate(name,value);
        }
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value','rows','cols');
        return attrs;
    }
}

customElements.define("exo-textarea", CustomExoTextArea);


/* js/controls/exo-toggle.js */


class CustomExoToggle extends CustomExoControl {
    constructor() {
        super();
    }

    exoBuild(parameters) {
        super.exoBuildCommon("input", parameters);

        var element = this.exoGetInputElement();
        element.setAttribute("type","checkbox");

        var label = document.createElement("label");
        label.setAttribute("class","exo-toggle");
        var parent = element.parentElement;
        parent.removeChild(element);
        var span = document.createElement("span");
        span.setAttribute("class","exo-toggle-slide");
        label.appendChild(element);
        span.appendChild(document.createTextNode(""));
        label.appendChild(span);
        parent.appendChild(label);

        this.label = label;
        this.tt_span = null;
        this.ft_span = null;

        this.slider_span = span;

        this.exoGetInputElement().addEventListener("change", evt => {
            let v = evt.target.checked;
            this.exoSetControlValue(v?"true":"false");
            this.checked = v;
            this.dispatchEvent(new CustomEvent("change"));
            evt.stopPropagation();
        });

        super.exoBuildComplete(parameters);
    }

    exoUpdate(name,value) {
        switch(name) {
            case "value":
                const bvalue = (value == "true") ? true : false;
                this.exoGetInputElement().checked = bvalue;
                this.exoSetControlValue(value);
                this.checked = bvalue;
                break;
            case "true-text":
                if (!this.tt_span) {
                    this.tt_span = document.createElement("span");
                    this.tt_span.setAttribute("class", "exo-toggle-true");
                    this.label.appendChild(this.tt_span);
                }
                ExoUtils.removeAllChildren(this.tt_span);
                if (value) {
                    this.tt_span.appendChild(document.createTextNode(value));
                }
                break;
            case "false-text":
                 if (!this.ft_span) {
                    this.ft_span = document.createElement("span");
                    this.ft_span.setAttribute("class", "exo-toggle-false");
                    this.label.appendChild(this.ft_span);
                }
                ExoUtils.removeAllChildren(this.ft_span);
                if (value) {
                    this.ft_span.appendChild(document.createTextNode(value));
                }
                break;
            case "fg-color":
                ExoUtils.removeClasses( this.slider_span, /(exo-)(.*)(-fg)/);
                ExoUtils.addClass(this.slider_span,"exo-"+value+"-fg");
                break;
            case "bg-color":
                ExoUtils.removeClasses(this.slider_span, /(exo-)(.*)(-bg)/);
                ExoUtils.addClass(this.slider_span,"exo-"+value+"-bg");
                break;
            default:
                super.exoUpdate(name,value);
        }
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push('value');
        attrs.push('true_text');
        attrs.push('false_text');
        return attrs;
    }
}

customElements.define("exo-toggle", CustomExoToggle);


/* js/controls/exo-download.js */


class CustomExoDownload extends CustomExoControl {

    constructor() {
        super();
        this.exo_download_content = null;
        this.exo_download_mimetype = null;
        this.exo_download_href = null;
        this.exo_download_filename = null;
        this.exo_a = null;
    }

    exoBuild(parameters) {
        super.exoBuildCommon("div", parameters);
        this.exoGetInputElement().setAttribute("class","exo-button");

        this.exo_a = document.createElement("a");
        this.exo_a.setAttribute("href","");
        this.exoGetInputElement().appendChild(this.exo_a);
        var that = this;

        this.exo_a.onclick = function (evt) {
            that.dispatchEvent(new CustomEvent("exo-download",{"detail":{}}));
            that.exoSetHref();
        }
        super.exoBuildComplete(parameters);
    }

    exoSetHref() {
        if (!this.exo_download_href) {
            var data_uri = "data:" + this.exo_download_mimetype + ";base64," + btoa(this.exo_download_content);
            this.exo_a.setAttribute("href", data_uri);
        }
    }

    exoUpdate(name,value) {
        switch(name) {
            case "download-filename":
                this.exo_download_filename = value;
                this.exo_a.setAttribute("download", value);
                ExoUtils.removeAllChildren(this.exo_a);
                this.exo_a.appendChild(document.createTextNode(value));
                break;
            case "download-mimetype":
            case "download-content":
                if (name == "download-mimetype") {
                    this.exo_download_mimetype = value;
                } else {
                    this.exo_download_content = value;
                }
                if (this.exo_download_mimetype && this.exo_download_content) {
                    this.exo_download_href = "";
                    this.exo_a.setAttribute("href", this.exo_download_href);
                }
                break;
            case "href":
                this.exo_download_href = value;
                this.exo_a.setAttribute("href", this.exo_download_href);
                break;
            case "fg-color":
                // apply the color to the anchor to override the default link style
                ExoUtils.removeClasses( this.exo_a, /exo-(.*)-fg/);
                ExoUtils.addClass(this.exo_a,"exo-"+value+"-fg");
                super.exoUpdate(name,value);
                break;
            default:
                super.exoUpdate(name,value);
        }
    }

    static get observedAttributes() {
        var attrs = CustomExoControl.observedAttributes;
        attrs.push("download-filename");
        attrs.push("download-content");
        attrs.push("download-mimetype");
        attrs.push("href");
        return attrs;
    }

}

customElements.define("exo-download", CustomExoDownload);

/* js/layouts/tree.js */


class ExoTree extends HTMLDivElement {
    constructor() {
      super();
      this.connected = false;
    }

    connectedCallback() {
        if (this.connected) {
            return;
        }
        this.connected = true;
        let p_elt = this.parentElement;
        if (p_elt.exo_ul == undefined) {

            // p_elt.exo_ul = ExoUtils.createElement("ul",{"class":"exo-tree"});
            p_elt.exo_ul = ExoUtils.createElement("ul",{});
            p_elt.appendChild(p_elt.exo_ul);
        }
        let li = ExoUtils.createElement("li",{"role":"treeitem"});
        let inp = ExoUtils.createElement("input",{"type":"checkbox","aria-hidden":"true"});
        this.label = ExoUtils.createElement("label");
        this.label.appendChild(document.createTextNode(this.getAttribute("label")));
        li.appendChild(inp);
        li.appendChild(this.label);
        p_elt.exo_ul.appendChild(li);
        li.appendChild(this);
        this.set
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name == "label" && this.label) {
            ExoUtils.removeAllChildren(this.label);
            this.label.appendChild(document.createTextNode(newValue));
        }
    }

    static get observedAttributes() {
        return ["label"];
    }
}

customElements.define(
  "exo-tree",
  ExoTree,
    {"extends":"div"}
);



/* js/layouts/tabs.js */


class ExoTab extends HTMLElement {
    constructor() {
      super();
      this.connected = false;
    }

    connectedCallback() {
        if (this.connected) {
            return;
        }
        this.connected = true;
        let p_elt = this.parentElement;
        if (p_elt.exo_tab_count == undefined) {
            p_elt.exo_tab_count = 0;
            p_elt.exo_tabs = [];
        }
        let parent_id = p_elt.getAttribute("id");
        let group_id = parent_id+"-tab-group";
        let tab_content_id = parent_id+"-tab-content";
        let cb_id = parent_id+"-cb";
        let first = false;
        let content_elt = null;
        if (p_elt.exo_tab_count == 0) {

            let cb_elt = ExoUtils.createElement("input",{"aria-hidden":"true", "type":"checkbox", "id":cb_id});
            let cb_label_open = ExoUtils.createElement("label",{
                "aria-hidden":"true",
                "class":"exo-tabs-open exo-button exo-icon exo-icon-medium exo-icon-menu",
                "for":cb_id});
            let cb_label_close = ExoUtils.createElement("label",{
                "aria-hidden":"true",
                "class":"exo-tabs-close exo-button exo-rounded exo-icon exo-icon-medium exo-icon-clear",
                "for":cb_id});

            let break_elt = document.createElement("br");
            content_elt = document.createElement("div");
            content_elt.setAttribute("class","exo-tabs-content");
            content_elt.setAttribute("id", tab_content_id);
            p_elt.insertBefore(content_elt,p_elt.firstElementChild);
            p_elt.insertBefore(break_elt,p_elt.firstElementChild);
            p_elt.insertBefore(cb_label_close,p_elt.firstElementChild);
            p_elt.insertBefore(cb_label_open,p_elt.firstElementChild);
            p_elt.insertBefore(cb_elt,p_elt.firstElementChild);
            first = true;
        } else {
            content_elt = document.getElementById(tab_content_id);
        }
        let content_id = parent_id + "-tab-"+p_elt.exo_tab_count;

        this.label = ExoUtils.createElement("label",{
            "for":content_id,
            "aria-hidden":"true",
            "class":"exo-tabs-item exo-white-bg"});
        this.label.appendChild(document.createTextNode(this.getAttribute("label")));

        let input = ExoUtils.createElement("input", {
            "type":"radio","name":group_id,"id":content_id
        });
        if (first) {
            input.setAttribute("checked","checked");
        }
        p_elt.insertBefore(input, content_elt);
        p_elt.insertBefore(this.label, content_elt);
        p_elt.exo_tabs.push(this);
        p_elt.exo_tab_count += 1;
        document.getElementById(tab_content_id).appendChild(this);
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name == "label" && this.label) {
            ExoUtils.removeAllChildren(this.label);
            this.label.appendChild(document.createTextNode(newValue));
        }
    }

    static get observedAttributes() {
        return ["label"];
    }
}

customElements.define(
  "exo-tab",
  ExoTab
);

/* js/layouts/modal.js */


var exo_modal_counter = 0;

class ExoModal extends HTMLDivElement {
    constructor() {
      super();
      this.connected = false;
    }

    connectedCallback() {
        if (this.connected) {
            return;
        }
        this.connected = true;
        this.modal_id = "exo_modal_id"+exo_modal_counter;
        exo_modal_counter += 1;
        this.setAttribute("class","exo-modal-window-content");
        var w = ExoUtils.createElement("div",{"class":"exo-modal-window"});
        var m = ExoUtils.createElement("div", {"class":"exo-modal"});
        this.checkbox = ExoUtils.createElement("input",{"type":"checkbox","id":this.modal_id});
        if (this.hasAttribute("display")) {
            this.checkbox.checked = (this.getAttribute("display") == "true") ? true : false;
        }
        this.label = ExoUtils.createElement("label",{"for":this.modal_id, "style":"display:none;"});
        this.open_button = ExoUtils.createElement("label",{"class":"exo-button","for":this.modal_id, "style":"display:none;"});
        m.appendChild(this.label);
        m.appendChild(this.checkbox);
        m.appendChild(this.open_button);
        m.appendChild(w);
        var cl = ExoUtils.createElement("label",{"for":this.modal_id});
        this.close_button = ExoUtils.createElement("span",{"tabindex":"-1","class":"exo-icon exo-modal-close"});
        cl.appendChild(this.close_button);
        let p_elt = this.parentElement;
        w.appendChild(this);
        this.appendChild(cl);
        p_elt.appendChild(m);

        ExoModal.observedAttributes.map((attr) => {
            if (this.hasAttribute(attr)) {
                this.attributeChangedCallback(attr,null,this.getAttribute(attr));
            }
        });
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (this.close_button) {
            switch(name) {
                case "button-text":
                    ExoUtils.removeAllChildren(this.open_button);
                    this.open_button.appendChild(document.createTextNode(newValue));
                    if (newValue) {
                        this.open_button.setAttribute("style","display:inline;");
                    } else {
                        this.open_button.setAttribute("style","display:none;");
                    }
                    break;
                case "button-label":
                    ExoUtils.removeAllChildren(this.label);
                    this.label.appendChild(document.createTextNode(newValue));
                    if (newValue) {
                        this.label.setAttribute("style","display:block;");
                    } else {
                        this.label.setAttribute("style","display:none;");
                    }
                    break;
                case "button-fg-color":
                   ExoUtils.applyColor(this.open_button,"fg",newValue);
                    break;
                case "button-bg-color":
                    ExoUtils.applyColor(this.open_button,"bg",newValue);
                    break;
                case "fg-color":
                   ExoUtils.applyColor(this,"fg",newValue);
                    break;
                case "bg-color":
                    ExoUtils.applyColor(this,"bg",newValue);
                    break;
                case "close-button-color":
                    ExoUtils.addClass(this.close_button,"exo-"+newValue);
                    break;
                case "border-color":
                    ExoUtils.applyColor(this, "border", newValue);
                    ExoUtils.addClass(this,"exo-border");
                    break;
                case "display":
                    this.checkbox.checked = (newValue == "true") ? true : false;
                    break;
                case "border":
                case "rounded":
                    ExoUtils.applySizedDimension(this,name,newValue);
                    break;
                case "width":
                    ExoUtils.addStyle(this,"width",newValue);
                    break;
                case "height":
                    ExoUtils.addStyle(this,"max-height",newValue);
                    break;
            }
        }
    }

    static get observedAttributes() {
        return ["button-text", "button-label", "button-fg-color", "button-bg-color", "fg-color", "bg-color", "close-button-color",
            "display", "border-color", "border", "margin", "rounded", "padding", "width", "height"];
    }
}

customElements.define(
  "exo-modal",
  ExoModal,
    {"extends":"div"}
);



/* js/layouts/autocell.js */


/*
    Call this function after the document is loaded (or whenever cell content is updated) to snap the cell width of all cells marked exo-auto-cell
 */
function exo_autocell_snap2grid() {

    function getElementWidth(p,e) {
        var sty = getComputedStyle(p);
        return e.getBoundingClientRect().width +
            parseFloat(sty.getPropertyValue('margin-left')) +
            parseFloat(sty.getPropertyValue('margin-right'));
    }

    var elts = document.getElementsByClassName("exo-auto-cell");
    for(var idx=0; idx<elts.length; idx++) {
        var elt = elts[idx];
        var elt0 = elt.firstElementChild;
        if (elt0) {
            ExoUtils.removeClasses(elt0, /exo-(.*)-cell/);
            var w = getElementWidth(elt,elt0);
            var cells = Math.min(Math.ceil(w/128),12);
            ExoUtils.addClass(elt0,"exo-"+cells+"-cell");
        }
    }
}

/* js/property_sheet/property_sheet.js */


class ExoPropertySheetInput {

    constructor(elt, parameters) {
        this.elt = elt;
        this.parameters = parameters;
        this.value = null;
        this.add_property_change_handler((value) => {
            this.value = value;
        })
    }

    set_property_value(value) {
        this.value = value;
        this.elt.value = value;
    }

    get_property_value() {
        return this.value;
    }

    set_error(message) {
        this.elt.setCustomValidity(message);
    }

    add_property_change_handler(handler) {
        if (this.elt.addEventListener) {
            this.elt.addEventListener("input", (evt) => {
                handler(evt.target.value);
            });
        }
    }
}

class ExoPropertySheetElement extends ExoPropertySheetInput {

    set_property_value(value) {
        this.value = value;
        this.elt.setAttribute("value", value);
    }

    add_property_change_handler(handler) {
        if (this.elt.addEventListener) {
            this.elt.addEventListener("change", (evt) => {
                handler(this.elt.value);
            });
        }
    }

    set_error(message) {
        this.elt.setAttribute("invalid",message);
    }
}

class ExoPropertySheetSelect extends ExoPropertySheetElement {

    constructor(elt, parameters) {
        super(elt,parameters);
        this.multiple = this.elt.hasAttribute("multiple");
    }

    set_property_value(value) {
        this.value = value;
        if (this.multiple) {
            this.elt.setAttribute("value", JSON.stringify(value));
        } else {
            this.elt.setAttribute("value", value);
        }
    }

    add_property_change_handler(handler) {
        if (this.elt.addEventListener) {
            this.elt.addEventListener("change", (evt) => {
                if (this.multiple) {
                    handler(JSON.parse(this.elt.value));
                } else {
                    handler(this.elt.value);
                }
            });
        }
    }
}

class ExoPropertySheetRadio extends ExoPropertySheetElement {

    constructor(elt, parameters) {
        super(elt,parameters);
    }

    set_property_value(value) {
        this.value = value;
        this.elt.setAttribute("value", value);
    }

    add_property_change_handler(handler) {
        if (this.elt.addEventListener) {
            this.elt.addEventListener("change", (evt) => {
                handler(this.elt.value);
            });
        }
    }

}

class ExoPropertySheetNumber extends ExoPropertySheetElement {

    constructor(elt, parameters) {
        super(elt,parameters);
        this.is_integer = parameters ? (parameters.is_integer === true) : false;
    }

    set_property_value(value) {
        this.value = value;
        this.elt.setAttribute("value", String(value));
    }

    add_property_change_handler(handler) {
        if (this.elt.addEventListener) {
            this.elt.addEventListener("change", (evt) => {
                let v = Number.parseInt(this.elt.value);
                if (this.is_integer) {
                    v = Math.round(v);
                }
                handler(v);
            });
        }
    }
}

class ExoPropertySheetCheckbox extends ExoPropertySheetElement {

    set_property_value(value) {
        this.value = value;
        this.elt.setAttribute("value", String(value));
    }

    add_property_change_handler(handler) {
        if (this.elt.addEventListener) {
            this.elt.addEventListener("change", (evt) => {
                handler(this.elt.value === "true");
            });
        }
    }
}

class ExoPropertySheetTable extends ExoPropertySheetElement {

    constructor(elt, parameters) {
        super(elt, parameters);
        this.single_column = parameters ? (parameters["single_column"] || false) : false;
    }

    set_property_value(value) {
        this.value = value;
        this.draw();
    }

    draw() {
        this.elt.innerHTML = "";
        for(let row=0; row<this.value.length; row+=1) {
            this.add_row(row,this.value[row])
        }
    }

    add_property_change_handler(handler) {
        if (this.property_change_handlers === undefined) {
            this.property_change_handlers = [];
        }
        this.property_change_handlers.push(handler);
    }

    add_row(row_index,values) {
        if (this.single_column) {
            values = [values];
        }
        let tr = document.createElement("tr");
        let td0 = document.createElement("td");
        let delete_btn = document.createElement("input");
        delete_btn.setAttribute("type", "button");
        delete_btn.setAttribute("value", "delete");
        delete_btn.addEventListener("click", () => {
            this.value = this.value.slice(0,row_index)
                .concat(this.value.slice(row_index+1));
            this.draw();
            if (this.property_change_handlers) {
                this.property_change_handlers.forEach((handler) => {
                    handler(this.value);
                });
            }
        });

        td0.appendChild(delete_btn);
        tr.appendChild(td0);
        for(let col=0; col<values.length; col++) {
            let td = document.createElement("td");
            td.appendChild(document.createTextNode(values[col]));
            tr.appendChild(td);
        }

        this.elt.appendChild(tr);
    }

    set_error(message) {
        // TODO
    }
}

function ExoPropertySheetElementFactory(element_id, parameters) {
    let elt = document.getElementById(element_id);
    switch(elt.tagName) {
        case "EXO-SELECT":
            return new ExoPropertySheetSelect(elt, parameters);
        case "EXO-RADIO":
            return new ExoPropertySheetRadio(elt, parameters);
        case "EXO-TEXTAREA":
        case "EXO-TEXT":
        case "EXO-DATE":
            return new ExoPropertySheetElement(elt, parameters);
        case "EXO-NUMBER":
        case "EXO-RANGE":
            return new ExoPropertySheetNumber(elt, parameters);
        case "EXO-TOGGLE":
        case "EXO-CHECKBOX":
            return new ExoPropertySheetCheckbox(elt, parameters);
        case "TBODY":
            return new ExoPropertySheetTable(elt, parameters);
        default:
            return new ExoPropertySheetInput(elt, parameters);
    }
}

class ExoPropertySheetManager {

    constructor(property_change_listener, apply_btn_id, reset_btn_id) {
        this.property_change_listener = property_change_listener;
        this.apply_btn = apply_btn_id ? document.getElementById(apply_btn_id): null;
        this.reset_btn = reset_btn_id ? document.getElementById(reset_btn_id): null;
        this.elements = {};
        this.reset_properties = {};
        this.property_constraints = [];

        if (this.apply_btn) {
            this.apply_btn.addEventListener("click",(evt) => {
                this.apply();
            })
        }
        if (this.reset_btn) {
            this.reset_btn.addEventListener("click",(evt) => {
                this.reset();
            })
        }
        this.disable_apply_reset();
    }

    apply() {
        let updated_properties = this.get_properties();
        if (this.property_change_listener) {
            this.property_change_listener(updated_properties);
        }
        this.reset_properties = window.structuredClone(updated_properties);
        this.disable_apply_reset();
    }

    reset() {
        this.set_properties(this.reset_properties);
    }

    disable_apply_reset() {
        if (this.apply_btn) { this.apply_btn.disabled = true; }
        if (this.reset_btn) { this.reset_btn.disabled = true; }
    }

    check_constraints() {
        let passes_constraints = true;
        if (this.property_constraints.length > 0) {
            for(let element_id in this.elements) {
                this.elements[element_id].set_error("");
            }
            let properties = this.get_properties();
            for(let idx=0; idx<this.property_constraints.length; idx++) {
                let errors = this.property_constraints[idx](properties);
                if (errors) {
                    for(let element_id in errors) {
                        passes_constraints = false;
                        this.elements[element_id].set_error(errors[element_id]);
                    }
                }
            }
        }
        return passes_constraints;
    }

    enable_apply_reset() {
        let passes_constraints = this.check_constraints();
        if (this.apply_btn) {
            if (passes_constraints) {
                this.apply_btn.disabled = false;
            } else {
                this.apply_btn.disabled = true;
            }
        }

        if (this.reset_btn) { this.reset_btn.disabled = false; }
    }

    add_element(element_id, parameters, pse) {
        pse = pse || ExoPropertySheetElementFactory(element_id, parameters);
        this.elements[element_id] = pse;
        pse.add_property_change_handler((value) => {
            if (this.apply_btn) {
                // note that the properties can be applied
                this.enable_apply_reset();
            } else {
                // if no apply button exists, update the properties immediately
                if (this.property_change_listener) {
                    this.property_change_listener(this.get_properties());
                }
            }
        });
        return this;
    }

    set_properties(properties) {
        this.reset_properties = window.structuredClone(properties);
        for(let element_id in properties) {
            if (element_id in this.elements) {
                this.elements[element_id].set_property_value(properties[element_id]);
            }
        }
        this.disable_apply_reset();
        return this;
    }

    get_properties() {
        let properties = {};
        for(let element_id in this.elements) {
            properties[element_id] = this.elements[element_id].get_property_value();
        }
        return properties;
    }

    get_property(element_id) {
        return this.elements[element_id].get_property_value();
    }

    update_property(element_id,value) {
        this.elements[element_id].set_property_value(value);
        this.enable_apply_reset();
    }

    add_property_change_handler(element_id, handler) {
        this.elements[element_id].add_property_change_handler(handler);
    }

    add_property_constraint(constraint_check) {
        this.property_constraints.push(constraint_check);
    }
}

