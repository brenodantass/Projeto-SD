Write-Host "=== Q1: Multicast com Ordenação Total ==="

# Mensagem A enviada pelo P0
Invoke-WebRequest -Uri "http://localhost:8000/multicast" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"text":"Mensagem A - enviada pelo P0"}'
Start-Sleep -Seconds 15

# Mensagem B enviada pelo P1
Invoke-WebRequest -Uri "http://localhost:8001/multicast" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"text":"Mensagem B - enviada pelo P1"}'
Start-Sleep -Seconds 15

# Mensagem C enviada pelo P2
Invoke-WebRequest -Uri "http://localhost:8002/multicast" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"text":"Mensagem C - enviada pelo P2"}'

Write-Host "=== Verifique os logs dos pods para ver o ordenamento total ==="
