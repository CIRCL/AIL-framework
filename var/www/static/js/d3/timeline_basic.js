//Requirement:	- D3v7
//				- jquery

// container_id = #container_id "data": [{"obj": username, "start": 1111111100000, "end": 2222222200000}, ...]
// tooltip = d3 tooltip object

const create_timeline_basic = (container_id, data) => {

    if(!Object.keys(data).length){
        return;
    }

    const width = 800;
    const height = 100;
    const margin = { top: 10, right: 10, bottom: 40, left: 40 };

    const colorScale = d3.scaleOrdinal(d3.schemeCategory10)
        .domain(data.map(d => d.obj));

    const xScale = d3.scaleTime()
        .domain([d3.min(data, d => d.start), d3.max(data, d => d.end)])
        .range([margin.left, width - margin.right]);

    const svg = d3.select(container_id)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)

    const tooltip = d3.select("body")
        .append("div")
        .attr("class", "tooltip_basic_timeline")
        .style("opacity", 0)
        //d3.select(".tooltip")
        .style("position", "absolute")
        .style("text-align", "center")
        .style("padding", " 8px")
        .style("font", "sans-serif")
        .style("font-size", "12px")
        .style("background", "whitesmoke")
        .style("border", "0px")
        .style("border-radius", "8px")
        .style("pointer-events", "none");

    // date-time format
    const dateTimeFormat = d3.timeFormat("%Y-%m-%d %H:%M");

    svg.selectAll("rect")
        .data(data)
        .enter()
        .append("rect")
        .attr("x", d => xScale(d.start))
        .attr("y", 20)
        .attr("width", d => xScale(d.end) - xScale(d.start))
        .attr("height", 20)
        .attr("fill", d => colorScale(d.obj))
        .on("mouseover", function(event, d) {
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            tooltip.html(`${d.obj}<br>⏳ ${dateTimeFormat(new Date(d.start))}<br>⌛ ${dateTimeFormat(new Date(d.end))}`)
                .style("left", (event.pageX + 5) + "px")
                .style("top", (event.pageY - 28) + "px");
        })
        .on("mousemove", function(event) {
            tooltip.style("left", (event.pageX + 5) + "px")
                .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", function() {
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        });

    svg.selectAll("text")
        .data(data)
        .enter()
        .append("text")
        .attr("x", d => xScale(d.start) + 5)
        .attr("y", 35)
        .text(d => d.obj)
        .attr("fill", "white")
        .style("pointer-events", "none");

    // Date format
    const dateFormat = d3.timeFormat("%Y-%m-%d");

    // x-axis
    const xAxis = d3.axisBottom(xScale)
        .ticks(d3.timeMonth.every(1))
        .tickFormat(dateFormat);

    svg.append("g")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(xAxis)
        .selectAll("text")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    const startDate = new Date(d3.min(data, d => d.start));
    const endDate = new Date(d3.max(data, d => d.end));

    svg.append("text")
        .attr("x", margin.left)
        .attr("y", height - margin.bottom + 14)
        .style("text-anchor", "end")
        .style("font-size", "10px")
        .attr("transform", `rotate(-90, ${margin.left}, ${height - margin.bottom + 10})`)
        .text(dateFormat(startDate));

    svg.append("text")
        .attr("x", width - margin.right)
        .attr("y", height - margin.bottom + 14)
        .style("text-anchor", "end")
        .style("font-size", "10px")
        .attr("transform", `rotate(-90, ${width - margin.right}, ${height - margin.bottom + 10})`)
        .text(dateFormat(endDate));

    //return svg.node();
}
