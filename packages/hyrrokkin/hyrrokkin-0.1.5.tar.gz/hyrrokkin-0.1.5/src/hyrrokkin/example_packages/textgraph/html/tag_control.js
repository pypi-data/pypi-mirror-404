/*   Skadi - A visual modelling tool for constructing directed graphs.

     Copyright (C) 2022-2025 Visual Topology Ltd

     Licensed under the MIT License
*/

class TagControl {

    constructor(input_id, add_input_id, tags_id) {
        this.tag_input = document.getElementById(input_id);
        this.add_tag_btn = document.getElementById(add_input_id);
        this.input_tags = document.getElementById(tags_id);
        this.tags = [];
        this.add_tag_btn.addEventListener("click", () => {
            let new_tags = this.tag_input.value.split(" ");
            new_tags.forEach((tag) => {
                this.create_tag(tag,false);
            });
            if (this.update_listener) {
                this.update_listener(this.tags);
            }
        });
        this.update_listener = null;
    }

    set_update_listener(update_listener) {
        this.update_listener = update_listener;
    }

    set_tags(tags) {
        this.input_tags.innerHTML = "";
        this.tags = [];
        for(var idx=0; idx<tags.length; idx++) {
            this.create_tag(tags[idx],true);
        }
    }

    create_tag(tag_text, append) {
        if (this.tags.includes(tag_text)) {
            return;
        }
        this.tags.push(tag_text);
        var new_span = document.createElement("span");
        new_span.setAttribute("class", "tags_area_tile")
        var txt = document.createTextNode(tag_text);
        new_span.appendChild(txt);
        var remove_btn = document.createElement("input");
        remove_btn.setAttribute("type", "button");
        remove_btn.setAttribute("value", "x");
        remove_btn.setAttribute("class", "remove_tag_btn");
        remove_btn.addEventListener("click", () => {
            this.input_tags.removeChild(new_span);
            this.tags = this.tags.filter(name => name !== tag_text);
            if (this.update_listener) {
                this.update_listener(this.tags);
            }
        });
        new_span.appendChild(remove_btn);
        if (append) {
            this.input_tags.appendChild(new_span);
        } else {
            this.input_tags.insertBefore(new_span, this.input_tags.firstElementChild);
        }
    }
}