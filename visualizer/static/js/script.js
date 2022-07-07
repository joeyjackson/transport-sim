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
const vehiclesGroup = canvas.append("g").attr("id", "vehicles");
const hubsGroup = canvas.append("g").attr("id", "hubs");
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

const EXTRA_RIGHT_PAD = 20;
const WIDTH = 800 + EXTRA_RIGHT_PAD;
const HEIGHT = 480;
const HUB_RADIUS = 8;
const VEHICLE_RADIUS = 5;

canvas
  .attr("width", WIDTH)
  .attr("height", HEIGHT);

let widthTransform = (d) => d;
let heightTransform = (d) => d;

function setTransforms(hubData) {
  widthTransform = d3.scaleLinear()
    .domain(d3.extent(hubData.map(d => d.pos.x)))
    .range([HUB_RADIUS * 2, WIDTH - HUB_RADIUS * 2 - EXTRA_RIGHT_PAD]);

  heightTransform = d3.scaleLinear()
    .domain(d3.extent(hubData.map(d => d.pos.y)))
    .range([HUB_RADIUS * 2, HEIGHT - HUB_RADIUS * 2 - EXTRA_RIGHT_PAD]);
}

function handleHubsData(data) {
  hubsGroup.selectAll(".hub")
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
  vehiclesGroup.selectAll(".vehicle").interrupt();
  vehiclesGroup.selectAll(".vehicle_label").interrupt();

  vehiclesGroup.selectAll(".vehicle").data(data)
    .join(
      enter => {
        const root = enter.append("g").classed("vehicle", true);
        root.append("circle")
          .attr("r", VEHICLE_RADIUS - 1)
          .style("stroke", "black")
          .style("stroke-width", 1)
          .style("fill", (d) => colorRange(d.vehicle_id));
        root.append("text")
          .classed("vehicle_label", true)
          .attr("dx", "6px")
          .style("font-size", "10px")
          .text((d) => d.vehicle)
          .style("opacity", 0)
          .transition()
            .duration(d => d.path_time * 1000 / 2)
            .ease(d3.easeExpOut)
            .delay(d => d.timestamp * 1000)
            .style("opacity", 1)
          .transition()
            .duration(d => d.path_time * 1000 / 2)
            .ease(d3.easeExpIn)
            .style("opacity", 0)
        return root;
      },
      update => {
        update.select("circle")
          .style("fill", (d) => colorRange(d.vehicle_id));
        update.select("text")
          .text((d) => d.vehicle)
          .style("opacity", 0)
          .transition()
            .duration(d => d.path_time * 1000 / 2)
            .ease(d3.easeExpOut)
            .delay(d => d.timestamp * 1000)
            .style("opacity", 1)
          .transition()
            .duration(d => d.path_time * 1000 / 2)
            .ease(d3.easeExpIn)
            .style("opacity", 0)
        return update;
      }
    )
      .attr("transform", (d) => "translate(" + widthTransform(d.startPos.x) + "," + heightTransform(d.startPos.y) + ")")
      .transition()
        .duration(d => d.path_time * 1000)
        .ease(d3.easeLinear)
        .delay(d => d.timestamp * 1000)
        .attr("transform", (d) => "translate(" + widthTransform(d.endPos.x) + "," + heightTransform(d.endPos.y) + ")");
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


