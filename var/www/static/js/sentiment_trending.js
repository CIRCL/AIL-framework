
 function generate_offset_to_time(num){
     var to_ret = {};
     for(i=0; i<=num; i++)
         to_ret[i] = new Date().getHours()-(23-i)+'h';
     return to_ret;
 };

 function generate_offset_to_date(day){
     var now = new Date();
     var to_ret = {};
     for(i=0; i<day; i++){
         for(j=0; j<24; j++){
             var t1 =now.getDate()-i + ":"; 
             var t2 =now.getHours()-(23-j)+"h";
             to_ret[j+24*i] = t1+t2;
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


$.getJSON("/sentiment_analysis_getplotdata/",
    function(data) {
        //console.log(data);
        var all_data = [];
        var plot_data = [];
        var graph_avg = [];
        var array_provider = Object.keys(data);
        var dates_providers = Object.keys(data[array_provider[0]]);
        var dateStart = parseInt(dates_providers[0]);
        var oneHour = 60*60;
        var oneWeek = oneHour*24*7;

        var all_graph_day_sum = 0.0;
        var all_graph_hour_sum = 0.0;

        for (graphNum=0; graphNum<8; graphNum++) {
            var max_value = 0.0;
            var graph_data = [];
            var spark_data = [];
            var curr_provider = array_provider[graphNum];
            var curr_sum = 0.0;
            var curr_sum_elem = 0.0;
            var day_sum = 0.0;
            var day_sum_elem = 0.0;
            var hour_sum = 0.0;

            for(curr_date=dateStart; curr_date<dateStart+oneWeek; curr_date+=oneHour){
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
                        //console.log(data_array[i].replace(/\'/g, '\"'));
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

                    if(curr_date >= dateStart+oneWeek-24*oneHour){
                        day_sum += (pos-neg);
                        day_sum_elem++;
                    }
                    if(curr_date >= dateStart+oneWeek-oneHour){
                        hour_sum += (pos-neg);
                    }

                }
            }
            all_graph_day_sum += day_sum;
            all_graph_hour_sum += hour_sum;

            var curr_avg = curr_sum / (curr_sum_elem); 
            //var curr_avg = curr_sum / (oneWeek/oneHour); 
            //var curr_avg = curr_sum / (spark_data.length); 
            graph_avg.push([curr_provider, curr_avg]);
            plot_data.push(spark_data);
            all_data.push(graph_data);
        

            sparklineOptions.chartRangeMax = max_value;
            sparklineOptions.chartRangeMin = -max_value;
            sparklineOptions.tooltipValueLookups = { names: offset_to_date};

            // print week
            var num = graphNum + 1;
            var placeholder = '.sparkLineStatsWeek' + num;
            $(placeholder).sparkline(plot_data[graphNum], sparklineOptions);
            $(placeholder+'t').text(curr_provider);
            $(placeholder+'s').text(curr_avg.toFixed(5));
        
            sparklineOptions.barWidth = 18;
            sparklineOptions.tooltipFormat = '<span style="color: {{color}}">&#9679;</span> Avg: {{value}} </span>'
            $(placeholder+'b').sparkline([curr_avg], sparklineOptions);
            sparklineOptions.tooltipFormat = '<span style="color: {{color}}">&#9679;</span> {{offset:names}}, {{value}} </span>'
            sparklineOptions.barWidth = 2;
            sparklineOptions.tooltipValueLookups = { names: offset_to_time};

            // print today
            var data_length = plot_data[graphNum].length;
            var data_today = plot_data[graphNum].slice(data_length-24, data_length);

            placeholder = '.sparkLineStatsToday' + num;
            sparklineOptions.barWidth = 14;
            $(placeholder).sparkline(data_today, sparklineOptions);
            $(placeholder+'t').text(curr_provider);

            sparklineOptions.barWidth = 18;
            sparklineOptions.tooltipFormat = '<span style="color: {{color}}">&#9679;</span> Avg: {{value}} </span>'
            //var day_avg = day_sum/24;
            var day_avg = day_sum/day_sum_elem;
            $(placeholder+'b').sparkline([day_avg], sparklineOptions);
            sparklineOptions.tooltipFormat = '<span style="color: {{color}}">&#9679;</span> {{offset:names}}, {{value}} </span>'
            sparklineOptions.barWidth = 2;
            $(placeholder+'s').text((day_avg).toFixed(5));

        }//for loop



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
        var piePercent = (all_graph_hour_sum / 8) / max_value;
        gaugeOptions.inc = piePercent;
        var gauge_today_last_hour = new FlexGauge(gaugeOptions);
        
        gaugeOptions2.appendTo = '#gauge_today_last_days';
        gaugeOptions2.dialLabel = 'Today';
        gaugeOptions2.elementId = 'gauge2';
        piePercent = (all_graph_day_sum / (8*24)) / max_value;
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
        for(graphNum=0; graphNum<8; graphNum++){
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
                    type: "bar",
                    color: "green",
                    dataPoints: [
                        {y: comp_sum_hour_pos/8}
                    ]
                },
                {
                    type: "bar",
                    color: "red",
                    dataPoints: [
                        {y: comp_sum_hour_neg/8}
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
                type: "bar",
                color: "green",
                dataPoints: [
                    {y: comp_sum_day_pos/8}
                ]
            },
            {
                type: "bar",
                color: "red",
                dataPoints: [
                    {y: comp_sum_day_neg/8}
                ]
            }
            ]
        };

        var chart_canvas2 = new CanvasJS.Chart("bar_today_last_days", options_canvasJS_2);
        
        chart_canvas1.render();
        chart_canvas2.render();


    }
);














