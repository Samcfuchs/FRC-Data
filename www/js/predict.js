"use strict";
(function() {

const HEIGHT = 200
const WIDTH = 800

const margin = { top:20, bottom:20, left:20, right:20 }

const BLUE = "#1f75b7"
const RED = "#e9373d"

const FILENAME = "../data/2019_end_ratings.csv"

const RESOLUTION = 0.1

let data = 0

function normal(mean, variance) {
    // Precompute portion of the function that does not depend on x
    var predicate = 1 / Math.sqrt(variance * 2 * Math.PI);

    return function(x) {
        return predicate * Math.exp( -Math.pow(x - mean, 2) / (2 * variance));
    };
};

function curve(row) {
    if (row === undefined) { return []; }

    let mu = Number(row.mu)
    let sigma = Number(row.sigma)

    let f = normal(mu, sigma);

    let lower = d3.max([mu - 4*sigma, x_scale.domain()[0]]);
    let upper = d3.min([mu + 4*sigma, x_scale.domain()[1]]);

    let x = d3.range(lower, upper, RESOLUTION);
    let y = x.map(f);

    return d3.zip(x,y);
}

var line = d3.line()
  .x(function(d) { return x_scale(d[0]);}) // apply the x scale to the x data
  .y(function(d) { return y_scale(d[1]);}); // apply the y scale to the y data

var svg = d3.select("#predict").append("svg")
    .attr("width", WIDTH)
    .attr("height", HEIGHT)
    .attr("id", "predict");

function drawAxes(x_scale, y_scale) {
    svg.append('g')
        .call(d3.axisBottom(x_scale))
        .attr("transform", `translate(0, ${y_scale.range()[0]})`)
        .attr("class", "axis");
}

// Create axis scales
let x_scale = d3.scaleLinear().range([margin.left, WIDTH-margin.right]);
let y_scale = d3.scaleLinear().range([HEIGHT-margin.bottom, margin.top]);

let mu = function(d) { return +d['mu']; }
let sigma = function(d) { return +d['sigma']; }
let rank = function(d) { return +d['rank']; }

let isImported = d3.csv(FILENAME)

isImported.then( function(d) {
    data = d
    x_scale.domain([
        d3.min(data, mu) - d3.max(data, sigma),
        d3.max(data, mu) + d3.max(data, sigma)
    ]);

    y_scale.domain([0, 0.4]);

    drawAxes(x_scale, y_scale)
});

function update() {
    let blue = d3.select("#blue").node().value;
    let red = d3.select("#red").node().value;

    let blue_rows = data.filter( obj => { return obj.Team === blue; });
    let red_rows = data.filter( obj => { return obj.Team === red; });

    svg.selectAll("path.curve").remove();
    
    let oblue = blue_rows[0]
    let ored = red_rows[0]

    let blue_c = curve(oblue)
    let red_c = curve(ored)

    svg.append("path")
        .attr('class', 'curve')
        .attr('d', line(blue_c))
        .style('stroke', BLUE)
        .style('fill', BLUE)

    svg.append("path")
        .attr('class', 'curve')
        .attr('d', line(red_c))
        .style('stroke', RED)
        .style('fill', RED)
}

// Trigger an update on any input in boxes
d3.select("input#blue")["_groups"][0][0].onkeyup = update;
d3.select("input#red")["_groups"][0][0].onkeyup = update;
})();
