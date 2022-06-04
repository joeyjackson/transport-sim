const url = '/api/movements';

function handleData(data) {
  console.log(data);
  const canvas = d3.select("#canvas")
    .selectAll("p")
    .data(data)
    .text(function(d) { return JSON.stringify(d); });

  canvas.enter().append("p")
    .text(function(d) { return JSON.stringify(d); });
    
  canvas.exit().remove();
}

fetch(url)
  .then(data => { return data.json(); })
  .then(res => { handleData(res.data); });
