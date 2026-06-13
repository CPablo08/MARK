"""Built-in HTML templates for the Visualize center panel."""

from __future__ import annotations

import re


def _parse_money(text: str) -> float | None:
    m = re.search(r"\$?\s*([\d,]+(?:\.\d+)?)\s*(?:/|per\s*)?month", text, re.I)
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r"save\s*\$?\s*([\d,]+(?:\.\d+)?)", text, re.I)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _parse_years(text: str) -> int | None:
    m = re.search(r"(\d+)\s*years?", text, re.I)
    return int(m.group(1)) if m else None


def _parse_rate(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*percent", text, re.I)
    return float(m.group(1)) if m else None


def parse_savings_defaults(user_message: str) -> dict[str, float | int]:
    monthly = _parse_money(user_message) or 10_000
    years = _parse_years(user_message) or 10
    rate_val = _parse_rate(user_message)
    rate = rate_val if rate_val is not None else 5.0
    return {"monthly": monthly, "years": years, "rate": rate}


def is_savings_calculator_request(message: str) -> bool:
    text = message.strip()
    if not text:
        return False
    has_calc = bool(re.search(r"\b(calculator|interactive|sliders?|adjust)\b", text, re.I))
    has_savings = bool(
        re.search(
            r"\b(savings?|save\s*\$|monthly|interest rate|time period|compound|invest)\b",
            text,
            re.I,
        )
    )
    has_viz = bool(re.search(r"\b(visuali[sz]e|chart|projection|scenario)\b", text, re.I))
    if (has_calc and has_savings) or (
        has_viz and has_savings and bool(re.search(r"\b(interactive|adjust|rate|amount|period)\b", text, re.I))
    ):
        return True
    # "Visualize saving $10k/month for 10 years" → interactive calculator, not Ops task
    if has_viz and (_parse_money(text) is not None or _parse_years(text) is not None):
        return bool(re.search(r"\b(save|saving|month|year)\b", text, re.I))
    return False


_HTML_VIZ = re.compile(
    r"\b("
    r"(another|new|separate|second|different|next)\s+(\w+\s+){0,4}(html|page|calculator|widget|tool|visuali[sz]ation)|"
    r"(create|make|generate|build|write|open)\s+(\w+\s+){0,5}(html|page|calculator|widget|visuali[sz]ation)|"
    r"html\s+(file|page|calculator|tool|widget|app)|"
    r"visuali[sz]ed\s+skill|visuali[sz]e\s+skill|using\s+(the\s+)?visuali[sz]"
    r")\b",
    re.I,
)


def is_html_visualize_request(message: str) -> bool:
    text = message.strip()
    if not text:
        return False
    if is_savings_calculator_request(text):
        return True
    return bool(_HTML_VIZ.search(text))


def is_newtons_cradle_request(message: str) -> bool:
    return bool(
        re.search(r"\b(newton'?s?\s*cradle|newtons?\s+cradle)\b", message.strip(), re.I)
    )


def is_interactive_visualize_request(message: str) -> bool:
    text = message.strip()
    if is_newtons_cradle_request(text):
        return True
    return bool(
        re.search(r"\b(visuali[sz]e|interactive|show me)\b", text, re.I)
        and re.search(
            r"\b(cradle|pendulum|simulation|demo|physics|chart|graph|calculator)\b", text, re.I
        )
    )


def newtons_cradle_html() -> str:
    """Claude-style interactive artifact — self-contained physics demo."""
    return r"""<style>
  .nc { max-width: 720px; margin: 0 auto; font-family: system-ui, sans-serif; color: #e5e7eb; }
  .nc h1 { font-size: 1.05rem; font-weight: 500; margin: 0 0 0.25rem; }
  .nc p { font-size: 0.72rem; color: #9ca3af; margin: 0 0 0.75rem; }
  canvas { width: 100%; height: 280px; display: block; background: #0a0b0d;
    border: 1px solid rgba(74,109,148,0.35); border-radius: 0.65rem; cursor: pointer; }
  .nc button { margin-top: 0.65rem; padding: 0.45rem 0.9rem; border-radius: 0.45rem;
    border: 1px solid rgba(74,109,148,0.45); background: rgba(58,86,122,0.2);
    color: #c5d4e8; font-size: 0.75rem; cursor: pointer; }
  .nc button:hover { background: rgba(58,86,122,0.35); }
</style>
<div class="nc">
  <h1>Newton's Cradle</h1>
  <p>Click or drag the left ball, then release. Watch momentum transfer.</p>
  <canvas id="c" width="640" height="280"></canvas>
  <button type="button" id="reset">Reset</button>
</div>
<script>
(function(){
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');
  const N = 5;
  const L = 120;
  const g = 0.35;
  const balls = [];
  let drag = -1;
  for (let i = 0; i < N; i++) {
    balls.push({ x: 0, y: 0, vx: 0, vy: 0, ox: 0, oy: 0, angle: 0, avel: 0 });
  }
  function layout() {
    const w = canvas.width, h = canvas.height;
    const cx = w / 2, gap = 34, start = cx - ((N - 1) * gap) / 2;
    for (let i = 0; i < N; i++) {
      balls[i].ox = start + i * gap;
      balls[i].oy = h * 0.22;
    }
  }
  layout();
  function step() {
    const w = canvas.width, h = canvas.height;
    for (let i = 0; i < N; i++) {
      const b = balls[i];
      b.avel += (-g / L) * Math.sin(b.angle) * 0.016;
      b.avel *= 0.9992;
      b.angle += b.avel;
      b.x = b.ox + Math.sin(b.angle) * L;
      b.y = b.oy + Math.cos(b.angle) * L;
    }
    for (let i = 0; i < N - 1; i++) {
      const a = balls[i], b = balls[i + 1];
      const dx = b.x - a.x, dy = b.y - a.y, dist = Math.hypot(dx, dy);
      if (dist < 30) {
        const tmp = a.avel;
        a.avel = b.avel * 0.98;
        b.avel = tmp * 0.98;
      }
    }
    ctx.clearRect(0, 0, w, h);
    for (let i = 0; i < N; i++) {
      const b = balls[i];
      ctx.strokeStyle = 'rgba(120,150,180,0.5)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(b.ox, b.oy);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
      const g = ctx.createRadialGradient(b.x - 4, b.y - 4, 2, b.x, b.y, 16);
      g.addColorStop(0, '#9cb4d0');
      g.addColorStop(1, '#3d5570');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(b.x, b.y, 15, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(step);
  }
  step();
  function hit(e) {
    const r = canvas.getBoundingClientRect();
    const x = (e.clientX - r.left) * (canvas.width / r.width);
    const y = (e.clientY - r.top) * (canvas.height / r.height);
    for (let i = 0; i < N; i++) {
      if (Math.hypot(x - balls[i].x, y - balls[i].y) < 22) return i;
    }
    return -1;
  }
  canvas.addEventListener('pointerdown', e => { drag = hit(e); });
  canvas.addEventListener('pointermove', e => {
    if (drag < 0) return;
    const r = canvas.getBoundingClientRect();
    const x = (e.clientX - r.left) * (canvas.width / r.width);
    const y = (e.clientY - r.top) * (canvas.height / r.height);
    const b = balls[drag];
    const dx = x - b.ox, dy = y - b.oy;
    b.angle = Math.atan2(dx, dy);
    b.avel = 0;
  });
  canvas.addEventListener('pointerup', () => {
    if (drag >= 0) balls[drag].avel = balls[drag].angle * 0.12;
    drag = -1;
  });
  document.getElementById('reset').onclick = () => {
    for (let i = 0; i < N; i++) { balls[i].angle = 0; balls[i].avel = 0; }
    layout();
  };
})();
</script>"""


async def generate_custom_visualization_html(
    user_message: str,
    *,
    context: str = "",
) -> tuple[str, str]:
    """LLM-generated HTML fragment for the Visualize center panel."""
    from mark_agents.llm import get_llm

    llm = get_llm("commander", temperature=0.25)
    prompt = f"""Build one self-contained HTML fragment (inline CSS + JS) for this request.
Use dark theme (background #0a0b0d, light text). Make it interactive when appropriate (sliders, inputs).
Chart.js from https://cdn.jsdelivr.net/npm/chart.js is allowed. No external file writes — runs in an iframe.
Return ONLY raw HTML (no markdown fences, no explanation).

Request: {user_message[:1200]}
{f"Context: {context[:600]}" if context else ""}"""
    result = await llm.ainvoke(prompt)
    raw = (result.content if hasattr(result, "content") else str(result)).strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw)
    title_m = re.search(r"<h1[^>]*>([^<]+)</h1>", raw, re.I)
    title = title_m.group(1).strip() if title_m else "Custom visualization"
    return title[:80], raw


def savings_calculator_html(
    *,
    monthly: float = 10_000,
    years: int = 10,
    rate: float = 5.0,
    initial: float = 0,
) -> str:
    """Interactive savings calculator — sliders + chart for the Visualize iframe."""
    monthly_i = int(monthly) if monthly == int(monthly) else monthly
    return f"""<style>
  .calc {{ max-width: 720px; margin: 0 auto; font-family: system-ui, sans-serif; }}
  .calc h1 {{ font-size: 1.1rem; font-weight: 500; margin: 0 0 0.25rem; color: #f3f4f6; }}
  .calc .sub {{ font-size: 0.75rem; color: #9ca3af; margin-bottom: 1.25rem; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }}
  @media (max-width: 520px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  .card {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(74,109,148,0.35);
    border-radius: 0.65rem;
    padding: 0.85rem 1rem;
  }}
  .card label {{ display: block; font-size: 0.65rem; text-transform: uppercase;
    letter-spacing: 0.08em; color: #9ca3af; margin-bottom: 0.35rem; }}
  .card .val {{ font-size: 1.15rem; color: #c5d4e8; font-variant-numeric: tabular-nums; }}
  input[type=range] {{ width: 100%; margin: 0.5rem 0 0; accent-color: #4a6d94; }}
  .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin: 1rem 0; }}
  .metric {{ text-align: center; padding: 0.65rem; background: rgba(58,86,122,0.15);
    border-radius: 0.5rem; border: 1px solid rgba(58,86,122,0.25); }}
  .metric .n {{ font-size: 1rem; font-weight: 600; color: #e5e7eb; }}
  .metric .l {{ font-size: 0.6rem; color: #9ca3af; text-transform: uppercase; margin-top: 0.2rem; }}
  canvas {{ width: 100% !important; height: 220px !important; margin-top: 0.5rem; }}
</style>
<div class="calc">
  <h1>Interactive Savings Calculator</h1>
  <p class="sub">Adjust sliders — totals and chart update instantly.</p>
  <motion-div class="grid">
    <div class="card">
      <label>Monthly savings</label>
      <div class="val" id="mLabel">${monthly_i:,}/mo</div>
      <input type="range" id="monthly" min="100" max="50000" step="100" value="{monthly_i}" />
    </div>
    <div class="card">
      <label>Annual interest rate</label>
      <div class="val" id="rLabel">{rate}%</motion-div>
      <input type="range" id="rate" min="0" max="15" step="0.1" value="{rate}" />
    </div>
    <div class="card">
      <label>Time period (years)</label>
      <div class="val" id="yLabel">{years} yrs</div>
      <input type="range" id="years" min="1" max="40" step="1" value="{years}" />
    </div>
    <div class="card">
      <label>Starting balance</label>
      <div class="val" id="iLabel">${initial:,.0f}</div>
      <input type="range" id="initial" min="0" max="500000" step="1000" value="{int(initial)}" />
    </div>
  </div>
  <div class="metrics">
    <div class="metric"><motion-div class="n" id="totalContrib">—</div><div class="l">You contribute</div></div>
    <div class="metric"><div class="n" id="interest">—</div><div class="l">Interest earned</div></div>
    <div class="metric"><div class="n" id="finalBal">—</div><div class="l">Final balance</div></div>
  </div>
  <canvas id="chart"></canvas>
</motion-div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
(function() {{
  const fmt = (n) => new Intl.NumberFormat('en-US', {{ style: 'currency', currency: 'USD', maximumFractionDigits: 0 }}).format(n);
  const monthly = document.getElementById('monthly');
  const rateEl = document.getElementById('rate');
  const yearsEl = document.getElementById('years');
  const initialEl = document.getElementById('initial');
  const mLabel = document.getElementById('mLabel');
  const rLabel = document.getElementById('rLabel');
  const yLabel = document.getElementById('yLabel');
  const iLabel = document.getElementById('iLabel');

  function project(m, rAnnual, y, start) {{
    const r = rAnnual / 100 / 12;
    const n = y * 12;
    let balance = start;
    const points = [{{ x: 0, y: balance }}];
    let contributed = start;
    for (let i = 1; i <= n; i++) {{
      balance = balance * (1 + r) + m;
      contributed += m;
      if (i % 12 === 0) points.push({{ x: i / 12, y: balance }});
    }}
    if (n % 12 !== 0) points.push({{ x: y, y: balance }});
    return {{ balance, contributed, interest: balance - contributed, points }};
  }}

  let chart;
  function render() {{
    const m = +monthly.value;
    const r = +rateEl.value;
    const y = +yearsEl.value;
    const start = +initialEl.value;
    mLabel.textContent = fmt(m) + '/mo';
    rLabel.textContent = r.toFixed(1) + '%';
    yLabel.textContent = y + ' yrs';
    iLabel.textContent = fmt(start);
    const {{ balance, contributed, interest, points }} = project(m, r, y, start);
    document.getElementById('totalContrib').textContent = fmt(contributed);
    document.getElementById('interest').textContent = fmt(interest);
    document.getElementById('finalBal').textContent = fmt(balance);
    const labels = points.map(p => 'Year ' + p.x);
    const data = points.map(p => p.y);
    if (!chart) {{
      chart = new Chart(document.getElementById('chart'), {{
        type: 'line',
        data: {{
          labels,
          datasets: [{{
            label: 'Balance',
            data,
            borderColor: '#6b9bc8',
            backgroundColor: 'rgba(74,109,148,0.25)',
            fill: true,
            tension: 0.25,
            pointRadius: 3,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af', maxTicksLimit: 12 }}, grid: {{ color: 'rgba(255,255,255,0.06)' }} }},
            y: {{ ticks: {{ color: '#9ca3af', callback: v => '$' + (v/1000).toFixed(0) + 'k' }}, grid: {{ color: 'rgba(255,255,255,0.06)' }} }}
          }}
        }}
      }});
    }} else {{
      chart.data.labels = labels;
      chart.data.datasets[0].data = data;
      chart.update();
    }}
  }}
  [monthly, rateEl, yearsEl, initialEl].forEach(el => el.addEventListener('input', render));
  render();
}})();
</script>""".replace("motion-", "")
