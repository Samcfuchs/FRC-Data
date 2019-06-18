const HEIGHT = 200
const WIDTH = 800

const margin = { top:20, bottom:40, left:40, right:20 }

const ALPHA = 0.5
const BLUE = "#1f75b7"
const RED = "#e9373d"

const FILENAME = "../data/2019_end_ratings.csv"

var data = 0

function normal(mean, variance) {
    // Precompute portion of the function that does not depend on x
    var predicate = 1 / Math.sqrt(variance * 2 * Math.PI);

    return function(x) {
        return predicate * Math.exp( -Math.pow(x - mean, 2) / (2 * variance));
    };
};

function curve(row) {
    if (row === undefined) { return []; }

    mu = Number(row.mu)
    sigma = Number(row.sigma)

    f = normal(mu, sigma);

    lower = d3.max([mu - 4*sigma, x_scale.domain()[0]]);
    upper = d3.min([mu + 4*sigma, x_scale.domain()[1]]);
    interval = .01

    x = d3.range(lower, upper, interval);
    y = x.map(f);

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

    svg.append('g')
        .call(d3.axisLeft(y_scale))
        .attr("transform", `translate(${x_scale.range()[0]},0)`)
        .attr("class", "axis");
}

// Create axis scales
x_scale = d3.scaleLinear().range([margin.left, WIDTH-margin.right]);
y_scale = d3.scaleLinear().range([HEIGHT-margin.bottom, margin.top]);

var mu = function(d) { return +d['mu']; }
var sigma = function(d) { return +d['sigma']; }
var rank = function(d) { return +d['rank']; }

isImported = d3.csv(FILENAME)

isImported.then( function(d) {
    data = d
    x_scale.domain([
        d3.min(data, mu) - d3.max(data, sigma),
        d3.max(data, mu) + d3.max(data, sigma)
    ]);

    y_scale.domain([0, 0.5]);

    drawAxes(x_scale, y_scale)
});

blue_c = 0
red_c = 0
function update() {
    blue = d3.select("#blue").node().value;
    red = d3.select("#red").node().value;

    blue_rows = data.filter( obj => { return obj.Team === blue; });
    red_rows = data.filter( obj => { return obj.Team === red; });

    if (blue_rows.length + red_rows.length > 0) {
        svg.selectAll("path.curve").remove();
        
        oblue = blue_rows[0]
        ored = red_rows[0]

        blue_c = curve(oblue)
        red_c = curve(ored)

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
}

