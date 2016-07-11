function Graph(id_pannel, path, header_size){
	this.path = path;
	this.id_pannel = id_pannel;

        // Hide every header during initialisation
        var false_tab = [];
        for(i=0; i<header_size; i++){
            false_tab[i] = false;
        }
        this.false_tab = false_tab;

        g2 = new Dygraph(
	    document.getElementById(this.id_pannel),
	    // path to CSV file
	    //"{{ url_for('static', filename='csv/tldstrendingdata.csv') }}",
	    //"../static//csv/tldstrendingdata.csv",
	    this.path,
	    //window.csv,
	    {
	    rollPeriod: 1,
	    showRoller: true,
	    //drawPoints: true,
	    //fillGraph: true,
	    logscale: true,
            
	    animatedZooms: true,
	    labelsKMB: true,
	    highlightCircleSize: 3,
	    highlightSeriesOpts: {
		strokeWidth: 3,
		strokeBorderWidth: 1,
		highlightCircleSize: 5,
	    },
	    underlayCallback: function(canvas, area, g) {
	    canvas.fillStyle = "rgba(255, 193, 37, 0.5)";

	    function highlight_period(x_start, x_end) {
		var canvas_left_x = g.toDomXCoord(x_start);
		var canvas_right_x = g.toDomXCoord(x_end);
		var canvas_width = canvas_right_x - canvas_left_x;
		canvas.fillRect(canvas_left_x, area.y, canvas_width, area.h);
	    }

	    var min_data_x = g.getValue(0,0);
	    var max_data_x = g.getValue(g.numRows()-1,0);

	    // get day of week
	    var d = new Date(min_data_x);
	    var dow = d.getUTCDay();
	    var ds = d.toUTCString();

	    var w = min_data_x;
	    // starting on Sunday is a special case
	    if (dow == 0) {
		highlight_period(w,w+12*3600*1000);
	    }
	    // find first saturday
	    while (dow != 5) {
		w += 24*3600*1000;
		d = new Date(w);
		dow = d.getUTCDay();
	    }

	    // shift back 1/2 day to center highlight around the point for the day
	    w -= 12*3600*1000;
	    while (w < max_data_x) {
		var start_x_highlight = w;
		var end_x_highlight = w + 2*24*3600*1000;
		// make sure we don't try to plot outside the graph
		if (start_x_highlight < min_data_x) {
		    start_x_highlight = min_data_x;
		}
		if (end_x_highlight > max_data_x) {
		    end_x_highlight = max_data_x;
		}
		highlight_period(start_x_highlight,end_x_highlight);
		// calculate start of highlight for next Saturday
		w += 7*24*3600*1000;
	    }
	    },
            visibility: false_tab
	});
        this.graph = g2;
        this.setVisibility = setVis;

	onclick = function(ev) {
	    if (g2.isSeriesLocked()) {
		g2.clearSelection();
	    }
	    else {
		g2.setSelection(g2.getSelection(), g2.getHighlightSeries(), true);
	    }
	};
	g2.updateOptions({clickCallback: onclick}, true);

	var linear = document.getElementById("linear");
	var log = document.getElementById("log");
	linear.onclick = function() { setLog(false); }
	log.onclick = function() { setLog(true); }
	var setLog = function(val) {
	    g2.updateOptions({ logscale: val });
	    linear.disabled = !val;
	    log.disabled = val;
	    }
	function unzoomGraph() {
	    g2.updateOptions({
		dateWindow:null,
		valueRange:null
	    });
	}

        // display the top headers
        function setVis(max_display){
            headings = this.graph.getLabels();
            headings.splice(0,1);
            var sorted_list = new Array();
            today = new Date().getDate();
            for( i=0; i<headings.length; i++){
                the_heading = headings[i];
                //console.log('heading='+the_heading+' tab['+(today-1)+']['+(parseInt(i)+1)+']='+g.getValue(today-1, parseInt(i)+1));
                sorted_list.push({dom: the_heading, val: this.graph.getValue(today-1, parseInt(i)+1), index: parseInt(i)});
                sorted_list.sort(function(a,b) {
                    return b.val - a.val;
                });

            }
            //var no_display_list = sorted_list.slice(10, sorted_list.length+1);
            var display_list = sorted_list.slice(0, max_display);
            for( i=0; i<display_list.length; i++){
                this.graph.setVisibility(display_list[i].index, true);
            }
       }

}
