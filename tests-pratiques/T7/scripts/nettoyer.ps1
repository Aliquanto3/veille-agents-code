# Nettoie les processus de test T7 (jamais les fenêtres Edge de l'utilisateur : filtre sur les profils temporaires de test).
Get-Process -Name 'agent-browser*' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process | Where-Object { $_.Name -in 'msedge.exe','chrome.exe','chrome-headless-shell.exe' -and $_.CommandLine -match 'agent-browser-chrome|t7\\tools\\browsers|ms-playwright|playwright_chromiumdev_profile|mcp-chrome|\.playwright' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
