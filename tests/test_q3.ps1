Write-Host ">>> Q3: Eleição de Líder (Algoritmo Valentão) <<<"

# Disparo da eleição pelo processo P0
Invoke-WebRequest -Uri "http://localhost:8000/election" -Method POST
Start-Sleep -Seconds 7
# Disparo da eleição pelo processo P1
Invoke-WebRequest -Uri "http://localhost:8001/election" -Method POST
Start-Sleep -Seconds 7
# Disparo da eleição pelo processo P2
Invoke-WebRequest -Uri "http://localhost:8002/election" -Method POST
Start-Sleep -Seconds 7

# Consulta do coordenador atual em cada processo
$ports = @(8000, 8001, 8002)
foreach ($p in $ports) {
   Invoke-WebRequest -Uri "http://localhost:8000/coordinator_msg" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"leader_id":2,"from_id":1}'
}

Write-Host ">>> Verifique nos logs: o maior ID ativo deve ser eleito como líder <<<"
