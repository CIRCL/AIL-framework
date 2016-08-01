/* Already defined variable (Before the input)
* 
* var chart_1_num_day = 5;
* var chart_2_num_day = 15;
*
*/


/* VARIABLES */
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
    
    /* Linked graph - remember the data */
    var plot_data_old = []
    var plot_old = []

/* FUNCTIONS */

function labelFormatter(label, series) {
    return "<div style='font-size:8pt; text-align:center; padding:2px; color:white;'>"
               + label + "<br/>" + Math.round(series.percent) + "%</div>";
}


/* Plot, and bind chart listener */
function plot_top_graph(module_name, init){

    /**** Pie Chart ****/
    
    // moduleCharts is used the decide the url to request data
    var moduleCharts = "size" == module_name ? "providersChart" : ("num" == module_name ? "providersChart" : "moduleCharts");
    var tot_sum = 0; // used to detect elements placed in 'Other' pie's part
    var data_other = []; // used to detect elements placed in 'Other' pie's part

    var createPie = $.getJSON($SCRIPT_ROOT+"/_"+moduleCharts+"?moduleName="+module_name+"&num_day="+chart_1_num_day,
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

                  if (init){ //prevent multiple binding due to the refresh function
                      $("#flot-pie-chart-"+module_name).bind("plotclick", function (event, pos, item) {
                          if (item == null)
                              return; 
                          var clicked_label = item.series.label;
                          
                          if (module_name == "size"){ // if Provider pie chart clicked, draw the two bar charts
                              update_bar_chart(moduleCharts, module_name, "#flot-bar-chart-"+module_name, clicked_label, 
                                               item.series.color, "%m/%d", false);
                              update_bar_chart(moduleCharts, "num", "#flot-bar-chart-"+"num", clicked_label,
                                               item.series.color, "%m/%d", true);
                          }
                          else if (module_name == "num"){
                              update_bar_chart(moduleCharts, module_name, "#flot-bar-chart-"+module_name, clicked_label, 
                                               item.series.color, "%m/%d", false);
                              update_bar_chart(moduleCharts, "size", "#flot-bar-chart-"+"size", clicked_label, 
                                               item.series.color, "%m/%d", true);
                          } else {
                              update_bar_chart(moduleCharts, module_name, "#flot-bar-chart-"+module_name, clicked_label, 
                                               item.series.color, "%m/%d", true);
                          }                          
                      });
                  }
    });
    
        
    /**** Bar Chart ****/

    function update_bar_chart(chartUrl, module_name, chartID, involved_item, serie_color, timeformat, can_bind){
        var num_day = chart_1_num_day;
        var barOptions = {
            series: {
                bars: { show: true, barWidth: 82800000 },
                lines: { show: false, fill: true }
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
        };

        var plot; // will contain the current plotting object
        /* If part 'Other' has been clicked */
        if (involved_item == "Other"){

            var all_other_temp_data = []; // the data_bar of all series
            var temp_data_bar; //the data_bar associated with one serie
            var promises = []; // Use to plot when everything has been received
            var involved_item

            for(i=0; i<data_other.length; i++){ // Get data for elements summed up in the part 'Other'
                involved_item = data_other[i];
                var request = $.getJSON($SCRIPT_ROOT+"/_"+chartUrl+"?keywordName="+involved_item+"&moduleName="+module_name+"&bar=true"+"&days="+num_day,
                        function(data) {
                            temp_data_bar = []
                            for(i=1; i<data.length; i++){
                                var curr_date = data[i][0].split('/');
                                var offset = (data_other.length/2 - data_other.indexOf(data[0]))*10000000
                                temp_data_bar.push([new Date(curr_date[0], curr_date[1]-1, curr_date[2]).getTime() + offset, data[i][1].toFixed(2)]);
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

                plot = $.plot($(chartID), dataBar, {
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

 
                /* rememeber the data for the two graph */
                if (plot_data_old.length>1){ // avoid adding plot_data for previous clicked pie part
                    plot_data_old = [];
                    plot_old = [];
                }
                plot_data_old.push(plot.getData());
                plot_old.push(plot);

                if (can_bind){ // avoid binding two listener for provider graphs
                    binder(module_name);
                    if (module_name == "size") // bind the linked provider graph
                        binder("num");
                    else if (module_name == "num")
                        binder("size");
                }               

            });

        } else { // Normal pie's part clicked

            $.getJSON($SCRIPT_ROOT+"/_"+chartUrl+"?keywordName="+involved_item+"&moduleName="+module_name+"&bar=true"+"&days="+num_day,
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
                    plot = $.plot($(chartID), [barData], barOptions);

                    /* rememeber the data for the two graph */
                    if ((module_name == "size") || (module_name == "num")) { // Add only for the provider graph
                        if (plot_data_old.length>1){ // avoid adding plot_data for previous clicked pie part
                            plot_data_old = [];
                            plot_old = [];
                        }
                        plot_data_old.push(plot.getData());
                        plot_old.push(plot);
                    }

                    if (can_bind){ // avoid binding two listener for provider graphs
                        $("#flot-bar-chart-"+module_name).unbind( "plothover.customHandler" );
                        binder(module_name);
                        if (module_name == "size"){ // bind the linked provider graph
                            $("#flot-bar-chart-"+"num").unbind( "plothover.customHandler" );
                            binder("num");
                        }
                        else if (module_name == "num"){
                            $("#flot-bar-chart-"+"size").unbind( "plothover.customHandler" );
                            binder("size");
                        }
                    }
               });
       }
    
    }; // end update_bar_chart

} // end plot_top_graph


/* Bind a listener to the graph to display the value under the cursor in the approriate div */
function binder(module_name){
    $("#flot-bar-chart-"+module_name).bind("plothover.customHandler", function (event, pos, item) {
       if (item) { // a correct item is hovered
           var x = item.datapoint[0]
           var y = item.datapoint[1]
           var date = new Date(parseInt(x));
           var formated_date = date.getMonth()+'/'+date.getDate();
           var color = item.series.color;
           var color_opac = "rgba" +  color.slice(3, color.length-1)+",0.15)";
    
           // display the hovered value in the chart div
           $("#tooltip_graph-"+module_name).html(item.series.label + " of " + formated_date + " = <b>" + y+"</b>")
               .css({padding: "2px", width: 'auto', 'background': color_opac , 'border': "3px solid "+color})
               .fadeIn(200);


           /* If provider bar chart hovered, highlight and display associated value */
           if (module_name == "size" || module_name == "num"){ 
               new_module_name = module_name == "size" ? "num" : "size";

               /* Used to get the corresponding associated value for providers charts */
               var plot_obj = plot_data_old[0]; //contain series

               for(serie=0; serie<plot_obj.length; serie++){ //for all series
                   var data_other = plot_obj[serie].data;

                   for(i=0; i<data_other.length; i++){ //for all datapoints
                       if (data_other[i][0] == date.getTime()){
                           if(y == data_other[i][1]){ // get the correct data and plot object
                               var other_graph_plot = plot_old[1];
                               var curr_data_other = plot_data_old[1][serie].data[i][1];
                           } else {
                               var other_graph_plot = plot_old[0];
                               var curr_data_other = data_other[i][1];
                           }
                           var datapoint = i;
                           var the_serie = serie;
                       }
                   }
               }

               $("#tooltip_graph-"+new_module_name).html(item.series.label + " of " + formated_date + " = <b>" + curr_data_other+"</b>")
                   .css({padding: "2px", width: 'auto', 'background': color_opac, 'border': "3px solid "+color})
                   .fadeIn(200);

               // clean up other highlighted bar

               for(i=0; i<data_other.length; i++)
                   for(s=0; s<plot_obj.length; s++)
                       other_graph_plot.unhighlight(s, i);

               other_graph_plot.highlight(the_serie, datapoint);

           }

       } else {
           // No correct item hovered, clean up the highlighted one
           for(i=0; i<plot_old.length; i++)
               for(j=0; j<plot_data_old[0][0].data.length; j++)
                   plot_old[i].unhighlight(0, j);
       }
    });
}
function plot_finished(module_name){
        
    }
