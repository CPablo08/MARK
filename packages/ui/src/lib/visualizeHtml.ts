/** Wrap agent HTML fragments in a safe preview document. */
export function wrapVisualizationHtml(html: string): string {
  const trimmed = html.trim();
  if (!trimmed) {
    return "<!DOCTYPE html><html><body><p style='color:#888'>Empty visualization</p></body></html>";
  }
  if (/<html[\s>]/i.test(trimmed)) return trimmed;
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: #0a0b0d;
      color: #e5e7eb;
      font-family: system-ui, -apple-system, sans-serif;
      padding: 1rem;
    }
  </style>
</head>
<body>${trimmed}</body>
</html>`;
}
