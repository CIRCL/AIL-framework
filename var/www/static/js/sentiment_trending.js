
/* Functions and config */

function getSyncScriptParams() {
         var scripts = document.getElementsByTagName('script');
         var lastScript = scripts[scripts.length-1];
         var scriptName = lastScript;
         return {
             url_sentiment_analysis_getplotdata : scriptName.getAttribute('data-url_sentiment_analysis_getplotdata'),
         };
}

var url_sentiment_analysis_getplotdata = getSyncScriptParams().url_sentiment_analysis_getplotdata;

function add_new_graph_today(id) {
    return "<div id=\"panel-today\" class=\"panel panel-default pannelToday"+id+"\">" +
                "<div class=\"panel-heading\">" +
                    "<strong class=\"sparkLineStatsToday"+id+"t\">Graph "+id+"</strong>" +
                    "<strong class=\"sparkLineStatsToday"+id+"s pull-right\">Avg</strong>" +
                "</div>" +
                "<div class=\"panel-body panelInside\">" +
                    "<table class=\"table\">" +
                        "<tbody>" +
                            "<tr>" +
                                "<td style=\"border-top: 0px solid #ddd;\"><div class=\"sparkLineStatsToday"+id+"\"></div></td> " +
                                "<td style=\"border-top: 0px solid #ddd;\"><div class=\"sparkLineStatsToday"+id+"b\"></div></td> " +
                            "</tr>" +
                         "</tbody>" +
                    "</table>" +
                "</div>" +
            "</div>";
};
function add_new_graph_week(id) {
    return "<div id=\"panel-week\" class=\"panel panel-default pannelWeek"+id+"\">" +
                "<div class=\"panel-heading\">" +
                    "<strong class=\"sparkLineStatsWeek"+id+"t\">Graph "+id+"</strong>" +
                    "<strong class=\"sparkLineStatsWeek"+id+"s pull-right\">Avg</strong>" +
                "</div>" +
                "<div class=\"panel-body panelInside\">" +
                    "<table class=\"table\">" +
                        "<tbody>" +
                            "<tr>" +
                                "<td style=\"border-top: 0px solid #ddd;\"><div class=\"sparkLineStatsWeek"+id+"\"></div></td> " +
                                "<td style=\"border-top: 0px solid #ddd;\"><div class=\"sparkLineStatsWeek"+id+"b\"></div></td> " +
                            "</tr>" +
                         "</tbody>" +
                    "</table>" +
                "</div>" +
            "</div>";
}

 function generate_offset_to_time(num){
     var to_ret = {};
     for(i=0; i<=num; i++) {
         var t1 = new Date().getHours()-(23-i);
         t1 = t1 < 0 ? 24+t1 : t1;
         to_ret[i] =  t1+'h';
     }
     return to_ret;
 };

 function generate_offset_to_date(day){
     day = day-1;
     var now = new Date();
     var to_ret = {};
     for(i=day; i>=0; i--){
         for(j=0; j<24; j++){
             var t1 =now.getDate()-i + ":";
             var t2 =now.getHours()-(23-j);
             t2 = t2 < 0 ? 24+t2 : t2;
             t2 += "h";
             to_ret[j+24*(day-i)] = t1+t2;
         }
     }
     return to_ret;
 };

 var offset_to_time = generate_offset_to_time(23);
 var offset_to_date = generate_offset_to_date(7);

 var sparklineOptions = {
        height: 80,//Height of the chart - Defaults to 'auto' (line height of the containing tag)

        chartRangeMin: -1,
        chartRangeMax: 1,

        type: 'bar',
        barSpacing: 0,
        barWidth: 2,
        barColor: '#00bf5f',
        negBarColor: '#f22929',
        zeroColor: '#ffff00',

        tooltipFormat: '<span style="color: {{color}}">&#9679;</span> {{offset:names}}, {{value}} </span>',
};


/* Plot and queries */

var all_graph_day_sum = 0.0;
var all_graph_hour_sum = 0.0;
var all_graph_hour_sum_minus = 0.0;
var all_graph_hour_maxVal = 0.0;
var all_day_avg = 0.0;
var all_day_avg_maxVal = 0.0;
var graph_avg = [];
var all_data = [];
var provider_already_loaded = [];
var totNumGraph = 0;

// Query all providers name then launch the query and plot process for each of them.
// When everything is terminated, plot the widgets (Gauge, canvasJS, table)
// input: all - set to 'True' if you take all providers
function draw_page(all) {
    $.getJSON(url_sentiment_analysis_getplotdata + "?getProviders=True&all="+all,
        function(data) {
            var promises = [];

            var the_length = provider_already_loaded.length == 0 ? 0 : provider_already_loaded.length;
            for(i=0; i<data.length; i++) {
                if(provider_already_loaded.indexOf(data[i]) != -1) {
                    continue;
                } else {
                    totNumGraph++;
                    if(i % 2 == 0) {
                        $("#today_divl").append(add_new_graph_today(i+the_length+1));
                        $("#week_divl").append(add_new_graph_week(i+the_length+1));
                    }
                    else {
                        $("#today_divr").append(add_new_graph_today(i+the_length+1));
                        $("#week_divr").append(add_new_graph_week(i+the_length+1));
                    }
                    provider_already_loaded.push(data[i])
                    promises.push(query_and_plot(data[i], i+the_length));

                }
            }

            $.when.apply($, promises).done( function (arg) {
                draw_widgets();
                $("#LoadAll").show('fast');
            });
        }
    );
}


// Query data and plot it for a given provider
// input - provider: The povider name to be plotted
// input - graphNum: The number of the graph (Use to plot on correct div)
function query_and_plot(provider, graphNum) {
    var query_plot = $.getJSON(url_sentiment_analysis_getplotdata + "?provider="+provider,
        function(data) {
            var plot_data = [];
            var array_provider = Object.keys(data);
            var dates_providers = Object.keys(data[array_provider[0]]);
            var dateStart = parseInt(dates_providers[0]);
            var oneHour = 60*60;
            var oneWeek = oneHour*24*7;

            var max_value = 0.0;
            var max_value_day = 0.0;
            var graph_data = [];
            var spark_data = [];
            var curr_provider = array_provider[0];
            var curr_sum = 0.0;
            var curr_sum_elem = 0.0;
            var day_sum = 0.0;
            var day_sum_elem = 0.0;
            var hour_sum = 0.0;

            for(curr_date=dateStart+oneHour; curr_date<=dateStart+oneWeek; curr_date+=oneHour){
                var data_array = data[curr_provider][curr_date];

                if (data_array.length == 0){
                    graph_data.push({'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compoundPos': 0.0, 'compoundNeg': 0.0});
                    spark_data.push(0);
                } else { //compute avg for a given date for a given graph
                    var compPosAvg = 0;
                    var compNegAvg = 0;
                    var pos = 0;
                    var neg = 0;
                    var neu = 0;

                    for(i=0; i<data_array.length; i++){
                        var curr_data = jQuery.parseJSON(data_array[i].replace(/\'/g, '\"'));
                        compPosAvg += curr_data['compoundPos'];
                        compNegAvg += curr_data['compoundNeg'];
                        pos += curr_data['pos'];
                        neg += curr_data['neg'];
                        neu += curr_data['neu'];
                    }
                    compPosAvg = compPosAvg/data_array.length;
                    compNegAvg = compNegAvg/data_array.length;
                    pos = pos/data_array.length;
                    neg = neg/data_array.length;
                    neu = neu/data_array.length;

                    graph_data.push({'neg': neg, 'neu': neu, 'pos': pos, 'compoundPos': compPosAvg, 'compoundNeg': compNegAvg});
                    spark_data.push(pos-neg);
                    curr_sum += (pos-neg);
                    curr_sum_elem++;
                    max_value = Math.abs(pos-neg) > max_value ? Math.abs(pos-neg) : max_value;

                    if(curr_date >= dateStart+oneWeek-23*oneHour){
                        max_value_day = Math.abs(pos-neg) > max_value_day ? Math.abs(pos-neg) : max_value_day; day_sum += (pos-neg);
                        day_sum_elem++;
                    }
                    if(curr_date > dateStart+oneWeek-2*oneHour && curr_date <=dateStart+oneWeek-oneHour){
                        hour_sum += (pos-neg);
                    }

                }
            }
            all_graph_day_sum += day_sum;
            all_graph_hour_sum += hour_sum;
            all_graph_hour_sum_minus += hour_sum > 0 ? 0 : 1;
            all_graph_hour_maxVal = Math.abs(hour_sum) > all_graph_hour_maxVal ? Math.abs(hour_sum) : all_graph_hour_maxVal;

            var curr_avg = curr_sum / (curr_sum_elem);
            if(isNaN(curr_avg))
                curr_avg = 0.0
            graph_avg.push([curr_provider, curr_avg]);
            plot_data.push(spark_data);
            all_data.push(graph_data);


            sparklineOptions.chartRangeMax = max_value;
            sparklineOptions.chartRangeMin = -max_value;
            sparklineOptions.tooltipValueLookups = { names: offset_to_date};

            // print week
            var num = graphNum + 1;
            var placeholder = '.sparkLineStatsWeek' + num;
            sparklineOptions.barWidth = 2;
            $(placeholder).sparkline(plot_data[0], sparklineOptions);
            $(placeholder+'t').text(curr_provider);
            var curr_avg_text = isNaN(curr_avg) ? "No data" : curr_avg.toFixed(5);
            $(placeholder+'s').text(curr_avg_text);

            sparklineOptions.barWidth = 18;
            sparklineOptions.tooltipFormat = '<span style="color: {{color}}">&#9679;</span> Avg: {{value}} </span>'
            $(placeholder+'b').sparkline([curr_avg], sparklineOptions);
            sparklineOptions.tooltipFormat = '<span style="color: {{color}}">&#9679;</span> {{offset:names}}, {{value}} </span>'

            sparklineOptions.tooltipValueLookups = { names: offset_to_time};
            sparklineOptions.chartRangeMax = max_value_day;
            sparklineOptions.chartRangeMin = -max_value_day;

            var avgName = ".pannelWeek" + num;
            if (curr_avg > 0) {
                $(avgName).addClass("panel-success")
            } else if(curr_avg < 0) {
                $(avgName).addClass("panel-danger")
            } else if(isNaN(curr_avg)) {
                $(avgName).addClass("panel-info")
            } else {
                $(avgName).addClass("panel-warning")
            }



            // print today
            var data_length = plot_data[0].length;
            var data_today = plot_data[0].slice(data_length-24, data_length);

            placeholder = '.sparkLineStatsToday' + num;
            sparklineOptions.barWidth = 14;
            $(placeholder).sparkline(data_today, sparklineOptions);
            $(placeholder+'t').text(curr_provider);

            sparklineOptions.barWidth = 18;
            sparklineOptions.tooltipFormat = '<span style="color: {{color}}">&#9679;</span> Avg: {{value}} </span>'
            //var day_avg = day_sum/24;
            var day_avg = isNaN(day_sum/day_sum_elem) ? 0 : day_sum/day_sum_elem;
            var day_avg_text = isNaN(day_sum/day_sum_elem) ? 'No data' : (day_avg).toFixed(5);
            all_day_avg += day_avg;
            all_day_avg_maxVal = Math.abs(day_avg) > all_day_avg_maxVal ? Math.abs(day_avg) : all_day_avg_maxVal;
            $(placeholder+'b').sparkline([day_avg], sparklineOptions);
            sparklineOptions.tooltipFormat = '<span style="color: {{color}}">&#9679;</span> {{offset:names}}, {{value}} </span>'
            $(placeholder+'s').text(day_avg_text);

            avgName = ".pannelToday" + num;
            if (day_avg > 0) {
                $(avgName).addClass("panel-success")
            } else if(day_avg < 0) {
                $(avgName).addClass("panel-danger")
            } else if(isNaN(day_sum/day_sum_elem)) {
                $(avgName).addClass("panel-info")
            } else {
                $(avgName).addClass("panel-warning")
            }


        }
    );
    return query_plot
}



function draw_widgets() {

    /* ---------------- Gauge ---------------- */
    var gaugeOptions = {
        animateEasing: true,

        elementWidth: 200,
        elementHeight: 125,

        arcFillStart: 10,
        arcFillEnd: 12,
        arcFillTotal: 20,
        incTot: 1.0,

        arcBgColorLight: 200,
        arcBgColorSat: 0,
        arcStrokeFg: 20,
        arcStrokeBg: 30,

        colorArcFg: '#FF3300',
        animateSpeed: 1,

    };
    // Clone object
    var gaugeOptions2 = jQuery.extend(true, {}, gaugeOptions);
    var gaugeOptions3 = jQuery.extend(true, {}, gaugeOptions);



    gaugeOptions.appendTo = '#gauge_today_last_hour';
    gaugeOptions.dialLabel = 'Last hour';
    gaugeOptions.elementId = 'gauge1';
    var piePercent = (all_graph_hour_sum / (totNumGraph - all_graph_hour_sum_minus)) / all_graph_hour_maxVal;
    gaugeOptions.inc = piePercent;
    var gauge_today_last_hour = new FlexGauge(gaugeOptions);

    gaugeOptions2.appendTo = '#gauge_today_last_days';
    gaugeOptions2.dialLabel = 'Today';
    gaugeOptions2.elementId = 'gauge2';
    piePercent = (all_day_avg / totNumGraph) / all_day_avg_maxVal;
    gaugeOptions2.inc = piePercent;
    var gauge_today_last_days = new FlexGauge(gaugeOptions2);

    gaugeOptions3.appendTo = '#gauge_week';
    gaugeOptions3.dialLabel = 'Week';
    gaugeOptions3.elementId = 'gauge3';

    var graph_avg_sum = 0.0;
    var temp_max_val = 0.0;
    for (i=0; i<graph_avg.length; i++){
        graph_avg_sum += graph_avg[i][1];
        temp_max_val = Math.abs(graph_avg[i][1]) > temp_max_val ? Math.abs(graph_avg[i][1]) : temp_max_val;
    }

    piePercent = (graph_avg_sum / graph_avg.length) / temp_max_val;
    gaugeOptions3.inc = piePercent;
    var gauge_today_last_days = new FlexGauge(gaugeOptions3);


    /* --------- Sort providers -------- */

    graph_avg.sort(function(a, b){return b[1]-a[1]});

    for (i=1; i<6; i++){
        $('.worst'+i).text(graph_avg[7-(i-1)][0]);
        $('.best'+i).text(graph_avg[i-1][0]);
    }

    /* ----------- CanvasJS ------------ */

    var comp_sum_day_pos = 0.0;
    var comp_sum_day_neg = 0.0;
    var comp_sum_hour_pos = 0.0;
    var comp_sum_hour_neg = 0.0;
    for(graphNum=0; graphNum<totNumGraph; graphNum++){
        curr_graphData = all_data[graphNum];
        var gauge_data = curr_graphData.slice(curr_graphData.length-24, curr_graphData.length);
        for (i=1; i< gauge_data.length; i++){
            comp_sum_day_pos += gauge_data[i].compoundPos;
            comp_sum_day_neg += gauge_data[i].compoundNeg;

            if(i == 23){
                comp_sum_hour_pos += gauge_data[i].compoundPos;
                comp_sum_hour_neg += gauge_data[i].compoundNeg;
            }
        }

    }

    var options_canvasJS_1 = {

        animationEnabled: true,
        axisY: {
            tickThickness: 0,
            lineThickness: 0,
            valueFormatString: " ",
            gridThickness: 0
        },
        axisX: {
            tickThickness: 0,
            lineThickness: 0,
            labelFontSize: 0.1,
        },
        data: [
            {
                toolTipContent: "<span style='\"'color: {color};'\"'><strong>Positive: </strong></span><span><strong>{y}</strong></span>",
                type: "bar",
                color: "green",
                dataPoints: [
                    {y: comp_sum_hour_pos/totNumGraph}
                ]
            },
            {
                toolTipContent: "<span style='\"'color: {color};'\"'><strong>Negative: </strong></span><span><strong>{y}</strong></span>",
                type: "bar",
                color: "red",
                dataPoints: [
                    {y: comp_sum_hour_neg/totNumGraph}
                ]
            }
        ]
    };

    var chart_canvas1 = new CanvasJS.Chart("bar_today_last_hour", options_canvasJS_1);

    var options_canvasJS_2 = {

        animationEnabled: true,
        axisY: {
            tickThickness: 0,
            lineThickness: 0,
            valueFormatString: " ",
            gridThickness: 0
        },
        axisX: {
            tickThickness: 0,
            lineThickness: 0,
            labelFontSize: 0.1,
        },
        data: [
        {
            toolTipContent: "<span style='\"'color: {color};'\"'><strong>Positive: </strong></span><span><strong>{y}</strong></span>",
            type: "bar",
            color: "green",
            dataPoints: [
                {y: comp_sum_day_pos/totNumGraph}
            ]
        },
        {
            toolTipContent: "<span style='\"'color: {color};'\"'><strong>Negative: </strong></span><span><strong>{y}</strong></span>",
            type: "bar",
            color: "red",
            dataPoints: [
                {y: comp_sum_day_neg/totNumGraph}
            ]
        }
        ]
    };

    var chart_canvas2 = new CanvasJS.Chart("bar_today_last_days", options_canvasJS_2);

    chart_canvas1.render();
    chart_canvas2.render();

}
