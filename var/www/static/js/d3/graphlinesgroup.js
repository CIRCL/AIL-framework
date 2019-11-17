//Requirement:	- D3v5
//							- jquery
// data input: var data = [{"name": "Name1","Data": [{"date": "20191101","value": "35"},{"date": "20191102","value": "12"}]},
//												 {"name": "Name2","Data": [{"date": "20191101","value": "23"},{"date": "20191102","value": "34"}]}

const multilines_group = (container_id, data, options) => {

	const defaults = {
        style: {
            stroke: "rgb(0, 0, 0)",
            strokeWidth: 2,
						strokeWidthHover: 4.5
        },
				margin: {top:5, right:150, bottom:40, left:40},
				width: 700,
				height: 400
	};

	options = $.extend(true, defaults, options);

	let width_graph = options.width - options.margin.left - options.margin.right;
	let height_graph = options.height - options.margin.top - options.margin.bottom;

	let parseDate = d3.timeParse("%Y%m%d");

	let x = d3.scaleTime()
	    .range([0, width_graph]);

	let y = d3.scaleLinear()
	    .range([height_graph, 0]);

	let color = d3.scaleOrdinal(d3.schemeCategory10);
	color.domain(data.map(function (d) { return d.name; }));

	let xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%m-%d"));
	let yAxis = d3.axisLeft(y);

	let line = d3.line()
					    .x(function (d) {
    						return x(d.date);
							})
					    .y(function (d) {
					    	return y(d.value);
							});

	data.forEach(function (kv) {
		kv.Data.forEach(function (d) {
			d.date = parseDate(d.date);
		});
	});

	let cities = data;

	let minX = d3.min(data, function (kv) { return d3.min(kv.Data, function (d) { return d.date; }) });
	let maxX = d3.max(data, function (kv) { return d3.max(kv.Data, function (d) { return d.date; }) });
	let minY = d3.min(data, function (kv) { return d3.min(kv.Data, function (d) { return d.value; }) });
	let maxY = d3.max(data, function (kv) { return d3.max(kv.Data, function (d) { return d.value; }) });

	x.domain([minX, maxX]);
	y.domain([minY, maxY]);

	let svg = d3.select("#"+container_id)
							.append("svg")
						    .attr("width", options.width)
						    .attr("height", options.height)
					    .append("g")
					    	.attr("transform", "translate("+options.margin.left+","+options.margin.top+")");

	svg.append("g")
				.attr("transform", "translate(0," + height_graph + ")")
				.call(xAxis)
				.selectAll("text")
					.style("text-anchor", "end")
					.attr("dx", "-.8em")
					.attr("dy", ".15em")
					.attr("transform", "rotate(-65)");

	svg.append("g")
				.call(yAxis)
				.append("text")
					.attr("transform", "rotate(-90)")
					.attr("y", 6)
					.attr("dy", ".71em")
					.style("text-anchor", "end");

	let name = svg.selectAll(".name")
	    .data(cities)
	    .enter().append("g")

	name.append("path")
	    .attr("d", function (d) {
			    return line(d.Data);
			})
			.style("fill", "none")
			.style("stroke-width", options.style.strokeWidth)
			.style("stroke", function (d) {
			    return color(d.name);
			})
			.on("mouseover", function(d) {
				d3.select(this).style("stroke-width", options.style.strokeWidthHover);
			})
			.on("mouseout", function(d) {
				d3.select(this).style("stroke-width", options.style.strokeWidth)
											 .style("stroke", function (d) {
											 		return color(d.name);
											 })
			});

	name.append("text")
	    .datum(function (d) {
	    	return {
	        name: d.name,
	        date: d.Data[d.Data.length - 1].date,
	        value: d.Data[d.Data.length - 1].value
	    	};
			})
	    .attr("transform", function (d) {
	    	return "translate(" + x(d.date) + "," + y(d.value) + ")";
			})
	    .attr("x", 3)
	    .attr("dy", ".35em")
			.style("stroke", function (d) {
			    return color(d.name);
			})
			.style("stroke-width", 0.5)
	    .text(function (d) {
	        return d.name;
			});

	return svg

}
