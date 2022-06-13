const WIDTH = 300;
const HEIGHT = 300;
const HUB_RADIUS = 10;
const VEHICLE_RADIUS = 5;

let widthTransform = (d) => d;
let heightTransform = (d) => d;

function setTransforms(hubData) {
  widthTransform = d3.scaleLinear()
    .domain(d3.extent(hubData.map(d => d.pos.x)))
    .range([HUB_RADIUS * 2, WIDTH - HUB_RADIUS * 2]);

  heightTransform = d3.scaleLinear()
    .domain(d3.extent(hubData.map(d => d.pos.y)))
    .range([HUB_RADIUS * 2, HEIGHT - HUB_RADIUS * 2]);
}

function handleHubsData(data) {
  console.log(data);
  const canvas = d3.select("#canvas");
  
  canvas.selectAll(".hub")
    .data(data)
    .enter()
    .append("circle")
    .classed("hub", true)

  canvas.selectAll(".hub")
    .attr("cx", function(d) { return widthTransform(d.pos.x); })
    .attr("cy", function(d) { return heightTransform(d.pos.y); })
    .attr("r", HUB_RADIUS - 1)
    .style("stroke", "black")
    .style("stroke-width", 1)
    .style("fill", "red");
    
  canvas.selectAll(".hub")
    .data(data)
    .exit()
    .remove();
}

function handleMovData(data) {
  console.log(data);

  d3.select("#canvas")
    .selectAll(".vehicle")
    .data(data)
    .enter()
    .append("circle")
    .classed("vehicle", true)

  d3.select("#canvas")
    .selectAll(".vehicle")
    .data(data)
    .attr("cx", function(d) { return widthTransform(d.startPos.x); })
    .attr("cy", function(d) { return heightTransform(d.startPos.y); })
    .attr("r", VEHICLE_RADIUS - 1)
    .style("stroke", "black")
    .style("stroke-width", 1)
    .style("fill", "green")
    .transition()
      .duration(d => d.path_time * 1000)
      .ease(d3.easeLinear)
      .delay(d => d.timestamp * 1000)
      .attr("cx", function(d) { return widthTransform(d.endPos.x); })
      .attr("cy", function(d) { return heightTransform(d.endPos.y); })

  d3.select("#canvas")
    .selectAll(".vehicle")
    .data(data)
    .exit()
    .remove();
}

d3.select("#canvas")
  .attr("width", WIDTH)
  .attr("height", HEIGHT);

const promises = [
  fetch('/api/hubs').then(data => { return data.json(); }),
  fetch('/api/movements').then(data => { return data.json(); })
];

Promise.all(promises)
  .then(([hubsRes, movRes]) => { 
    setTransforms(hubsRes.data);
    handleHubsData(hubsRes.data); 
    handleMovData(movRes.data); 
  });
