const sparkline = (container_id, data, options) => {

	const defaults = {
        style: {
            stroke: "rgb(0, 0, 0)",
            strokeWidth: 2
        },
				margin: {top:3, right:3, bottom:3, left:3},
				width: 100,
				height: 60
	};

	options = $.extend(true, defaults, options);


	let width_spark = options.width - options.margin.left - options.margin.right;
	let height_spark = options.height - options.margin.top - options.margin.bottom;

	let maxX = data.length;
	let maxY = d3.max(data, function(d) { return d } );

	let x = d3.scaleLinear()
						.range([0, width_spark - 10])
						.domain([0,maxX]);

	let y = d3.scaleLinear()
						.range([height_spark, 0])
						.domain([0,maxY]);

	let line = d3.line()
						.x(function(d, i) {return x(i)})
						.y(function(d) {return y(d)});

	let res = d3.select( "#"+container_id ).append('svg')
				.attr('width', options.width)
				.attr('height', options.height)
		 .append('g')
		 		.attr("transform", "translate("+options.margin.left+","+options.margin.top+")")
		 .append('path')
				.datum(data)
				.attr('d', line)
				.style("fill", "none")
				.style("stroke", options.style.stroke)
				.style("stroke-width", options.style.strokeWidth);

	return res

}
