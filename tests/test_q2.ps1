Write-Host "=== Q2: Exclusão Mútua Distribuída (Token Ring) ==="
# P0 inicia com o token
Invoke-WebRequest -Uri "http://localhost:8000/init_token" -Method POST
# P0 entra e libera
Invoke-WebRequest -Uri "http://localhost:8000/request_cs" -Method POST
Start-Sleep -Seconds 5
Invoke-WebRequest -Uri "http://localhost:8000/release_cs" -Method POST
Start-Sleep -Seconds 15   # atraso para mostrar espera

# P1 entra e libera
Invoke-WebRequest -Uri "http://localhost:8001/request_cs" -Method POST
Start-Sleep -Seconds 5
Invoke-WebRequest -Uri "http://localhost:8001/release_cs" -Method POST
Start-Sleep -Seconds 15

# P2 entra e libera
Invoke-WebRequest -Uri "http://localhost:8002/request_cs" -Method POST
Start-Sleep -Seconds 5
Invoke-WebRequest -Uri "http://localhost:8002/release_cs" -Method POST

Write-Host "=== Verifique os logs: apenas um processo por vez entra na seção crítica ==="
