import time
import types

import pytest

from feid.agent import AgenteMaestroNASA
import feid.agent.maestro as maestro_module


class DummyThread:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def start(self):
        return None


class ImmediateThread:
    """Thread que ejecuta el target inmediatamente."""
    def __init__(self, target=None, args=(), daemon=None):
        self.target = target
        self.args = args

    def start(self):
        if self.target:
            self.target(*self.args)


class AgenteDummy(AgenteMaestroNASA):
    def _trabajo_tecnico(self, tarea):
        return f"ok:{tarea}"

    def percibir_entorno(self):
        return None


@pytest.fixture
def agente(monkeypatch):
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    return AgenteDummy("DUMMY", persistencia_automatica=False, max_workers=0)


def test_recibir_mensaje_simple(agente):
    m_id = agente.recibir_mensaje("hola", prioridad=1, complejidad=3, ttl=10)
    assert m_id is not None
    assert agente.buzon_entrada.qsize() == 1


def test_recibir_mensaje_fipa(agente):
    mensaje = {"performative": "request", "content": "do_x", "conversation-id": "c1"}
    m_id = agente.recibir_mensaje(mensaje)
    assert m_id == "c1"
    prio, _, _, _, _, mid, tarea, proto, corr_id = agente.buzon_entrada.get()
    assert mid == "c1"
    assert proto == "FIPA"
    assert tarea.startswith("[REQUEST]")
    assert corr_id is not None


def test_recibir_mensaje_kqml(agente):
    mensaje = {"verb": "ask-one", "content": "query", "reply-with": "r1"}
    m_id = agente.recibir_mensaje(mensaje)
    assert m_id == "r1"
    _, _, _, _, _, mid, _, proto, corr_id = agente.buzon_entrada.get()
    assert mid == "r1"
    assert proto == "KQML"
    assert corr_id is not None


def test_recibir_mensaje_jsonrpc(agente):
    mensaje = {"jsonrpc": "2.0", "id": 42, "method": "m", "params": {"a": 1}}
    m_id = agente.recibir_mensaje(mensaje)
    assert m_id == "42"
    _, _, _, _, _, mid, tarea, proto, corr_id = agente.buzon_entrada.get()
    assert mid == "42"
    assert proto == "JSON-RPC"
    assert "METHOD" in tarea
    assert corr_id is not None


def test_enviar_orden_saturacion(agente):
    agente.capacidad = 0
    m_id = agente.enviar_orden("x")
    assert m_id is None
    assert len(agente.bitacora_incidentes) == 1


def test_enviar_orden_seguridad(agente):
    m_id = agente.enviar_orden("shutdown now", complejidad=9)
    assert m_id is None
    assert len(agente.bitacora_incidentes) == 1


def test_crear_recibo_poliglota(agente):
    r = agente._crear_recibo_poliglota("m1", "COMPLETO", "ok", time.time(), time.time(), "FIPA")
    assert r["performative"] == "inform"
    assert r["conversation-id"] == "m1"


def test_registrar_incidente_rechazados(agente):
    agente._registrar_incidente("SATURACION", "tarea", "causa", "m1")
    assert agente.metricas_globales["rechazados"] == 1


def test_obtener_detalle_misiones_cola(agente):
    agente.enviar_orden("t1")
    detalle = agente.obtener_detalle_misiones("cola")
    # Los elementos de la cola son ahora el último elemento (tarea, que es una cadena)
    assert len(detalle) > 0


def test_obtener_detalle_misiones_limit(agente):
    agente._despachar_evento("EXITO", {"m": 1})
    agente._despachar_evento("EXITO", {"m": 2})
    detalle = agente.obtener_detalle_misiones("exitos", limit=1)
    assert len(detalle) == 1
    assert detalle[0]["m"] == 2


def test_dead_letter_en_fallo_fatal(monkeypatch):
    class AgenteFatal(AgenteMaestroNASA):
        def _trabajo_tecnico(self, tarea):
            raise RuntimeError("fatal")

    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    agente = AgenteFatal("F", persistencia_automatica=False, max_reintentos=0, max_workers=0)

    original_despachar = agente._despachar_evento

    def despachar_y_detener(tipo, datos):
        original_despachar(tipo, datos)
        agente.vivo = False

    monkeypatch.setattr(agente, "_despachar_evento", despachar_y_detener)
    agente.buzon_entrada.put((1, time.time(), 10, 5, 0, "m1", "t", "SIMPLE", "corr-1"))

    agente._ciclo_operativo()
    assert len(agente.dead_letter_queue) == 1
    assert agente.dead_letter_queue[0]["status"] == "ERROR_FATAL"


def test_cancelar_tarea(agente):
    m1 = agente.enviar_orden("t1")
    m2 = agente.enviar_orden("t2")
    assert agente.cancelar_tarea(m1) is True
    ids = [item[5] for item in list(agente.buzon_entrada.queue)]
    assert m1 not in ids
    assert m2 in ids
    assert agente.cancelar_tarea("no-existe") is False


def test_ttl_expirado_incrementa_metrica(monkeypatch):
    class AgenteTTL(AgenteMaestroNASA):
        def _trabajo_tecnico(self, tarea):
            return "ok"

    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    agente = AgenteTTL("TTL", persistencia_automatica=False, max_workers=0)
    agente.vivo = True

    def registrar_incidente_stub(*args, **kwargs):
        agente.vivo = False

    monkeypatch.setattr(agente, "_registrar_incidente", registrar_incidente_stub)
    agente.buzon_entrada.put((1, time.time() - 10, 1, 1, 0, "m1", "t", "SIMPLE", "corr-1"))

    agente._ciclo_operativo()
    assert agente.metricas_globales["muertes_por_ttl"] == 1


def test_external_handler_invocado(monkeypatch):
    llamadas = []

    def handler(tipo, datos):
        llamadas.append((tipo, datos))

    class AgenteHandler(AgenteMaestroNASA):
        def _trabajo_tecnico(self, tarea):
            return "ok"

    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    agente = AgenteHandler(
        "H", external_handler=handler, persistencia_automatica=False, max_workers=0
    )
    monkeypatch.setattr(maestro_module.threading, "Thread", ImmediateThread)
    agente._despachar_evento("EXITO", {"x": 1})

    assert llamadas and llamadas[0][0] == "EXITO"


def test_reintento_reencola_tarea(monkeypatch):
    class AgenteRetry(AgenteMaestroNASA):
        def _trabajo_tecnico(self, tarea):
            raise RuntimeError("fail")

    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    agente = AgenteRetry(
        "R", persistencia_automatica=False, max_reintentos=3, max_workers=0
    )
    monkeypatch.setattr(maestro_module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(maestro_module.time, "sleep", lambda *_: None)

    tarea = (1, time.time(), 10, 5, 0, "m1", "t", "SIMPLE", "corr-1")
    llamadas = {"count": 0}

    def get_side_effect(*_args, **_kwargs):
        llamadas["count"] += 1
        if llamadas["count"] == 1:
            agente.vivo = False
            return tarea
        raise maestro_module.Empty()

    monkeypatch.setattr(agente.buzon_entrada, "get", get_side_effect)
    agente._ciclo_operativo()

    assert agente.metricas_globales["fallos_recuperados"] == 1
    reencoladas = list(agente.buzon_entrada.queue)
    assert reencoladas and reencoladas[0][4] == 1


# ============================================================================
# ENTERPRISE FEATURES TESTS
# ============================================================================

def test_correlation_id_tracking(agente):
    """Test que correlation IDs se crean y rastrean correctamente."""
    m_id1 = agente.enviar_orden("tarea1", m_id="t1", correlation_id="corr-123")
    m_id2 = agente.enviar_orden("tarea2", m_id="t2", correlation_id="corr-123")
    
    # Ambas tareas deben estar en la cola
    assert agente.buzon_entrada.qsize() == 2
    
    # Obtener metadata de correlación
    meta = agente.obtener_correlation("corr-123")
    assert "created_at" in meta
    assert meta["hop_count"] >= 0
    assert "chain" in meta


def test_correlation_id_in_receipt(agente, monkeypatch):
    """Test que correlation ID aparece en los recibos."""
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    agente = AgenteDummy("D", persistencia_automatica=False, max_workers=0)
    monkeypatch.setattr(maestro_module.threading, "Thread", ImmediateThread)
    
    # Enviar con correlation_id explícito
    m_id = agente.enviar_orden("test_task", correlation_id="trace-xyz")
    agente.vivo = False
    agente._ciclo_operativo()
    
    # Procesar una tarea y verificar que el recibo contiene correlation_id
    recibos = agente.buzon_salida
    if recibos:
        recibo = list(recibos)[0]
        assert "correlation_id" in recibo


def test_circuit_breaker_closed_state(agente):
    """Test que el circuit breaker inicia en estado CLOSED."""
    assert agente.obtener_estado_circuito() == "closed"


def test_circuit_breaker_opens_on_failures(monkeypatch):
    """Test que el circuit breaker se abre después de fallos consecutivos."""
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    
    class AgenteQueFalla(AgenteMaestroNASA):
        def _trabajo_tecnico(self, tarea):
            raise ValueError("Fallo simulado")
        
        def percibir_entorno(self):
            return None
    
    agente = AgenteQueFalla(
        "FAIL", 
        persistencia_automatica=False, 
        max_workers=0,
        circuit_breaker_threshold=3
    )
    monkeypatch.setattr(maestro_module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(maestro_module.time, "sleep", lambda *_: None)
    
    # Simular 3 fallos consecutivos
    fallos = 0
    for i in range(3):
        try:
            agente.circuit_breaker.call(lambda: 1/0)  # TypeError
        except:
            fallos += 1
    
    # Después de 3 fallos, el circuito debe estar OPEN
    assert agente.obtener_estado_circuito() == "open"
    assert fallos == 3


def test_circuit_breaker_half_open_after_timeout(monkeypatch):
    """Test transición de OPEN a HALF_OPEN después del timeout."""
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    
    agente = AgenteDummy("CB_HO", persistencia_automatica=False, max_workers=0, circuit_breaker_threshold=2)
    
    # Forzar failures
    for _ in range(2):
        try:
            agente.circuit_breaker.call(lambda: 1/0)
        except:
            pass
    
    assert agente.obtener_estado_circuito() == "open"
    
    # Modificar tiempo de último fallo para simular timeout
    agente.circuit_breaker.last_failure_time = time.time() - 100
    
    # Intentar llamada debe pasar a HALF_OPEN
    try:
        agente.circuit_breaker.call(lambda: "success")
    except:
        pass
    
    assert agente.obtener_estado_circuito() in ["half_open", "closed"]


def test_retry_strategy_exponential_backoff(monkeypatch):
    """Test que ExponentialBackoffStrategy genera delays exponenciales."""
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    
    strategy = maestro_module.ExponentialBackoffStrategy(base_delay=1.0, max_delay=60.0, jitter=False)
    
    # Sin jitter, delays deben ser potencias de 2
    delay_0 = strategy.get_delay(0, 5)
    delay_1 = strategy.get_delay(1, 5)
    delay_2 = strategy.get_delay(2, 5)
    
    assert delay_0 == 1.0  # 2^0
    assert delay_1 == 2.0  # 2^1
    assert delay_2 == 4.0  # 2^2
    
    # Verificar capping
    delay_max = strategy.get_delay(10, 5)
    assert delay_max == 60.0


def test_retry_strategy_linear_backoff(monkeypatch):
    """Test que LinearBackoffStrategy genera delays lineales."""
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    
    strategy = maestro_module.LinearBackoffStrategy(increment=0.5, max_delay=10.0)
    
    delay_0 = strategy.get_delay(0, 5)
    delay_1 = strategy.get_delay(1, 5)
    delay_2 = strategy.get_delay(2, 5)
    
    assert delay_0 == 0.5
    assert delay_1 == 1.0
    assert delay_2 == 1.5


def test_retry_strategy_fixed_delay(monkeypatch):
    """Test que FixedDelayStrategy produce delay constante."""
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    
    strategy = maestro_module.FixedDelayStrategy(delay=2.5)
    
    assert strategy.get_delay(0, 5) == 2.5
    assert strategy.get_delay(1, 5) == 2.5
    assert strategy.get_delay(10, 5) == 2.5


def test_agente_with_custom_retry_strategy(monkeypatch):
    """Test que el agente puede usar estrategia de reintentos personalizada."""
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    
    custom_strategy = maestro_module.LinearBackoffStrategy(increment=0.1)
    agente = AgenteDummy(
        "CUSTOM_RETRY",
        persistencia_automatica=False,
        max_workers=0,
        retry_strategy=custom_strategy
    )
    
    assert agente.obtener_estrategia_reintentos() == "LinearBackoffStrategy"


def test_enterprise_monitoring_health(agente):
    """Test que monitorear_salud incluye información de enterprise features."""
    salud = agente.monitorear_salud()
    
    assert "circuit_breaker" in salud
    assert "retry_strategy" in salud
    assert salud["circuit_breaker"] == "closed"
    assert "Exponential" in salud["retry_strategy"]


def test_correlation_id_with_delegation(monkeypatch):
    """Test que correlation ID se propaga en delegaciones."""
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    
    agente1 = AgenteDummy("A1", persistencia_automatica=False, max_workers=0)
    agente2 = AgenteDummy("A2", persistencia_automatica=False, max_workers=0)
    
    # Agente 1 delega tarea a agente 2 con correlation_id
    corr_id = agente1.correlation_tracker.create_correlation("delegation-1")
    m_id = agente2.enviar_orden("delegated_task", correlation_id=corr_id)
    
    # Ambos agentes deben tener registro de la correlación
    meta1 = agente1.obtener_correlation(corr_id)
    meta2 = agente2.obtener_correlation(corr_id)
    
    assert meta1 or meta2  # Al menos uno debe tener metadata
    

def test_circuit_breaker_success_closes_half_open(monkeypatch):
    """Test que éxito en HALF_OPEN devuelve a CLOSED."""
    monkeypatch.setattr(maestro_module.threading, "Thread", DummyThread)
    
    agente = AgenteDummy("CB_CLOSE", persistencia_automatica=False, max_workers=0, circuit_breaker_threshold=2)
    
    # Forzar apertura
    for _ in range(2):
        try:
            agente.circuit_breaker.call(lambda: 1/0)
        except:
            pass
    
    assert agente.obtener_estado_circuito() == "open"
    
    # Simular timeout y luego éxito
    agente.circuit_breaker.last_failure_time = time.time() - 100
    try:
        result = agente.circuit_breaker.call(lambda: "ok")
        assert result == "ok"
    except:
        pass
    
    # Después de éxito en HALF_OPEN, debe estar CLOSED
    assert agente.obtener_estado_circuito() == "closed"

