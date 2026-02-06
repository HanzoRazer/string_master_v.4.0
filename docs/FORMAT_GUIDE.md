# Format Options Guide for `zt-gravity explain`

The `explain` command now supports **three output formats** for maximum flexibility across different use cases.

---

## 📋 Available Formats

| Format | Flag | Best For |
|--------|------|----------|
| **Text** | `--format text` (default) | Terminal/console, logs, plain text |
| **HTML** | `--format html` or `--html` | SaaS frontends, web apps, styled docs |
| **Markdown** | `--format markdown` | GitHub READMEs, docs sites, Markdown editors |

---

## 🎯 Usage Examples

### Default (Text)

```bash
zt-gravity explain --chords "Dm7 G7 Cmaj7"
```

**Output:**
- Plain text with ASCII-art tables
- Unicode arrows: ↓4, ↑4, ±1, ±2
- Terminal-optimized formatting
- Best for: Command-line analysis, debugging

### HTML Mode

```bash
zt-gravity explain --chords "Dm7 G7 Cmaj7" --format html
# or legacy shortcut:
zt-gravity explain --chords "Dm7 G7 Cmaj7" --html
```

**Output:**
- Semantic HTML5 markup
- `<article>`, `<table>`, `<h1>`, `<h2>` tags
- CSS-ready with `.zt-explain` class
- HTML entities: `&ndash;`, `&rarr;`
- Best for: Web embedding, SaaS dashboards, styled documentation

### Markdown Mode (NEW!)

```bash
zt-gravity explain --chords "Dm7 G7 Cmaj7" --format markdown
```

**Output:**
- Pure Markdown tables
- `#` headers, `##` subheaders
- `|` pipe tables (GitHub-compatible)
- Inline code blocks: `` `Dm7` ``
- Unicode arrows preserved
- Best for: GitHub READMEs, GitBook, Docusaurus, MkDocs

---

## 💾 Saving to Files

### Save as Markdown for documentation:

```bash
zt-gravity explain --chords "C7 F7 Bb7 Eb7" --format markdown > docs/dominant-cycle.md
```

### Save as HTML for web deployment:

```bash
zt-gravity explain --chords "G7 Cmaj7 Am7 D7" --html > public/turnaround-analysis.html
```

### Batch generate docs from chord list:

```bash
# Bash/Linux:
for prog in "Dm7 G7 Cmaj7" "C7 F7 Bb7" "Am7 D7 Gmaj7"; do
  name=$(echo "$prog" | tr ' ' '_')
  zt-gravity explain --chords "$prog" --format markdown > "docs/${name}.md"
done

# PowerShell:
@("Dm7 G7 Cmaj7", "C7 F7 Bb7", "Am7 D7 Gmaj7") | ForEach-Object {
  $name = $_ -replace ' ', '_'
  python -m zone_tritone.cli explain --chords $_ --format markdown > "docs/$name.md"
}
```

---

## 📊 Format Comparison

### Text Format Features

✅ Fixed-width ASCII tables  
✅ Terminal colors (if supported)  
✅ Compact, readable in SSH sessions  
✅ Works in any text editor  
✅ Good for logging/debugging  

❌ No styling control  
❌ Not suitable for web  

### HTML Format Features

✅ Full semantic markup  
✅ CSS styling via `.zt-explain` class  
✅ Responsive design-ready  
✅ Web browser rendering  
✅ Embeddable in SaaS apps  

❌ Requires HTML renderer  
❌ More verbose output  

### Markdown Format Features

✅ GitHub/GitLab compatible  
✅ Works in all Markdown renderers  
✅ Clean, human-readable source  
✅ Version control friendly  
✅ Easy to edit manually  
✅ Converts to PDF/HTML via Pandoc  

❌ Limited styling control  
❌ Table rendering varies by renderer  

---

## 🎨 Example Outputs

### Markdown Table Output

```markdown
## Per-chord gravity anchors

| # | Chord | Root | pc | Zone   | Tritone axis (3,7) |
|---|-------|------|----|--------|---------------------|
| 0 | `Dm7` | D | 2 | Zone 1 | C–F# |
| 1 | `G7` | G | 7 | Zone 2 | F–B |
| 2 | `Cmaj7` | C | 0 | Zone 1 | E–Bb |
```

Renders as:

| # | Chord | Root | pc | Zone   | Tritone axis (3,7) |
|---|-------|------|----|--------|---------------------|
| 0 | `Dm7` | D | 2 | Zone 1 | C–F# |
| 1 | `G7` | G | 7 | Zone 2 | F–B |
| 2 | `Cmaj7` | C | 0 | Zone 1 | E–Bb |

---

## 🔧 Integration Examples

### Python API Usage

```python
import subprocess
import sys

def analyze_progression(chords: str, format: str = "text") -> str:
    """Run explain command and return output."""
    result = subprocess.run(
        [sys.executable, "-m", "zone_tritone.cli", "explain", 
         "--chords", chords, "--format", format],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.stdout

# Generate Markdown for docs
markdown_output = analyze_progression("Dm7 G7 Cmaj7", "markdown")
with open("analysis.md", "w", encoding="utf-8") as f:
    f.write(markdown_output)

# Generate HTML for web
html_output = analyze_progression("C7 F7 Bb7", "html")
```

### GitHub Actions Workflow

```yaml
name: Generate Chord Analysis Docs

on:
  push:
    paths:
      - 'chord-examples/*.txt'

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install zone-tritone
        run: pip install zone-tritone
      
      - name: Generate Markdown docs
        run: |
          mkdir -p docs/analysis
          for file in chord-examples/*.txt; do
            name=$(basename "$file" .txt)
            zt-gravity explain --file "$file" --format markdown > "docs/analysis/${name}.md"
          done
      
      - name: Commit docs
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add docs/analysis/
          git commit -m "Update chord analysis docs"
          git push
```

---

## 🚀 Advanced Use Cases

### 1. README Documentation

Generate analysis for your README:

```bash
zt-gravity explain --chords "Dm7 G7 Cmaj7 A7" --format markdown >> README.md
```

### 2. Static Site Generator

Feed Markdown output to Hugo/Jekyll/MkDocs:

```bash
zt-gravity explain --chords "C7 F7 Bb7" --format markdown > content/theory/dominant-cycle.md
```

### 3. Web API Response

Return HTML for client-side rendering:

```python
@app.route('/analyze')
def analyze():
    chords = request.args.get('chords')
    html = analyze_progression(chords, format='html')
    return render_template('analysis.html', content=html)
```

### 4. PDF Generation via Pandoc

```bash
# Generate Markdown, convert to PDF
zt-gravity explain --chords "Dm7 G7 Cmaj7" --format markdown | \
  pandoc -f markdown -t pdf -o analysis.pdf
```

---

## ✅ Testing

All three formats have smoke tests:

```bash
# Test all formats
pytest tests/test_cli_smoke.py -v

# Results:
# test_cli_explain_smoke (text) ✓
# test_cli_explain_html_smoke ✓
# test_cli_explain_markdown_smoke ✓
```

Run full suite (18 tests):

```bash
pytest tests/ -v
```

---

## 🔮 Future Enhancements

Potential additions:

- `--format json` — Machine-readable structured data
- `--format latex` — Academic paper integration with `\begin{tabular}`
- `--format asciidoc` — AsciiDoc format for technical docs
- `--theme` flag — CSS/color themes (dark/light/academic)
- `--save <file>` — Built-in file output (no need for `>`)

---

## 📚 Examples in This Repo

Check out these generated files:

- [turnaround.md](turnaround.md) — Jazz turnaround (Markdown)
- [dominant_example.md](dominant_example.md) — Dominant cycle (Markdown)
- [example.html](example.html) — HTML output sample
- [jazz_turnaround.html](jazz_turnaround.html) — HTML with more chords

---

## 💡 Tips

1. **For terminal use:** Stick with default text format
2. **For GitHub READMEs:** Use `--format markdown`
3. **For web apps:** Use `--format html` with custom CSS
4. **For docs sites:** Use `--format markdown` (works with most static generators)
5. **For printing:** Markdown → Pandoc → PDF
6. **For email:** HTML format with inline styles

---

**The Zone–Tritone System — now in your favorite format! 🎵📝✨**
