# Parte 1 – Multicast com Ordenação Total

## 📌 Objetivo
Implementar e demonstrar um **sistema distribuído** com 3 processos que utilizam **multicast com ordenação total**.  
A comunicação é feita via **API REST**, e a execução ocorre em um cluster **Kubernetes local com Minikube**.

---

## ⚙️ Arquitetura
- **Cluster:** Minikube (driver Docker).
- **Pods:** `coord-app-0`, `coord-app-1`, `coord-app-2` (StatefulSet).
- **Imagem:** `coord-total-order:latest`.
- **Porta exposta:** `8000`.
- **Endpoints REST:**
  - `POST /message` → Envio de mensagem.
  - `POST /ack` → Confirmação de recebimento (ACK).

---

## 🚀 Passos de execução

### 1. Iniciar o cluster
```bash
minikube start --driver=docker
kubectl get nodes


2. Conectar Docker ao Minikube
& minikube docker-env --shell powershell | Invoke-Expression
docker info   # deve mostrar "Name: minikube"


3. Construir a imagem
docker build -t coord-total-order:latest .
docker images | findstr coord-total-order


4. Aplicar os manifests
kubectl apply -f k8s/namespace.yaml
kubectl -n q1 apply -f k8s/service.yaml
kubectl -n q1 apply -f k8s/statefulset.yaml
kubectl -n q1 get pods


5. Port-forward para os pods
kubectl -n q1 port-forward coord-app-0 8000:8000
kubectl -n q1 port-forward coord-app-1 8001:8000
kubectl -n q1 port-forward coord-app-2 8002:8000


6. Acompanhar logs
kubectl -n q1 logs -f coord-app-0
kubectl -n q1 logs -f coord-app-1
kubectl -n q1 logs -f coord-app-2



🧪 Testes
Teste 1 – Mensagem simples
Invoke-WebRequest -Uri "http://localhost:8000/message" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"text":"Mensagem A"}'


Teste 2 – Múltiplas mensagens
Invoke-WebRequest -Uri "http://localhost:8001/message" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"text":"Mensagem B"}'
Invoke-WebRequest -Uri "http://localhost:8002/message" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"text":"Mensagem C"}'


Teste 3 – Atraso de ACK
Configurar atraso:
kubectl -n q1 set env statefulset/coord-app DELAY_MS=2000 --containers=app
kubectl -n q1 rollout status statefulset/coord-app


Enviar mensagem:
Invoke-WebRequest -Uri "http://localhost:8000/message" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"text":"Mensagem com atraso"}'


Remover atraso:
kubectl -n q1 set env statefulset/coord-app DELAY_MS=0 --containers=app
kubectl -n q1 rollout status statefulset/coord-app



📖 Conceitos utilizados
- Relógio lógico: Cada processo mantém um contador que incrementa a cada envio/recebimento.
- Fila de prioridade: Mensagens são ordenadas por (timestamp, id) garantindo a mesma ordem global.
- ACKs: Uma mensagem só é processada após todos os processos confirmarem o recebimento.
- Simulação de atraso: Um processo pode atrasar o ACK, bloqueando o processamento nos demais.
