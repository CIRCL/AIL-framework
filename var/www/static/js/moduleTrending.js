/* Already defined variable (Before the input)
* 
* var chart_1_num_day = 5;
* var chart_2_num_day = 15;
*
*/

var pie_threshold = 0.05
var options = {
         series: {  pie: {  show: true,
                            radius: 3/5,
                            combine: {
                                color: '#999',
                                threshold: pie_threshold
                            },
                            label: {
                                show: true,
                                radius: 1,
                                formatter: labelFormatter,
                                background: {
                                    opacity: 0.5,
                                    color: '#000'
                                }
                            }
                        }
         },
         grid: { hoverable: true, clickable: true },
         legend: { show: false  },
     };

function labelFormatter(label, series) {
    return "<div style='font-size:8pt; text-align:center; padding:2px; color:white;'>"
               + label + "<br/>" + Math.round(series.percent) + "%</div>";
}


function plot_top_graph(module_name){

    /**** Pie Chart ****/
    
    // moduleCharts is used the decide the url to request data
    var moduleCharts = "size" == module_name ? "providersChart" : ("num" == module_name ? "providersChart" : "moduleCharts");
    var tot_sum = 0; // used to detect elements putted in 'Other' pie's part
    var data_other = []; // used to detect elements putted in 'Other' pie's part


    $.getJSON($SCRIPT_ROOT+"/_"+moduleCharts+"?moduleName="+module_name+"&num_day="+chart_1_num_day,
        function(data) {
                  var temp_data_pie = [];
                  for(i=0; i<data.length; i++){
                      if (i==0 && data[0][0] == "passed_days"){ // If there is no data today, take it from the past
                         if (data[0][1] > 0 && data[0][1] < 7){ // If data is [1:6] day(s) old, put the panel in yellow
                             $("#day-"+module_name).text(data[0][1] + " Day(s) ago "); 
                             $("#panel-"+module_name).removeClass("panel-green")
                             $("#panel-"+module_name).addClass("panel-yellow")
                         } else if (data[0][1] > 6) { // data old of more than 7 days, put the panel in red
                             $("#day-"+module_name).text(data[0][1] + " Day(s) ago "); 
                             $("#panel-"+module_name).removeClass("panel-green")
                             $("#panel-"+module_name).addClass("panel-red")
                         }
                      } else {
                          temp_data_pie.push({label: data[i][0], data: data[i][1]});
                          tot_sum += data[i][1]
                      }
                  }
                  for(i=0; i<temp_data_pie.length; i++){ // Detect element below a certain threshold
                      if (parseInt(temp_data_pie[i].data) / tot_sum < pie_threshold)
                          data_other.push(temp_data_pie[i].label);
                  }

                  $.plot($("#flot-pie-chart-"+module_name), temp_data_pie, options);

                  $("#flot-pie-chart-"+module_name).bind("plotclick", function (event, pos, item) {
                      if (item == null)
                          return; 
                      var clicked_label = item.series.label;
                      update_bar_chart(moduleCharts, "#flot-bar-chart-"+module_name, clicked_label, item.series.color, chart_1_num_day, "%m/%d");
                  });
    });
    
        
    /**** Bar Chart ****/

    function update_bar_chart(chartUrl, chartID, involved_item, serie_color, num_day, timeformat){
        var barOptions = {
            series: {
                bars: { show: false, barWidth: 82800000 },
                lines: { show: true, fill: true }
            },
            xaxis: {
                mode: "time",
                timeformat: timeformat,
                tickSize: [1, 'day'],
                minTickSize: [1, "day"]
            },
            grid: { hoverable: true },
            legend: { show: true,
                      noColumns: 0,
                      position: "nw"
            },
            tooltip: true,
            tooltipOpts: { content: "x: %x, y: %y" }
        };

        if (involved_item == "Other"){ // If part 'Other' has been clicked
            var all_other_temp_data = [];
            var temp_data_bar = [];
            var promises = []; // Use to plot when everything have been received
            for(i=0; i<data_other.length; i++){ // Get data for elements summed up in the part 'Other'
                promises.push(
                    $.getJSON($SCRIPT_ROOT+"/_"+chartUrl+"?keywordName="+data_other[i]+"&moduleName="+module_name+"&bar=true"+"&days="+num_day,
                        function(data) {
                            temp_data_bar = []
                            for(i=0; i<data.length; i++){
                                var curr_date = data[i][0].split('/');
                                temp_data_bar.push([new Date(curr_date[0], curr_date[1]-1, curr_date[2]), data[i][1]]);
                            }
                        all_other_temp_data.push(temp_data_bar);
                        }
                    )
                );
                var barData = {
                    label: involved_item,
                    data: all_other_temp_data,
                    color: serie_color
                };
            }

            $.when.apply($, promises).done( function () {
                var dataBar = []
                for(i=0; i<data_other.length; i++) //format data for the plot
                    dataBar.push({label: data_other[i], data: all_other_temp_data[i]})
            
                $.plot($(chartID), dataBar, {
                	series: {
                		stack: true,
                		lines: { show: true, fill: true, steps: false },
                		bars: { show: false, barWidth: 82800000 },
                	},
                    xaxis: {
                        mode: "time",
                        timeformat: timeformat,
                        tickSize: [1, 'day'],
                        minTickSize: [1, "day"]
                    },
                    grid: { hoverable: true },
                    legend: { show: true,
                      noColumns: 1,
                      position: "nw"
                    },
                    tooltip: true,
                    tooltipOpts: { content: "x: %x, y: %y" }
                });
            });

        } else { // Normal pie's part clicked

            $.getJSON($SCRIPT_ROOT+"/_"+chartUrl+"?keywordName="+involved_item+"&moduleName="+module_name+"&bar=true"+"&days="+num_day,
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
        }
    };
}
