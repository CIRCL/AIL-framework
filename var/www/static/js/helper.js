// sanitise str_to_sanitize
function sanitize_text(str_to_sanitize) {
    return $("<span\>").text(str_to_sanitize).html()
}

// REQUIRE var url_obj_description
function show_obj_tooltip(container, obj_gid) {
    container = $(container);

    if (container.data('bs.popover')) {
        container.popover('show');
    } else {
        let pop_header = "<div class=\"card text-white\"><div class=\"card-header bg-dark pb-0\">" + sanitize_text(obj_gid) + "/div>";
        let spinner = "<div class=\"card-body bg-dark pt-0\"><div class=\"spinner-border text-warning\" role=\"status\"></div> Loading...</div>";

        container.popover({
            title: pop_header,
            content: spinner,
            html: true,
            container: container,
        })
        container.popover('show');

        let popoverInstance = container.data('bs.popover');


        $.getJSON(url_obj_description + obj_gid, function (data) {

            let desc = "<div class=\"card-body bg-dark text-white pb-1 pt-2\"><dl class=\"row py-0 my-0\">"
            Object.keys(data).forEach(function(key) {
                if (key=="status") {
                    desc = desc + "<dt class=\"col-sm-3 px-0\">status</dt><dd class=\"col-sm-9 px-0\"><div class=\"badge badge-pill badge-light flex-row-reverse\" style=\"color:"
                    if (data["status"]) {
                        desc = desc + "Green"
                    } else {
                        desc = desc + "Red"
                    }
                    desc = desc + ";\"><i class=\"fas "
                    if (data["status"]) {
                        desc = desc + "fa-check-circle\"></i>UP"
                    } else {
                        desc = desc + "fa-times-circle\"></i>DOWN"
                    }
                    desc = desc + "</div></dd>"
                } else if (key!=="tags" && key!=="id" && key!=="img" && key!=="svg_icon" && key!=="icon" && key!=="link" && key!=="type") {
                    if (data[key]) {
                        if ((key==="first_seen" || key==="last_seen") && data[key].length===8) {
                            let date = sanitize_text(data[key])
                            desc = desc + "<dt class=\"col-sm-3 px-0\">" + sanitize_text(key) + "</dt><dd class=\"col-sm-9 px-0 mb-1\">" + date.slice(0, 4) + "-" + date.slice(4, 6) + "-" + date.slice(6, 8) + "</dd>"
                        } else {
                            desc = desc + "<dt class=\"col-sm-3 px-0\">" + sanitize_text(key) + "</dt><dd class=\"col-sm-9 px-0 mb-1\">" + sanitize_text(data[key]) + "</dd>"
                        }
                    }
                }
            });
            desc = desc + "</dl>"

            if (data["tags"]) {
                data["tags"].forEach(function(tag) {
                    desc = desc + "<span class=\"badge badge-warning\">"+ sanitize_text(tag) +"</span>";
                });
            }

            /*if (data["img"]) {
                if (data["tags_safe"]) {
                    if (data["type"] === "screenshot") {
                        desc = desc + "<img src={{ url_for('objects_item.screenshot', filename="") }}"
                    } else if (data["type"] === "favicon") {
                        desc = desc + "<img src={{ url_for('objects_favicon.favicon', filename="") }}"
                    } else {
                        desc = desc + "<img src={{ url_for('objects_image.image', filename="") }}"
                    }
                    desc = desc + data["img"] +" class=\"img-thumbnail blured\" id=\"tooltip_screenshot_correlation\" style=\"\"/>";
                } else {
                    desc = desc + "<span class=\"my-2 fa-stack fa-4x\"><i class=\"fas fa-stack-1x fa-image\"></i><i class=\"fas fa-stack-2x fa-ban\" style=\"color:Red\"></i></span>";
                }
            }*/

            desc = desc + "</div></div>"
            //div.html(desc)
            //    .style("left", (d3_pageX) + "px")
            //    .style("top", (d3_pageY - 28) + "px");
            //d.popover = desc

            if (data["img"]) {
                blur_tooltip();
            }

            popoverInstance.config.content = desc;
            popoverInstance.setContent();
            popoverInstance.update();


        //let popoverid = container.attr('aria-describedby');
        //$('#' + popoverid).find('.popover-header').html(newTitle);
        //$('#' + popoverid).find('.popover-body').html('newContesssnt');

        }).fail(function(error) {
            let desc = "<div class=\"card-body bg-dark text-white pt-0\"><i class=\"fas fa-3x fa-times text-danger\"></i>"+ error.statusText +"</div>"
            popoverInstance.config.content = desc;
            popoverInstance.setContent();
            popoverInstance.update();

        });

        container.popover('hide');
        container.popover('show');
    }

}

function hide_obj_tooltip(container) {
    container = $(container);
    container.popover('hide')

}

function blur_tooltip(){
    var image = $('#tooltip_screenshot_correlation')[0];
    if (image) {
        let blurValue = $('#blur-slider-correlation').val();
        blurValue = 15 - blurValue;
        image.style.filter = "blur(" + blurValue + "px)";
    }
}

function show_search_helper_tooltip(container) {
    container = $(container);

    if (container.data('bs.popover')) {
        container.popover('show');
    } else {
        let c_helper = "<div class=\"pt-0\"><ul><li>Use <kbd>\"double quotes\"</kbd> for exact phrase searches.</li><li>Use <kbd>-</kbd> to exclude specific words.</li><li>Use <kbd>.</kbd> to match any single character.</li><li>A maximum of 10 words can be used in a search query.</li></ul></div>";

        container.popover({
            content: c_helper,
            html: true,
            container: 'body',
        })
        container.popover('show');

        //let popoverInstance = container.data('bs.popover');
        //container.popover('hide');
        //container.popover('show');
    }

}

function show_text_tooltip(container, text) {
    container = $(container);

    if (container.data('bs.popover')) {
        container.popover('show');
    } else {
        let c_helper = "<p style=\"white-space: pre-wrap\">" + text + "</p>";

        container.popover({
            content: c_helper,
            html: true,
            container: 'body',
        })
        container.popover('show');
    }

}