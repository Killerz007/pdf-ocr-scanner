# PDF OCR Scanner

**PDF OCR Scanner** is the repository and project name. The Windows desktop application in this repository is named **Scan2Doc**.

Scan2Doc is a local Windows desktop wrapper around PaddleOCR 3.7 and PP-StructureV3. It converts scanned PDFs into one combined Markdown file and one editable Word document while keeping page-level results so interrupted jobs can resume.

## Install

1. Open the [Releases page](https://github.com/Killerz007/pdf-ocr-scanner/releases), select the newest release, and download **Source code (zip)** under Assets. Developers may instead clone the repository with Git.
2. Extract the downloaded archive to a folder where you want to keep the application. Keep all extracted files together.
3. Install 64-bit Python 3.10, 3.11, 3.12, or 3.13 from [python.org](https://www.python.org/downloads/windows/) if none is already installed. The installer automatically chooses the newest supported version. Python 3.14 is not yet used because the pinned Paddle runtime does not provide a compatible Windows package.
4. Double-click **Install Scan2Doc.bat**. The isolated environment is large, so allow several gigabytes of free disk space.
5. Double-click **Start Scan2Doc.bat**.

The first OCR run downloads PaddleOCR's official model files to the current Windows user's `.paddlex` model cache. This is a one-time online operation for each selected model/profile. Click **Prepare offline models** before disconnecting from the internet.

The included installer configures the CPU version of PaddlePaddle. The `gpu:0` option requires a compatible official PaddlePaddle GPU installation performed separately and is not covered by this project's automated tests.

## Use

- Drop one PDF onto the app window, or drop it onto **Start Scan2Doc.bat**. The **Choose PDF** button is always available.
- Confirm the output folder and language code.
- Keep **quality** for the most accurate layout and recognition. Use **fast_cpu** for long, mostly straightforward documents on a computer without an NVIDIA GPU.
- Keep page and text rotation enabled. Enable **Unwarp** only for visibly curved or photographed pages. Formula and chart recognition are off by default because they add large models and processing time.
- Click **Start / Resume**. **Stop after current page** leaves a safe checkpoint.

The output folder contains:

- `<source name>.md` - combined Markdown with source-page comments
- `<source name>.docx` - combined editable Word file with page breaks
- `assets/` - images referenced by Markdown
- `scan2doc.log` - timestamps, page errors, and diagnostic traces
- `.scan2doc/manifest.json` - resumable state and per-page status

Do not delete `.scan2doc` until the job is complete and you are satisfied with the output. If a page fails after two attempts, the combined outputs contain a clearly labeled error page and the log contains the cause. Clicking Start / Resume retries failed pages on the next run.

## Recommended settings

| Situation | Profile | Tables | Unwarp | Formulas/charts |
|---|---|---:|---:|---:|
| Highest accuracy, GPU available | `quality`, `gpu:0` | On | As needed | As needed |
| Highest accuracy, CPU only | `quality`, `cpu` | On | As needed | Off unless present |
| 500-page text-heavy scan, CPU only | `fast_cpu`, `cpu` | Off if absent | Off | Off |
| English-only material | Language `en` | As present | As needed | As present |

On the test sample, the quality profile took about 174 seconds for one page on the test machine's CPU. At that rate 500 pages is approximately 24 hours, so use the fast profile or a separately configured compatible GPU for large jobs. Actual time varies greatly with CPU/GPU, resolution, tables, formulas, and page density.

## Offline and privacy behavior

OCR inference is local. Scan2Doc passes only a local file path to PP-StructureV3; it does not call the PaddleOCR hosted API and contains no telemetry. Online mode can contact Paddle model hosts to locate/download missing models. Offline mode sets PaddleX and Hugging Face offline flags; it works only after all selected models are cached.

## Command-line use

From a Command Prompt opened in this folder:

```bat
.venv\Scripts\python.exe scan2doc.py "C:\Scans\book.pdf" --cli --language en --profile quality
```

Useful options are `--output`, `--device gpu:0`, `--profile fast_cpu`, `--offline`, `--markdown-only`, `--docx-only`, `--formulas`, `--charts`, and `--unwarp`.

## Accuracy expectations

No OCR engine guarantees error-free text. The real sample preserved headings, question order, answer choices, and paragraph order well, but visible substitutions remained, including `pitfalls` becoming `pitfalts` and `roll-back` becoming `roli-back`. Proofread names, numbers, legal text, financial data, and exam answers. DOCX reconstructs an editable document; it is not a pixel-identical copy of the scan.

## Troubleshooting

- **PaddleOCR is not installed:** run **Install Scan2Doc.bat**.
- **Offline model missing:** clear Offline, click **Prepare offline models**, then try again.
- **Out of memory / very slow:** use `fast_cpu`, turn off tables/formulas/charts that are absent, close other applications, or use a GPU.
- **Output folder belongs to a different job:** choose a new folder. This guard prevents accidental overwriting.
- **Password-protected PDF:** make an unlocked copy first; passwords are intentionally not stored.
- **Audit dependencies:** run **Run Security Audit.bat** while online.

## Security and contributing

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md). Do not include unredacted documents, logs, local paths, or exploit details in a public issue.

See [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for the project comparison, threat review, and residual risks. Practical contribution steps are in [CONTRIBUTING.md](CONTRIBUTING.md).
