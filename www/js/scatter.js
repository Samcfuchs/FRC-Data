"use strict";
(function() {

const HEIGHT = 600
const WIDTH = 800

const margin = { top:20, bottom:40, left:40, right:20 }

const RADIUS = 4
const COLOR = 'black'
const ALPHA = 0.1

const FILENAME = "../data/2019_end_ratings.csv"

var data = 0

var main = d3.select("#scatter").append("svg")
    .attr("width", WIDTH)
    .attr("height", HEIGHT)
    .attr("id", "scatter")

var tooltip_div = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

function drawAxes(x_scale, y_scale) {
    // Making axes & labels
    main.append("g")
        .call(d3.axisBottom(x_scale))
        .attr("transform", `translate(0, ${y_scale.range()[0]})`)
        .attr("class", "axis");

    main.append("g")
        .call(d3.axisLeft(y_scale))
        .attr("transform", `translate(${x_scale.range()[0]},0)`)
        .attr("class", "axis");
         
    // Add axis labels
    main.append("text").text('μ')
        .attr("transform", `translate(${WIDTH/2}, ${HEIGHT-.25*margin.bottom})`)
        .attr('font-size', '20px')
        .attr("class", "axislabel");

    main.append("text").text('σ')
        .attr("transform", `translate(${.5*margin.left}, ${HEIGHT/2}) rotate(-90)`)
        .attr('font-size', '20px')
        .attr('font-family', 'italic')
        .attr("class", "axislabel");
}

function round(d) {
    return Number(Math.round(d+'e'+2)+'e-'+2);
}

function drawPoint(row) {
    if (row.point != undefined) {
        row.point["_groups"][0][0].remove();
    }

    let point = main.append('circle')
    row.point = point
    row.point.attr('cx', x_scale(mu(row)))
        .attr('cy', y_scale(sigma(row)))
        .attr('r', RADIUS)
        .attr('fill', COLOR)
        .attr('fill-opacity', ALPHA)

        .on("mouseover", function(d) {
            tooltip_div.transition()
                .duration(100)
                .style("opacity", .60);
            tooltip_div.html(
                "team: <b>" + row.Team + "</b></br>" +
                "mu: <b>" + round(row.mu) + "</b></br>" +
                "sigma: <b>" + round(row.sigma) + "</b></br>"
            )
            .style("left", (d3.event.pageX + 15) + "px")
            .style("top", (d3.event.pageY + 10) + "px");

            row.point.attr("stroke", "black");
        })
        // Make the tooltip follow the mouse
        .on("mousemove", function(d) {
            tooltip_div.style("left", (d3.event.pageX + 15) + "px");
            tooltip_div.style("top", (d3.event.pageY + 10) + "px");
        })
        .on("mouseleave", function(d) {
            row.point.attr("stroke", "none");
            tooltip_div.transition()
                .duration(100)
                .style("opacity", 0);
        });
}

// Create axis scales
let x_scale = d3.scaleLinear().range([margin.left, WIDTH-margin.right]);
let y_scale = d3.scaleLinear().range([HEIGHT-margin.bottom, margin.top]);

let mu = function(d) { return +d['mu']; }
let sigma = function(d) { return +d['sigma']; }

let isImported = d3.csv(FILENAME)

isImported.then( function(d) {
    data = d

    x_scale.domain([ 0, d3.max(data,mu) ]);
    y_scale.domain([ 0, d3.max(data,sigma) ]);

    drawAxes(x_scale, y_scale);

    data.forEach(row => {
        drawPoint(row);
    });
});

function update() {
    // Reset colors
    data.forEach( row => { 
        row.point.attr('fill', COLOR)
            .attr('fill-opacity', ALPHA);
    });

    let team = d3.select("#team").node().value;
    let rows = data.filter( obj => { return obj.Team === team; } );
    console.log(rows)

    if (rows.length > 0) {
        drawPoint(rows[0])
        rows[0].point.attr('fill', 'coral')
            .attr('fill-opacity', 1.0);
        
        d3.select('#rank').text(round(rows[0].Rank));
        d3.select('#mu').text(round(rows[0].mu));
        d3.select('#sigma').text(round(rows[0].sigma));
    }

}

d3.select("input#team")["_groups"][0][0].onkeyup = update;
})();
