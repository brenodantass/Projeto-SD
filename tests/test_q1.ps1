Write-Host ">>> Q1: Multicast com Ordenação Total <<<"

# Enviar mensagem (timestamp adicionado automaticamente)
Invoke-WebRequest -Uri "http://localhost:8000/multicast" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"text":"Mensagem A"}'

# P0 envia primeira mensagem
Invoke-WebRequest -Uri "http://localhost:8000/multicast" -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"text":"Msg-Alpha enviada por P0"}'
Start-Sleep -Seconds 12

# P1 envia segunda mensagem
Invoke-WebRequest -Uri "http://localhost:8001/multicast" -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"text":"Msg-Beta enviada por P1"}'
Start-Sleep -Seconds 10

# P2 envia terceira mensagem
Invoke-WebRequest -Uri "http://localhost:8002/multicast" -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"text":"Msg-Gamma enviada por P2"}'

Write-Host ">>> Cheque os pods: a ordenação total deve aparecer nos logs <<<"