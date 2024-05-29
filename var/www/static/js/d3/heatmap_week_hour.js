//Requirement:	- D3v7
//				- jquery
// data input: var data = [{"count":0,"date":"2023-11-20","day":0,"hour":0}
// based on gist nbremer/62cf60e116ae821c06602793d265eaf6

// container_id = #heatmapweekhour

const create_heatmap_week_hour = (container_id, data, options) => {


    var days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
        times = d3.range(24);

    var margin = {
        top: 80,
        right: 50,
        bottom: 20,
        left: 50
    };

    var width = Math.max(Math.min(window.innerWidth, 1000), 500) - margin.left - margin.right - 20,
        gridSize = Math.floor(width / times.length),
        height = gridSize * (days.length + 2);

    var heatmap_font_size = width * 62.5 / 900;

//SVG container
    var svg = d3.select(container_id)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // create a tooltip
    const tooltip = d3.select("body")
        .append("div")
        .attr("class", "tooltip_heatmap")
        .style("opacity", 0)
        .style("position", "absolute")
        .style("pointer-events", "none")
        .style("background-color", "white")
        .style("border", "solid")
        .style("border-width", "2px")
        .style("border-radius", "5px")
        .style("padding", "5px")

    // Three function that change the tooltip when user hover / move / leave a cell
    const mouseover = function(event, d) {
        d3.select(event.target)
            .style("stroke", "black")
            .style("stroke-opacity", 1)

        let d3_pageX = event.pageX;
        let d3_pageY = event.pageY;

        tooltip.html(d.date + " " + d.hour + "-" + (d.hour + 1) + "h: <b>" + d.count + "</b> messages")
            .style("left", (d3_pageX) + "px")
		    .style("top", (d3_pageY - 28) + "px");
        tooltip.transition()
		    .duration(200)
		    .style("opacity", 1);
    }
    const mouseleave = function(event, d) {
        d3.select(event.target)
            .style("stroke", "white")
            //.style("stroke-opacity", 0.8)
        tooltip.transition()
		    .duration(200)
            .style("opacity", 0)
    }

///////////////////////////////////////////////////////////////////////////
//////////////////////////// Draw Heatmap /////////////////////////////////
///////////////////////////////////////////////////////////////////////////

    var colorScale = d3.scaleLinear()
        .domain([0, d3.max(data, function (d) {
            return d.count;
        }) / 2, d3.max(data, function (d) {
            return d.count;
        })])
        .range(["#FFFFF6", "#3E9583", "#1F2D86"])
    //.interpolate(d3.interpolateHcl);

    var dayLabels = svg.selectAll(".dayLabel")
        .data(days)
        .enter().append("text")
        .text(function (d) {
            return d;
        })
        .attr("x", 0)
        .attr("y", function (d, i) {
            return i * gridSize;
        })
        .style("text-anchor", "end")
        .attr("transform", "translate(-36, -11)")
        .attr("class", function (d, i) {
            return ((i >= 0 && i <= 4) ? "dayLabel mono axis axis-workweek" : "dayLabel mono axis");
        })
        .style("font-size", heatmap_font_size + "%");

    var timeLabels = svg.selectAll(".timeLabel")
        .data(times)
        .enter().append("text")
        .text(function (d) {
            return d;
        })
        .attr("x", function (d, i) {
            return i * gridSize;
        })
        .attr("y", 0)
        .style("text-anchor", "middle")
        .attr("transform", "translate(-" + gridSize / 2 + ", -36)")
        .attr("class", function (d, i) {
            return ((i >= 8 && i <= 17) ? "timeLabel mono axis axis-worktime" : "timeLabel mono axis");
        })
        .style("font-size", heatmap_font_size + "%");

    var heatMap = svg.selectAll(".hour")
        .data(data)
        .enter().append("rect")
            .attr("x", function (d) {
                return (d.hour - 1) * gridSize;
            })
            .attr("y", function (d) {
                return (d.day - 1) * gridSize;
            })
            .attr("class", "hour bordered")
            .attr("width", gridSize)
            .attr("height", gridSize)
            .style("stroke", "white")
            .style("stroke-opacity", 0.6)
            .style("fill", function (d) {
                return colorScale(d.count);
            })
            .on("mouseover", mouseover)
            .on("mouseleave", mouseleave);

//Append title to the top
    svg.append("text")
        .attr("class", "title")
        .attr("x", width / 2)
        .attr("y", -60)
        .style("text-anchor", "middle")
        .text("Chat Messages");

///////////////////////////////////////////////////////////////////////////
//////////////// Create the gradient for the legend ///////////////////////
///////////////////////////////////////////////////////////////////////////

//Extra scale since the color scale is interpolated
    var countScale = d3.scaleLinear()
        .domain([0, d3.max(data, function (d) {
            return d.count;
        })])
        .range([0, width])

//Calculate the variables for the temp gradient
    var numStops = 10;
    countRange = countScale.domain();
    countRange[2] = countRange[1] - countRange[0];
    countPoint = [];
    for (var i = 0; i < numStops; i++) {
        countPoint.push(i * countRange[2] / (numStops - 1) + countRange[0]);
    }

//Create the gradient
    svg.append("defs")
        .append("linearGradient")
        .attr("id", "legend-heatmap")
        .attr("x1", "0%").attr("y1", "0%")
        .attr("x2", "100%").attr("y2", "0%")
        .selectAll("stop")
        .data(d3.range(numStops))
        .enter().append("stop")
        .attr("offset", function (d, i) {
            return countScale(countPoint[i]) / width;
        })
        .attr("stop-color", function (d, i) {
            return colorScale(countPoint[i]);
        });

///////////////////////////////////////////////////////////////////////////
////////////////////////// Draw the legend ////////////////////////////////
///////////////////////////////////////////////////////////////////////////

    var legendWidth = Math.min(width * 0.8, 400);
//Color Legend container
    var legendsvg = svg.append("g")
        .attr("class", "legendWrapper")
        .attr("transform", "translate(" + (width / 2) + "," + (gridSize * days.length) + ")");  // 319

//Draw the Rectangle
    legendsvg.append("rect")
        .attr("class", "legendRect")
        .attr("x", -legendWidth / 2)
        .attr("y", 0)
        //.attr("rx", hexRadius*1.25/2)
        .attr("width", legendWidth)
        .attr("height", 10)
        .style("fill", "url(#legend-heatmap)");

//Append title
    legendsvg.append("text")
        .attr("class", "legendTitle")
        .attr("x", 0)
        .attr("y", -10)
        .style("text-anchor", "middle")
        .text("Number of Messages");

//Set scale for x-axis
    var xScale = d3.scaleLinear()
        .range([-legendWidth / 2, legendWidth / 2])
        .domain([0, d3.max(data, function (d) {
            return d.count;
        })]);

//Define x-axis
    var xAxis = d3.axisBottom(xScale)
        //.orient("bottom")
        .ticks(5);
    //.tickFormat(formatPercent)

//Set up X axis
    legendsvg.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(0," + (10) + ")")
        .call(xAxis);
    
// return svg ???
	// return svg

}
