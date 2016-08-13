
/* ---------- Sparkline Charts ---------- */
//generate random number for charts
randNum = function(){
    var num = Math.random();
    if(num > 0.5)
        num = -1+num;
    //console.log(Math.floor(num*101));
    return Math.floor(num*101);
    //return (Math.floor( Math.random()* (1+40-20) ) ) + 20;
}



 var sparklineOptions = {
        height: 80,//Height of the chart - Defaults to 'auto' (line height of the containing tag)

        chartRangeMin: -1,
        chartRangeMax: 1,

        type: 'bar',
        barSpacing: 0,
        barWidth: 2,
        barColor: '#00bf5f',
        negBarColor: '#f22929',
        zeroColor: '#ffff00'
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

        for (graphNum=0; graphNum<8; graphNum++) {
            var graph_data = [];
            var spark_data = [];
            var curr_provider = array_provider[graphNum];
            var curr_sum = 0.0;
            var day_sum = 0.0;

            for(curr_date=dateStart; curr_date<dateStart+oneWeek; curr_date+=oneHour){
                var data_array = data[curr_provider][curr_date];

                if (data_array.length == 0){
                    graph_data.push({'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compoundPos': 0.0, 'compoundNeg': 0.0});
                    spark_data.push(0);
                } else { //compute avg
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

                    if(curr_date >= dateStart+oneWeek-24*oneHour){
                        day_sum += (pos-neg);
                    }

                }
            }
            var curr_avg = curr_sum / (oneWeek/oneHour); 
            graph_avg.push(curr_avg);
            plot_data.push(spark_data);
            all_data.push(graph_data);
        
            // print week
            var num = graphNum + 1;
            var placeholder = '.sparkLineStatsWeek' + num;
            $(placeholder).sparkline(plot_data[graphNum], sparklineOptions);
            //console.log(plot_data[graphNum]);
        
            sparklineOptions.barWidth = 7;
            $(placeholder+'b').sparkline([curr_avg], sparklineOptions);
            sparklineOptions.barWidth = 2;

            // print today
            var data_length = plot_data[graphNum].length;
            var data_today = plot_data[graphNum].slice(data_length-24*2, data_length-24*1);

            placeholder = '.sparkLineStatsToday' + num;
            sparklineOptions.barWidth = 14;
            $(placeholder).sparkline(data_today, sparklineOptions);

            //console.log(day_sum);
            sparklineOptions.barWidth = 7;
            $(placeholder+'b').sparkline([day_sum/24], sparklineOptions);
            //$(placeholder+'b').sparkline(10, sparklineOptions);
            sparklineOptions.barWidth = 2;

        }//for loop
    }
);








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
gaugeOptions.inc = -0.9;
var gauge_today_last_hour = new FlexGauge(gaugeOptions);

gaugeOptions2.appendTo = '#gauge_today_last_days';
gaugeOptions2.dialLabel = 'Today';
gaugeOptions2.elementId = 'gauge2';
gaugeOptions2.inc = 0.4;
var gauge_today_last_days = new FlexGauge(gaugeOptions2);

gaugeOptions3.appendTo = '#gauge_week';
gaugeOptions3.dialLabel = 'Week';
gaugeOptions3.elementId = 'gauge3';
gaugeOptions3.inc = -0.3;
var gauge_today_last_days = new FlexGauge(gaugeOptions3);








/* ----------- CanvasJS ------------ */
var options_canvasJS = {
  
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
            {y: 25}
        ]
    },
    {
        type: "bar",
        color: "red",
        dataPoints: [
            {y: -13}
        ]
    }
    ]
};

var chart_canvas1 = new CanvasJS.Chart("bar_today_last_hour", options_canvasJS);
var chart_canvas2 = new CanvasJS.Chart("bar_today_last_days", options_canvasJS);

chart_canvas1.render();
chart_canvas2.render();

