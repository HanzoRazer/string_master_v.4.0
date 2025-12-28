# HTML Output Examples for `zt-gravity explain`

The `explain` command now supports **two output formats**:

1. **Plain text** (default) — for terminal/console viewing
2. **HTML** (with `--html` flag) — for SaaS, docs, or web embedding

---

## 📝 Usage

### Plain text output (default):

```bash
zt-gravity explain --chords "Dm7 G7 Cmaj7"
```

### HTML output:

```bash
zt-gravity explain --chords "Dm7 G7 Cmaj7" --html
```

### Save to file:

```bash
zt-gravity explain --chords "C7 F7 Bb7 Eb7" --html > dominant_cycle.html
```

---

## 🎯 HTML Features

The HTML output includes:

✅ **Semantic markup** — `<article>`, `<h1>`, `<h2>`, `<table>` tags  
✅ **CSS-ready** — `.zt-explain` class for custom styling  
✅ **HTML entities** — Proper encoding (e.g., `&ndash;`, `&rarr;`)  
✅ **Markdown-compatible** — Most renderers accept raw HTML blocks  
✅ **Unicode symbols** — ↓4, ↑4, ±1, ±2 motion tags preserved  

---

## 📊 HTML Structure

```html
<article class='zt-explain'>
  <h1>Zone–Tritone EXPLAIN</h1>
  
  <h2>Chord progression</h2>
  <p><code>Dm7 G7 Cmaj7</code></p>
  
  <h2>Per-chord gravity anchors</h2>
  <table>
    <!-- Root, zone, tritone axis for each chord -->
  </table>
  
  <h2>Step-by-step transitions</h2>
  <table>
    <!-- From/to, interval, zone-relation, explanation -->
  </table>
  
  <h2>Gravity comparison</h2>
  <p><strong>Theoretical chain:</strong> C → F → Bb → Eb</p>
  <p><strong>Actual progression:</strong> C → F → Bb → Eb</p>
  
  <h2>Reading guide</h2>
  <ul>
    <li>Descending 4th (↓4) = functional gravity</li>
    <li>Semitone (±1) = chromatic zone-crossing</li>
    <li>Whole-step (±2) = modal/color motion</li>
    <li>Other = tension against gravity</li>
  </ul>
</article>
```

---

## 🎨 Custom Styling

Add CSS to match your brand:

```css
.zt-explain {
  font-family: 'Inter', sans-serif;
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
  background: #f5f5f5;
  border-radius: 8px;
}

.zt-explain h1 {
  color: #1A4D8F;  /* Zone 1 blue */
  border-bottom: 3px solid #D4860F;  /* Zone 2 amber */
}

.zt-explain table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.zt-explain th {
  background: #2C2C2C;
  color: white;
  padding: 0.75rem;
  text-align: left;
}

.zt-explain td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #ddd;
}

.zt-explain code {
  background: #2C2C2C;
  color: #4FD1C5;  /* Zone 1 cyan */
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'JetBrains Mono', monospace;
}
```

---

## 🚀 SaaS Integration

### Use case 1: Real-time analysis endpoint

```python
from zone_tritone.cli import cmd_explain
import argparse

def analyze_progression(chord_string: str) -> str:
    """Generate HTML analysis for web display."""
    args = argparse.Namespace(
        chords=chord_string,
        file=None,
        html=True
    )
    # Capture output to string instead of stdout
    import io
    import sys
    output = io.StringIO()
    sys.stdout = output
    cmd_explain(args)
    sys.stdout = sys.__stdout__
    return output.getvalue()
```

### Use case 2: Static documentation generator

```bash
#!/bin/bash
# Generate HTML docs for all examples

for example in "Dm7 G7 Cmaj7" "C7 F7 Bb7" "Am7 D7 Gmaj7"
do
  name=$(echo "$example" | tr ' ' '_')
  zt-gravity explain --chords "$example" --html > "docs/${name}.html"
done
```

---

## 📚 Examples Generated

This repo includes example HTML files:

- [example.html](example.html) — Simple dominant cycle (C7 F7 Bb7 Eb7)
- [jazz_turnaround.html](jazz_turnaround.html) — Jazz progression (G7 Cmaj7 Am7 D7 Gmaj7)

Open in browser to see formatted output!

---

## 🔮 Future Enhancements

Potential additions:

- `--format markdown` — Pure Markdown tables (no HTML)
- `--format json` — Machine-readable structured data
- `--format latex` — Academic paper integration
- CSS theme presets (`--theme dark/light/academic`)
- SVG diagram generation

Suggest features via GitHub issues!

---

## ✅ Testing

Run smoke tests:

```bash
# Test plain text mode
pytest tests/test_cli_smoke.py::test_cli_explain_smoke -v

# Test HTML mode
pytest tests/test_cli_smoke.py::test_cli_explain_html_smoke -v

# All tests (17 total)
pytest tests/ -v
```

---

**The Zone–Tritone System — now web-ready! 🎵✨**
