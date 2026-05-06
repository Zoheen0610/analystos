from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from app.services.graph import (
    get_graph_state, add_summary_node, get_last_node_id,
    compare_sessions, get_all_summary_nodes, workflow_graph
)
import json

router = APIRouter()


@router.get("/graph")
async def get_graph():
    return JSONResponse(content=get_graph_state())


@router.post("/graph/summarize")
async def summarize_session():
    parent = get_last_node_id()
    if not parent:
        raise HTTPException(status_code=404, detail="No workflow started yet")
    result = add_summary_node(parent)
    return JSONResponse(content=result)


@router.get("/graph/summaries")
async def list_summaries():
    summaries = get_all_summary_nodes()
    if not summaries:
        raise HTTPException(status_code=404, detail="No summaries yet")
    return JSONResponse(content={"summaries": summaries})


@router.get("/graph/compare/{node_id_a}/{node_id_b}")
async def compare(node_id_a: str, node_id_b: str):
    result = compare_sessions(node_id_a, node_id_b)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return JSONResponse(content=result)


@router.get("/graph/visualize", response_class=HTMLResponse)
async def visualize_graph():
    if not workflow_graph.nodes:
        raise HTTPException(status_code=404, detail="No graph data yet")

    graph_data = get_graph_state()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>AnalystOS — Workflow Mind Map</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;700;800&display=swap');
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #080b14;
    font-family: 'DM Mono', monospace;
    overflow: hidden;
    width: 100vw; height: 100vh;
  }}
  #canvas {{ width: 100%; height: 100%; }}
  body::before {{
    content: '';
    position: fixed; inset: 0;
    background-image:
      linear-gradient(rgba(99,179,237,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(99,179,237,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
  }}
  .node-group {{ cursor: grab; }}
  .node-group:active {{ cursor: grabbing; }}
  .node-circle {{ transition: filter 0.25s ease, opacity 0.25s ease; filter: drop-shadow(0 0 12px var(--glow)); }}
  .node-label {{ font-family: 'DM Mono', monospace; font-size: 10px; fill: #e2e8f0; pointer-events: none; text-anchor: middle; transition: opacity 0.25s ease; }}
  .node-sublabel {{ font-family: 'DM Mono', monospace; font-size: 8px; fill: #94a3b8; pointer-events: none; text-anchor: middle; transition: opacity 0.25s ease; }}
  .link {{ stroke: #1e3a5f; stroke-width: 1.5; fill: none; transition: opacity 0.25s ease, stroke 0.25s ease; }}
  .link.highlighted {{ stroke: #63b3ed; stroke-width: 2.5; }}
  .link.faded {{ opacity: 0.08; }}
  .node-group.faded .node-circle {{ opacity: 0.12; }}
  .node-group.faded .node-label,
  .node-group.faded .node-sublabel {{ opacity: 0.08; }}
  #tooltip {{
    position: fixed;
    background: #0d1526;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 12px 16px;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #94a3b8;
    max-width: 300px;
    line-height: 1.6;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s ease;
    z-index: 100;
    box-shadow: 0 0 30px rgba(99,179,237,0.08);
  }}
  #tooltip.visible {{ opacity: 1; }}
  #tooltip .tip-title {{ font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 700; color: #e2e8f0; margin-bottom: 6px; }}
  #tooltip .tip-row {{ display: flex; gap: 8px; margin-top: 3px; }}
  #tooltip .tip-key {{ color: #4a6fa5; min-width: 80px; }}
  #tooltip .tip-val {{ color: #a0c4e8; word-break: break-all; }}
  #legend {{ position: fixed; bottom: 24px; left: 24px; display: flex; flex-direction: column; gap: 8px; }}
  .legend-item {{ display: flex; align-items: center; gap: 10px; font-family: 'DM Mono', monospace; font-size: 10px; color: #64748b; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
  #title {{ position: fixed; top: 24px; left: 28px; font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 800; color: #e2e8f0; letter-spacing: -0.5px; }}
  #title span {{ color: #63b3ed; }}
  #hint {{ position: fixed; top: 52px; left: 29px; font-family: 'DM Mono', monospace; font-size: 9px; color: #334155; letter-spacing: 0.5px; }}
  #node-count {{ position: fixed; top: 24px; right: 28px; font-family: 'DM Mono', monospace; font-size: 9px; color: #334155; text-align: right; line-height: 1.8; }}
</style>
</head>
<body>
<div id="title">Analyst<span>OS</span> — Workflow Mind Map</div>
<div id="hint">hover to inspect · drag to rearrange · scroll to zoom</div>
<div id="node-count"></div>
<svg id="canvas"></svg>
<div id="tooltip"></div>
<div id="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#3b82f6;box-shadow:0 0 8px #3b82f6"></div>Dataset</div>
  <div class="legend-item"><div class="legend-dot" style="background:#22c55e;box-shadow:0 0 8px #22c55e"></div>Profiling</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f59e0b;box-shadow:0 0 8px #f59e0b"></div>Session Summary</div>
</div>
<script>
const rawData = {json.dumps(graph_data)};

// stats
document.getElementById('node-count').innerHTML =
  `${{rawData.total_nodes}} nodes · ${{rawData.total_edges}} edges`;

const colorMap = {{ dataset:'#3b82f6', profiling:'#22c55e', session_summary:'#f59e0b' }};
const sizeMap  = {{ dataset: 28, profiling: 22, session_summary: 20 }};

const nodes = rawData.nodes.map(n => ({{ ...n, r: sizeMap[n.type] || 18 }}));
const links = rawData.edges.map(e => ({{ source: e.from, target: e.to }}));

const svg = d3.select('#canvas');
const W = window.innerWidth, H = window.innerHeight;
svg.attr('viewBox', `0 0 ${{W}} ${{H}}`);
const g = svg.append('g');

svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => g.attr('transform', e.transform)));

svg.append('defs').append('marker')
  .attr('id', 'arrow').attr('viewBox', '0 -4 8 8')
  .attr('refX', 8).attr('refY', 0)
  .attr('markerWidth', 6).attr('markerHeight', 6)
  .attr('orient', 'auto')
  .append('path').attr('d', 'M0,-4L8,0L0,4').attr('fill', '#1e3a5f');

const typeDepth = {{ dataset: 0, profiling: 1, session_summary: 2 }};

const simulation = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(links).id(d => d.id).distance(140).strength(0.9))
  .force('charge', d3.forceManyBody().strength(-500))
  .force('x', d3.forceX(W / 2).strength(0.04))
  .force('y', d3.forceY(d => 150 + (typeDepth[d.type] ?? 1) * 220).strength(0.7))
  .force('collision', d3.forceCollide(d => d.r + 45));

const link = g.append('g').selectAll('path').data(links).join('path')
  .attr('class', 'link').attr('marker-end', 'url(#arrow)');

const nodeGroup = g.append('g').selectAll('g').data(nodes).join('g')
  .attr('class', 'node-group')
  .call(d3.drag()
    .on('start', (e,d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }})
    .on('drag',  (e,d) => {{ d.fx=e.x; d.fy=e.y; }})
    .on('end',   (e,d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; }})
  );

// glow ring
nodeGroup.append('circle')
  .attr('r', d => d.r + 7).attr('fill', 'none')
  .attr('stroke', d => colorMap[d.type] || '#64748b')
  .attr('stroke-width', 0.5).attr('opacity', 0.25);

// pulse ring (animation)
nodeGroup.append('circle')
  .attr('r', d => d.r + 7).attr('fill', 'none')
  .attr('stroke', d => colorMap[d.type] || '#64748b')
  .attr('stroke-width', 1).attr('opacity', 0)
  .each(function(d, i) {{
    const el = d3.select(this);
    function pulse() {{
      el.attr('r', d.r + 7).attr('opacity', 0.4)
        .transition().duration(1800).ease(d3.easeCubicOut)
        .attr('r', d.r + 22).attr('opacity', 0)
        .on('end', pulse);
    }}
    setTimeout(pulse, i * 300);
  }});

// main circle
nodeGroup.append('circle')
  .attr('class', 'node-circle')
  .attr('r', d => d.r)
  .attr('fill', d => colorMap[d.type] || '#64748b')
  .attr('fill-opacity', 0.15)
  .attr('stroke', d => colorMap[d.type] || '#64748b')
  .attr('stroke-width', 2)
  .style('--glow', d => colorMap[d.type] || '#64748b');

// labels
nodeGroup.append('text').attr('class', 'node-label').attr('dy', -6)
  .text(d => {{
    if (d.type === 'dataset') return d.filename || d.id;
    if (d.type === 'profiling') return 'Profiling';
    if (d.type === 'session_summary') return d.date || 'Summary';
    return d.id;
  }});

nodeGroup.append('text').attr('class', 'node-sublabel').attr('dy', 8)
  .text(d => {{
    if (d.type === 'dataset') return `${{d.rows || ''}} rows · ${{d.columns || ''}} cols`;
    if (d.type === 'profiling') return `${{(d.missing_columns||[]).length}} missing · ${{(d.skewed_columns||[]).length}} skewed`;
    if (d.type === 'session_summary') return `${{d.questions_count || 0}} questions`;
    return '';
  }});

// tooltip
const tooltip = document.getElementById('tooltip');

function buildTooltip(d) {{
  let rows = '';
  if (d.type === 'dataset') {{
    rows = `
      <div class="tip-row"><span class="tip-key">file</span><span class="tip-val">${{d.filename}}</span></div>
      <div class="tip-row"><span class="tip-key">rows</span><span class="tip-val">${{d.rows}}</span></div>
      <div class="tip-row"><span class="tip-key">columns</span><span class="tip-val">${{d.columns}}</span></div>
      <div class="tip-row"><span class="tip-key">uploaded</span><span class="tip-val">${{(d.timestamp||'').slice(0,10)}}</span></div>`;
  }} else if (d.type === 'profiling') {{
    rows = `
      <div class="tip-row"><span class="tip-key">missing</span><span class="tip-val">${{(d.missing_columns||[]).join(', ')||'none'}}</span></div>
      <div class="tip-row"><span class="tip-key">skewed</span><span class="tip-val">${{(d.skewed_columns||[]).join(', ')||'none'}}</span></div>
      <div class="tip-row"><span class="tip-key">outliers</span><span class="tip-val">${{(d.outlier_columns||[]).join(', ')||'none'}}</span></div>`;
  }} else if (d.type === 'session_summary') {{
    const s = (d.summary||'').slice(0,200) + ((d.summary||'').length>200?'…':'');
    rows = `
      <div class="tip-row"><span class="tip-key">date</span><span class="tip-val">${{d.date}}</span></div>
      <div class="tip-row"><span class="tip-key">questions</span><span class="tip-val">${{d.questions_count}}</span></div>
      <div style="margin-top:8px;font-size:9px;color:#64748b;line-height:1.6">${{s}}</div>`;
  }}
  return `<div class="tip-title">${{d.type.replace(/_/g,' ').toUpperCase()}}</div>${{rows}}`;
}}

nodeGroup
  .on('mouseenter', function(e, d) {{
    const connectedIds = new Set([d.id]);
    links.forEach(l => {{
      const s = typeof l.source==='object' ? l.source.id : l.source;
      const t = typeof l.target==='object' ? l.target.id : l.target;
      if (s===d.id) connectedIds.add(t);
      if (t===d.id) connectedIds.add(s);
    }});
    d3.selectAll('.node-group').classed('faded', nd => !connectedIds.has(nd.id));
    d3.selectAll('.link')
      .classed('faded', l => {{
        const s = typeof l.source==='object'?l.source.id:l.source;
        const t = typeof l.target==='object'?l.target.id:l.target;
        return !(connectedIds.has(s) && connectedIds.has(t));
      }})
      .classed('highlighted', l => {{
        const s = typeof l.source==='object'?l.source.id:l.source;
        const t = typeof l.target==='object'?l.target.id:l.target;
        return connectedIds.has(s) && connectedIds.has(t);
      }});
    tooltip.innerHTML = buildTooltip(d);
    tooltip.classList.add('visible');
  }})
  .on('mousemove', e => {{
    const tx = e.clientX + 18;
    const ty = Math.min(e.clientY - 10, window.innerHeight - 220);
    tooltip.style.left = tx + 'px';
    tooltip.style.top  = ty + 'px';
  }})
  .on('mouseleave', () => {{
    d3.selectAll('.node-group').classed('faded', false);
    d3.selectAll('.link').classed('faded', false).classed('highlighted', false);
    tooltip.classList.remove('visible');
  }});

simulation.on('tick', () => {{
  link.attr('d', d => {{
    const dx = d.target.x - d.source.x;
    const dy = d.target.y - d.source.y;
    const dist = Math.sqrt(dx*dx + dy*dy) || 1;
    const x1 = d.source.x + (dx/dist)*(d.source.r+2);
    const y1 = d.source.y + (dy/dist)*(d.source.r+2);
    const x2 = d.target.x - (dx/dist)*(d.target.r+10);
    const y2 = d.target.y - (dy/dist)*(d.target.r+10);
    const mx = (x1+x2)/2 - dy*0.15;
    const my = (y1+y2)/2 + dx*0.15;
    return `M${{x1}},${{y1}} Q${{mx}},${{my}} ${{x2}},${{y2}}`;
  }});
  nodeGroup.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
}});

window.addEventListener('resize', () =>
  svg.attr('viewBox', `0 0 ${{window.innerWidth}} ${{window.innerHeight}}`)
);
</script>
</body>
</html>"""
    return HTMLResponse(content=html)