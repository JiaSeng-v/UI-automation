cd C:\path\to\ui-auto
Expand-Archive C:\path\to\ui-auto-wheelhouse.zip .\wheelhouse -Force

uv venv --python 3.12 --no-python-downloads
uv pip sync --python .\.venv\Scripts\python.exe --no-index --find-links .\wheelhouse .\requirements.lock.txt