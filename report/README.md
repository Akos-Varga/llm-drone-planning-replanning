# Aarhus University Computer Engineering Master's Thesis LaTeX Template

This is a clean, unofficial thesis starter template aimed at a master's thesis in Computer Engineering.

## Files

- `main.tex` — main thesis file
- `chapters/` — chapter files
- `references.bib` — bibliography database
- `figures/` — put your figures here

## Compile

Example with `pdflatex` + `bibtex`:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Or with `latexmk`:

```bash
latexmk -pdf main.tex
```

## Notes

- Edit the metadata commands near the top of `main.tex`
- Replace placeholders with your own content
- Check current AU and department requirements before submission
- If your thesis must follow a strict official cover page or report format, adapt the title page accordingly
