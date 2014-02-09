/*
 * jquery.graphview.js
 *
 * displays graph data results retrieved by querying a specified index
 * 
 * created by Mark MacGillivray - mark@cottagelabs.com
 *
 * copyheart 2013
 *
 * VERSION - COMPLETELY CUSTOM GRAPHVIEW FOR LEVIATHAN
 * THIS DOES NOT WORK WHEN SEPARATED FROM THE LEVIATHAN INDEX PAGE
 * IT IS NOT REALLY A SEPARABLE JQUERY THING - IT WAS JUST USEFUL TO BUILD 
 * DOWN FROM GRAPHVIEW TO THIS, AND TO KEEP IT OUT OF THE INDEX PAGE
 *
 *
 */


/* this software comes with some defaults for building a UI on the page, for 
binding actions to that UI, for reading and sending a query to the target, 
for building results onto the page when the response is retrieved. All of these 
can be overwritten. See the defaults for some overview and look at the individual 
default functions defined below to figure out how to copy and augment one.

For example provide custom uitemplate and uibindings functions to build specific 
UIs. Then provide custom query and executequery functions to read the query from 
the UI and to execute it with some cleaning. Then provide custom showresults to 
put them on the page as desired. Or some combination of the lot. */


// Deal with indexOf issue in <IE9
// provided by commentary in repo issue - https://github.com/okfn/facetview/issues/18
if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(searchElement /*, fromIndex */ ) {
        "use strict";
        if (this == null) {
            throw new TypeError();
        }
        var t = Object(this);
        var len = t.length >>> 0;
        if (len === 0) {
            return -1;
        }
        var n = 0;
        if (arguments.length > 1) {
            n = Number(arguments[1]);
            if (n != n) { // shortcut for verifying if it's NaN
                n = 0;
            } else if (n != 0 && n != Infinity && n != -Infinity) {
                n = (n > 0 || -1) * Math.floor(Math.abs(n));
            }
        }
        if (n >= len) {
            return -1;
        }
        var k = n >= 0 ? n : Math.max(len - Math.abs(n), 0);
        for (; k < len; k++) {
            if (k in t && t[k] === searchElement) {
                return k;
            }
        }
        return -1;
    }
}


(function($){
    $.fn.graphview = function(options) {


        // ===============================================
        // ===============================================
        //
        // set defaults
        //
        // ===============================================
        // ===============================================

        var defaults = {
            "target": '/graph',
            "searchonload": true, // run default search as soon as page loads
            
        };





        // ===============================================
        // ===============================================
        // 
        // force directed network graph functions
        //
        // these are used by the default results display
        //
        // ===============================================
        // ===============================================


        var label = function(d,t) {
            // calculate a label
            var label = '';
            if ( d.className ) {
                label += d.className;
            }
            if ( t == "text" && d.type != "question" && d.type != "tag" ) {
                return "";
            } else {
                return label;
            }
        }
    
        var force = function() {

            /*// a function to check the dict of linked things
            function isConnected(a, b) {
                return options.response.linksindex[a.index + "," + b.index] || options.response.linksindex[b.index + "," + a.index];
            }
            // when a node is hovered, opacify any nodes / links not connected to it
            var highlight = function(opacity) {
                return function(d) {
                    node.style("stroke","transparent").style("stroke", function(o) {
                        thisOpacity = d === o && opacity != 1 ? "#333" : "transparent";
                        return thisOpacity;
                    });

                    link.style("stroke", function(o) {
                        return opacity == 1 ? "#aaa" : "#333";
                    }).style("stroke", function(o) {
                        return isConnected(d,o.source) && isConnected(d,o.target) && opacity != 1 ? "#333" : "#aaa";
                    }).style("stroke-width", function(o) {
                        return opacity == 1 ? 1 : 1.5;
                    }).style("stroke-width", function(o) {
                        return isConnected(d,o.source) && isConnected(d,o.target) && opacity != 1 ? 1.5 : 1;
                    });
                };
            };*/

            // build the vis area
            var w = obj.width();
            var h = obj.height();
            var vis = d3.select(".graphview_panel")
                .append("svg:svg")
                .attr("width", w)
                .attr("height", h)
                .attr("pointer-events", "all")
                .append('svg:g')
                .call(d3.behavior.zoom().on("zoom", redraw))
                .append('svg:g');

            vis.append('svg:rect')
                .attr('width', w)
                .attr('height', h)
                .attr('fill', 'transparent');

            // fade in whenever transitions occur
            vis.style("opacity", 1e-6)
                .transition()
                .duration(1000)
                .style("opacity", 1);

            // redraw on zoom
            function redraw() {
                vis.attr("transform",
                    "translate(" + d3.event.translate + ")"
                    + " scale(" + d3.event.scale + ")"
                );
            }

            // start the force layout
            var force = d3.layout.force()
                .charge(-160)
                .linkDistance(100)
                .nodes(options.response.nodes)
                .links(options.response.links)
                .size([w, h])
                .start();


            // put links on it
            var link = vis.selectAll("line.link")
                .data(options.response.links)
                .enter().append("svg:line")
                .attr("class", "link")
                .attr("stroke", "#aaa")
                .attr("stroke-opacity", 0.8)
                .style("stroke-width", function(d) { return Math.sqrt(d.value); })
                .attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            // put the nodes on it
            var dom = d3.extent(options.response.nodes, function(d) {
                return d.value;
            });
            var cr = d3.scale.sqrt().range([5, 25]).domain(dom);
            var node = vis.selectAll("circle.node")
                .data(options.response.nodes)
                .enter().append("svg:circle")
                .attr("class", "node")
                .attr("name", function(d) { return label(d); })
                .attr("cx", function(d) { return d.x; })
                .attr("cy", function(d) { return d.y; })
                .attr("r", function(d) { return cr(d.value); })
                .style("fill", function(d) { return d.color; })
                .call(force.drag)
                .on("click",function(d) { getquestion(d.id); })
                //.on("mouseover", highlight(.1))
                //.on("mouseout", highlight(1))

            // put a hover a label on
            node.append("svg:title")
                .text(function(d) { return label(d,"hover"); });

            // make the cursor a click pointer whenever hovering a node
            $('.node').css({"cursor":"pointer"});

            // put a label next to each node
            // TODO: change to only show labels on question objects
            var texts = vis.selectAll("text.label")
                .data(options.response.nodes)
                .enter().append("text")
                .attr("class", "svglabel")
                .attr("fill", "#666")
                .text(function(d) {  return label(d,"text"); });

            // define the changes that happen when the diagram ticks over
            force.on("tick", function() {
                link.attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node.attr("cx", function(d) { return d.x; })
                    .attr("cy", function(d) { return d.y; });

                texts.attr("transform", function(d) {
                    return "translate(" + (d.x - cr(d.value) + 15) + "," + (d.y + cr(d.value) + 5) + ")";
                });

            });
        
        };
        



        // ===============================================
        // ===============================================
        //
        // default results display
        //
        // ===============================================
        // ===============================================
        
        defaults.showresults = function(data) {
            // put the response data in the response option
            data ? options.response = data : false;
            // do some cleaning
            $('.graphview_panel', obj).html('');
            $('.graphview_panel', obj).css({"overflow":"visible"});
            
            force();

            $('.graphview_loading', obj).hide();
        };
        


        // ===============================================
        // ===============================================
        //
        // default query functions
        //
        // defaults.executequery() sends the query to the 
        // target and calls showresults when a suitable 
        // response is retrieved
        //
        // ===============================================
        // ===============================================

        defaults.executequery = function(event) {
            // show the loading image
            $('.graphview_loading', obj).show();

            var tgt = options.target + '?';
            if ( $('#showtags').is(':checked') ) {
                tgt += 'tag=yes&';
            }
            if ( $('#showusernames').is(':checked') ) {
                tgt += 'usernames=yes&';
            }
            if ( $('#showanswers').is(':checked') ) {
                tgt += 'answers=yes&';
            }
            if ( $('#showhierarchy').is(':checked') ) {
                tgt += 'hierarchy=yes&';
            }
            if ( tags.length ) {
                tgt += 'selectedtags=';
                var fst = true;
                $.each(tags, function(k, v) {
                    if ( fst ) {
                        fst = false;
                    } else {
                        tgt += ',';
                    }
                    tgt += v;
                });
                tgt += '&'
            }
            if ( keywords.length ) {
                tgt += 'selectedkeywords=';
                var fst = true;
                $.each(keywords, function(k, v) {
                    if ( fst ) {
                        fst = false;
                    } else {
                        tgt += ',';
                    }
                    tgt += v;
                });
                tgt += '&'
            }
            if ( $('#searchbox').val() ) {
                tgt += 'query=' + $('#searchbox').val() + '&';
            }
            if ( qinfo.id ) {
                tgt += 'question=' + qinfo.id + '&';
            }

            // set the ajax options then execute
            $.ajax({
                type: 'GET',
                url: tgt,
                contentType: "application/json; charset=utf-8",
                dataType: 'JSON',
                success: options.showresults
            });
        };
        




        // ===============================================
        // ===============================================
        //
        // now set the options from the defaults and those provided
        // and create the plugin on the target element
        // and bind everything up for starting
        //
        // ===============================================
        // ===============================================
        $.fn.graphview.options = $.extend(defaults, options);
        var options = $.fn.graphview.options;

        var obj = undefined;
        return this.each(function() {
            obj = $(this);
            options.searchonload ? options.executequery() : false;

        });

    };
    
    // define options here then they are written to above, then they become available externally
    $.fn.graphview.options = {};
    
})(jQuery);
