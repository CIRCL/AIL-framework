//Requirement:	- D3v5
//				- jquery
// data input: var data = [{ date: "2024-02-21", down: 0, up: 0}, { date: "2024-02-22", down: 1, up: 3}]
//

const barchart_stack = (container_id, data, options) => {

	const defaults = {
        style: {
            stroke: "rgb(0, 0, 0)",
            strokeWidth: 2,
			strokeWidthHover: 4.5
        },
		margin: {top:20, right:90, bottom:55, left:0},
		width: 500,
		height: 500
	};

	options = $.extend(true, defaults, options);

	let width_graph = options.width - options.margin.left - options.margin.right;
	let height_graph = options.height - options.margin.top - options.margin.bottom;

	let x = d3.scaleBand().rangeRound([0, width_graph]).padding(0.1);
	let y = d3.scaleLinear().rangeRound([height_graph, 0]);

	let xAxis = d3.axisBottom(x);
	let yAxis = d3.axisLeft(y);

	let color = d3.scaleOrdinal(d3.schemeSet3);

	let svg = d3.select("#"+container_id).append("svg")
			.attr("viewBox", "0 0 "+width_graph+" "+options.height)
			.attr("width",  options.width)
			.attr("height", options.height)
        .append("g")
			.attr("transform", "translate("+options.margin.left+","+options.margin.top+")");

	// popover
	$('[data-toggle="popover"]').popover({
		placement: 'top',
		container: 'body',
		html : true,
	});

    const mouseover = function(d) {
        $(this).popover({
			title: d.name,
			placement: 'top',
			container: 'body',
			trigger: 'manual',
			html : true,
			content: function() {
          		return d.label + "<br/>num: " + d3.format(",")(d.value ? d.value: d.y1 - d.y0);
			}
      	});
      	$(this).popover('show')
    }
    const mouseleave = function(d) {
        $('.popover').each(function() {
			$(this).remove();
        });
    }

	let labelVar = 'date';
	let varNames = d3.keys(data[0])
						.filter(function (key) { return key !== labelVar;});

	data.forEach(function (d) {
		let y0 = 0;
		d.mapping = varNames.map(function (name) {
			return {
				name: name,
		        label: d[labelVar],
		        y0: y0,
		        y1: y0 += +d[name]
			};
		});
		d.total = d.mapping[d.mapping.length - 1].y1;
	});

	x.domain(data.map(function (d) { return (d.date); }));
	y.domain([0, d3.max(data, function (d) { return d.total; })]);

	svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height_graph + ")")
        .call(xAxis)
			.selectAll("text")
				.style("fill", "steelblue")
				.attr("transform", "rotate(-18)" )
				//.attr("transform", "rotate(-40)" )
				.style("text-anchor", "end");

	svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
      	.append("text")
        	.attr("transform", "rotate(-90)")
        	.attr("y", 6)
        	.attr("dy", ".71em")
        	.style("text-anchor", "end");

	let selection = svg.selectAll(".series")
		.data(data)
		.enter().append("g")
		      .attr("transform", function (d) { return "translate(" + x((d.date)) + ",0)"; });

	selection.selectAll("rect")
		.data(function (d) { return d.mapping; })
	    .enter().append("rect")
			  	.attr("width", x.bandwidth())
			  	.attr("y", function (d) { return y(d.y1); })
			  	.attr("height", function (d) { return y(d.y0) - y(d.y1); })
			  	.style("fill", function (d) { return color(d.name); })
			  	.style("stroke", "grey")
			  	.on("mouseover", mouseover)
				.on("mouseout", mouseleave)


	data.forEach(function(d) {
		if(d.total != 0){
			svg.append("text")
				.attr("dy", "-.35em")
				.attr('x', x(d.date) + x.bandwidth()/2)
				.attr('y', y(d.total))
				.style("text-anchor", "middle")
				.text(d.total);
		}
	});

	// drawLegend(varNames)
	let legend = svg.selectAll(".legend")
            .data(varNames.slice().reverse())
			.enter().append("g")
				.attr("transform", function (d, i) { return "translate(0," + i * 20 + ")"; });

	legend.append("rect")
		.attr("x", width_graph)
		.attr("width", 10)
		.attr("height", 10)
		.style("fill", color)
		.style("stroke", "grey");

	legend.append("text")
		.attr("x", width_graph - 2)
		.attr("y", 6)
		.attr("dy", ".35em")
		.style("text-anchor", "end")
		.text(function (d) { return d; });

	return svg

}
