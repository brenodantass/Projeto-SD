import asyncio
import uuid
import httpx
import logging
from fastapi import FastAPI, Body, HTTPException
from config import get_config
from logic import TotalOrderState

# ---------- Q1 ------------------------

# Configuração de logger
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

cfg = get_config()
raw_id = cfg["process_id"]
try:
    PROCESS_ID = int(str(raw_id).split("-")[-1])  # ex: "q1-app-0" → 0
except Exception:
    PROCESS_ID = int(raw_id) if str(raw_id).isdigit() else 0

PEERS = cfg["peers"]
NUM_PROCESSES = cfg["num_processes"]
DELAY_MESSAGE_ID = cfg["delay_message_id"]
DELAY_MS = cfg["delay_ms"]
INITIAL_CLOCK = cfg["initial_clock"]

app = FastAPI(title=f"Q1 Total Order - P{PROCESS_ID}")
state = TotalOrderState(process_id=PROCESS_ID, num_processes=NUM_PROCESSES, initial_clock=INITIAL_CLOCK)

@app.get("/health")
async def health():
    return {"status": "ok", "process_id": PROCESS_ID, "clock": state.clock}

# multicast de mensagem para todos os processos 
@app.post("/multicast")
async def multicast(payload: dict = Body(...)):
    ts = state.tick_send()
    message_id = str(uuid.uuid4())
    msg = {
        "message_id": message_id,
        "origin_id": str(PROCESS_ID),
        "timestamp": ts,
        "payload": payload,
    }

    targets = PEERS + [f"http://localhost:{8000 + PROCESS_ID}/message"]

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [client.post(t, json=msg) for t in targets]
        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(f"[MULTICAST] P{PROCESS_ID} enviou mid={message_id} ts={ts} payload={payload}")
    return {"status": "sent", "message_id": message_id, "timestamp": ts, "process_id": PROCESS_ID}

# recebe mensagem multicast
@app.post("/message")
async def receive_message(msg: dict = Body(...)):
    if not isinstance(msg, dict):
        raise HTTPException(status_code=400, detail="Invalid payload: expected JSON object")

    ts_val = msg.get("timestamp")
    if ts_val is None:
        raise HTTPException(status_code=400, detail="Missing 'timestamp' in message")
    try:
        incoming_ts = int(ts_val)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid 'timestamp' value")

    state.tick_receive(incoming_ts)
    await state.enqueue_message(msg)

    message_id = msg.get("message_id", "<unknown>")
    origin_id = msg.get("origin_id", "<unknown>")
    ack = {"message_id": message_id, "from_id": PROCESS_ID, "ts": state.clock}
    targets = [
        f"http://coord-app-{i}.coord-app.q1.svc.cluster.local:8000/ack"
        for i in range(NUM_PROCESSES)
    ]

    if PROCESS_ID == 2 and DELAY_MS > 0:
        await asyncio.sleep(DELAY_MS / 1000.0)

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [client.post(t, json=ack) for t in targets]
        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(f"[RECEIVE] P{PROCESS_ID} recebeu mid={message_id} ts={incoming_ts} de P{origin_id}")
    return {"status": "received", "clock": state.clock}

# recebe ACK de mensagem, adiciona e processa se possível
@app.post("/ack")
async def receive_ack(ack: dict = Body(...)):
    incoming_ts = int(ack.get("ts", state.clock))
    state.tick_receive(incoming_ts)

    message_id = ack.get("message_id")
    if not message_id:
        raise HTTPException(status_code=400, detail="Missing 'message_id' in ACK")

    from_id = int(ack.get("from_id", PROCESS_ID))
    await state.add_ack(message_id, from_id)
    processed = await state.try_process_head()

    logger.info(f"[ACK] P{PROCESS_ID} recebeu ACK para mid={message_id} de P{from_id}")
    return {"status": "ack", "updated": message_id, "processed": processed, "clock": state.clock}

# ---------- Q2 ------------------------

# para pedir entrada na seção crítica
@app.post("/request_cs")
async def request_cs():
    if not state.has_token:
        logger.warning(f"[CS] P{PROCESS_ID} não possui token. Status: waiting")
        return {"status": "waiting", "has_token": False}
    
    if state.in_cs:
        logger.warning(f"[CS] P{PROCESS_ID} já está na seção crítica")
        return {"status": "already_in", "has_token": True}
    
    state.in_cs = True
    logger.info(f"[CS] P{PROCESS_ID} entrou na seção crítica")
    return {"status": "entered", "has_token": True, "process_id": PROCESS_ID}

# para liberar a seção crítica e passar o token
@app.post("/release_cs")
async def release_cs():
    if not state.in_cs:
        logger.warning(f"[CS] P{PROCESS_ID} não está na seção crítica")
        return {"status": "not_in_cs", "has_token": state.has_token}
    
    state.in_cs = False
    state.has_token = False
    next_id = (PROCESS_ID + 1) % NUM_PROCESSES
    target = f"http://coord-app-{next_id}.coord-app.q1.svc.cluster.local:8000/token"

    # aplica atraso antes de enviar o token
    if DELAY_MS > 0 and PROCESS_ID == 1:
        logger.info(f"[CS] P{PROCESS_ID} aplicando atraso de {DELAY_MS}ms antes de enviar token")
        await asyncio.sleep(DELAY_MS / 1000.0)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(target, json={"from": PROCESS_ID})
            logger.info(f"[CS] P{PROCESS_ID} liberou a seção crítica e passou o token para P{next_id} (status={resp.status_code})")
    except Exception as e:
        logger.error(f"[CS] P{PROCESS_ID} falhou ao enviar token para P{next_id}: {e}")
        return {"status": "error_sending_token", "target": target, "error": str(e)}

    return {"status": "released", "next_holder": next_id, "process_id": PROCESS_ID}


# receber token para entrar na seção crítica
@app.post("/token")
async def receive_token(data: dict = Body(...)):
    from_id = data.get("from", "unknown")
    state.has_token = True
    logger.info(f"[TOKEN] P{PROCESS_ID} recebeu token de P{from_id}")
    return {"status": "token_received", "from": from_id, "process_id": PROCESS_ID}

# ---------- Q3 ------------------------

# Utilidades
def peer_url(i: int) -> str:
    return f"http://coord-app-{i}.coord-app.q1.svc.cluster.local:8000"

# Endpoint para obter o coordenador atual
@app.get("/coordinator")
async def coordinator():
    return {"leader_id": state.leader_id, "process_id": PROCESS_ID}

# Iniciar eleição, enviar mensagens e tratar respostas
@app.post("/election")
async def start_election():
    if state.in_election:
        logger.info(f"[ELECTION] P{PROCESS_ID} já está em eleição")
        return {"status": "already_in_election"}
    state.in_election = True
    state.leader_id = None
    logger.info(f"[ELECTION] P{PROCESS_ID} iniciou eleição")

    higher_ids = [i for i in range(PROCESS_ID + 1, NUM_PROCESSES)]
    got_ok = False

    async with httpx.AsyncClient(timeout=5.0) as client:
        tasks = []
        for i in higher_ids:
            url = f"{peer_url(i)}/election_msg"
            tasks.append(client.post(url, json={"from_id": PROCESS_ID}))
        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for resp in responses:
                if isinstance(resp, httpx.Response) and resp.status_code == 200:
                    got_ok = True

    if got_ok:
        logger.info(f"[ELECTION] P{PROCESS_ID} recebeu OK de processo superior. Aguardando coordenador...")
        # Aguarda anúncio de coordenador por algum tempo
        try:
            await asyncio.wait_for(wait_for_coordinator(), timeout=10.0)
            state.in_election = False
            return {"status": "waiting_coordinator", "leader_id": state.leader_id}
        except asyncio.TimeoutError:
            logger.info(f"[ELECTION] P{PROCESS_ID} não recebeu coordenador. Assume liderança.")
            await announce_coordinator(PROCESS_ID)
            state.in_election = False
            return {"status": "self_elected", "leader_id": PROCESS_ID}
    else:
        # Ninguém superior respondeu -> eu sou o maior ativo
        logger.info(f"[ELECTION] P{PROCESS_ID} não recebeu OK. Assume liderança.")
        await announce_coordinator(PROCESS_ID)
        state.in_election = False
        return {"status": "leader", "leader_id": PROCESS_ID}

async def wait_for_coordinator():
    # Poll simples do endpoint /coordinator nos peers
    async with httpx.AsyncClient(timeout=3.0) as client:
        for _ in range(10):
            for i in range(NUM_PROCESSES):
                try:
                    resp = await client.get(f"{peer_url(i)}/coordinator")
                    data = resp.json()
                    if data.get("leader_id") is not None:
                        state.leader_id = data["leader_id"]
                        return
                except Exception:
                    pass
            await asyncio.sleep(1)

async def announce_coordinator(winner_id: int):
    state.leader_id = winner_id
    async with httpx.AsyncClient(timeout=5.0) as client:
        tasks = []
        for i in range(NUM_PROCESSES):
            try:
                url = f"{peer_url(i)}/coordinator_msg"
                tasks.append(client.post(url, json={"leader_id": winner_id, "from_id": PROCESS_ID}))
            except Exception:
                pass
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(f"[COORDINATOR] P{winner_id} anunciado como líder por P{PROCESS_ID}")

#responde mensagem de eleição e dispara eleição 
@app.post("/election_msg")
async def election_msg(body: dict = Body(...)):
    from_id = int(body["from_id"])
    # Responde "OK" ao processo de menor ID
    logger.info(f"[ELECTION] P{PROCESS_ID} recebeu ELEIÇÃO de P{from_id} e respondeu OK")
    # Dispara uma eleição própria (pois sou superior e ativo)
    asyncio.create_task(start_election())
    return {"status": "ok"}

#recebe anúncio de coordenador
@app.post("/coordinator_msg")
async def coordinator_msg(body: dict = Body(...)):
    leader_id = int(body["leader_id"])
    state.leader_id = leader_id
    state.in_election = False
    logger.info(f"[COORDINATOR] P{PROCESS_ID} registrou líder = P{leader_id} (anunciado por P{body['from_id']})")
    print(f"[Processo {PROCESS_ID}] Coordenador atual: {state.leader_id}")
    return {"status": "coordinator_set", "leader_id": leader_id}