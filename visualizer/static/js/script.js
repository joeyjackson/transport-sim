// ----------------------------------------------------------------------------
//                                   UTIL
// ----------------------------------------------------------------------------
function round(num) {
  return Math.round((num + Number.EPSILON) * 100) / 100;
}

// ----------------------------------------------------------------------------
//                                   DOM
// ----------------------------------------------------------------------------
const canvas = d3.select("#canvas");
const vehicles = canvas.append("g").attr("id", "vehicles");
const hubs = canvas.append("g").attr("id", "hubs");
const resetBtn = d3.select("#reset_btn");
const inconsistencies = d3.select("#inconsistencies")

const tooltip = d3.select("body")
  .append("div")
  .style("position", "absolute")
  .style("z-index", "10")
  .style("visibility", "hidden")
  .style("background", "#fff")
  .style("text-align", "center")
  .style("padding", "2px")
  .style("font", "12px sans-serif")
  .style("border-radius", "5px");

// ----------------------------------------------------------------------------
//                              INCONSISTENCIES
// ----------------------------------------------------------------------------
inconsistencies
  .attr("width", "100%")
  .style("margin", "1em");

function inconsistencyText(data) {
  // data = {
  //   "movement_id": int,
  //   "vehicle_id": int, 
  //   "timestamp": int,
  //   "inconsistency_type": string
  // }

  return "MOVEMENT INCONSISTENCY DETECTED: " + JSON.stringify(data);
}

function handleInconsistencyData(data) {
  inconsistencies.selectAll("div")
    .data(data)
    .join("div")
      .style("background-color", "#FF3131")
      .style("border-radius", "5px")
      .style("border", "2px solid black")
      .style("padding", "5px")
      .style("margin", "5px")
      .text(inconsistencyText);
}

// ----------------------------------------------------------------------------
//                                  CANVAS
// ----------------------------------------------------------------------------

const WIDTH = 300;
const HEIGHT = 300;
const HUB_RADIUS = 10;
const VEHICLE_RADIUS = 5;

canvas
  .attr("width", WIDTH)
  .attr("height", HEIGHT);

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
  hubs.selectAll(".hub")
    .data(data)
    .join(enter => enter.append("circle").classed("hub", true))
      .attr("cx", (d) => widthTransform(d.pos.x))
      .attr("cy", (d) => heightTransform(d.pos.y))
      .attr("r", HUB_RADIUS - 1)
      .style("stroke", "black")
      .style("stroke-width", 1)
      .style("fill", "red")
      .on("mouseover", (event, d) => { 
        tooltip.text(d.label + " (" + round(d.pos.x) + ", " + round(d.pos.y) + ")"); 
        return tooltip.style("visibility", "visible"); 
      })
      .on("mousemove", (event) => tooltip.style("top", (event.pageY - 10) + "px").style("left", (event.pageX + 10) + "px"))
      .on("mouseout", (event) => tooltip.style("visibility", "hidden"));
}

function handleMovData(data) {
  // Color vehicles based on their vehicle_id
  const colorRange = d3.scaleLinear()
    .domain(d3.extent(data.map(d => d.vehicle_id)))
    .range(["yellow", "blue"]);

  // Cancel any pending transitions
  vehicles.selectAll(".vehicle").interrupt();

  vehicles.selectAll(".vehicle").data(data)
    .join(enter => enter.append("circle").classed("vehicle", true))
      .attr("cx", (d) => widthTransform(d.startPos.x))
      .attr("cy", (d) => heightTransform(d.startPos.y))
      .attr("r", VEHICLE_RADIUS - 1)
      .style("stroke", "black")
      .style("stroke-width", 1)
      .style("fill", (d) => colorRange(d.vehicle_id))
      .transition()
        .duration(d => d.path_time * 1000)
        .ease(d3.easeLinear)
        .delay(d => d.timestamp * 1000)
        .attr("cx", (d) => widthTransform(d.endPos.x))
        .attr("cy", (d) => heightTransform(d.endPos.y));
}

function init() {
  resetBtn.attr('disabled', true);

  const promises = [
    fetch('/api/inconsistencies').then(data => data.json()),
    fetch('/api/hubs').then(data => data.json()),
    fetch('/api/movements').then(data => data.json())
  ];
  
  Promise.all(promises)
    .then(([inconsistencyRes, hubsRes, movRes]) => { 
      handleInconsistencyData(inconsistencyRes.data)
      setTransforms(hubsRes.data);
      handleMovData(movRes.data); 
      handleHubsData(hubsRes.data); 
      resetBtn.attr('disabled', null);
    });
}

init();
resetBtn.on('click', init);


