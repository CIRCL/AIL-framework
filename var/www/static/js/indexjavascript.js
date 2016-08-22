var time_since_last_pastes_num;

//If we do not received info from global, set pastes_num to 0
function checkIfReceivedData(){
    if ((new Date().getTime() - time_since_last_pastes_num) > 45*1000)
        window.paste_num_tabvar = 0;
    setTimeout(checkIfReceivedData, 45*1000);
}

setTimeout(checkIfReceivedData, 45*1000);

function initfunc( csvay, scroot) {
  window.csv = csvay;
  window.scroot = scroot;
};

function update_values() {
  $SCRIPT_ROOT = window.scroot ;
    $.getJSON($SCRIPT_ROOT+"/_stuff",
        function(data) {
            window.glob_tabvar = data;
        });
    };


// Plot and update the number of processed pastes
$(function() {
    var data = [];
    var default_minute = (typeof window.default_minute !== "undefined") ? parseInt(window.default_minute) : 10;
    var totalPoints = 60*parseInt(default_minute); //60s*minute
    var curr_max = 0;
    
    function getData() {
        if (data.length > 0){
             var data_old = data[0];
             data = data.slice(1);
             curr_max = curr_max == data_old ? Math.max.apply(null, data) : curr_max;
        }
        
        while (data.length < totalPoints) {
            var y = (typeof window.paste_num_tabvar !== "undefined") ? parseInt(window.paste_num_tabvar) : 0;
            curr_max = y > curr_max ? y : curr_max;
            data.push(y);
        }
        // Zip the generated y values with the x values
        var res = [];
        for (var i = 0; i < data.length; ++i) {
            res.push([i, data[i]])
        }
        return res;
    }

    var updateInterval = 1000;
    var options = {
        series: { shadowSize: 1 },
        lines: { fill: true, fillColor: { colors: [ { opacity: 1 }, { opacity: 0.1 } ] }},
        yaxis: { min: 0, max: 40 },
        colors: ["#a971ff"],
        grid: {
            tickColor: "#dddddd",
            borderWidth: 0 
        },
    };
    var plot = $.plot("#realtimechart", [ getData() ], options);
    
    function update() {
        plot.setData([getData()]);
        plot.getOptions().yaxes[0].max = curr_max;
        plot.setupGrid();
        plot.draw();
        setTimeout(update, updateInterval);
    }
    update();
});

function initfunc( csvay, scroot) {
  window.csv = csvay;
  window.scroot = scroot;
};

function update_values() {
  $SCRIPT_ROOT = window.scroot ;
    $.getJSON($SCRIPT_ROOT+"/_stuff",
        function(data) {
            window.glob_tabvar = data;
        });
    };

var source = new EventSource('/_logs');

source.onmessage = function(event) {
    var feed = jQuery.parseJSON( event.data );
    create_log_table(feed);
};

function pad_2(number)
{
     return (number < 10 ? '0' : '') + number;
}

function create_log_table(obj_json) {
    tableBody = document.getElementById("tab_body")
    var tr = document.createElement('TR')
    var time = document.createElement('TD')
    var chan = document.createElement('TD')
    var level = document.createElement('TD')
    var scrpt = document.createElement('TD')
    var src = document.createElement('TD')
    var pdate = document.createElement('TD')
    var nam = document.createElement('TD')
    var msage = document.createElement('TD')

    var chansplit = obj_json.channel.split('.');
    var parsedmess = obj_json.data.split(';');


    if (parsedmess[0] == "Global"){
        var paste_processed = parsedmess[4].split(" ")[2];
        window.paste_num_tabvar = paste_processed;
        time_since_last_pastes_num = new Date().getTime();
        return;
    }

    if( chansplit[1] == "INFO" ){
        tr.className = "info";
    }
    else if ( chansplit[1] == "WARNING" ){
        tr.className = "warning";
    }
    else if ( chansplit[1] == "CRITICAL"){
        tr.className = "danger"
    }

    source_link = document.createElement("A");
    if (parsedmess[1] == "slexy.org"){
        soruce_url = "http://"+parsedmess[1]+"/view/"+parsedmess[3].split(".")[0];
    }
    else{
        source_url = "http://"+parsedmess[1]+"/"+parsedmess[3].split(".")[0];
    }
    source_link.setAttribute("HREF",source_url);
    source_link.setAttribute("TARGET", "_blank")
    source_link.appendChild(document.createTextNode(parsedmess[1]));

    src.appendChild(source_link);

    var now = new Date();
    var timepaste = pad_2(now.getHours()) + ":" + pad_2(now.getMinutes()) + ":" + pad_2(now.getSeconds());

    time.appendChild(document.createTextNode(timepaste));
    chan.appendChild(document.createTextNode(chansplit[0]));
    level.appendChild(document.createTextNode(chansplit[1]));

    scrpt.appendChild(document.createTextNode(parsedmess[0]));
    pdate.appendChild(document.createTextNode(parsedmess[2]));
    nam.appendChild(document.createTextNode(parsedmess[3]));

    var iconspan = document.createElement('SPAN');
    if (parsedmess[4].split(" ")[0] == "Detected"){
        iconspan.className = "glyphicon glyphicon-eye-open";
    }
    else if (parsedmess[4].split(" ")[0] == "Checked"){
        iconspan.className = "glyphicon glyphicon-thumbs-up";
    }
    iconspan.innerHTML = "&nbsp;";
    msage.appendChild(iconspan);
    var message = parsedmess[4].split(" ");
    message.shift();

    msage.appendChild(document.createTextNode(message.join(" ")));

    tr.appendChild(time)
    tr.appendChild(chan);
    tr.appendChild(level);
    tr.appendChild(scrpt);
    tr.appendChild(src);
    tr.appendChild(pdate);
    tr.appendChild(nam);
    tr.appendChild(msage);

    if (tr.className == document.getElementById("checkbox_log_info").value && document.getElementById("checkbox_log_info").checked  == true) {
           tableBody.appendChild(tr);
       }
    if (tr.className == document.getElementById("checkbox_log_warning").value && document.getElementById("checkbox_log_warning").checked == true) {
        tableBody.appendChild(tr);
    }
    if (tr.className == document.getElementById("checkbox_log_critical").value && document.getElementById("checkbox_log_critical").checked == true) {
        tableBody.appendChild(tr);
    };

    var sel = document.getElementById("log_select")
    if (tableBody.rows.length > sel.options[sel.options.selectedIndex].value){
        while (tableBody.rows.length != sel.options[sel.options.selectedIndex].value){
            tableBody.deleteRow(0);
        }
    }
}

function create_queue_table() {
    document.getElementById("queueing").innerHTML = "";
    var Tablediv = document.getElementById("queueing")
    var table = document.createElement('TABLE')
    table.className = "table table-bordered table-hover table-striped";
    var tableHead = document.createElement('THEAD')
    var tableBody = document.createElement('TBODY')

    table.appendChild(tableHead);
    table.appendChild(tableBody);
    var heading = new Array();
    heading[0] = "Queue Name"
    heading[1] = "Amount"
    var tr = document.createElement('TR');
    tableHead.appendChild(tr);

    for (i = 0; i < heading.length; i++) {
        var th = document.createElement('TH')
        th.width = '100';
        th.appendChild(document.createTextNode(heading[i]));
        tr.appendChild(th);
    }

    for(i = 0; i < (glob_tabvar.row1).length;i++){
        var tr = document.createElement('TR')
        for(j = 0; j < (glob_tabvar.row1[i]).length; j++){
            var td = document.createElement('TD')
            td.appendChild(document.createTextNode(glob_tabvar.row1[i][j]));
            tr.appendChild(td)
        }
        tableBody.appendChild(tr);
    }
    Tablediv.appendChild(table);
}

$(document).ready(function () {
    if (typeof glob_tabvar == "undefined")
        location.reload();
    if (typeof glob_tabvar.row1 == "undefined")
        location.reload();

    var data = [];
    var data2 = [];
    var tmp_tab = [];
    var tmp_tab2 = [];
    var curves_labels = [];
    var curves_labels2 = [];
    var x = new Date();

    for (i = 0; i < glob_tabvar.row1.length; i++){
        if (glob_tabvar.row1[i][0] == 'Categ' || glob_tabvar.row1[i][0] == 'Curve'){
            tmp_tab2.push(0);
            curves_labels2.push(glob_tabvar.row1[i][0]);
        }
        else {
            tmp_tab.push(0);
            curves_labels.push(glob_tabvar.row1[i][0]);
        }
    }
    tmp_tab.unshift(x);
    tmp_tab2.unshift(x);
    curves_labels.unshift("date");
    curves_labels2.unshift("date");
    data.push(tmp_tab);
    data2.push(tmp_tab2);

    var g = new Dygraph(document.getElementById("Graph"), data,
    {
    labels: curves_labels,
    drawPoints: false,
    showRoller: true,
    rollPeriod: 30,
    labelsKMB: true,
    logscale: true,
    //drawGapEdgePoints: true,
    //legend: "always",
    //connectSeparatedPoints: true,
    stackedGraph: true,
    fillGraph: true,
    includeZero: true,
    });

    var g2 = new Dygraph(document.getElementById("Graph2"), data2,
    {
    labels: curves_labels2,
    drawPoints: false,
    showRoller: true,
    rollPeriod: 30,
    labelsKMB: true,
    logscale: true,
    //drawGapEdgePoints: true,
    //legend: "always",
    //connectSeparatedPoints: true,
    stackedGraph: true,
    fillGraph: true,
    includeZero: true,
    });


    var interval = 1000;   //number of mili seconds between each call
    var refresh = function() {

        $.ajax({
            url: "",
            cache: false,
            success: function(html) {
                $('#server-name').html(html);
                setTimeout(function() {
                    var x = new Date();
                    var tmp_values = [];
                    var tmp_values2 = [];
                    refresh();
                    update_values();

                    if($('#button-toggle-queues').prop('checked')){
                        create_queue_table();
                    }
                    else{
                        $("#queueing").html('');
                    }


                    for (i = 0; i < (glob_tabvar.row1).length; i++){
                        if (glob_tabvar.row1[i][0] == 'Categ' || glob_tabvar.row1[i][0] == 'Curve'){
                            tmp_values2.push(glob_tabvar.row1[i][1]);
                        }
                        else {
                            tmp_values.push(glob_tabvar.row1[i][1]);
                        }
                    }
                    tmp_values.unshift(x);
                    data.push(tmp_values);

                    tmp_values2.unshift(x);
                    data2.push(tmp_values2);

                    if (data.length > 1800) {
                        data.shift();
                        data2.shift();
                    }
                    g.updateOptions( { 'file': data } );
                    g2.updateOptions( { 'file': data2 } );


                   // TagCanvas.Reload('myCanvas');

                }, interval);
            }
        });
    };

    refresh();

    try {
      var options = {
      weight:true,
      weightMode:"both",
      noMouse:true,
      textColour: '#2E9AFE'
      }
      TagCanvas.Start('myCanvas','',options);
      TagCanvas.SetSpeed('myCanvas', [0.05, -0.15]);
    } catch(e) {
      // something went wrong, hide the canvas container
      document.getElementById('myCanvasContainer').style.display = 'none';
    }

});


