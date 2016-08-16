var li_text = "<li><div class='checkbox'></div><label class='provider'><input value='" 
var li_text_mid = "' type='checkbox'></input> "
var li_text_end = "</label></li>"


/* Get Providers List and display them by row */
$.getJSON('/sentiment_analysis_plot_tool_getdata/?getProviders=True', function(data){
    for(i=0; i<data.length; i++){
        var providerList = i%2 == 0 ? '#providerList1' : '#providerList2';
        $(providerList).append(li_text + data[i] + li_text_mid + data[i] + li_text_end);
    }
});


/* Create the slider and button*/
var today = Date.now();
var old_day = today - (31*24*60*60)*1000;
$( ".sliderRange" ).slider({
    range: true,
    min: old_day,
    max: today,
    values: [ today - (7*24*60*60)*1000, today ],
    step: 24*60*60*1000,
    slide: function( event, ui ) {
        $( "#amount" ).val( new Date(ui.values[ 0 ]).toLocaleDateString() + " - " + new Date(ui.values[ 1 ]).toLocaleDateString() );
    }
});

$( "#amount" ).val( new Date($( ".sliderRange" ).slider( "values", 0 )).toLocaleDateString() +
  " - " + new Date($( ".sliderRange" ).slider( "values", 1 )).toLocaleDateString() );

$('#plot_btn').click(plotData); 


/* Plot the requested data (if available) stored in slider and checkboxes */

function plotData(){
    var graph_options = {
                            series: {
            	                stack: true,
                                lines: { show: false,
                                lineWidth: 2,
                                fill: true, fillColor: { colors: [ { opacity: 0.5 }, { opacity: 0.2 } ] }
                                },
                                bars: {show: true, barWidth: 60*60*1000},
                                shadowSize: 0
                            },
                            grid: { 
                                hoverable: true, 
                                clickable: true, 
                                tickColor: "#f9f9f9",
                                borderWidth: 0
                            },
                            xaxis: {
                                  mode: "time",
                                  timeformat: "%m/%d:%Hh",
                                  minTickSize: [1, "hour"]
                            },
                            yaxis: {
                                autoscaleMargin: 0.1,
                            },
                        }
    var query = $( "input:checked" ).map(function () {return this.value;}).get().join(",");
    var Qdate = new Date($( ".sliderRange" ).slider( "values", 0 )).toLocaleDateString() +'-'+ new Date($( ".sliderRange" ).slider( "values", 1 )).toLocaleDateString()
        

    // retreive the data from the server
    $.getJSON('/sentiment_analysis_plot_tool_getdata/?getProviders=False&query='+query+'&Qdate='+Qdate, function(data){
        var to_plot = [];
        for (provider in data){
            var nltk_data = Object.keys(data[provider]).map(function (key) { return data[provider][key]; });
            var nltk_key = Object.keys(data[provider]).map(function (key) { return key; });

            var pos = 0.0;
            var neg = 0.0;
            var XY_data = [];
            for (i=0; i<nltk_data.length; i++){
                if (nltk_data[i].length == 0)
                    continue;
                else {
                    for (j=0; j<nltk_data[i].length; j++){
                        var curr_data = jQuery.parseJSON(nltk_data[i][j].replace(/\'/g, '\"'));
                        pos += curr_data['pos'];
                        neg += curr_data['neg'];
                    }
                    pos = pos/nltk_data.length;
                    neg = neg/nltk_data.length;
                }
                XY_data.push([nltk_key[i]*1000, pos-neg]);
            }
        to_plot.push({ data: XY_data, label: provider}); 
        }
	var plot = $.plot($("#graph"), to_plot, graph_options);
    });
}
