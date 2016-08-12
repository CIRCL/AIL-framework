

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
gaugeOptions.inc = -0.7;
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









/* ---------- Sparkline Charts ---------- */
//generate random number for charts
randNum = function(){
    var num = Math.random();
    if(num > 0.5)
        num = -1+num;
    console.log(Math.floor(num*101));
    return Math.floor(num*101);
    //return (Math.floor( Math.random()* (1+40-20) ) ) + 20;
}



 var sparklineOptions = {
        width: 250,//Width of the chart - Defaults to 'auto' - May be any valid css width - 1.5em, 20px, etc (using a number without a unit specifier won't do what you want) - This option does nothing for bar and tristate chars (see barWidth)
        height: 80,//Height of the chart - Defaults to 'auto' (line height of the containing tag)
        type: 'bar',
        barSpacing: 0,
        barWidth: 10,
        barColor: '#00bf5f',
        negBarColor: '#f22929',
        zeroColor: '#ffff00'
    };


//sparklines (making loop with random data for all 10 sparkline)
i=1;
for (i=1; i<10; i++) {
    var data = [3+randNum(), 5+randNum(), 8+randNum(), 11+randNum(),14+randNum(),17+randNum(),20+randNum(),15+randNum(),18+randNum(),22+randNum()];
    placeholder = '.sparkLineStatsToday' + i;
	
    $(placeholder).sparkline(data, sparklineOptions);

}

//sparklines (making loop with random data for all 10 sparkline)
i=1;
for (i=1; i<10; i++) {
    var data = [3+randNum(), 5+randNum(), 8+randNum(), 11+randNum(),14+randNum(),17+randNum(),20+randNum(),15+randNum(),18+randNum(),22+randNum()];
    placeholder = '.sparkLineStatsWeek' + i;

    $(placeholder).sparkline(data, sparklineOptions);

}


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

