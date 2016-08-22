/**
 *  FlexGauge
 *  Version: 1.0
 *  Author: Jeff Millies
 *  Author URI:
 *
 *  Slight modification for better display in Sentiment webpages
 */
(function ($) {
    var FlexGauge = function (o) {
        if (typeof o === 'object') {
            this._extendOptions(o, false);
            this._build();
        }
    };
    FlexGauge.prototype = {
        /**
         *  {String} Element that you would like to append to. ie '#idname', '.classname', 'div#idname', etc..
         */
        appendTo: 'body',
        /**
         *  {String} Id of Canvas already created or Id of canvas that will be created automatically
         */
        elementId: 'canvas',
        /**
         *  {String} Class of canvas created
         */
        elementClass: 'canvas',
        /**
         *  {Int} Canvas Width & Height
         */
        elementWidth: 200,
        elementHeight: 200,
        /**
         *  {Boolean|String} Generate Dial Value for the Gauge, true will use arcFillPercent or arcFillInt
         *  depending on provided values and specified dialUnits, string will use specified value
         */
        dialValue: false,
        /**
         *  {String} Class applied to div when dial is generated.
         */
        dialClass: 'fg-dial',
        /**
         *  {string: %|$| } Type of unit to use for the dial
         */
        dialUnit: '%',
        /**
         *  {string: before|after} Where the dial unit will be displayed
         */
        dialUnitPosition: 'after',
        /**
         *  {Boolean|String} Generate Label for the Gauge, true will use default "FlexGauge", string will use specified
         */
        dialLabel: false,
        /**
         *  {String} Class applied to div when label is generated.
         */
        dialLabelClass: 'fg-dial-label',
        /**
         *  {Int} Radius of the arc
         */
        inc: 0.0,
        incTot: 1.0,
        /**
         *  {Doule} Increment value
         */
        arcSize: 85,
        /**
         *  {double} Starting and Ending location of the arc, End always needs to be larger
         *  arc(x, y, radius, startAngle, endAngle, anticlockwise)
         */
        arcAngleStart: 0.85,
        arcAngleEnd: 2.15,
        /**
         *  {double} Percentage the arc fills
         */
        arcFillPercent: .5,
        /**
         *  {Int} Starting and Ending values that are used to
         *  find a difference for amount of units
         *  ie: 60 (arcFillEnd) - 10 (arcFillStart) = 50
         */
        arcFillStart: null,
        arcFillEnd: null,
        /**
         *  {Int} Data used to find out what percentage of the
         *  arc to fill. arcFillInt can be populated by
         *  the difference of arcFillStart and arcFillEnd
         */
        arcFillInt: null,
        arcFillTotal: null,
        /**
         *  {Int} Color lightness: 0 - 255, 0 having no white added, 255 having all white and no color
         */
        arcBgColorLight: 80,
        /**
         *  {Int} Color saturation: 0 - 100, 0 having no color, 100 is full color
         */
        arcBgColorSat: 60,
        /**
         *  {Int} Size of the line marking the percentage
         */
        arcStrokeFg: 30,
        /**
         *  {Int} Size of the container holding the line
         */
        arcStrokeBg: 30,

        /**
         *  {string: hex} Color of the line marking the percentage
         */
        colorArcFg: '#5bc0de',
        /**
         *  {string: hex} Color of the container holding the line, default is using the Fg color and lightening it
         */
        colorArcBg: null,

        /**
         *  {String} Instead of providing a color or hex for the color, you can provide a class from the style
         *  sheet and specify what you would like to grab for the color in styleSrc
         */
        styleArcFg: null,
        styleArcBg: null,
        styleSrc: 'color',

        /**
         *  {Boolean} If set to false, then the graph will not be animated
         */
        animateEasing: true,
        /**
         *  {Int} Speed for the animation, 1 is fastest, higher the number, slower the animation
         */
        animateSpeed: 5,
        /**
         *  {Int} Math used in animation speed
         */
        animateNumerator: 12,
        animateDivisor: 15,

        /**
         *  {double} Placeholder for current percentage while animating
         */
        _animatePerc: 0.00,

        /**
         *  {Object} Placeholder for setInterval
         */
        _animateLoop: null,

        /**
         *  {Object} Placeholder for canvas
         */
        _canvas: null,

        /**
         *  {Object} Placeholder for canvas context
         */
        _ctx: null,

        update: function (o) {
            if (typeof o === 'object') {
                var difference;

                // if using int, convert to percent to check difference
                if (typeof o.arcFillInt !== 'undefined' && o.arcFillInt == this.arcFillInt &&
                    typeof o.arcFillTotal !== 'undefined' && o.arcFillTotal == this.arcFillTotal) {
                    o.arcFillPercent = this.arcFillPercent;
                } else if (typeof o.arcFillInt !== 'undefined' && typeof o.arcFillTotal !== 'undefined' &&
                    (o.arcFillInt != this.arcFillInt || o.arcFillTotal == this.arcFillTotal)) {
                    o.arcFillPercent = (o.arcFillInt / o.arcFillTotal);
                } else if (typeof o.arcFillInt !== 'undefined' && typeof o.arcFillTotal === 'undefined' &&
                    (o.arcFillInt != this.arcFillInt)) {
                    o.arcFillPercent = (o.arcFillInt / this.arcFillTotal);
                }

                if (typeof o.arcFillPercent !== 'undefined') {
                    difference = Math.abs((this.arcFillPercent - o.arcFillPercent));
                } else {
                    difference = this.arcFillPercent;
                }

                this._extendOptions(o, true);

                clearInterval(this._animateLoop);

                if (difference > 0) {
                    var that = this;
                    this._animateLoop = setInterval(function () {
                        return that._animate();
                    }, (this.animateSpeed * this.animateNumerator) / (difference * this.animateDivisor));
                }
            }
        },

        _extendOptions: function (o, update) {
            var color = false;
            if (update)
                color = this.colorArcFg;

            $.extend(this, o, true);

            if (typeof o.arcFillStart !== 'undefined' && typeof o.arcFillEnd !== 'undefined' && typeof o.arcFillTotal !== 'undefined') {
                this.arcFillInt = (o.arcFillEnd - o.arcFillStart);
            }

            if (typeof o.arcFillPercent === 'undefined' && this.arcFillInt !== null && this.arcFillInt >= 0 && this.arcFillTotal !== null && this.arcFillTotal > 0) {
                this.arcFillPercent = this.arcFillInt / this.arcFillTotal;
            }

            if (typeof o.elementId === 'undefined') {
                this.elementId = 'fg-' + this.appendTo + '-canvas';
            }
            // supporting color if pass, changing to hex
            if (typeof o.colorArcFg !== 'undefined') {
                this.colorArcFg = colorToHex(o.colorArcFg);
            }

            if (typeof o.colorArcBg !== 'undefined') {
                this.colorArcBg = colorToHex(o.colorArcBg);
            }

            // only use the styleArcFg if colorArcFg wasn't specified in the options
            if (typeof o.styleArcFg !== 'undefined' && typeof o.colorArcFg === 'undefined') {
                this.colorArcFg = getStyleRuleValue(this.styleSrc, this.styleArcFg);
            }

            if (typeof o.colorArcBg === 'undefined' && this.colorArcBg === null && this.colorArcFg !== null) {
                this.colorArcBg = this.colorArcFg;
            }

            if (typeof this.colorArcBg !== null && (!update || colorToHex(this.colorArcFg) != colorToHex(color))) {
                if (colorToHex(this.colorArcFg) != colorToHex(color))
                    this.colorArcBg = this.colorArcFg;

                this.colorArcBg = shadeColor(this.colorArcBg, this.arcBgColorLight, this.arcBgColorSat);
            }

            if (typeof o.dialLabel === 'boolean' && o.dialLabel) {
                this.dialLabel = 'FlexGauge';
            }

        },

        _build: function () {
            if (document.getElementById(this.elementId) === null) {
                $(this.appendTo).append('<canvas id="' + this.elementId + '" width="' + this.elementWidth + '" height="' + this.elementHeight + '"></canvas>');
            }

            this._canvas = document.getElementById(this.elementId);
            this._ctx = this._canvas.getContext("2d");

            this.arcAngleStart = this.arcAngleStart * Math.PI;
            this.arcAngleEnd = this.arcAngleEnd * Math.PI;
            if (this.animateEasing === false) {
                this._animatePerc = this.arcFillPercent;
            }

            var that = this;
            this._animateLoop = setInterval(function () {
                return that._animate();
            }, (this.animateSpeed * this.animateNumerator) / (this.arcFillPercent * this.animateDivisor));
        },

        _animate: function () {
            var animateInt = Math.round(this._animatePerc * 100);
            var arcInt = Math.round(this.arcFillPercent * 100);

            if (animateInt < arcInt)
                animateInt++;
            else
                animateInt--;

            this._animatePerc = (animateInt / 100);
            if (animateInt === arcInt) {
                this.arcFillPercent = this._animatePerc;
                clearInterval(this._animateLoop);
                this._draw();
            }
            this._draw();
        },

        _draw: function () {
            //Clear the canvas everytime a chart is drawn
            this._ctx.clearRect(0, 0, this.elementWidth, this.elementHeight);

            //Background 360 degree arc
            this._ctx.beginPath();
            this._ctx.strokeStyle = this.colorArcBg;
            this._ctx.lineWidth = this.arcStrokeBg;
            this._ctx.arc(
                this.elementWidth / 2,
                this.elementHeight / 2 + 50,
                this.arcSize,
                0,
                Math.PI,
                true
            );

            this._ctx.stroke();

            //var newEnd = ((this.arcAngleEnd - this.arcAngleStart) * this._animatePerc) + this.arcAngleStart;
            var newStart;
            var newEnd;

            var incArc = this.inc*Math.PI/2;
            if (this.inc >= 0.0){
                newStart = -Math.PI/2;
                newEnd = newStart + incArc;
            } else {
                newStart = -Math.PI/2 + incArc;
                newEnd = -Math.PI/2;
            }

            var colorShadesTabRed = ['#ff0000','#ff4000','#ff8000','#ff9900','#ffbf00','#ffff00'];
            var colorShadesTabGreen = ['#ffff00','#E0FF00','#D0FF00','#a0ff00','#00ff00','#00ff40',];
            var colorValue = parseInt(Math.abs((this.inc / this.incTot) * 5));
            var theColor;
            if (this.inc >= 0.0)
                theColor = colorShadesTabGreen[colorValue];
            else
                theColor = colorShadesTabRed[5-colorValue];
            this.colorArcFg = theColor;

            this._ctx.beginPath();
            this._ctx.strokeStyle = this.colorArcFg;
            this._ctx.lineWidth = this.arcStrokeFg;
            this._ctx.arc(
                this.elementWidth / 2,
                this.elementHeight / 2 + 50,
                this.arcSize,
                newStart,
                newEnd,
                false
            );
            this._ctx.stroke();
            this._renderLabel();
        },

        _renderLabel: function () {
            if (this.dialValue) {
                var dialVal;
                var dial = $(this.appendTo).find('div.' + this.dialClass);
                if (dial.length === 0) {
                    $(this.appendTo).append('<div class="' + this.dialClass + '"></div>');
                }
                dial = $(this.appendTo).find('div.' + this.dialClass);
                if (typeof this.dialValue === 'boolean') {
                    switch (this.dialUnit) {
                        case '%':
                            dialVal = Math.round(this._animatePerc * 100);
                            break;
                        default:
                            dialVal = Math.round(this.arcFillInt * (this._animatePerc / this.arcFillPercent));
                            break;
                    }
                    dialVal = (isNaN(dialVal) ? 0 : dialVal);
                    switch (this.dialUnitPosition) {
                        case 'before':
                            dialVal = this.dialUnit + dialVal;
                            break;
                        case 'after':
                            dialVal = dialVal + this.dialUnit;
                            break;
                    }
                } else {
                    dialVal = this.dialValue;
                }
                dial.html(dialVal)
            }
            if (this.dialLabel) {
                var label = $(this.appendTo).find('div.' + this.dialLabelClass);
                if (label.length === 0) {
                    $(this.appendTo).append('<div class="' + this.dialLabelClass + '"></div>');
                }
                label = $(this.appendTo).find('div.' + this.dialLabelClass);
                label.html(this.dialLabel);
            }
        }
    };

    function shadeColor(col, amt, sat) {
        if (col[0] == "#") {
            col = col.slice(1);
        }

        var num = parseInt(col, 16);

        var r = (num >> 16) + amt;

        if (r > 255) r = 255;
        else if (r < 0) r = 0;

        var b = ((num >> 8) & 0x00FF) + amt;

        if (b > 255) b = 255;
        else if (b < 0) b = 0;

        var g = (num & 0x0000FF) + amt;

        if (g > 255) g = 255;
        else if (g < 0) g = 0;

        var gray = r * 0.3086 + g * 0.6094 + b * 0.0820;
        sat = (sat / 100);

        r = Math.round(r * sat + gray * (1 - sat));
        g = Math.round(g * sat + gray * (1 - sat));
        b = Math.round(b * sat + gray * (1 - sat));
        return "#" + (g | (b << 8) | (r << 16)).toString(16);
    }

    function getStyleRuleValue(style, selector) {
        $('body').append('<div id="getStyleRuleValue-' + selector + '"></div>');
        var element = $('#getStyleRuleValue-' + selector);
        element.addClass(selector);
        var color = element.css(style);
        var hex = colorToHex(color);
        element.remove();
        return hex;
    }

    function colorToHex(color) {
        if (color[0] != 'r')
            return color;

        var rgb = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
        return "#" +
            ("0" + parseInt(rgb[1], 10).toString(16)).slice(-2) +
            ("0" + parseInt(rgb[2], 10).toString(16)).slice(-2) +
            ("0" + parseInt(rgb[3], 10).toString(16)).slice(-2);
    }

    if (typeof define === 'function') {
        define('flex-gauge', ['jquery'], function ($) {
            return FlexGauge;
        });
    } else {
        window.FlexGauge = FlexGauge;
    }
})(jQuery);
