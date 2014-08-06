var width = 960,
    height = 800;

var color = d3.scale.category20();

/**
* Un-set the node from being fixed
* @param {object} d Node
* @this {object}
*/
function dblclick(d) {
  d3.select(this).classed('fixed', d.fixed = false);
}

/**
* Set the node to be fixed
* @param {object} d Node
* @this {object}
*/
function dragstart(d) {
  d3.select(this).classed('fixed', d.fixed = true);
}

var force = d3.layout.force()
    .charge(-120)
    .linkDistance(30)
    .size([width, height]);

var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height);

d3.json('d3artifact_tree.json', function(error, graph) {
  force
      .nodes(graph.nodes)
      .links(graph.links)
      .start();

  var link = svg.selectAll(".link")
      .data(graph.links)
      .enter().append("line")
      .attr("class", "link")
      .style("stroke-width", function(d) { return Math.sqrt(d.value); });

  var gnodes = svg.selectAll(".node")
      .data(graph.nodes)
    .enter().append("circle")
      .attr("class", "node")
      .attr("r", 5)
      .style("fill", function(d) { return color(d.group); })
      .call(force.drag);

  gnodes.append("title")
        .text(function(d) { return d.name; });


  gnodes.on('mouseover', function(d) {
    link.style('stroke-width', function(l) {
    if (d === l.source || d === l.target)
      return 4;
    else
      return 1.5;
    });
    d3.select(this).select('circle').transition()
        .duration(500)
        .attr('r', 16);

  });

  gnodes.on('mouseout', function(d) {
    link.style('stroke-width', 1.5);
    d3.select(this).select('circle').transition()
      .duration(500)
      .attr('r', 8);
    tooltip.style('visibility', 'hidden');
  });

  force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    gnodes.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  });
});

