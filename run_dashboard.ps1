Set-Location -LiteralPath $PSScriptRoot
& ".\.venv\Scripts\streamlit.exe" run "app.py" --server.headless true --server.port 8501 *> "streamlit.launch.log"
