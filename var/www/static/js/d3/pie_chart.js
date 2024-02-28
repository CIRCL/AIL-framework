//Requirement:	- D3v5
//							- jquery
// data input: var data = [{"name":"down","value":0},{"name":"up","value":3}]

const pie_chart = (container_id, data, options) => {

	const defaults = {
        style: {
            strokeWidth: 2,
        },
		opacity: .8,
		padding: 10,
		width: 200,
		height: 200
	};

	options = $.extend(true, defaults, options);

	let radius = Math.min(options.width - options.padding, options.height - options.padding) / 2;
	let color = d3.scaleOrdinal(d3.schemeSet3);

	const tooltip = d3.select("#"+container_id).append("div")
			.style("opacity", 0)
			.style("padding", "2px");

	const mouseover = function(d) {
		tooltip.style("opacity", 1)
		tooltip.html("<h4>"+d.data.name + ": </h4>" + d.data.value)
            .style("left", (d3.event.pageX) + "px")
            .style("top", (d3.event.pageY - 28) + "px");
    }
    const mouseleave = function(d) {
        tooltip.style("opacity", 0)
    }

	let svg = d3.select("#"+container_id).append('svg')
				.attr("width", options.width)
				.attr("height", options.height)
				.attr('viewBox','0 0 '+Math.min(options.width, options.height) +' '+Math.min(options.width, options.height) )
				.attr('preserveAspectRatio','xMinYMin')

	let g_pie = svg.append('g')
				.attr('transform', 'translate(' + (options.width/2) + ',' + (options.height/2) + ')');

	let arc_pie = d3.arc()
				.innerRadius(0)
				.outerRadius(radius);


	let pie_pie = d3.pie()
					.value(function(d) { return d.value; })
					.sort(null);

	g_pie.selectAll('path')
		.data(pie_pie(data))
		.enter()
		.append("g")
		.append('path')
		.attr('d', arc_pie)
		.attr('fill', (d,i) => color(i))
		.on("mouseover", mouseover)
		.on("mouseleave", mouseleave)
		.style('opacity', options.opacity)
		.style('stroke', 'white');

	return svg

}
