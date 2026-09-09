# OCR foundation and security review

Review date: 9 September 2026

## Decision

PaddleOCR 3.7.0 with PP-StructureV3 is the best single foundation for this workflow. It directly exports both Markdown and DOCX and combines OCR with layout ordering, table recognition, optional formulas/charts, and document orientation. The code and packages are Apache-2.0 licensed. The delivered wrapper uses only local inference and adds per-page isolation, retries, atomic manifests, resumability, logging, safe asset names, and a Windows drag-and-drop interface.

The reviewed upstream checkout is `PaddlePaddle/PaddleOCR` commit `2661c7c0ef5c613e8f93c6e93b2e052399f0f854` (22 July 2026). The app deliberately pins the earlier signed release line `paddleocr==3.7.0`, `paddlex==3.7.2`, and `paddlepaddle==3.3.1` rather than installing an unpinned branch. PaddleOCR 3.7.0 was released on 11 June 2026, and PP-StructureV3's documented outputs include `save_to_word`, `save_to_markdown`, and multi-page Markdown concatenation ([PaddleOCR releases](https://github.com/PaddlePaddle/PaddleOCR/releases), [PP-StructureV3 documentation](https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/pipeline_usage/PP-StructureV3.html)).

## Candidate comparison

| Candidate | OCR and layout quality | DOCX / Markdown | Languages | Large jobs and Windows | Offline | License | Decision |
|---|---|---|---|---|---|---|---|
| PaddleOCR PP-StructureV3 | Strong OCR plus reading order, layout, tables, formulas and charts; high-quality and smaller model choices | Native DOCX and Markdown | Broad; model choice matters | Windows supported; generator API; wrapper adds per-page resume | Yes after model cache | Apache-2.0 code/packages | Selected |
| Docling | Strong neural layout and TableFormer; multiple OCR backends | Excellent Markdown/JSON/HTML; DOCX is not its main native export path | Depends on OCR backend | Windows/local; large dependency and parser surface | Yes after model cache | MIT code; individual model licenses | Excellent alternative, but needs another DOCX conversion stage and had several 2026 parser advisories |
| Marker | Strong Markdown for papers/books, equations and layout; CPU can be very slow | Markdown first; DOCX needs conversion | Broad | PyTorch/model runtime is heavy on Windows CPU | Yes after model download | Apache-2.0 code; model has use/revenue restrictions | Rejected for licensing and missing native DOCX |
| OCRmyPDF + Tesseract | Mature searchable-PDF normalization; Tesseract accuracy depends heavily on scan/language | Neither DOCX nor structured Markdown by itself | Very broad Tesseract trained-data set | Excellent batching; Windows setup includes external tools | Yes | OCRmyPDF MPL-2.0; Tesseract Apache-2.0; other tool licenses vary | Useful preprocessing/fallback, not a complete converter |
| NAPS2 | Polished Windows scanning/OCR experience using Tesseract | Searchable PDF/images, not DOCX/Markdown | Broad via Tesseract | Best ready-made Windows UI | Yes after language download | GPL-2.0-or-later | Good scanner UI, wrong output targets |

Supporting sources: [PaddleOCR repository and Apache license](https://github.com/PaddlePaddle/PaddleOCR), [Docling local Windows/layout overview](https://docling.org/), [Docling repository and MIT license](https://github.com/docling-project/docling), [Marker repository and model terms](https://github.com/datalab-to/marker), [OCRmyPDF repository and MPL-2.0 terms](https://github.com/ocrmypdf/OCRmyPDF), and [NAPS2 repository and GPL terms](https://github.com/cyanfish/naps2).

## Dependency vulnerability results

The exact final requirements were resolved and scanned with `pip-audit 2.10.1` against the Python Packaging Advisory Database on 9 September 2026. Result: **no known vulnerabilities found** in the final requirements graph.

An earlier isolated test environment inherited `setuptools 58.1.0` from Python's virtual-environment bootstrap and the audit found seven advisory records affecting it. The installer and requirements now explicitly install `setuptools 84.0.0`; the final audit is clean. A clean result only means no matching published advisory was known to that database at scan time. It is not proof that the dependencies are vulnerability-free.

## Upstream code and behavior review

- No telemetry, analytics, Sentry, or background document upload was found in the inspected PaddleOCR package paths. The repository contains optional hosted API clients and Qianfan/OpenAI-compatible integration code, but Scan2Doc does not instantiate or call those components.
- Model discovery/download code can contact Hugging Face, AIStudio, ModelScope, or Baidu Object Storage. Scan2Doc prefers Baidu Object Storage during online preparation and sets `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK`, `HF_HUB_OFFLINE`, and `TRANSFORMERS_OFFLINE` in offline mode. The user's PDF is never supplied as a URL or request body.
- Paddle's own security guidance warns that loading untrusted models can execute code because some model loading paths use pickle. Scan2Doc accepts no model path or model upload and uses only named official models. Do not replace cached model files with third-party files ([Paddle security guidance](https://github.com/PaddlePaddle/Paddle/security)).
- PP-StructureV3 imports native Paddle, PDFium, OpenCV, and image-processing code. A maliciously crafted PDF could still exploit an unknown parser bug or exhaust memory. The wrapper validates a local `.pdf` file and PDF header, rejects password-protected files, splits one page at a time, and continues after page errors, but it is not an OS sandbox. Process untrusted PDFs in Windows Sandbox or a disposable VM.
- Embedded Markdown image paths are reduced to safe base filenames and written only beneath the selected output directory. DOCX page exports are isolated in page-specific directories. The output manifest is written atomically, and a mismatched PDF/settings fingerprint is refused instead of overwriting another job.
- Logs contain local file paths, timestamps, error strings, and stack traces. They are local but may reveal usernames/folder names if shared.
- `tkinterdnd2 0.6.3` is MIT-licensed and supplies precompiled Tk drag-and-drop binaries. Its PyPI release was not published with Trusted Publishing, which is a residual supply-chain concern. It is pinned, and drag-to-`Start Scan2Doc.bat` plus the file chooser remain usable if an organization removes this optional package.
- PaddleOCR's PyPI 3.7.0 upload was not made with Trusted Publishing; PaddleX 3.7.0 did publish attestations. Versions are pinned, but all transitive wheels are not hash-locked because Paddle and platform wheels differ across supported Python versions. For managed deployment, build an internal wheelhouse, malware-scan it, record hashes, and install with `--no-index`.

## Public advisory and project-health review

- PaddleOCR was active in 2026 and released v3.7.0 with PP-OCRv6. No published PaddleOCR repository advisory was found during this review. The absence of an advisory is not evidence of absence.
- Docling is very active and MIT licensed, but its GitHub security page listed multiple 2026 advisories: unsafe EasyOCR zip extraction, XML entity expansion, archive/path traversal, unsafe HTML URI/rendering, and an August 2026 arbitrary local file read. This materially increases the care needed when processing untrusted multi-format inputs ([Docling security page](https://github.com/docling-project/docling/security)).
- Tesseract's security page listed two moderate 2026 advisories involving crafted `.traineddata` files (heap out-of-bounds read/write). Only official, updated language data should be used ([Tesseract advisories](https://github.com/tesseract-ocr/tesseract/security/advisories)).
- OCRmyPDF is mature and actively released, but it orchestrates qpdf, Ghostscript, Tesseract and other native components. Its documentation explicitly notes that qpdf repair improves success but provides no security guarantee. This is another reason not to treat arbitrary PDFs as safe merely because conversion succeeds.
- Marker is active and its code is permissively licensed, but its current model license includes commercial/use restrictions and remote-update language. That is a supply-chain/licensing disadvantage for a durable desktop foundation ([Marker model license](https://github.com/datalab-to/marker/blob/master/MODEL_LICENSE)).

## Sample acceptance test

The supplied `Cisa 01 - 1-100-4-10.pdf` was inspected as a 7-page, unencrypted, image-only A4 PDF with no embedded JavaScript or forms. Three page images were visually inspected. Page 1 was processed end-to-end with the English quality profile on Windows CPU:

- layout order and three question headings were preserved;
- all answer choices and explanatory paragraphs were present in Markdown and DOCX;
- the combined Markdown and DOCX opened structurally;
- measured OCR/inference plus export time was approximately 174 seconds for the dense page;
- visible OCR substitutions remained (`pitfalls` -> `pitfalts`, `roll-back` -> `roli-back`, and an initial capital `I` read like lowercase `l`);
- a Windows Paddle oneDNN crash was reproduced and fixed by disabling that acceleration path;
- two undocumented PaddleOCR 3.7 Word-export filename/directory behaviors were reproduced and handled;
- four automated tests pass for retry, resume, manifest collision protection, asset path traversal containment, Markdown assembly, and DOCX assembly.

The runtime lacked bundled LibreOffice, so the test DOCX could not be visually rasterized in this environment. It was reopened with `python-docx`, and all 21 expected paragraphs were readable with no broken package relationships. A final human review in Microsoft Word remains recommended, especially for tables and image-heavy pages.

## Residual limitations

- OCR remains probabilistic and requires proofreading for high-stakes use.
- The quality profile is slow on CPU; a GPU or `fast_cpu` profile is recommended for 500 pages.
- Exact page geometry, fonts, handwritten text, stamps, complex tables, and equations may not match the scan.
- The first model download needs network access and several gigabytes of space. Fully air-gapped deployment needs a prebuilt internal model cache.
- One process handles one page at a time for stability. The wrapper intentionally avoids multi-process model duplication that can exhaust RAM/VRAM.

