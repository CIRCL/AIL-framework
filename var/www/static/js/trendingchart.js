
/* Already defined variable (Before the input)
* 
* var chart_1_num_day = 5;
* var chart_2_num_day = 15;
*
*/

function plot_top_graph(trendingName){
    /**** Flot Pie Chart ****/
    var options = {
                      series: {  pie: {  show: true  } },
                      grid: { hoverable: true, clickable: true },
                      legend: { show: false  }
                  };
    
    
    // Graph1
    $.getJSON($SCRIPT_ROOT+"/_progressionCharts?trendingName="+trendingName+"&num_day="+chart_1_num_day,
        function(data) {
                  temp_data_pie = [];
                  for(i=0; i<data.length; i++){
                      temp_data_pie.push({label: data[i][0], data: data[i][1]});
                  }
                  $.plot($("#flot-pie-chart1-"+trendingName), temp_data_pie, options);

                  setTimeout(function() { 
                     $("#flot-pie-chart1-"+trendingName).bind("plotclick", function (event, pos, item) {
                         if (item == null)
                             return; 
                         var clicked_label = item.series.label;
                         update_bar_chart("#flot-bar-chart1-"+trendingName, clicked_label, item.series.color, chart_1_num_day, "%m/%d");
                         update_bar_chart("#flot-bar-chart2-"+trendingName, clicked_label, item.series.color, chart_2_num_day);
                     });
                  }, 500);
    });
    
        
    // flot bar char
    function update_bar_chart(chartID, involved_item, serie_color, num_day, timeformat){
        var barOptions = {
            series: {
                bars: { show: true, barWidth: 82800000 }
            },
            xaxis: {
                mode: "time",
                timeformat: timeformat,
                tickSize: [1, 'day'],
                minTickSize: [1, "day"]
            },
            grid: { hoverable: true },
            legend: { show: true },
            tooltip: true,
            tooltipOpts: { content: "x: %x, y: %y" }
        };
    
        $.getJSON($SCRIPT_ROOT+"/_progressionCharts?attributeName="+involved_item+"&bar=true"+"&days="+num_day,
            function(data) {
                var temp_data_bar = []
                for(i=0; i<data.length; i++){
                    var curr_date = data[i][0].split('/');
                    temp_data_bar.push([new Date(curr_date[0], curr_date[1]-1, curr_date[2]), data[i][1]]);
                }
                var barData = {
                    label: involved_item,
                    data: temp_data_bar,
                    color: serie_color
                };
                $.plot($(chartID), [barData], barOptions);
            });
    };
};
