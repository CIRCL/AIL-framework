var time_since_last_pastes_num = {};
var data_for_processed_paste = {};
var list_feeder = [];
window.paste_num_tabvar_all = {};

function getSyncScriptParams() {
         var scripts = document.getElementsByTagName('script');
         var lastScript = scripts[scripts.length-1];
         var scriptName = lastScript;
         return {
             //urlstuff : scriptName.getAttribute('data-urlstuff'),
             urllog : scriptName.getAttribute('data-urllog')
         };
}

//var urlstuff = getSyncScriptParams().urlstuff;
var urllog = getSyncScriptParams().urllog;

//If we do not received info from mixer, set pastes_num to 0
function checkIfReceivedData(){
    for (i in list_feeder) {
        if(list_feeder[i] == "global"){
            if ((new Date().getTime() - time_since_last_pastes_num[list_feeder[i]]) > 35*1000){
                window.paste_num_tabvar_all[list_feeder[i]] = 0;
            }
        } else {
            if ((new Date().getTime() - time_since_last_pastes_num["Proc"+list_feeder[i]]) > 35*1000){
                window.paste_num_tabvar_all["Proc"+list_feeder[i]] = 0;
                window.paste_num_tabvar_all["Dup"+list_feeder[i]] = 0;
            }
        }
    }
    setTimeout(checkIfReceivedData, 35*1000);
}


// function initfunc( csvay, scroot) {
//     window.csv = csvay;
//     window.scroot = scroot;
// };

// function update_values() {
//     $.getJSON(urlstuff,
//         function(data) {
//             window.glob_tabvar = data;
//     });
// }


// Plot and update the number of processed pastes
// BEGIN PROCESSED PASTES
var default_minute = (typeof window.default_minute !== "undefined") ? parseInt(window.default_minute) : 10;
var totalPoints = 2*parseInt(default_minute); //60s*minute
var curr_max = {"global": 0};

function fetch_data(dataset, curr_data, feeder_name) {
    if (curr_data.length > 0){
        var data_old = curr_data[0];
        curr_data = curr_data.slice(1);
        curr_max[dataset] = curr_max[dataset] == data_old ? Math.max.apply(null, curr_data) : curr_max[dataset];
    }

    while (curr_data.length < totalPoints) {
        var y = (typeof window.paste_num_tabvar_all[dataset] !== "undefined") ? parseInt(window.paste_num_tabvar_all[dataset]) : 0;
        curr_max[dataset] = y > curr_max[dataset] ? y : curr_max[dataset];
        curr_data.push(y);
    }
    // Zip the generated y values with the x values
    var res = [];
    for (var i = 0; i < curr_data.length; ++i) {
        res.push([i, curr_data[i]])
    }
    data_for_processed_paste[dataset] = curr_data;
    return { label: feeder_name, data: res };
}

function getData(dataset_group, graph_type) {
    var curr_data;

    var all_res = [];
    if (dataset_group == "global") {
        if (data_for_processed_paste["global"] ===  undefined) { // create feeder dataset if not exists yet
            data_for_processed_paste["global"] = [];
        }
        curr_data = data_for_processed_paste["global"];
        all_res.push(fetch_data("global", curr_data, "global"));
    } else {
        for(d_i in list_feeder) {
            if(list_feeder[d_i] == "global") {
                continue;
            }

            dataset = graph_type+list_feeder[d_i];
            if (data_for_processed_paste[dataset] ===  undefined) { // create feeder dataset if not exists yet
                data_for_processed_paste[dataset] = [];
            }
            curr_data = data_for_processed_paste[dataset];
            all_res.push(fetch_data(dataset, curr_data, list_feeder[d_i]));
        }
    }
    return all_res;
}

var updateInterval = 30*1000; //30s = 30*1000ms
var options_processed_pastes = {
    series: {   shadowSize: 0 ,
                lines: { fill: true, fillColor: { colors: [ { opacity: 1 }, { opacity: 0.1 } ] }}
            },
    yaxis: { min: 0, max: 40 },
    xaxis: { ticks: [[0, 0], [2, 1], [4, 2], [6, 3], [8, 4], [10, 5], [12, 6], [14, 7], [16, 8], [18, 9], [20, 10]] },
    grid: {
        tickColor: "#dddddd",
        borderWidth: 0
    },
    legend: {
        show: true,
        position: "nw",
    }
};

function update_processed_pastes(graph, dataset, graph_type) {
    graph.setData(getData(dataset, graph_type));
    graph.getOptions().yaxes[0].max = curr_max[dataset];
    graph.setupGrid();
    graph.draw();
    setTimeout(function(){ update_processed_pastes(graph, dataset, graph_type); }, updateInterval);
}


// END PROCESSED PASTES

// function initfunc( csvay, scroot) {
//   window.csv = csvay;
//   window.scroot = scroot;
// };

var source = new EventSource(urllog);

source.onmessage = function(event) {
    var feed = JSON.parse( event.data );
    create_log_table(feed);
};
source.onerror = function(event) {
    console.error('EventSource failed:', event);
    source.close();
};

function pad_2(number) {
    return (number < 10 ? '0' : '') + number;
}

function create_log_table(obj_json) {
    //console.log("create_log_table")
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
    var inspect = document.createElement('TD')

    var chansplit = obj_json.channel.split('.');
    var parsedmess = obj_json.data.split(';');


    if (parsedmess[0] == "Mixer"){
        var feeder = parsedmess[4].split(" ")[1];
        var paste_processed = parsedmess[4].split(" ")[3];
        var msg_type = parsedmess[4].split(" ")[2];

        if (feeder == "All_feeders"){
            if(list_feeder.indexOf("global") == -1) {
                list_feeder.push("global");

                options_processed_pastes.legend.show = false;
                var total_proc = $.plot("#global", [ getData("global", null) ], options_processed_pastes);
                options_processed_pastes.legend.show = true;
                options_processed_pastes.series.lines = { show: true, fill: true };
                data_for_processed_paste["global"] = Array(totalPoints+1).join(0).split('');

                var feederProc = $.plot("#Proc_feeder", [ getData(feeder, "Proc") ], options_processed_pastes);
                var feederDup = $.plot("#Dup_feeder", [ getData(feeder, "Dup") ], options_processed_pastes);

                update_processed_pastes(feederProc, "feeder", "Proc");
                update_processed_pastes(feederDup, "feeder", "Dup");
                update_processed_pastes(total_proc, "global");
                setTimeout(checkIfReceivedData, 45*1000);
            }
           window.paste_num_tabvar_all["global"] = paste_processed;
           time_since_last_pastes_num["global"] = new Date().getTime();
        } else {
            if (list_feeder.indexOf(feeder) == -1) {
                list_feeder.push(feeder);
                data_for_processed_paste["Proc"+feeder] = Array(totalPoints+1).join(0).split('');
                data_for_processed_paste["Dup"+feeder] = Array(totalPoints+1).join(0).split('');
            }

            var feederName = msg_type == "Duplicated" ? "Dup"+feeder : "Proc"+feeder;
            window.paste_num_tabvar_all[feederName] = paste_processed;
            time_since_last_pastes_num[feederName] = new Date().getTime();
        }
        return;
    }

    if( parsedmess.length>2 ){
      if( chansplit[1] == "INFO" ){
          tr.className = "table-disabled";
      }
      else if ( chansplit[1] == "WARNING" ){
          tr.className = "table-log-warning";
      }
      else if ( chansplit[1] == "CRITICAL"){
          tr.className = "table-danger"
      }

      // source_link = document.createElement("A");
      // if (parsedmess[1] == "slexy.org"){
      //     source_url = "http://"+parsedmess[1]+"/view/"+parsedmess[3].split(".")[0];
      // }
      // else{
      //     source_url = "http://"+parsedmess[1]+"/"+parsedmess[3].split(".")[0];
      // }
      // source_link.setAttribute("HREF",source_url);
      // src.appendChild(source_link);

      src.appendChild(document.createTextNode(parsedmess[1]));


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
          iconspan.className = "fas fa-eye";
      }
      else if (parsedmess[4].split(" ")[0] == "Checked"){
          iconspan.className = "far fa-thumbs-up";
      }
      iconspan.innerHTML = "&nbsp;";
      msage.appendChild(iconspan);
      var message = parsedmess[4].split(" ");
      message.shift();

      msage.appendChild(document.createTextNode(message.join(" ")));

      // console.log(parsedmess)

      var paste_path = parsedmess[5];
      var url_to_saved_paste = url_showSavedPath+"?gid="+paste_path;

      var action_icon_a = document.createElement("A");
      action_icon_a.setAttribute("TARGET", "_blank");
      action_icon_a.setAttribute("HREF", url_to_saved_paste);
      var action_icon_span = document.createElement('SPAN');
      action_icon_span.className = "fas fa-search-plus";
      action_icon_a.appendChild(action_icon_span);

      inspect.appendChild(action_icon_a);
      inspect.setAttribute("style", "text-align:center;");

      tr.appendChild(time)
      tr.appendChild(chan);
      tr.appendChild(level);
      tr.appendChild(scrpt);
      tr.appendChild(src);
      tr.appendChild(pdate);
      tr.appendChild(nam);
      tr.appendChild(msage);
      tr.appendChild(inspect);

      if (chansplit[1] == document.getElementById("checkbox_log_info").value && document.getElementById("checkbox_log_info").checked  == true) {
             tableBody.appendChild(tr);
         }
      if (chansplit[1] == document.getElementById("checkbox_log_warning").value && document.getElementById("checkbox_log_warning").checked == true) {
          tableBody.appendChild(tr);
      }
      if (chansplit[1] == document.getElementById("checkbox_log_critical").value && document.getElementById("checkbox_log_critical").checked == true) {
          tableBody.appendChild(tr);
      };

      var sel = document.getElementById("log_select")
      if (tableBody.rows.length > sel.options[sel.options.selectedIndex].value) {
          while (tableBody.rows.length != sel.options[sel.options.selectedIndex].value){
              tableBody.deleteRow(0);
          }
      }
    }
}

/*
function create_queue_table(data) {
    document.getElementById("queueing").innerHTML = "";
    var Tablediv = document.getElementById("queueing")
    var table = document.createElement('TABLE')
    table.className = "table table-bordered table-hover tableQueue";
    var tableHead = document.createElement('THEAD')
    var tableBody = document.createElement('TBODY')

    table.appendChild(tableHead);
    table.appendChild(tableBody);
    var heading = new Array();
    heading[0] = "Queue Name.PID"
    heading[1] = "Amount"
    var tr = document.createElement('TR');
    tableHead.appendChild(tr);

    for (i = 0; i < heading.length; i++) {
        var th = document.createElement('TH')
        if (heading[i] == "Amount") {
          th.width = '50';
        } else {
          th.width = '100';
        }
        th.appendChild(document.createTextNode(heading[i]));
        tr.appendChild(th);
    }

    if ((data).length == 0) {
        var tr = document.createElement('TR');
        var td = document.createElement('TD');
        var td2 = document.createElement('TD');
        td.appendChild(document.createTextNode("No running queues"));
        td2.appendChild(document.createTextNode("Or no feed"));
        td.className += " table-danger";
        td2.className += " table-danger";
        tr.appendChild(td);
        tr.appendChild(td2);
        tableBody.appendChild(tr);
    }
    else {
        for(i = 0; i < (data).length;i++){
            var tr = document.createElement('TR')
            for(j = 0; j < 2; j++){
                var td = document.createElement('TD')
                var moduleNum = j == 0 ? "." + data[i][3] : "";
                td.appendChild(document.createTextNode(data[i][j] + moduleNum));
                tr.appendChild(td)
            }
            // Used to decide the color of the row
            // We have data[][j] with:
            // - j=0: ModuleName
            // - j=1: queueLength
            // - j=2: LastProcessedPasteTime
            // - j=3: Number of the module belonging in the same category
            if (data[i][3]==="Not Launched")
                tr.className += " bg-danger text-white";
            else if (parseInt(data[i][2]) > window.threshold_stucked_module && parseInt(data[i][1]) > 2)
                tr.className += " table-danger";
            else if (parseInt(data[i][1]) === 0)
                tr.className += " table-disabled";
            else
                tr.className += " table-success";
            tableBody.appendChild(tr);
        }
    }
    Tablediv.appendChild(table);
}*/

/*
function load_queues() {
    var data = [];
    var data2 = [];
    var tmp_tab = [];
    var tmp_tab2 = [];
    var curves_labels = [];
    var curves_labels2 = [];
    var x = new Date();

    for (i = 0; i < glob_tabvar.row1.length; i++){
        if (glob_tabvar.row1[i][0].split(".")[0] == 'Categ' || glob_tabvar.row1[i][0].split(".")[0] == 'Curve'){
            if (curves_labels2.indexOf(glob_tabvar.row1[i][0].split(".")[0]) == -1) {
                tmp_tab2.push(0);
                curves_labels2.push(glob_tabvar.row1[i][0].split(".")[0]);
            }
        }
        else {
            if (curves_labels.indexOf(glob_tabvar.row1[i][0].split(".")[0]) == -1) {
                tmp_tab.push(0);
                curves_labels.push(glob_tabvar.row1[i][0].split(".")[0]);
            }
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

        $.ajax({ ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
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
                        $("#queue-color-legend").show();
                        create_queue_table();
                    }
                    else{
                        $("#queueing").html('');
                        $("#queue-color-legend").hide();
                    }


                    queues_pushed = []
                    for (i = 0; i < (glob_tabvar.row1).length; i++){
                        if (glob_tabvar.row1[i][0].split(".")[0] == 'Categ' || glob_tabvar.row1[i][0].split(".")[0] == 'Curve'){
                            if (queues_pushed.indexOf(glob_tabvar.row1[i][0].split(".")[0]) == -1) {
                                queues_pushed.push(glob_tabvar.row1[i][0].split(".")[0]);
                                tmp_values2.push(parseInt(glob_tabvar.row1[i][1]));
                            }
                        }
                        else {
                            if (queues_pushed.indexOf(glob_tabvar.row1[i][0].split(".")[0]) == -1) {
                                queues_pushed.push(glob_tabvar.row1[i][0].split(".")[0]);
                                tmp_values.push(parseInt(glob_tabvar.row1[i][1]));
                            }

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

                }, interval);
            }
        });
    };

    refresh();
}
*/

// function manage_undefined() {
//     if (typeof glob_tabvar == "undefined")
//         setTimeout(function() { if (typeof glob_tabvar == "undefined") { manage_undefined(); } else { /*load_queues();*/ } }, 1000);
//     else if (typeof glob_tabvar.row1 == "undefined")
//         setTimeout(function() { if (typeof glob_tabvar.row1 == "undefined") { manage_undefined(); } else { load_queues(); } }, 1000);
//     else
//         load_queues();
// }


// $(document).ready(function () {
//     manage_undefined();
// });
