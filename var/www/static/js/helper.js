// sanitise str_to_sanitize
function sanitize_text(str_to_sanitize) {
    return $("<span\>").text(str_to_sanitize).html()
}
