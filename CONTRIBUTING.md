# Contributing

Thanks for helping improve PDF OCR Scanner and the Scan2Doc application.

1. Open an issue before starting a large change or changing OCR behavior.
2. Create a focused branch and keep unrelated formatting or refactoring out of the change.
3. On 64-bit Windows with Python 3.10 through 3.13, run `Install Scan2Doc.bat` or install `requirements.txt` in a virtual environment.
4. Run `python -m unittest discover -s tests -v` and `python -m compileall -q scan2doc.py scan2doc_core.py tests` before opening a pull request.
5. Explain what changed, how it was tested, and any user-visible limitations in the pull request.

Never commit source PDFs, OCR outputs, model caches, virtual environments, credentials, personal files, or private logs. Use synthetic, redistributable fixtures if a test document is essential.

Contributions are accepted under the repository's [MIT License](LICENSE).
