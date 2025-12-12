import asyncio
import logging

# Configuração do logger integrado ao Uvicorn
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class TotalOrderState:
    def __init__(self, process_id: int, num_processes: int, initial_clock: int = 0):
        self.process_id = process_id
        self.num_processes = num_processes
        self.clock = initial_clock
        self.queue = []
        self.acks = {}
        self.has_token = (self.process_id == 0)  # só P0 começa com token
        self.in_cs = False
        self.leader_id = None          # ID do coordenador atual
        self.in_election = False       # Flag de eleição em andamento
        self.alive_peers = set()       # Peers que responderam "ok" (opcional para depuração)

    def tick_send(self) -> int:
        """Incrementa relógio ao enviar mensagem"""
        self.clock += 1
        return self.clock

    def tick_receive(self, incoming_ts: int):
        """Atualiza relógio ao receber mensagem ou ACK"""
        self.clock = max(self.clock, incoming_ts) + 1

    async def enqueue_message(self, msg: dict):
        """Enfileira mensagem recebida"""
        self.queue.append(msg)
        mid = msg["message_id"]
        self.acks[mid] = set()

    async def add_ack(self, mid: str, from_id: int):
        """Adiciona ACK recebido para uma mensagem.

        Args:
            mid: message_id
            from_id: id do processo que enviou o ACK
        """
        if mid not in self.acks:
            self.acks[mid] = set()
        try:
            self.acks[mid].add(int(from_id))
        except Exception:
            # fallback: registre o próprio id para evitar KeyError
            self.acks[mid].add(self.process_id)

    async def try_process_head(self):
        """Tenta processar a mensagem no topo da fila se todos os ACKs chegaram"""
        if not self.queue:
            return None

        head = self.queue[0]
        mid = head["message_id"]

        # Se todos os processos já deram ACK
        if len(self.acks.get(mid, set())) == self.num_processes:
            self.queue.pop(0)
            ts = head["timestamp"]
            origin = head["origin_id"]

            # Log integrado ao Uvicorn
            logger.info(
                f"[PROC] P{self.process_id} processou mid={mid} ts={ts} origin={origin} clock={self.clock} payload={head.get('payload')}"
            )

            return head

        return None
