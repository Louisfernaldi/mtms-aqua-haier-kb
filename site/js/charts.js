function svgEl(tag, attrs) {
  var n = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (var k in attrs) n.setAttribute(k, attrs[k]);
  return n;
}

function drawBarChart(containerId, rows, opts) {
  var host = document.getElementById(containerId);
  if (!host) return;
  opts = opts || {};
  var W = 760, H = opts.height || 340;
  var padL = 46, padR = 14, padT = 26, padB = 52;
  var maxV = 0;
  rows.forEach(function (r) {
    if (r[1] > maxV) maxV = r[1];
  });
  maxV = Math.ceil(maxV * 1.12);
  var svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, role: "img" });
  var n = rows.length;
  var plotW = W - padL - padR;
  var slot = plotW / n;
  var bw = Math.min(64, slot * 0.6);
  function y(v) { return padT + (1 - v / maxV) * (H - padT - padB); }
  for (var g = 0; g <= 4; g++) {
    var gv = (maxV / 4) * g;
    var gy = y(gv);
    svg.appendChild(svgEl("line", { x1: padL, y1: gy, x2: W - padR, y2: gy, stroke: "currentColor", "stroke-opacity": 0.15 }));
    var lab = svgEl("text", { x: padL - 8, y: gy + 4, "text-anchor": "end", "font-size": 11, fill: "currentColor", opacity: 0.7 });
    lab.textContent = opts.suffix ? gv + opts.suffix : gv;
    svg.appendChild(lab);
  }
  rows.forEach(function (r, i) {
    var cx = padL + slot * i + slot / 2;
    var bh = y(0) - y(r[1]);
    var rect = svgEl("rect", {
      x: cx - bw / 2, y: y(r[1]), width: bw, height: bh,
      rx: 4, fill: r[2] || "#0097d6", opacity: 0.9
    });
    svg.appendChild(rect);
    var vl = svgEl("text", { x: cx, y: y(r[1]) - 6, "text-anchor": "middle", "font-size": 12, "font-weight": 700, fill: "currentColor" });
    vl.textContent = r[1] + (opts.suffix || "");
    svg.appendChild(vl);
    var bl = svgEl("text", {
      x: cx, y: y(0) + 18, "text-anchor": "middle", "font-size": 11, fill: "currentColor", opacity: 0.85
    });
    bl.textContent = r[0];
    svg.appendChild(bl);
    if (opts.subLabel) {
      var sl = svgEl("text", { x: cx, y: y(0) + 34, "text-anchor": "middle", "font-size": 9, fill: "currentColor", opacity: 0.55 });
      sl.textContent = opts.subLabel[i] || "";
      svg.appendChild(sl);
    }
  });
  host.appendChild(svg);
}

function drawScatter(containerId, points, opts) {
  var host = document.getElementById(containerId);
  if (!host) return;
  opts = opts || {};
  var W = 760, H = opts.height || 380;
  var padL = 52, padR = 20, padT = 26, padB = 54;
  var xs = points.map(function (p) { return p[0]; });
  var ys = points.map(function (p) { return p[1]; });
  var xMin = Math.floor(Math.min.apply(null, xs) / 50) * 50 - 50;
  var xMax = Math.ceil(Math.max.apply(null, xs) / 50) * 50 + 50;
  var yMin = 0;
  var yMax = Math.ceil(Math.max.apply(null, ys) / 5) * 5 + 5;
  function sx(v) { return padL + ((v - xMin) / (xMax - xMin)) * (W - padL - padR); }
  function sy(v) { return padT + (1 - (v - yMin) / (yMax - yMin)) * (H - padT - padB); }
  var svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, role: "img" });
  for (var gx = xMin; gx <= xMax; gx += 50) {
    var lx = svgEl("line", { x1: sx(gx), y1: padT, x2: sx(gx), y2: H - padB, stroke: "currentColor", "stroke-opacity": 0.12 });
    svg.appendChild(lx);
    var tx = svgEl("text", { x: sx(gx), y: H - padB + 18, "text-anchor": "middle", "font-size": 11, fill: "currentColor", opacity: 0.7 });
    tx.textContent = gx + "L";
    svg.appendChild(tx);
  }
  for (var gy = 0; gy <= yMax; gy += 5) {
    var ly = svgEl("line", { x1: padL, y1: sy(gy), x2: W - padR, y2: sy(gy), stroke: "currentColor", "stroke-opacity": 0.12 });
    svg.appendChild(ly);
    var ty = svgEl("text", { x: padL - 8, y: sy(gy) + 4, "text-anchor": "end", "font-size": 11, fill: "currentColor", opacity: 0.7 });
    ty.textContent = gy + "jt";
    svg.appendChild(ty);
  }
  var xl = svgEl("text", { x: padL + (W - padL - padR) / 2, y: H - 12, "text-anchor": "middle", "font-size": 12, fill: "currentColor", opacity: 0.75 });
  xl.textContent = opts.xLabel || "Kapasitas (L)";
  svg.appendChild(xl);
  var yl = svgEl("text", { x: 14, y: padT + (H - padT - padB) / 2, "text-anchor": "middle", "font-size": 12, fill: "currentColor", opacity: 0.75, transform: "rotate(-90 14 " + (padT + (H - padT - padB) / 2) + ")" });
  yl.textContent = opts.yLabel || "Harga (Rp juta)";
  svg.appendChild(yl);
  points.forEach(function (p) {
    var c = svgEl("circle", { cx: sx(p[0]), cy: sy(p[1]), r: 6, fill: p[2] || "#0097d6", opacity: 0.9 });
    svg.appendChild(c);
    var t = svgEl("text", { x: sx(p[0]), y: sy(p[1]) - 10, "text-anchor": "middle", "font-size": 10, fill: "currentColor", opacity: 0.85 });
    t.textContent = p[3] || "";
    svg.appendChild(t);
  });
  host.appendChild(svg);
}
