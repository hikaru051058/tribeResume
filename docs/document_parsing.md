# Document Parsing

## Purpose

The document parser lets the resume-response simulator accept common resume formats while keeping the downstream reviewer and TRIBE-stimulus scaffolds text-first.

Supported inputs:

- `.txt`
- `.md`
- `.docx`
- `.pdf` when the PDF contains extractable text

OCR is not included yet.

## Parser Architecture

All supported formats normalize into the same dictionary shape:

```json
{
  "source_path": "examples/resume_sample.pdf",
  "file_type": "pdf",
  "text": "Extracted resume text...",
  "metadata": {
    "extraction_method": "pypdf",
    "page_count": 1,
    "char_count": 2400,
    "word_count": 350
  },
  "warnings": []
}
```

This shape lets the rest of the system work with text regardless of the original file type.

## Format Handling

### TXT

Plain text files are read as UTF-8 with fallback replacement for invalid characters.

### Markdown

Markdown is read as text. Headings and bullets remain in the text stream, but no Markdown AST parsing is performed yet.

### DOCX

DOCX parsing uses `python-docx`.

The parser extracts:

- Paragraph text.
- Table cell text.
- Paragraph count.
- Table count.
- Table cell count.

DOCX tables are parsed, but layout may not be preserved. A table-based resume may lose some visual relationship between columns.

### PDF

PDF parsing uses `pypdf`.

The parser extracts text page by page and records:

- Page count.
- Pages with no extracted text.
- Character count.
- Word count.

PDF visual layout is not fully understood yet. Multi-column resumes, headers, footers, and decorative layout may extract in a different order than they appear visually.

## Warnings

The parser adds warnings when:

- Extracted text is very short.
- PDF pages have no text.
- The file type is unsupported.
- The file does not exist.

Very short PDF extraction usually means the PDF may be scanned or image-based.

## Why Normalize Into Text First

The current reviewer-agent layer works on resume text. Normalizing all formats into text keeps the MVP simple and testable:

```text
PDF/DOCX/Markdown/TXT -> parsed text -> reviewer agents -> rewrite -> compare
```

The TRIBE v2 scaffold also starts from text events, so text normalization is the right first step.

## Limitations

- No OCR yet.
- Scanned PDFs are not supported.
- Image-only PDFs will produce little or no text.
- Layout extraction is approximate.
- Tables may lose visual structure.
- The parser does not yet produce line-level evidence IDs.

## Future OCR Support

Future OCR could add:

- Image-based PDF text extraction.
- Confidence per OCR page.
- Warnings for low-confidence text.
- Side-by-side original page preview.

OCR output should be clearly labeled because it can introduce recognition errors.

## Future Layout-Aware Analysis

Future layout-aware analysis could add:

- Section bounding boxes.
- Column detection.
- Bullet grouping.
- Visual density metrics.
- ATS parse-risk scoring.
- Optional TRIBE v2 stimulus-response experiments on rendered pages.

TRIBE v2 should remain an optional stimulus-response layer, not a resume-quality judge.

