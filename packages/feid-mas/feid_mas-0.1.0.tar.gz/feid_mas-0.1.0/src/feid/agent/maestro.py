import threading
import time
import uuid
import logging
import sys
import random
from abc import ABC, abstractmethod
from queue import PriorityQueue, Empty
import json
from collections import deque
import heapq
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, Dict, Any, Callable

# CONFIGURACIÓN DE LOGGING PROFESIONAL
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | [%(levelname)s] | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


# ============================================================================
# ENTERPRISE FEATURES: Correlation IDs, Circuit Breaker, Retry Strategies
# ============================================================================

class CorrelationTracker:
    """Tracks correlation IDs across agent delegation for distributed tracing."""
    
    def __init__(self):
        self.correlations: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
    
    def create_correlation(self, root_id: Optional[str] = None) -> str:
        """Create new correlation chain or extend existing one."""
        corr_id = root_id or str(uuid.uuid4())
        with self.lock:
            if corr_id not in self.correlations:
                self.correlations[corr_id] = {
                    "created_at": time.time(),
                    "chain": [corr_id],
                    "hop_count": 0
                }
            else:
                self.correlations[corr_id]["chain"].append(str(uuid.uuid4()))
                self.correlations[corr_id]["hop_count"] += 1
        return corr_id
    
    def get_chain(self, corr_id: str) -> list:
        """Get full delegation chain for this correlation ID."""
        with self.lock:
            if corr_id in self.correlations:
                return self.correlations[corr_id]["chain"].copy()
        return []
    
    def get_metadata(self, corr_id: str) -> Dict[str, Any]:
        """Get correlation metadata including timing and hop count."""
        with self.lock:
            if corr_id in self.correlations:
                meta = self.correlations[corr_id].copy()
                meta["lifetime_seconds"] = time.time() - meta["created_at"]
                return meta
        return {}


class CircuitBreakerState(Enum):
    """States for circuit breaker pattern."""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, reject requests
    HALF_OPEN = "half_open"    # Testing recovery


class CircuitBreaker:
    """Implements circuit breaker pattern for fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: float = 60.0):
        """
        Args:
            failure_threshold: Consecutive failures before opening
            timeout_seconds: Duration before attempting half-open
        """
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.last_failure_time: Optional[float] = None
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.failure_count = 0
                else:
                    raise RuntimeError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            with self.lock:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
            return result
        except Exception as e:
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.timeout_seconds
    
    def get_state(self) -> str:
        """Get current circuit state."""
        with self.lock:
            return self.state.value


class RetryStrategy(ABC):
    """Base class for retry strategies."""
    
    @abstractmethod
    def get_delay(self, attempt: int, max_attempts: int) -> float:
        """Calculate delay (seconds) before next retry attempt."""
        pass
    
    @abstractmethod
    def should_retry(self, exception: Exception, attempt: int, max_attempts: int) -> bool:
        """Determine if retry should be attempted."""
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """Exponential backoff with optional jitter."""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
    
    def get_delay(self, attempt: int, max_attempts: int) -> float:
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        if self.jitter:
            delay = delay * (0.5 + random.random())
        return delay
    
    def should_retry(self, exception: Exception, attempt: int, max_attempts: int) -> bool:
        return attempt < max_attempts


class LinearBackoffStrategy(RetryStrategy):
    """Linear backoff strategy."""
    
    def __init__(self, increment: float = 1.0, max_delay: float = 60.0):
        self.increment = increment
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int, max_attempts: int) -> float:
        return min(self.increment * (attempt + 1), self.max_delay)
    
    def should_retry(self, exception: Exception, attempt: int, max_attempts: int) -> bool:
        return attempt < max_attempts


class FixedDelayStrategy(RetryStrategy):
    """Fixed delay between retries."""
    
    def __init__(self, delay: float = 2.0):
        self.delay = delay
    
    def get_delay(self, attempt: int, max_attempts: int) -> float:
        return self.delay
    
    def should_retry(self, exception: Exception, attempt: int, max_attempts: int) -> bool:
        return attempt < max_attempts


# ============================================================================
# LIFECYCLE HOOKS, EVENT SCHEMA, Y VALIDADORES
# ============================================================================

class EventoSchema:
    """Schema para eventos versionados con validación."""
    
    SCHEMA_VERSION = "1.0"
    
    TIPOS_VALIDOS = {
        "EXITO", "ERROR", "TIMEOUT", "REINTENTO", "INCIDENTE",
        "TTL_EXPIRADO", "SATURACION", "CUSTOM"
    }
    
    @staticmethod
    def validar(tipo: str, datos: Dict[str, Any], max_kb: int = 100) -> bool:
        """Valida evento contra schema."""
        if tipo not in EventoSchema.TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido: {tipo}")
        
        size_bytes = len(json.dumps(datos, default=str).encode('utf-8'))
        if size_bytes > max_kb * 1024:
            raise ValueError(f"Evento > {max_kb}KB")
        
        return True


class LifecycleHooks:
    """Gestiona hooks del ciclo de vida del agente."""
    
    def __init__(self):
        self._hooks = {
            "on_start": [],
            "on_stop": [],
            "on_error": [],
        }
        self.lock = threading.Lock()
    
    def registrar(self, evento: str, callback: Callable):
        """Registra callback para evento del ciclo de vida."""
        if evento not in self._hooks:
            raise ValueError(f"Evento inválido: {evento}")
        with self.lock:
            self._hooks[evento].append(callback)
    
    def invocar(self, evento: str, *args, **kwargs):
        """Invoca callbacks registrados para evento."""
        with self.lock:
            callbacks = self._hooks.get(evento, []).copy()
        for cb in callbacks:
            try:
                if callable(cb):
                    cb(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error en hook {evento}: {e}")


class ValidadorPayload:
    """Validador de payload para tareas."""
    
    def __init__(self, max_bytes: int = 1_000_000, tipos_permitidos: Optional[list] = None):
        self.max_bytes = max_bytes
        self.tipos_permitidos = tipos_permitidos or ["str", "dict", "list", "int", "float", "bool"]
    
    def validar(self, tarea: Any) -> bool:
        """Valida payload de tarea."""
        tipo = type(tarea).__name__
        if tipo not in self.tipos_permitidos:
            raise TypeError(f"Tipo no permitido: {tipo}")
        
        size = len(json.dumps(tarea, default=str).encode('utf-8'))
        if size > self.max_bytes:
            raise ValueError(f"Payload muy grande: {size}bytes")
        
        return True


class RateLimiter:
    """Token bucket rate limiter per agent/origin."""
    
    def __init__(self, tasa_tokens: float = 100.0, capacidad_max: float = 100.0):
        """
        Inicializa rate limiter con token bucket.
        
        Args:
            tasa_tokens: Tokens generados por segundo
            capacidad_max: Capacidad máxima del bucket
        """
        self.tasa_tokens = tasa_tokens
        self.capacidad_max = capacidad_max
        self.tokens = capacidad_max
        self.ultimo_relleno = time.time()
        self.lock = threading.Lock()
        self.limites_por_origen: Dict[str, Dict[str, float]] = {}
    
    def _rellenar_tokens(self):
        """Rellena tokens basado en tiempo transcurrido."""
        ahora = time.time()
        tiempo_transcurrido = ahora - self.ultimo_relleno
        tokens_a_añadir = tiempo_transcurrido * self.tasa_tokens
        self.tokens = min(self.capacidad_max, self.tokens + tokens_a_añadir)
        self.ultimo_relleno = ahora
    
    def permitir(self, costo: float = 1.0) -> bool:
        """
        Verifica si se puede consumir tokens.
        
        Args:
            costo: Tokens a consumir (default 1.0)
        
        Returns:
            True si se permite, False si está limitado
        """
        with self.lock:
            self._rellenar_tokens()
            if self.tokens >= costo:
                self.tokens -= costo
                return True
            return False
    
    def registrar_limite_origen(self, origen: str, tasa: float, capacidad: float):
        """Registra límite específico para un origen."""
        with self.lock:
            self.limites_por_origen[origen] = {
                "tasa": tasa,
                "capacidad": capacidad,
                "tokens": capacidad,
                "ultimo_relleno": time.time()
            }
    
    def permitir_por_origen(self, origen: str, costo: float = 1.0) -> bool:
        """Verifica límite para origen específico."""
        with self.lock:
            if origen not in self.limites_por_origen:
                # Si no tiene límite específico, usar global
                self._rellenar_tokens()
                if self.tokens >= costo:
                    self.tokens -= costo
                    return True
                return False
            
            limite = self.limites_por_origen[origen]
            ahora = time.time()
            tiempo_transcurrido = ahora - limite["ultimo_relleno"]
            tokens_a_añadir = tiempo_transcurrido * limite["tasa"]
            limite["tokens"] = min(limite["capacidad"], limite["tokens"] + tokens_a_añadir)
            limite["ultimo_relleno"] = ahora
            
            if limite["tokens"] >= costo:
                limite["tokens"] -= costo
                return True
            return False
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Retorna estado actual del limiter."""
        with self.lock:
            return {
                "tokens_disponibles": self.tokens,
                "capacidad_max": self.capacidad_max,
                "tasa_tokens": self.tasa_tokens,
                "limites_por_origen": dict(self.limites_por_origen)
            }


class ColectorMetricas:
    """Colecciona métricas de rendimiento: latencia, throughput, tasa de error."""
    
    def __init__(self, ventana_segundos: int = 60):
        """
        Inicializa colector de métricas.
        
        Args:
            ventana_segundos: Ventana de tiempo para calcular métricas (default 60s)
        """
        self.ventana_segundos = ventana_segundos
        self.latencias: deque = deque(maxlen=10000)  # Última 10k mediciones
        self.tareas_completadas = 0
        self.tareas_fallidas = 0
        self.timestamps_inicio: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def registrar_inicio_tarea(self, tarea_id: str):
        """Registra cuando inicia una tarea."""
        with self.lock:
            self.timestamps_inicio[tarea_id] = time.time()
    
    def registrar_fin_tarea(self, tarea_id: str, exitosa: bool = True):
        """Registra cuando termina una tarea y calcula latencia."""
        with self.lock:
            if tarea_id not in self.timestamps_inicio:
                return
            
            inicio = self.timestamps_inicio.pop(tarea_id)
            latencia = time.time() - inicio
            self.latencias.append(latencia)
            
            if exitosa:
                self.tareas_completadas += 1
            else:
                self.tareas_fallidas += 1
    
    def obtener_latencia_promedio(self) -> float:
        """Retorna latencia promedio."""
        with self.lock:
            return self._obtener_latencia_promedio_sin_lock()
    
    def _obtener_latencia_promedio_sin_lock(self) -> float:
        """Retorna latencia promedio (sin lock, para uso interno)."""
        if not self.latencias:
            return 0.0
        return sum(self.latencias) / len(self.latencias)
    
    def obtener_latencia_p95(self) -> float:
        """Retorna percentil 95 de latencia."""
        with self.lock:
            return self._obtener_latencia_p95_sin_lock()
    
    def _obtener_latencia_p95_sin_lock(self) -> float:
        """Retorna percentil 95 de latencia (sin lock, para uso interno)."""
        if not self.latencias:
            return 0.0
        sorted_latencias = sorted(self.latencias)
        idx = int(len(sorted_latencias) * 0.95)
        return sorted_latencias[idx] if idx < len(sorted_latencias) else sorted_latencias[-1]
    
    def obtener_throughput(self) -> float:
        """Retorna throughput: tareas completadas por segundo."""
        with self.lock:
            return self._obtener_throughput_sin_lock()
    
    def _obtener_throughput_sin_lock(self) -> float:
        """Retorna throughput (sin lock, para uso interno)."""
        total_tareas = self.tareas_completadas + self.tareas_fallidas
        if total_tareas == 0:
            return 0.0
        if self.latencias:
            tiempo_total = sum(self.latencias)
            return total_tareas / max(tiempo_total, 1.0)
        return 0.0
    
    def obtener_tasa_error(self) -> float:
        """Retorna tasa de error: fallos / total."""
        with self.lock:
            return self._obtener_tasa_error_sin_lock()
    
    def _obtener_tasa_error_sin_lock(self) -> float:
        """Retorna tasa de error (sin lock, para uso interno)."""
        total = self.tareas_completadas + self.tareas_fallidas
        if total == 0:
            return 0.0
        return self.tareas_fallidas / total
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Retorna estado completo de métricas."""
        with self.lock:
            total = self.tareas_completadas + self.tareas_fallidas
            return {
                "tareas_completadas": self.tareas_completadas,
                "tareas_fallidas": self.tareas_fallidas,
                "total_tareas": total,
                "latencia_promedio": self._obtener_latencia_promedio_sin_lock(),
                "latencia_p95": self._obtener_latencia_p95_sin_lock(),
                "throughput_tareas_por_seg": self._obtener_throughput_sin_lock(),
                "tasa_error": self._obtener_tasa_error_sin_lock(),
                "num_muestras_latencia": len(self.latencias)
            }
    
    def limpiar(self):
        """Limpia estadísticas."""
        with self.lock:
            self.latencias.clear()
            self.tareas_completadas = 0
            self.tareas_fallidas = 0
            self.timestamps_inicio.clear()


class PoliticaCola(Enum):
    """Políticas de despacho de la cola."""
    FIFO = "fifo"  # First In First Out (orden de llegada)
    LIFO = "lifo"  # Last In First Out (orden inverso)
    PRIORITY = "priority"  # Por prioridad y complejidad


class GestorColaPolitica:
    """Gestiona despacho de tareas según política configurada."""
    
    def __init__(self, politica: PoliticaCola = PoliticaCola.PRIORITY):
        """
        Inicializa gestor de cola.
        
        Args:
            politica: Política de despacho (FIFO, LIFO, PRIORITY)
        """
        self.politica = politica
        # Mantenemos colas internas para cada política
        self.cola_fifo: deque = deque()
        self.cola_prioridad: list = []  # Heap: (prioridad, t_llegada, tarea_info)
        self.lock = threading.Lock()
    
    def encolar(self, tarea_info: tuple):
        """Encola una tarea según la política."""
        with self.lock:
            if self.politica == PoliticaCola.FIFO:
                self.cola_fifo.append(tarea_info)
            elif self.politica == PoliticaCola.LIFO:
                self.cola_fifo.append(tarea_info)  # Se usa como stack
            elif self.politica == PoliticaCola.PRIORITY:
                # tarea_info = (prioridad, t_llegada, ttl, comp, intentos, m_id, tarea, proto, corr_id)
                heapq.heappush(self.cola_prioridad, (tarea_info[0], tarea_info[1], tarea_info))
    
    def desencolar(self) -> Optional[tuple]:
        """Desencola una tarea según la política."""
        with self.lock:
            if self.politica == PoliticaCola.FIFO:
                return self.cola_fifo.popleft() if self.cola_fifo else None
            elif self.politica == PoliticaCola.LIFO:
                return self.cola_fifo.pop() if self.cola_fifo else None
            elif self.politica == PoliticaCola.PRIORITY:
                if self.cola_prioridad:
                    _, _, tarea_info = heapq.heappop(self.cola_prioridad)
                    return tarea_info
                return None
        return None
    
    def qsize(self) -> int:
        """Retorna tamaño de la cola."""
        with self.lock:
            if self.politica in [PoliticaCola.FIFO, PoliticaCola.LIFO]:
                return len(self.cola_fifo)
            else:
                return len(self.cola_prioridad)
    
    def cambiar_politica(self, nueva_politica: PoliticaCola):
        """Cambia la política de despacho."""
        with self.lock:
            # Si hay tareas encoladas con la política anterior, 
            # conservarlas (es un comportamiento especial)
            logging.info(f"Cambiando política de cola a {nueva_politica.value}")
            self.politica = nueva_politica
    
    def limpiar(self):
        """Limpia la cola."""
        with self.lock:
            self.cola_fifo.clear()
            self.cola_prioridad.clear()


class AuditorEstructurado:
    """Auditoría estructurada JSON sin PII (Personally Identifiable Information)."""
    
    def __init__(self, nombre_agente: str, max_registros: int = 10000):
        """
        Inicializa auditor estructurado.
        
        Args:
            nombre_agente: Nombre del agente
            max_registros: Máximo de registros en memoria antes de rotar
        """
        self.nombre_agente = nombre_agente
        self.max_registros = max_registros
        self.registros: deque = deque(maxlen=max_registros)
        self.lock = threading.Lock()
        self.contador_archivo = 0
    
    def registrar(self, 
                 evento: str,
                 nivel: str = "INFO",
                 detalles: Optional[Dict[str, Any]] = None,
                 ocultar_campos: Optional[list] = None):
        """
        Registra evento estructurado sin PII.
        
        Args:
            evento: Tipo de evento (TAREA_ENVIADA, TAREA_COMPLETADA, ERROR, etc)
            nivel: Nivel (INFO, WARNING, ERROR, CRITICAL)
            detalles: Dict con detalles del evento
            ocultar_campos: Campos a ofuscar (ej: ['password', 'token'])
        """
        detalles = detalles or {}
        ocultar_campos = ocultar_campos or []
        
        # Ofuscar campos sensibles
        detalles_seguros = {}
        for k, v in detalles.items():
            if k.lower() in ocultar_campos or any(pii in k.lower() for pii in ['password', 'token', 'secret', 'key']):
                detalles_seguros[k] = "***OCULTO***"
            else:
                detalles_seguros[k] = v
        
        registro = {
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agente": self.nombre_agente,
            "evento": evento,
            "nivel": nivel,
            "detalles": detalles_seguros,
            "version_audit": "1.0"
        }
        
        with self.lock:
            self.registros.append(registro)
            
            # Log a través de logging también
            logging.log(
                getattr(logging, nivel, logging.INFO),
                f"[AUDIT] {evento}: {json.dumps(detalles_seguros)}"
            )
    
    def registrar_tarea_enviada(self, m_id: str, prioridad: int, ttl: int):
        """Registra envío de tarea."""
        self.registrar(
            "TAREA_ENVIADA",
            "INFO",
            {"tarea_id": m_id, "prioridad": prioridad, "ttl": ttl}
        )
    
    def registrar_tarea_completada(self, m_id: str, latencia: float):
        """Registra tarea completada."""
        self.registrar(
            "TAREA_COMPLETADA",
            "INFO",
            {"tarea_id": m_id, "latencia_segundos": round(latencia, 3)}
        )
    
    def registrar_error(self, m_id: str, tipo_error: str, mensaje: str):
        """Registra error en tarea."""
        self.registrar(
            "ERROR_TAREA",
            "ERROR",
            {"tarea_id": m_id, "tipo_error": tipo_error, "mensaje": mensaje[:100]}  # Limitar mensaje
        )
    
    def registrar_rate_limit(self, origen: str):
        """Registra cuando rate limit rechaza solicitud."""
        self.registrar(
            "RATE_LIMIT_EXCEDIDO",
            "WARNING",
            {"origen": origen}
        )
    
    def registrar_cambio_config(self, config_name: str, valor_anterior: str, valor_nuevo: str):
        """Registra cambios de configuración."""
        self.registrar(
            "CAMBIO_CONFIG",
            "INFO",
            {
                "config": config_name,
                "valor_anterior": valor_anterior,
                "valor_nuevo": valor_nuevo
            }
        )
    
    def obtener_registros(self, últimos: int = 100) -> list:
        """Retorna últimos N registros."""
        with self.lock:
            return list(self.registros)[-últimos:]
    
    def obtener_registros_por_evento(self, evento: str) -> list:
        """Retorna registros filtrados por evento."""
        with self.lock:
            return [r for r in self.registros if r["evento"] == evento]
    
    def exportar_json(self) -> str:
        """Exporta todos los registros como JSON."""
        with self.lock:
            return json.dumps(list(self.registros), default=str, indent=2)
    
    def limpiar(self):
        """Limpia todos los registros."""
        with self.lock:
            self.registros.clear()


class ConfigAgente:
    """Configuración versionada para agentes."""
    
    VERSION_ACTUAL = "1.0"
    
    def __init__(self, 
                 capacidad: int = 50,
                 max_reintentos: int = 3,
                 ttl_defecto: float = 10.0,
                 backpressure_threshold: float = 0.8,
                 max_workers: int = 4,
                 circuit_breaker_threshold: int = 5,
                 rate_limit_tokens: float = 100.0,
                 rate_limit_capacidad: float = 100.0):
        """
        Crea configuración versionada.
        
        Todos los parámetros por defecto se pueden modificar.
        """
        self.version = self.VERSION_ACTUAL
        self.capacidad = capacidad
        self.max_reintentos = max_reintentos
        self.ttl_defecto = ttl_defecto
        self.backpressure_threshold = backpressure_threshold
        self.max_workers = max_workers
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.rate_limit_tokens = rate_limit_tokens
        self.rate_limit_capacidad = rate_limit_capacidad
        self.timestamp_creacion = time.time()
    
    def actualizar(self, **kwargs) -> Dict[str, Any]:
        """
        Actualiza parámetros de configuración.
        
        Retorna dict con cambios realizados.
        """
        cambios = {}
        for clave, valor in kwargs.items():
            if hasattr(self, clave):
                valor_anterior = getattr(self, clave)
                setattr(self, clave, valor)
                cambios[clave] = {"anterior": valor_anterior, "nuevo": valor}
        return cambios
    
    def validar(self) -> bool:
        """Valida que la configuración sea válida."""
        if self.capacidad <= 0:
            raise ValueError("Capacidad debe ser > 0")
        if self.max_reintentos < 0:
            raise ValueError("Max reintentos no puede ser negativo")
        if not (0.0 < self.backpressure_threshold <= 1.0):
            raise ValueError("Backpressure threshold debe estar entre 0 y 1")
        if self.rate_limit_tokens <= 0:
            raise ValueError("Rate limit tokens debe ser > 0")
        return True
    
    def a_diccionario(self) -> Dict[str, Any]:
        """Exporta configuración como diccionario."""
        return {
            "version": self.version,
            "capacidad": self.capacidad,
            "max_reintentos": self.max_reintentos,
            "ttl_defecto": self.ttl_defecto,
            "backpressure_threshold": self.backpressure_threshold,
            "max_workers": self.max_workers,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "rate_limit_tokens": self.rate_limit_tokens,
            "rate_limit_capacidad": self.rate_limit_capacidad,
            "timestamp_creacion": self.timestamp_creacion
        }
    
    def a_json(self) -> str:
        """Exporta configuración como JSON."""
        return json.dumps(self.a_diccionario(), default=str, indent=2)
    
    @staticmethod
    def desde_diccionario(datos: Dict[str, Any]) -> 'ConfigAgente':
        """Carga configuración desde diccionario."""
        # Ignorar versión y timestamp, usar solo parámetros conocidos
        params = {k: v for k, v in datos.items() 
                 if k not in ['version', 'timestamp_creacion']}
        return ConfigAgente(**params)
    
    @staticmethod
    def desde_json(json_str: str) -> 'ConfigAgente':
        """Carga configuración desde JSON."""
        datos = json.loads(json_str)
        return ConfigAgente.desde_diccionario(datos)


class PoliticaError(Enum):
    """Políticas para manejar errores en tareas fallidas."""
    RETRY = "retry"  # Reintentar según retry_strategy
    DISCARD = "discard"  # Descartar silenciosamente
    DLQ = "dlq"  # Enviar a Dead Letter Queue
    BACKOFF = "backoff"  # Backoff exponencial antes de reintentar


class GestorPoliticasError:
    """Gestiona políticas de error para tareas fallidas."""
    
    def __init__(self, politica_defecto: PoliticaError = PoliticaError.DLQ):
        """
        Inicializa gestor de políticas de error.
        
        Args:
            politica_defecto: Política a usar por defecto
        """
        self.politica_defecto = politica_defecto
        self.politicas_por_tipo_error: Dict[str, PoliticaError] = {}
        self.lock = threading.Lock()
    
    def registrar_politica_por_tipo(self, tipo_error: str, politica: PoliticaError):
        """Registra política específica para tipo de error."""
        with self.lock:
            self.politicas_por_tipo_error[tipo_error.lower()] = politica
            logging.info(f"Política de error registrada: {tipo_error} -> {politica.value}")
    
    def obtener_politica(self, tipo_error: str) -> PoliticaError:
        """Obtiene política para tipo de error."""
        with self.lock:
            tipo_key = tipo_error.lower()
            return self.politicas_por_tipo_error.get(tipo_key, self.politica_defecto)
    
    def debe_reintentar(self, tipo_error: str) -> bool:
        """Determina si se debe reintentar según política."""
        politica = self.obtener_politica(tipo_error)
        return politica in [PoliticaError.RETRY, PoliticaError.BACKOFF]
    
    def debe_enviar_dlq(self, tipo_error: str) -> bool:
        """Determina si enviar a DLQ según política."""
        politica = self.obtener_politica(tipo_error)
        return politica == PoliticaError.DLQ


class GestorAntiInanicion:
    """Previene inanición (starvation) de tareas de baja prioridad.
    
    Las tareas de baja prioridad pueden quedar bloqueadas indefinidamente
    si el sistema recibe continuamente tareas de alta prioridad. Este gestor
    asegura que cada N tareas de alta prioridad, se procese al menos una
    de baja prioridad.
    """
    
    def __init__(self, ratio_minimo_baja_prioridad: float = 0.2):
        """
        Inicializa gestor anti-inanición.
        
        Args:
            ratio_minimo_baja_prioridad: Proporción mínima de tareas de baja 
                                        prioridad a ejecutar (0.0 a 1.0)
        """
        self.ratio_minimo = max(0.0, min(1.0, ratio_minimo_baja_prioridad))
        self.contador_tareas = 0
        self.tareas_baja_prioridad_ejecutadas = 0
        self.lock = threading.Lock()
    
    def puede_saltarse_baja_prioridad(self) -> bool:
        """Determina si se puede saltarse una tarea de baja prioridad."""
        with self.lock:
            if self.contador_tareas == 0:
                return False
            
            # Si no hemos alcanzado el ratio mínimo, NO saltamos tareas de baja prioridad
            ratio_actual = self.tareas_baja_prioridad_ejecutadas / self.contador_tareas
            puede_saltarse = ratio_actual >= self.ratio_minimo
            
            return puede_saltarse
    
    def registrar_tarea_ejecutada(self, es_baja_prioridad: bool):
        """Registra una tarea ejecutada."""
        with self.lock:
            self.contador_tareas += 1
            if es_baja_prioridad:
                self.tareas_baja_prioridad_ejecutadas += 1
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del gestor anti-inanición."""
        with self.lock:
            if self.contador_tareas == 0:
                ratio = 0.0
            else:
                ratio = self.tareas_baja_prioridad_ejecutadas / self.contador_tareas
            
            return {
                "total_tareas": self.contador_tareas,
                "tareas_baja_prioridad": self.tareas_baja_prioridad_ejecutadas,
                "ratio_actual": ratio,
                "ratio_minimo_requerido": self.ratio_minimo,
            }
    
    def limpiar(self):
        """Limpia estadísticas."""
        with self.lock:
            self.contador_tareas = 0
            self.tareas_baja_prioridad_ejecutadas = 0


class SandboxSeguridad:
    """Proporciona validación de seguridad para tareas (denylist/whitelist).
    
    Permite configurar:
    - Denylist: patrones prohibidos
    - Whitelist: patrones permitidos (si está habilitado)
    - Máximo de coincidencias permitidas
    """
    
    def __init__(self, habilitar_whitelist: bool = False):
        """
        Inicializa sandbox de seguridad.
        
        Args:
            habilitar_whitelist: Si True, usa whitelist instead de denylist
        """
        self.denylist: Set[str] = set()
        self.whitelist: Set[str] = set()
        self.habilitar_whitelist = habilitar_whitelist
        self.lock = threading.Lock()
        self.contador_rechazos = 0
        
        # Denylist por defecto: comandos peligrosos
        self._inicializar_denylist_defecto()
    
    def _inicializar_denylist_defecto(self):
        """Agrega patrones peligrosos por defecto."""
        patrones_peligrosos = {
            "rm -rf",  # Borrado recursivo
            "del /s",  # Borrado en Windows
            ">NUL",    # Redirección peligrosa
            "exec(",   # Ejecución dinámica
            "__import__",  # Import dinámico
            "eval(",   # Evaluación dinámica
            "os.system",  # Llamadas al sistema
            "subprocess",  # Spawning procesos
        }
        self.denylist.update(patrones_peligrosos)
    
    def agregar_denylist(self, patron: str):
        """Agrega patrón a denylist."""
        with self.lock:
            self.denylist.add(patron.lower())
            logging.debug(f"Patrón agregado a denylist: {patron}")
    
    def agregar_whitelist(self, patron: str):
        """Agrega patrón a whitelist."""
        with self.lock:
            self.whitelist.add(patron.lower())
            logging.debug(f"Patrón agregado a whitelist: {patron}")
    
    def es_segura_tarea(self, tarea: str) -> bool:
        """Valida si la tarea es segura según políticas.
        
        Returns:
            True si la tarea es segura, False si es rechazada.
        """
        with self.lock:
            tarea_lower = str(tarea).lower()
            
            if self.habilitar_whitelist:
                # Modo whitelist: solo permitir patrones en whitelist
                es_segura = any(patron in tarea_lower for patron in self.whitelist) \
                            or len(self.whitelist) == 0
            else:
                # Modo denylist: rechazar si contiene patrón prohibido
                es_segura = not any(patron in tarea_lower for patron in self.denylist)
            
            if not es_segura:
                self.contador_rechazos += 1
            
            return es_segura
    
    def obtener_estadisticas_seguridad(self) -> Dict[str, Any]:
        """Obtiene estadísticas de validaciones de seguridad."""
        with self.lock:
            return {
                "tareas_rechazadas": self.contador_rechazos,
                "modo": "whitelist" if self.habilitar_whitelist else "denylist",
                "denylist_size": len(self.denylist),
                "whitelist_size": len(self.whitelist),
            }
    
    def limpiar_estadisticas(self):
        """Limpia contadores."""
        with self.lock:
            self.contador_rechazos = 0


class SondeoSalud:
    """Health probe para verificar salud del agente (Kubernetes-style).
    
    Proporciona tres tipos de sondeos:
    - Liveness: ¿El agente está vivo/responsive? (rescata procesos colgados)
    - Readiness: ¿El agente está listo para procesar tareas?
    - Startup: ¿El agente completó la inicialización?
    """
    
    def __init__(self, nombre_agente: str, umbral_inactividad: float = 60.0):
        """
        Inicializa sondeo de salud.
        
        Args:
            nombre_agente: Nombre del agente
            umbral_inactividad: Segundos de inactividad antes de marcar como no vivo
        """
        self.nombre_agente = nombre_agente
        self.umbral_inactividad = umbral_inactividad
        self.timestamp_inicio = time.time()
        self.ultimoContacto = time.time()
        self.lock = threading.Lock()
    
    def marcar_contacto(self):
        """Marca que el agente está activo."""
        with self.lock:
            self.ultimoContacto = time.time()
    
    def sondeo_liveness(self) -> Dict[str, Any]:
        """
        Verifica si el agente está vivo y responsive.
        
        Returns:
            Dict con status: "alive" o "dead"
        """
        with self.lock:
            inactividad_actual = time.time() - self.ultimoContacto
            esta_vivo = inactividad_actual < self.umbral_inactividad
            
            return {
                "status": "alive" if esta_vivo else "dead",
                "segundos_inactivo": round(inactividad_actual, 2),
                "umbral_segundos": self.umbral_inactividad,
                "tipo": "liveness",
                "timestamp": time.time(),
            }
    
    def sondeo_readiness(self, agente_vivo: bool, tamaño_cola: int, capacidad_cola: int) -> Dict[str, Any]:
        """
        Verifica si el agente está listo para procesar tareas.
        
        Args:
            agente_vivo: ¿El agente tiene vivo=True?
            tamaño_cola: Tamaño actual de la cola
            capacidad_cola: Capacidad máxima de la cola
        
        Returns:
            Dict con status: "ready" o "not_ready"
        """
        with self.lock:
            # Agente NO está listo si: no está vivo OR cola está saturada (>80%)
            porcentaje_saturacion = (tamaño_cola / capacidad_cola * 100) if capacidad_cola > 0 else 0
            esta_listo = agente_vivo and porcentaje_saturacion < 80.0
            
            return {
                "status": "ready" if esta_listo else "not_ready",
                "agente_vivo": agente_vivo,
                "tamaño_cola": tamaño_cola,
                "capacidad_cola": capacidad_cola,
                "porcentaje_saturacion": round(porcentaje_saturacion, 2),
                "tipo": "readiness",
                "timestamp": time.time(),
            }
    
    def sondeo_startup(self, inicializacion_completa: bool) -> Dict[str, Any]:
        """
        Verifica si el agente completó la inicialización.
        
        Args:
            inicializacion_completa: ¿Se completó la inicialización?
        
        Returns:
            Dict con status: "started" o "starting"
        """
        with self.lock:
            tiempo_desde_inicio = time.time() - self.timestamp_inicio
            
            return {
                "status": "started" if inicializacion_completa else "starting",
                "tiempo_desde_inicio": round(tiempo_desde_inicio, 2),
                "inicializacion_completa": inicializacion_completa,
                "tipo": "startup",
                "timestamp": time.time(),
            }
    
    def obtener_estado_general(self, agente_vivo: bool, tamaño_cola: int, capacidad_cola: int) -> Dict[str, Any]:
        """Obtiene estado general de todos los sondeos."""
        liveness = self.sondeo_liveness()
        readiness = self.sondeo_readiness(agente_vivo, tamaño_cola, capacidad_cola)
        startup = self.sondeo_startup(agente_vivo)
        
        return {
            "agente": self.nombre_agente,
            "liveness": liveness,
            "readiness": readiness,
            "startup": startup,
            "saludable": liveness["status"] == "alive" and readiness["status"] == "ready",
        }


class SandboxSeguridad:
    """Proporciona validación de seguridad para tareas (denylist/whitelist).
    
    Permite configurar:
    - Denylist: patrones prohibidos
    - Whitelist: patrones permitidos (si está habilitado)
    - Máximo de coincidencias permitidas
    """
    
    def __init__(self, habilitar_whitelist: bool = False):
        """
        Inicializa sandbox de seguridad.
        
        Args:
            habilitar_whitelist: Si True, usa whitelist instead de denylist
        """
        self.denylist: Set[str] = set()
        self.whitelist: Set[str] = set()
        self.habilitar_whitelist = habilitar_whitelist
        self.lock = threading.Lock()
        self.contador_rechazos = 0
        
        # Denylist por defecto: comandos peligrosos
        self._inicializar_denylist_defecto()
    
    def _inicializar_denylist_defecto(self):
        """Agrega patrones peligrosos por defecto."""
        patrones_peligrosos = {
            "rm -rf",  # Borrado recursivo
            "del /s",  # Borrado en Windows
            ">NUL",    # Redirección peligrosa
            "exec(",   # Ejecución dinámica
            "__import__",  # Import dinámico
            "eval(",   # Evaluación dinámica
            "os.system",  # Llamadas al sistema
            "subprocess",  # Spawning procesos
        }
        self.denylist.update(patrones_peligrosos)
    
    def agregar_denylist(self, patron: str):
        """Agrega patrón a denylist."""
        with self.lock:
            self.denylist.add(patron.lower())
            logging.debug(f"Patrón agregado a denylist: {patron}")
    
    def agregar_whitelist(self, patron: str):
        """Agrega patrón a whitelist."""
        with self.lock:
            self.whitelist.add(patron.lower())
            logging.debug(f"Patrón agregado a whitelist: {patron}")
    
    def es_segura_tarea(self, tarea: str) -> bool:
        """Valida si la tarea es segura según políticas.
        
        Returns:
            True si la tarea es segura, False si es rechazada.
        """
        with self.lock:
            tarea_lower = str(tarea).lower()
            
            if self.habilitar_whitelist:
                # Modo whitelist: solo permitir patrones en whitelist
                es_segura = any(patron in tarea_lower for patron in self.whitelist) \
                            or len(self.whitelist) == 0
            else:
                # Modo denylist: rechazar si contiene patrón prohibido
                es_segura = not any(patron in tarea_lower for patron in self.denylist)
            
            if not es_segura:
                self.contador_rechazos += 1
            
            return es_segura
    
    def obtener_estadisticas_seguridad(self) -> Dict[str, Any]:
        """Obtiene estadísticas de validaciones de seguridad."""
        with self.lock:
            return {
                "tareas_rechazadas": self.contador_rechazos,
                "modo": "whitelist" if self.habilitar_whitelist else "denylist",
                "denylist_size": len(self.denylist),
                "whitelist_size": len(self.whitelist),
            }
    
    def limpiar_estadisticas(self):
        """Limpia contadores."""
        with self.lock:
            self.contador_rechazos = 0


class GestorAntiInanicion:
    """Previene inanición (starvation) de tareas de baja prioridad.
    
    Las tareas de baja prioridad pueden quedar bloqueadas indefinidamente
    si el sistema recibe continuamente tareas de alta prioridad. Este gestor
    asegura que cada N tareas de alta prioridad, se procese al menos una
    de baja prioridad.
    """
    
    def __init__(self, ratio_minimo_baja_prioridad: float = 0.2):
        """
        Inicializa gestor anti-inanición.
        
        Args:
            ratio_minimo_baja_prioridad: Proporción mínima de tareas de baja 
                                        prioridad a ejecutar (0.0 a 1.0)
        """
        self.ratio_minimo = max(0.0, min(1.0, ratio_minimo_baja_prioridad))
        self.contador_tareas = 0
        self.tareas_baja_prioridad_ejecutadas = 0
        self.lock = threading.Lock()
    
    def puede_saltarse_baja_prioridad(self) -> bool:
        """Determina si se puede saltarse una tarea de baja prioridad."""
        with self.lock:
            if self.contador_tareas == 0:
                return False
            
            # Si no hemos alcanzado el ratio mínimo, NO saltamos tareas de baja prioridad
            ratio_actual = self.tareas_baja_prioridad_ejecutadas / self.contador_tareas
            puede_saltarse = ratio_actual >= self.ratio_minimo
            
            return puede_saltarse
    
    def registrar_tarea_ejecutada(self, es_baja_prioridad: bool):
        """Registra una tarea ejecutada."""
        with self.lock:
            self.contador_tareas += 1
            if es_baja_prioridad:
                self.tareas_baja_prioridad_ejecutadas += 1
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del gestor anti-inanición."""
        with self.lock:
            if self.contador_tareas == 0:
                ratio = 0.0
            else:
                ratio = self.tareas_baja_prioridad_ejecutadas / self.contador_tareas
            
            return {
                "total_tareas": self.contador_tareas,
                "tareas_baja_prioridad": self.tareas_baja_prioridad_ejecutadas,
                "ratio_actual": ratio,
                "ratio_minimo_requerido": self.ratio_minimo,
            }
    
    def limpiar(self):
        """Limpia estadísticas."""
        with self.lock:
            self.contador_tareas = 0
            self.tareas_baja_prioridad_ejecutadas = 0


class AgenteMaestroNASA(ABC):
    def __init__(
        self,
        nombre,
        capacidad=50,
        max_reintentos=3,
        external_handler=None,
        persistencia_automatica=True,
        max_workers=4,
        backpressure_threshold=0.8,
        retry_strategy: Optional[RetryStrategy] = None,
        circuit_breaker_threshold: int = 5,
    ):
        """Inicializa el agente base.

        Args:
            nombre: Identificador del agente.
            capacidad: Tamaño máximo de la cola de entrada.
            max_reintentos: Reintentos máximos por tarea.
            external_handler: Callback para persistencia externa.
            persistencia_automatica: Persistencia local en JSONL.
            max_workers: Límite de hilos para tareas auxiliares.
            backpressure_threshold: Umbral de carga para backpressure.
            retry_strategy: Estrategia personalizada de reintentos.
            circuit_breaker_threshold: Fallos consecutivos antes de abrir circuito.
        """
        # --- ATRIBUTOS BASE ---
        self.nombre = nombre
        self.buzon_entrada = PriorityQueue()
        self.capacidad = capacidad
        self.max_reintentos = max_reintentos
        self.vivo = True
        self.estado = "IDLE"
        self._ultima_actividad = time.time()

        # --- CONFIGURACIÓN DE EXTENSIONES ---
        self.external_handler = external_handler
        self.persistencia_automatica = persistencia_automatica
        self.lock = threading.Lock()
        self.backpressure_threshold = backpressure_threshold
        self.executor = (
            ThreadPoolExecutor(max_workers=max_workers) if max_workers else None
        )

        # --- ENTERPRISE FEATURES ---
        # Correlation IDs para distributed tracing
        self.correlation_tracker = CorrelationTracker()
        
        # Circuit breaker para fault tolerance
        self.circuit_breaker = CircuitBreaker(failure_threshold=circuit_breaker_threshold)
        
        # Retry strategy personalizable
        self.retry_strategy = retry_strategy or ExponentialBackoffStrategy()
        
        # Lifecycle hooks
        self.lifecycle_hooks = LifecycleHooks()
        
        # Validador de payload
        self.validador_payload = ValidadorPayload(max_bytes=1_000_000)
        
        # Rate limiter: 100 tokens/segundo, capacidad máxima 100
        self.rate_limiter = RateLimiter(tasa_tokens=100.0, capacidad_max=100.0)
        
        # Colector de métricas de rendimiento
        self.colector_metricas = ColectorMetricas(ventana_segundos=60)
        
        # Gestor de política de cola
        self.gestor_cola_politica = GestorColaPolitica(politica=PoliticaCola.PRIORITY)
        
        # Auditor estructurado
        self.auditor = AuditorEstructurado(nombre_agente=nombre)
        
        # Gestor de políticas de error
        self.gestor_politicas_error = GestorPoliticasError(politica_defecto=PoliticaError.DLQ)
        
        # Gestor anti-inanición: 20% de tareas deben ser de baja prioridad
        self.gestor_anti_inanicion = GestorAntiInanicion(ratio_minimo_baja_prioridad=0.2)
        
        # Sandbox de seguridad con denylist de comandos riesgosos
        self.sandbox_seguridad = SandboxSeguridad(habilitar_whitelist=False)
        
        # Sondeo de salud (Kubernetes-style health probes)
        self.sondeo_salud = SondeoSalud(nombre_agente=nombre, umbral_inactividad=60.0)

        # --- PROTECCIÓN DE MEMORIA (RAM) ---
        # Usamos deque para evitar que la lista crezca infinitamente si el agente corre meses
        self.max_memoria = 2000
        self.buzon_salida = deque(maxlen=self.max_memoria)
        self.bitacora_incidentes = deque(maxlen=self.max_memoria)
        self.dead_letter_queue = deque(maxlen=self.max_memoria)

        # --- PERSISTENCIA AUTOMÁTICA (ROTACIÓN) ---
        self.max_registros_por_archivo = 2000
        self.contador_registros = 0
        self.version_log = 1
        self.archivo_log_actual = f"auto_log_{self.nombre}_v{self.version_log}.json"

        # --- MÉTRICAS ---
        self.metricas_globales = {
            "exitos": 0,
            "fallos_recuperados": 0,
            "fallos_fatales": 0,
            "rechazados": 0,
            "muertes_por_ttl": 0,
        }

        # Bloque de percepcion
        self.frecuencia_percepcion = 5  # Segundos entre escaneos
        # Nuevo hilo para la capa de Percepción
        self.hilo_perceptivo = threading.Thread(
            target=self._motor_percepcion, daemon=True
        )
        self.hilo_perceptivo.start()

        # --- INICIO DEL MOTOR ---
        self.hilo_trabajo = threading.Thread(target=self._ciclo_operativo, daemon=True)
        self.hilo_trabajo.start()
        
        # --- INVOCAR HOOK on_start ---
        self.lifecycle_hooks.invocar("on_start", {"agente": self.nombre, "timestamp": time.time()})

    # --- SISTEMA DE PERSISTENCIA Y EVENTOS ---

    def _registrar_en_archivo_automatico(self, tipo, datos):
        """Escribe en disco registro por registro si está habilitado."""
        if not self.persistencia_automatica:
            return
        with self.lock:
            self.contador_registros += 1
            if self.contador_registros > self.max_registros_por_archivo:
                self.version_log += 1
                self.archivo_log_actual = (
                    f"auto_log_{self.nombre}_v{self.version_log}.json"
                )
                self.contador_registros = 1

            registro = {"ts": time.ctime(), "tipo": tipo, "datos": datos}
            try:
                with open(self.archivo_log_actual, "a") as f:
                    f.write(json.dumps(registro) + "\n")
            except Exception as e:
                logging.error(f"Error en persistencia automática: {e}")

    def _despachar_evento(self, tipo_evento, datos):
        """Envía el evento a RAM, Disco y Handler Externo."""
        with self.lock:
            if tipo_evento == "EXITO":
                self.buzon_salida.append(datos)
            else:
                self.bitacora_incidentes.append(datos)

        # Guardado en log rotativo
        self._registrar_en_archivo_automatico(tipo_evento, datos)

        # Ejecución del Handler Externo (en hilo separado para no bloquear)
        if self.external_handler:
            try:
                if self.executor:
                    self.executor.submit(self.external_handler, tipo_evento, datos)
                else:
                    threading.Thread(
                        target=self.external_handler,
                        args=(tipo_evento, datos),
                        daemon=True,
                    ).start()
            except Exception as e:
                logging.error(f"Error en manejador externo: {e}")

    # --- CAPA DE COMUNICACIÓN MULTI-PROTOCOLO ---

    def recibir_mensaje(self, mensaje, prioridad=2, complejidad=5, ttl=10):
        """Decodifica FIPA, KQML, JSON-RPC y Texto Simple.

        Returns:
            ID de la tarea en cola.
        """
        protocolo = "SIMPLE"
        m_id = str(uuid.uuid4())[:8]
        tarea = str(mensaje)

        if isinstance(mensaje, dict):
            # FIPA ACL
            if "performative" in mensaje:
                protocolo = "FIPA"
                m_id = mensaje.get("conversation-id", m_id)
                tarea = f"[{mensaje['performative'].upper()}] {mensaje['content']}"
            # KQML
            elif "verb" in mensaje:
                protocolo = "KQML"
                m_id = mensaje.get("reply-with", m_id)
                tarea = f"[{mensaje['verb'].upper()}] {mensaje['content']}"
            # JSON-RPC
            elif "jsonrpc" in mensaje:
                protocolo = "JSON-RPC"
                m_id = str(mensaje.get("id", m_id))
                tarea = f"[METHOD:{mensaje.get('method')}] {json.dumps(mensaje.get('params', {}))}"

        return self.enviar_orden(tarea, prioridad, complejidad, ttl, m_id, protocolo)

    def enviar_orden(
        self,
        tarea,
        prioridad=2,
        complejidad=5,
        ttl=10,
        m_id=None,
        protocolo="SIMPLE",
        backpressure=False,
        max_backpressure_delay=0.5,
        correlation_id: Optional[str] = None,
    ):
        """Valida saturación y riesgo antes de encolar.

        Args:
            correlation_id: ID de correlación para distributed tracing (opcional).
        
        Raises:
            ValueError: si los parámetros son inválidos.
        """
        if tarea is None:
            raise ValueError("La tarea no puede ser None")
        if not isinstance(prioridad, int) or not 0 <= prioridad <= 5:
            raise ValueError("La prioridad debe ser un entero entre 0 y 5")
        if not isinstance(complejidad, int) or not 1 <= complejidad <= 10:
            raise ValueError("La complejidad debe ser un entero entre 1 y 10")
        if not isinstance(ttl, (int, float)) or ttl <= 0:
            raise ValueError("El ttl debe ser un número mayor a 0")
        
        # Validar payload
        try:
            self.validador_payload.validar(tarea)
        except (TypeError, ValueError) as e:
            logging.error(f"Validación de payload fallida: {e}")
            self.metricas_globales["rechazados"] += 1
            return None
        
        # Rate limiting check
        origen = m_id or "default"
        if not self.rate_limiter.permitir_por_origen(origen, costo=1.0):
            logging.warning(f"Rate limit excedido para origen: {origen}")
            self._registrar_incidente("RATE_LIMIT", tarea, "Limitado por tasa", m_id)
            self.metricas_globales["rechazados"] += 1
            return None
        
        if self.capacidad <= 0:
            self._registrar_incidente("SATURACION", tarea, "Capacidad inválida", m_id)
            return None
        carga_actual = self.buzon_entrada.qsize() / self.capacidad
        if backpressure and carga_actual >= self.backpressure_threshold:
            exceso = min(1.0, (carga_actual - self.backpressure_threshold) / max(0.01, (1 - self.backpressure_threshold)))
            demora = max_backpressure_delay * exceso
            if demora > 0:
                time.sleep(demora)

        if self.buzon_entrada.qsize() >= self.capacidad:
            self._registrar_incidente("SATURACION", tarea, "Cola llena", m_id)
            return None

        # Evaluación de Seguridad
        if (complejidad > 7 and carga_actual > 0.8) or any(
            p in tarea.lower() for p in ["shutdown", "format", "delete_all"]
        ):
            self._registrar_incidente("SEGURIDAD", tarea, "Riesgo detectado", m_id)
            return None

        final_id = m_id if m_id else str(uuid.uuid4())[:8]
        
        # Create or track correlation ID for distributed tracing
        if correlation_id:
            self.correlation_tracker.create_correlation(correlation_id)
        else:
            correlation_id = self.correlation_tracker.create_correlation()
        
        # Registrar en auditoría
        self.auditor.registrar_tarea_enviada(final_id, prioridad, ttl)
        
        self.buzon_entrada.put(
            (prioridad, time.time(), ttl, complejidad, 0, final_id, tarea, protocolo, correlation_id)
        )
        return final_id

    def cancelar_tarea(self, m_id):
        """Cancela una tarea en cola por su ID.

        Returns:
            True si se eliminó, False si no existía.
        """
        if not m_id:
            return False
        removed = 0
        with self.buzon_entrada.mutex:
            items = list(self.buzon_entrada.queue)
            self.buzon_entrada.queue.clear()
            for item in items:
                if item[5] == m_id:
                    removed += 1
                    continue
                self.buzon_entrada.queue.append(item)
            heapq.heapify(self.buzon_entrada.queue)
            if removed:
                self.buzon_entrada.unfinished_tasks = max(
                    0, self.buzon_entrada.unfinished_tasks - removed
                )
        return removed > 0

    # --- MOTOR DE PROCESAMIENTO ---

    def _ciclo_operativo(self):
        """Loop principal de procesamiento de tareas con circuit breaker y retry strategy."""
        logging.info(f"AGENTE {self.nombre}: Modo NASA Industrial Iniciado.")
        while self.vivo:
            try:
                # Unpack with correlation_id (new field)
                item = self.buzon_entrada.get(timeout=1)
                if len(item) == 9:  # Nueva estructura con correlation_id
                    prio, t_llegada, ttl, comp, intentos, m_id, tarea, proto, corr_id = item
                else:  # Compatibilidad hacia atrás
                    prio, t_llegada, ttl, comp, intentos, m_id, tarea, proto = item
                    corr_id = None
                
                self.ultima_actividad = time.time()

                # Verificación de caducidad (TTL)
                if (time.time() - t_llegada) > ttl:
                    self._registrar_incidente("TTL_EXPIRADO", tarea, "Caducidad", m_id)
                    if corr_id:
                        logging.debug(f"[TRACE:{corr_id}] Tarea expirada por TTL")
                    with self.lock:
                        self.metricas_globales["muertes_por_ttl"] += 1
                    self.buzon_entrada.task_done()
                    continue

                self.estado = "TRABAJANDO"
                t_inicio = time.time()
                
                # Registrar inicio de tarea en métricas
                self.colector_metricas.registrar_inicio_tarea(m_id)
                
                if corr_id:
                    logging.debug(f"[TRACE:{corr_id}] Iniciando procesamiento de {m_id}")

                try:
                    # Use circuit breaker to protect external handler execution
                    def execute_trabajo():
                        return self._trabajo_tecnico(tarea)
                    
                    resultado = self.circuit_breaker.call(execute_trabajo)
                    
                    recibo = self._crear_recibo_poliglota(
                        m_id, "COMPLETO", resultado, t_llegada, t_inicio, proto, corr_id
                    )
                    self._despachar_evento("EXITO", recibo)
                    with self.lock:
                        self.metricas_globales["exitos"] += 1
                    
                    # Registrar fin exitoso
                    latencia = time.time() - t_inicio
                    self.colector_metricas.registrar_fin_tarea(m_id, exitosa=True)
                    self.auditor.registrar_tarea_completada(m_id, latencia)
                    
                    self.buzon_entrada.task_done()
                    if corr_id:
                        logging.debug(f"[TRACE:{corr_id}] Tarea {m_id} completada exitosamente")
                        
                except Exception as e:
                    # Usar retry strategy para determinar si reintentar
                    should_retry = self.retry_strategy.should_retry(e, intentos, self.max_reintentos)
                    
                    if should_retry:
                        delay = self.retry_strategy.get_delay(intentos, self.max_reintentos)
                        if corr_id:
                            logging.debug(f"[TRACE:{corr_id}] Reintentando {m_id} en {delay:.2f}s (intento {intentos+1}/{self.max_reintentos})")

                        def reencolar():
                            time.sleep(delay)
                            self.buzon_entrada.put(
                                (prio, t_llegada, ttl, comp, intentos + 1, m_id, tarea, proto, corr_id)
                            )

                        if self.executor:
                            self.executor.submit(reencolar)
                        else:
                            threading.Thread(target=reencolar, daemon=True).start()
                        with self.lock:
                            self.metricas_globales["fallos_recuperados"] += 1
                        self.buzon_entrada.task_done()
                    else:
                        recibo = self._crear_recibo_poliglota(
                            m_id, "ERROR_FATAL", str(e), t_llegada, t_inicio, proto, corr_id
                        )
                        self._despachar_evento("INCIDENTE", recibo)
                        with self.lock:
                            self.dead_letter_queue.append(recibo)
                        with self.lock:
                            self.metricas_globales["fallos_fatales"] += 1
                        
                        # Registrar fin fallido
                        self.colector_metricas.registrar_fin_tarea(m_id, exitosa=False)
                        self.auditor.registrar_error(m_id, type(e).__name__, str(e)[:100])
                        
                        self.buzon_entrada.task_done()
                        if corr_id:
                            logging.error(f"[TRACE:{corr_id}] Fallo fatal en {m_id}: {str(e)}")

                self.estado = "IDLE"
            except Empty:
                continue

    # --- MÉTRICA ABSTRACTA ---
    @abstractmethod
    def _trabajo_tecnico(self, tarea):
        """Este método DEBE ser implementado por el agente hijo."""
        raise NotImplementedError(
            "El agente hijo debe definir su propia lógica en _trabajo_tecnico"
        )

    def _crear_recibo_poliglota(self, m_id, status, resultado, t_llegada, t_inicio, proto, correlation_id=None):
        """Encapsula la respuesta en el protocolo original con correlation ID."""
        core = {
            "mision_id": m_id,
            "status": status,
            "resultado": resultado,
            "espera": round(t_inicio - t_llegada, 4),
            "ejecucion": round(time.time() - t_inicio, 4),
        }
        if correlation_id:
            core["correlation_id"] = correlation_id
        if proto == "FIPA":
            return {"performative": "inform", "content": core, "conversation-id": m_id}
        if proto == "KQML":
            return {"verb": "tell", "content": core, "reply-with": m_id}
        if proto == "JSON-RPC":
            return {"jsonrpc": "2.0", "result": core, "id": m_id}
        return core

    def _registrar_incidente(self, tipo, tarea, causa, m_id=None):
        """Centraliza el registro de errores y rechazos."""
        datos = {
            "tipo": tipo,
            "mision_id": m_id,
            "tarea": tarea,
            "causa": causa,
            "ts": time.ctime(),
        }
        self._despachar_evento("INCIDENTE", datos)
        if tipo in ["SATURACION", "SEGURIDAD"]:
            with self.lock:
                self.metricas_globales["rechazados"] += 1

    # --- MÉTODOS DE DIAGNÓSTICO (Consistentes con el Test) ---

    def obtener_resumen_operativo(self):
        """Retorna métricas operativas del agente."""
        with self.lock:
            return {
                "agente": self.nombre,
                "estado_actual": self.estado,
                "tareas_exitosas": self.metricas_globales["exitos"],
                "tareas_rechazadas_totales": self.metricas_globales["rechazados"],
                "tareas_caducadas_ttl": self.metricas_globales["muertes_por_ttl"],
                "recuperaciones_exitosas": self.metricas_globales[
                    "fallos_recuperados"
                ],
                "tareas_en_espera": self.buzon_entrada.qsize(),
            }

    def obtener_detalle_misiones(self, categoria="exitos", limit=None):
        """Retorna listas detalladas en memoria.

        Args:
            categoria: "exitos", "incidentes" o "cola".
            limit: número máximo de elementos a retornar (desde el final).
        """
        with self.lock:
            if categoria == "exitos":
                if limit is not None:
                    return list(deque(self.buzon_salida, maxlen=limit))
                return list(self.buzon_salida)
            if categoria == "incidentes":
                if limit is not None:
                    return list(deque(self.bitacora_incidentes, maxlen=limit))
                return list(self.bitacora_incidentes)
            if categoria == "cola":
                if limit is not None:
                    return [t[-1] for t in list(deque(self.buzon_entrada.queue, maxlen=limit))]
                return [t[-1] for t in list(self.buzon_entrada.queue)]
            if categoria == "dead_letter":
                if limit is not None:
                    return list(deque(self.dead_letter_queue, maxlen=limit))
                return list(self.dead_letter_queue)
            return {"error": "Categoría no válida"}

    # --- ENTERPRISE FEATURES API ---
    
    def obtener_correlation(self, correlation_id: str) -> Dict[str, Any]:
        """Obtiene el estado y cadena de delegación de una correlación.
        
        Args:
            correlation_id: ID de correlación a rastrear.
        
        Returns:
            Diccionario con metadata y cadena de delegación.
        """
        return self.correlation_tracker.get_metadata(correlation_id)
    
    def obtener_estado_circuito(self) -> str:
        """Obtiene el estado actual del circuit breaker.
        
        Returns:
            "closed", "open", o "half_open".
        """
        return self.circuit_breaker.get_state()
    
    def obtener_estrategia_reintentos(self) -> str:
        """Obtiene la clase de estrategia de reintentos en uso.
        
        Returns:
            Nombre de la clase de estrategia.
        """
        return self.retry_strategy.__class__.__name__

    def monitorear_salud(self):
        """Estado rápido de vitalidad."""
        inactividad = time.time() - self.ultima_actividad
        return {
            "agente": self.nombre,
            "estado": self.estado,
            "inactivo_hace": round(inactividad, 2),
            "circuit_breaker": self.obtener_estado_circuito(),
            "retry_strategy": self.obtener_estrategia_reintentos(),
        }

    # --- CIERRE DE SISTEMA ---

    def apagar_agente(self):
        """Guarda informes finales y detiene el agente."""
        logging.info(f"AGENTE {self.nombre}: Guardando bitácoras finales...")

        with self.lock:
            lista_exitos = list(self.buzon_salida)
            lista_incidentes = list(self.bitacora_incidentes)

        try:
            # Guardado de los dos archivos solicitados
            with open(f"exitos_{self.nombre}.json", "w") as f:
                json.dump(lista_exitos, f, indent=4)
            with open(f"incidentes_{self.nombre}.json", "w") as f:
                json.dump(lista_incidentes, f, indent=4)

            self.vivo = False
            if self.executor:
                self.executor.shutdown(wait=False, cancel_futures=True)
            logging.info(f"AGENTE {self.nombre}: Apagado exitosamente.")
        except Exception as e:
            logging.error(f"Error al guardar bitácoras finales: {e}")

    def enviar_a_otro_agente(self, agente_destino, mensaje, prioridad=2):
        """Permite asignar una tarea a otro agente de la flota."""
        logging.info(f"🔄 {self.nombre} delegando tarea a {agente_destino.nombre}")
        return agente_destino.recibir_mensaje(mensaje, prioridad=prioridad)

    def _motor_percepcion(self):
        while self.vivo:
            # Si la cola está muy llena, esperamos para no saturar
            logging.debug(
                "Agente %s: ciclo de percepcion", self.nombre
            )
            if self.buzon_entrada.qsize() < (self.capacidad / 2):
                try:
                    self.percibir_entorno()
                except Exception as e:
                    logging.error("Error en percepcion: %s", e)

            # Lógica de "Ir a dormir" si no hay actividad
            if self.estado == "IDLE":
                time.sleep(self.frecuencia_percepcion * 2)  # Duerme más si está ocioso
            else:
                time.sleep(self.frecuencia_percepcion)

    def percibir_entorno(self):
        """Método opcional: el hijo decide CÓMO mirar el mundo."""
        return None

    @property
    def ultima_actividad(self):
        with self.lock:
            return self._ultima_actividad

    @ultima_actividad.setter
    def ultima_actividad(self, valor):
        with self.lock:
            self._ultima_actividad = valor    
    # --- LIFECYCLE HOOKS ---
    
    def registrar_hook(self, evento: str, callback: Callable):
        """Registra callback para evento del ciclo de vida.
        
        Eventos disponibles:
            - on_start: Agente iniciado
            - on_stop: Agente detenido
            - on_error: Error no recuperable
        """
        try:
            self.lifecycle_hooks.registrar(evento, callback)
        except ValueError as e:
            logging.error(f"Error registrando hook: {e}")
    
    def invocar_hook_custom(self, nombre_hook: str, *args, **kwargs):
        """Invoca hooks registrados (uso interno)."""
        self.lifecycle_hooks.invocar(nombre_hook, *args, **kwargs)
    
    def configurar_rate_limit(self, tasa_tokens: float, capacidad_max: float):
        """Configura el rate limiter global."""
        self.rate_limiter.tasa_tokens = tasa_tokens
        self.rate_limiter.capacidad_max = capacidad_max
    
    def agregar_limite_origen(self, origen: str, tasa_tokens: float, capacidad_max: float):
        """Agrega límite específico para un origen."""
        self.rate_limiter.registrar_limite_origen(origen, tasa_tokens, capacidad_max)
    
    def obtener_estado_rate_limiter(self) -> Dict[str, Any]:
        """Retorna estado del rate limiter."""
        return self.rate_limiter.obtener_estado()
    
    def obtener_metricas(self) -> Dict[str, Any]:
        """Retorna métricas de rendimiento."""
        return self.colector_metricas.obtener_estado()
    
    def obtener_latencia_promedio(self) -> float:
        """Retorna latencia promedio en segundos."""
        return self.colector_metricas.obtener_latencia_promedio()
    
    def obtener_latencia_p95(self) -> float:
        """Retorna percentil 95 de latencia."""
        return self.colector_metricas.obtener_latencia_p95()
    
    def obtener_throughput(self) -> float:
        """Retorna throughput: tareas por segundo."""
        return self.colector_metricas.obtener_throughput()
    
    def obtener_tasa_error(self) -> float:
        """Retorna tasa de error (0.0 a 1.0)."""
        return self.colector_metricas.obtener_tasa_error()
    
    def limpiar_metricas(self):
        """Limpia todas las métricas recolectadas."""
        self.colector_metricas.limpiar()
    
    def cambiar_politica_cola(self, politica: PoliticaCola):
        """Cambia la política de despacho de la cola."""
        self.gestor_cola_politica.cambiar_politica(politica)
    
    def obtener_politica_cola(self) -> str:
        """Retorna la política de cola actual."""
        return self.gestor_cola_politica.politica.value
    
    def obtener_registros_auditoria(self, últimos: int = 100) -> list:
        """Retorna últimos N registros de auditoría."""
        return self.auditor.obtener_registros(últimos)
    
    def obtener_registros_auditoria_por_evento(self, evento: str) -> list:
        """Retorna registros de auditoría filtrados por evento."""
        return self.auditor.obtener_registros_por_evento(evento)
    
    def exportar_auditoria_json(self) -> str:
        """Exporta auditoría como JSON."""
        return self.auditor.exportar_json()
    
    def configurar_politica_error_defecto(self, politica: PoliticaError):
        """Configura política de error por defecto."""
        self.gestor_politicas_error.politica_defecto = politica
        logging.info(f"Política de error defecto: {politica.value}")
    
    def registrar_politica_error_por_tipo(self, tipo_error: str, politica: PoliticaError):
        """Registra política específica para tipo de error."""
        self.gestor_politicas_error.registrar_politica_por_tipo(tipo_error, politica)
    
    def obtener_politica_error(self, tipo_error: str) -> str:
        """Retorna la política configurada para un tipo de error."""
        politica = self.gestor_politicas_error.obtener_politica(tipo_error)
        return politica.value
    
    def obtener_estadisticas_anti_inanicion(self) -> Dict[str, Any]:
        """Retorna estadísticas de protección contra inanición."""
        return self.gestor_anti_inanicion.obtener_estadisticas()
    
    def establecer_ratio_minimo_baja_prioridad(self, ratio: float):
        """Establece el ratio mínimo de tareas de baja prioridad (0.0 a 1.0)."""
        ratio = max(0.0, min(1.0, ratio))
        self.gestor_anti_inanicion.ratio_minimo = ratio
        logging.info(f"Ratio mínimo de baja prioridad establecido: {ratio}")
    
    def limpiar_estadisticas_anti_inanicion(self):
        """Limpia estadísticas del gestor anti-inanición."""
        self.gestor_anti_inanicion.limpiar()
    
    def agregar_patron_denylist(self, patron: str):
        """Agrega patrón prohibido al sandbox de seguridad."""
        self.sandbox_seguridad.agregar_denylist(patron)
    
    def agregar_patron_whitelist(self, patron: str):
        """Agrega patrón permitido al sandbox de seguridad."""
        self.sandbox_seguridad.agregar_whitelist(patron)
    
    def validar_tarea_segura(self, tarea: str) -> bool:
        """Valida si una tarea es segura según políticas de sandbox."""
        return self.sandbox_seguridad.es_segura_tarea(tarea)
    
    def obtener_estadisticas_seguridad(self) -> Dict[str, Any]:
        """Obtiene estadísticas de validaciones de seguridad."""
        return self.sandbox_seguridad.obtener_estadisticas_seguridad()
    
    def habilitar_modo_whitelist(self, habilitar: bool = True):
        """Habilita o deshabilita el modo whitelist en sandbox."""
        self.sandbox_seguridad.habilitar_whitelist = habilitar
        modo = "whitelist" if habilitar else "denylist"
        logging.info(f"Sandbox modo cambiado a: {modo}")
    
    def limpiar_estadisticas_seguridad(self):
        """Limpia contadores de seguridad."""
        self.sandbox_seguridad.limpiar_estadisticas()
    
    def sondeo_liveness(self) -> Dict[str, Any]:
        """Obtiene estado de liveness del agente (¿está vivo?)."""
        return self.sondeo_salud.sondeo_liveness()
    
    def sondeo_readiness(self) -> Dict[str, Any]:
        """Obtiene estado de readiness del agente (¿está listo?)."""
        return self.sondeo_salud.sondeo_readiness(
            self.vivo,
            self.buzon_entrada.qsize(),
            self.capacidad
        )
    
    def sondeo_startup(self) -> Dict[str, Any]:
        """Obtiene estado de startup del agente (¿terminó inicialización?)."""
        return self.sondeo_salud.sondeo_startup(self.vivo)
    
    def obtener_estado_salud_general(self) -> Dict[str, Any]:
        """Obtiene estado general de salud del agente."""
        return self.sondeo_salud.obtener_estado_general(
            self.vivo,
            self.buzon_entrada.qsize(),
            self.capacidad
        )
    
    def detener_graceful(self, timeout: float = 30.0) -> Dict[str, Any]:
        """
        Detiene el agente de forma elegante (graceful shutdown).
        
        Pasos:
        1. Señal de parada (vivo=False)
        2. Espera a que la cola se vacíe (hasta timeout)
        3. Espera a que terminen los threads
        4. Guarda estado final
        5. Limpia recursos
        
        Args:
            timeout: Segundos máximo para esperar (default 30s)
        
        Returns:
            Dict con estadísticas de shutdown
        """
        logging.info(f"[SHUTDOWN] {self.nombre}: Iniciando parada elegante...")
        inicio_shutdown = time.time()
        
        # 1. Señalar parada
        self.vivo = False
        
        # Invocar hook on_stop
        self.lifecycle_hooks.invocar("on_stop", {"agente": self.nombre, "timestamp": time.time()})
        
        # 2. Esperar a que cola se vacíe (con timeout)
        logging.info(f"[SHUTDOWN] {self.nombre}: Esperando vaciado de cola...")
        inicio_vaciado = time.time()
        while not self.buzon_entrada.empty() and (time.time() - inicio_vaciado) < (timeout * 0.5):
            tamaño_cola = self.buzon_entrada.qsize()
            if tamaño_cola > 0 and tamaño_cola % 10 == 0:
                logging.debug(f"[SHUTDOWN] {self.nombre}: Cola tiene {tamaño_cola} tareas pendientes...")
            time.sleep(0.1)
        
        # 3. Esperar a que terminen threads de trabajo
        logging.info(f"[SHUTDOWN] {self.nombre}: Esperando término de threads...")
        tiempo_espera = timeout - (time.time() - inicio_shutdown)
        
        if self.hilo_trabajo and self.hilo_trabajo.is_alive():
            self.hilo_trabajo.join(timeout=tiempo_espera * 0.5)
        
        if self.hilo_perceptivo and self.hilo_perceptivo.is_alive():
            self.hilo_perceptivo.join(timeout=tiempo_espera * 0.5)
        
        # 4. Ejecutor de tareas
        if self.executor:
            logging.info(f"[SHUTDOWN] {self.nombre}: Apagando executor...")
            self.executor.shutdown(wait=True, cancel_futures=False)
        
        # 5. Guardar estado final
        logging.info(f"[SHUTDOWN] {self.nombre}: Guardando estado final...")
        try:
            lista_exitos = [dict(r) for r in self.buzon_salida]
            lista_incidentes = [dict(r) for r in self.bitacora_incidentes]
            
            with open(f"exitos_{self.nombre}_shutdown.json", "w") as f:
                json.dump(lista_exitos, f, indent=2)
            with open(f"incidentes_{self.nombre}_shutdown.json", "w") as f:
                json.dump(lista_incidentes, f, indent=2)
            
            # Exportar auditoría
            with open(f"auditoria_{self.nombre}_shutdown.json", "w") as f:
                f.write(self.exportar_auditoria_json())
            
        except Exception as e:
            logging.error(f"[SHUTDOWN] {self.nombre}: Error guardando estado: {e}")
        
        # Calcular estadísticas finales
        tiempo_total = time.time() - inicio_shutdown
        stats = {
            "agente": self.nombre,
            "timestamp_shutdown": time.time(),
            "tiempo_parada_segundos": round(tiempo_total, 2),
            "tareas_exitosas": self.metricas_globales["exitos"],
            "tareas_fallidas": self.metricas_globales["fallos_fatales"],
            "tareas_recuperadas": self.metricas_globales["fallos_recuperados"],
            "tareas_rechazadas": self.metricas_globales["rechazados"],
            "dead_letter_size": len(self.dead_letter_queue),
            "cola_pendiente": self.buzon_entrada.qsize(),
            "threads_activos": sum([
                1 if self.hilo_trabajo and self.hilo_trabajo.is_alive() else 0,
                1 if self.hilo_perceptivo and self.hilo_perceptivo.is_alive() else 0
            ]),
            "metricas_completas": self.colector_metricas.obtener_estado()
        }
        
        logging.info(f"[SHUTDOWN] {self.nombre}: Parada completada en {tiempo_total:.2f}s")
        return stats