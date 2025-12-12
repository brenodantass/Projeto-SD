Write-Host "=== Q3: Eleição de Líder (Valentão) ==="

# Inicia eleição no P0
Invoke-WebRequest -Uri "http://localhost:8000/election" -Method POST
Start-Sleep -Seconds 10

# Consulta coordenador em todos os pods
Invoke-WebRequest -Uri "http://localhost:8000/coordinator" -Method GET
Invoke-WebRequest -Uri "http://localhost:8001/coordinator" -Method GET
Invoke-WebRequest -Uri "http://localhost:8002/coordinator" -Method GET

Write-Host "=== Verifique os logs: o maior ID ativo deve ser eleito líder ==="

