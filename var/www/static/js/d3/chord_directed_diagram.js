//Requirement:	- D3v7
//				- jquery

// container_id = #container_id{"meta": {obj_gid: label, ...}, "data": [{"source": source, "target": target, "value": value}, ...]}
// tooltip = d3 tooltip object

// TODO: - Mouseover object

const create_directed_chord_diagram = (container_id, data, fct_mouseover, fct_mouseout, options) => {

    function getMaxCharsToShow(angle, radius) {
        const approximateCharWidth = 7; // Approximate width of a character in pixels
        const arcLength = angle * radius; // Length of the arc
        return Math.floor(arcLength / approximateCharWidth); // Maximum number of characters that can fit
    }

    const width = 900;
    const height = width;
    const innerRadius = Math.min(width, height) * 0.5 - 20;
    const outerRadius = innerRadius + 6;

    const labels_meta = data.meta
    data = data.data

    // Compute a dense matrix from the weighted links in data.
    var names = Array.from(d3.union(data.flatMap(d => [d.source, d.target])));
    const index = new Map(names.map((name, i) => [name, i]));
    const matrix = Array.from(index, () => new Array(names.length).fill(0));
    for (const {source, target, value} of data) matrix[index.get(source)][index.get(target)] += value;

    const chord = d3.chordDirected()
        .padAngle(12 / innerRadius)
        .sortSubgroups(d3.descending)
        .sortChords(d3.descending);

    const arc = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius);

    const ribbon = d3.ribbonArrow()
        .radius(innerRadius - 0.5)
        .padAngle(1 / innerRadius);

    const colors = d3.schemeCategory10;

    const svg = d3.select(container_id)
        .append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("viewBox", [-width / 2, -height / 2, width, height])
            .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

    const chords = chord(matrix);

    const textId = `text-${Math.random().toString(36).substring(2, 15)}`;

    svg.append("path")
        .attr("id", textId)
        .attr("fill", "none")
        .attr("d", d3.arc()({outerRadius, startAngle: 0, endAngle: 2 * Math.PI}));

    svg.append("g")
        .attr("fill-opacity", 0.75)
        .selectAll("path")
        .data(chords)
        .enter()
        .append("path")
            .attr("d", ribbon)
            .attr("fill", d => colors[d.target.index])
            .style("mix-blend-mode", "multiply")
        .append("title")
            .text(d => `${labels_meta[names[d.source.index]]}
=> ${d.source.value} Messages
${labels_meta[names[d.target.index]]}`);

    const g = svg.append("g")
        .selectAll("g")
        .data(chords.groups)
        .enter()
        .append("g");

    g.append("path")
        .attr("d", arc)
        .attr("fill", d => colors[d.index])
        .attr("stroke", "#fff")
        .on("mouseover", function(event, d) {
            fct_mouseover(event, d, names[d.index], labels_meta[names[d.index]]);
        })
	    .on("mouseout", fct_mouseout);

    g.each(function(d) {
        const group = d3.select(this);
        const angle = d.endAngle - d.startAngle;
        const text = labels_meta[names[d.index]];
        const maxCharsToShow = getMaxCharsToShow(angle, outerRadius);

        let displayedText
        if (maxCharsToShow <= 1) {
            displayedText = text[0];
        } else {
            displayedText = text.length > maxCharsToShow ? text.slice(0, maxCharsToShow - 1) + "…" : text;
        }

        let info_text = "OUT: " + d3.sum(matrix[d.index]) + " ; IN: " + d3.sum(matrix, row => row[d.index]) + " Messages"

        if (displayedText) {
            group.append("text")
                .attr("dy", -3)
                .append("textPath")
                .attr("xlink:href", `#${textId}`)
                .attr("startOffset", d.startAngle * outerRadius)
                .on("mouseover", function(event, d) {
                    fct_mouseover(event, d, names[d.index], labels_meta[names[d.index]], info_text);
                })
                .on("mouseout", fct_mouseout)
                .text(displayedText);
        }
    });

    //return svg.node();
}



// return svg ???
	// return svg

