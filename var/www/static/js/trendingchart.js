
/* Already defined variable (Before the input)
* 
* var chart_1_num_day = 5;
* var chart_2_num_day = 15;
*
*/

function plot_top_graph(trendingName, init){
    /**** Flot Pie Chart ****/
    var tot_sum = 0; // used to detect elements placed in 'Other' pie's part
    var data_other = []; // used to detect elements placed in 'Other' pie's part

    var pie_threshold = 0.05
    var options = {
                      series: {  
                          pie: {  
                              show: true,
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
                      legend: { show: false  }
                  };
    
    function labelFormatter(label, series) {
        return "<div style='font-size:8pt; text-align:center; padding:2px; color:white;'>"
               + label + "<br/>" + Math.round(series.percent) + "%</div>";
    }


    
    // Graph1
    $.getJSON($SCRIPT_ROOT+"/_progressionCharts?trendingName="+trendingName+"&num_day="+chart_1_num_day,
        function(data) {
                  temp_data_pie = [];
                  for(i=0; i<data.length; i++){
                      temp_data_pie.push({label: data[i][0], data: data[i][1]});
                      tot_sum += data[i][1];
                  }

                  for(i=0; i<temp_data_pie.length; i++){ // Detect element below a certain threshold
                      if (parseInt(temp_data_pie[i].data) / tot_sum < pie_threshold)
                          data_other.push(temp_data_pie[i].label);
                  }

                  $.plot($("#flot-pie-chart1-"+trendingName), temp_data_pie, options);

                  if (init){ //prevent multiple binding due to the refresh function
                      setTimeout(function() { 
                         $("#flot-pie-chart1-"+trendingName).bind("plotclick", function (event, pos, item) {
                             if (item == null)
                                 return; 
                             var clicked_label = item.series.label;
                             update_bar_chart("#flot-bar-chart1-"+trendingName, clicked_label, item.series.color, chart_1_num_day, "%m/%d");
                             update_bar_chart("#flot-bar-chart2-"+trendingName, clicked_label, item.series.color, chart_2_num_day);
                         });
                      }, 500);
                  }
    });
    
        
    // flot bar char
    function update_bar_chart(chartID, involved_item, serie_color, num_day, timeformat, can_bind){
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
    
        if (involved_item == "Other"){
   
            var all_other_temp_data = []; // the data_bar of all series
            var temp_data_bar; //the data_bar associated with one serie
            var promises = []; // Use to plot when everything has been received
            var involved_item

            for(i=0; i<data_other.length; i++){ // Get data for elements summed up in the part 'Other'
                involved_item = data_other[i];
                var request = $.getJSON($SCRIPT_ROOT+"/_progressionCharts?attributeName="+involved_item+"&bar=true"+"&days="+num_day,
                        function(data) {
                            temp_data_bar = []
                            for(i=1; i<data.length; i++){
                                var curr_date = data[i][0].split('/');
                                var offset = (data_other.length/2 - data_other.indexOf(data[0]))*10000000
                                temp_data_bar.push([new Date(curr_date[0], curr_date[1]-1, curr_date[2]).getTime() + offset, data[i][1].toFixed(2)]);
                                //console.log(new Date(curr_date[0], curr_date[1]-1, curr_date[2]).getTime() + offset);
                                
                            }
                            // Insert temp_data_bar in order so that color and alignement correspond for the provider graphs
                            all_other_temp_data.splice(data_other.indexOf(data[0]), 0, [ data[0], temp_data_bar, data_other.indexOf(data[0])]); 
                        }
                )
                promises.push(request);
            }

            /* When everything has been received, start the plotting process */
            $.when.apply($, promises).done( function (arg) {
                var dataBar = []

                for(i=0; i<all_other_temp_data.length; i++) //format data for the plot
                    dataBar.push({bars: { barWidth: 8280000, order: all_other_temp_data[i][2] }, label: all_other_temp_data[i][0], data: all_other_temp_data[i][1]});

                $.plot($(chartID), dataBar, {
                    series: {
                    	stack: false,
                    	lines: { show: false, fill: true, steps: false },
                    	bars: { show: true},
                    },
                    xaxis: {
                        mode: "time",
                        timeformat: timeformat,
                        tickSize: [1, 'day'],
                        minTickSize: [1, "day"]
                    },
                    yaxis: {
                        //transform: function (v) { return v < 1 ? v : Math.log(v); }
                    },
                    grid: { hoverable: true },
                    legend: { show: true,
                      noColumns: 1,
                      position: "nw"
                    },
                    tooltip: true,
                    tooltipOpts: { content: "x: %x, y: %y" },
                    colors: ["#72a555", "#ab62c0", "#c57c3c", "#638ccc", "#ca5670"]
                })

            });

        } else {

            $.getJSON($SCRIPT_ROOT+"/_progressionCharts?attributeName="+involved_item+"&bar=true"+"&days="+num_day,
            function(data) {
                var temp_data_bar = []
                for(i=1; i<data.length; i++){
                    var curr_date = data[i][0].split('/');
                    temp_data_bar.push([new Date(curr_date[0], curr_date[1]-1, curr_date[2]).getTime(), data[i][1].toFixed(2)]);
                }
                var barData = {
                    label: involved_item,
                    data: temp_data_bar,
                    color: serie_color
                };
                $.plot($(chartID), [barData], barOptions);
            });

        }// end else
    };
};


// Bar chart hover binder for the 2 graphs
function binder(module_name){
    $("#flot-bar-chart1-"+module_name).bind("plothover.customHandler", function (event, pos, item) {
       if (item) { // a correct item is hovered
           var x = item.datapoint[0]
           var y = item.datapoint[1]
           var date = new Date(parseInt(x));
           var formated_date = date.getMonth()+'/'+date.getDate();
           var color = item.series.color;
           var color_opac = "rgba" +  color.slice(3, color.length-1)+",0.15)";
    
           // display the hovered value in the chart div
           $("#tooltip_graph1-"+module_name).html(item.series.label + " of " + formated_date + " = <b>" + y+"</b>")
               .css({padding: "2px", width: 'auto', 'background': color_opac , 'border': "3px solid "+color})
               .fadeIn(200);

        }
    });
    
    $("#flot-bar-chart2-"+module_name).bind("plothover.customHandler", function (event, pos, item) {
       if (item) { // a correct item is hovered
           var x = item.datapoint[0]
           var y = item.datapoint[1]
           var date = new Date(parseInt(x));
           var formated_date = date.getMonth()+'/'+date.getDate();
           var color = item.series.color;
           var color_opac = "rgba" +  color.slice(3, color.length-1)+",0.15)";
    
           // display the hovered value in the chart div
           $("#tooltip_graph2-"+module_name).html(item.series.label + " of " + formated_date + " = <b>" + y+"</b>")
               .css({padding: "2px", width: 'auto', 'background': color_opac , 'border': "3px solid "+color})
               .fadeIn(200);

        }
    });
}
