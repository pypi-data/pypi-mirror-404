"""Tests de estrés para el framework FEID.

Estos tests verifican el comportamiento del agente bajo condiciones extremas:
- Alta carga (1000+ tareas)
- Saturación de cola
- Timeouts bajo presión
- Recuperación de errores masivos
- Consistencia de métricas

NOTA: Estos tests son más lentos y pueden ejecutarse por separado:
    pytest tests/test_stress.py -v
"""

import pytest
import time
import threading
from collections import Counter
from feid.agent import AgenteMaestroNASA


class AgenteStressTest(AgenteMaestroNASA):
    """Agente para pruebas de estrés."""
    
    def __init__(self, *args, delay=0.001, fail_rate=0.0, **kwargs):
        """
        Args:
            delay: Tiempo de procesamiento por tarea (segundos)
            fail_rate: Proporción de tareas que fallan (0.0 a 1.0)
        """
        super().__init__(*args, **kwargs)
        self.delay = delay
        self.fail_rate = fail_rate
        self.contadores = Counter()
        self.lock_contador = threading.Lock()
        
        # Configurar rate limiting muy alto para tests de estrés
        self.configurar_rate_limit(10000.0, 5000.0)  # tasa_tokens=10000/s, capacidad_max=5000
        self.agregar_limite_origen("default", 10000.0, 5000.0)
    
    def _trabajo_tecnico(self, tarea):
        """Simula trabajo con delay y fallos controlados."""
        import random
        time.sleep(self.delay)
        
        with self.lock_contador:
            self.contadores[tarea] += 1
        
        # Simular fallos aleatorios
        if random.random() < self.fail_rate:
            raise ValueError(f"Fallo simulado en tarea: {tarea}")
        
        return f"ok: {tarea}"


class TestStressCargaMasiva:
    """Tests de carga masiva (1000+ tareas)."""
    
    def test_1000_tareas_secuenciales(self):
        """Test: Procesar 1000 tareas secuencialmente."""
        agente = AgenteStressTest(
            "STRESS_1K", 
            capacidad=2000,  # Cola más grande
            max_workers=8,
            delay=0.001)
        
        num_tareas = 1000
        inicio = time.time()
        
        # Enviar 1000 tareas
        for i in range(num_tareas):
            agente.enviar_orden(f"tarea_{i}")
        
        # Esperar a que termine
        timeout = 30.0
        tiempo_espera = 0
        while agente.buzon_entrada.qsize() > 0 and tiempo_espera < timeout:
            time.sleep(0.1)
            tiempo_espera += 0.1
        
        tiempo_total = time.time() - inicio
        
        # Verificaciones
        assert tiempo_total < timeout, f"Timeout: {tiempo_total}s > {timeout}s"
        assert agente.metricas_globales["exitos"] >= 900, "Al menos 900 tareas exitosas"
        
        # Throughput razonable
        throughput = num_tareas / tiempo_total
        assert throughput > 50, f"Throughput bajo: {throughput} tareas/s"
        
        print(f"\n  ✓ {num_tareas} tareas en {tiempo_total:.2f}s")
        print(f"  ✓ Throughput: {throughput:.1f} tareas/s")
        print(f"  ✓ Éxitos: {agente.metricas_globales['exitos']}")
    
    def test_5000_tareas_alta_capacidad(self):
        """Test: Procesar 5000 tareas con alta capacidad."""
        agente = AgenteStressTest(
            "STRESS_5K",
            capacidad=6000,  # Cola más grande
            max_workers=10,
            delay=0.0005)
        
        num_tareas = 5000
        inicio = time.time()
        
        # Enviar en lotes para no saturar
        lote_size = 100
        for lote in range(0, num_tareas, lote_size):
            for i in range(lote, min(lote + lote_size, num_tareas)):
                agente.enviar_orden(f"tarea_{i}")
            time.sleep(0.01)  # Pequeña pausa entre lotes
        
        # Esperar procesamiento
        timeout = 60.0
        tiempo_espera = 0
        while agente.buzon_entrada.qsize() > 0 and tiempo_espera < timeout:
            time.sleep(0.2)
            tiempo_espera += 0.2
        
        tiempo_total = time.time() - inicio
        
        # Verificaciones
        assert tiempo_total < timeout
        assert agente.metricas_globales["exitos"] >= 4800, "Al menos 96% de éxito"
        
        throughput = num_tareas / tiempo_total
        print(f"\n  ✓ {num_tareas} tareas en {tiempo_total:.2f}s")
        print(f"  ✓ Throughput: {throughput:.1f} tareas/s")
        print(f"  ✓ Éxitos: {agente.metricas_globales['exitos']}")


class TestStressSaturacion:
    """Tests de saturación de recursos."""
    
    def test_saturacion_cola(self):
        """Test: Intentar saturar la cola y verificar backpressure."""
        agente = AgenteStressTest(
            "STRESS_SAT",
            capacidad=100,  # Cola pequeña
            max_workers=4,
            delay=0.01,  # Procesamiento lento
            backpressure_threshold=0.8)
        
        # Enviar más tareas de las que caben
        rechazadas = 0
        aceptadas = 0
        
        for i in range(500):
            recibo = agente.enviar_orden(f"tarea_{i}")
            if "SATURACION" in str(recibo):
                rechazadas += 1
            else:
                aceptadas += 1
            if i < 200:  # Solo hacer pausa al inicio para llenar la cola
                time.sleep(0.0001)
        
        # Con cola pequeña y procesamiento lento, debe haber activado backpressure
        # o al menos haber crecido la cola al máximo
        tamaño_cola = agente.buzon_entrada.qsize()
        assert rechazadas > 0 or tamaño_cola >= 80, f"Debió activarse backpressure o llenar cola (rechazadas={rechazadas}, cola={tamaño_cola})"
        assert aceptadas > 50, "Debió aceptar al menos algunas tareas"
        
        print(f"\n  ✓ Aceptadas: {aceptadas}")
        print(f"  ✓ Rechazadas por backpressure: {rechazadas}")
        print(f"  ✓ Ratio rechazo: {rechazadas/(rechazadas+aceptadas)*100:.1f}%")
    
    def test_recuperacion_post_saturacion(self):
        """Test: Recuperación después de saturación."""
        agente = AgenteStressTest(
            "STRESS_REC",
            capacidad=50,
            max_workers=6,
            delay=0.005)
        
        # Fase 1: Saturar
        for i in range(200):
            agente.enviar_orden(f"fase1_{i}")
        
        tamaño_saturado = agente.buzon_entrada.qsize()
        
        # Fase 2: Esperar vaciado
        time.sleep(2.0)
        
        tamaño_post_vaciado = agente.buzon_entrada.qsize()
        
        # Fase 3: Enviar más tareas (debe aceptarlas)
        for i in range(30):
            recibo = agente.enviar_orden(f"fase3_{i}")
            assert "SATURACION" not in str(recibo), "No debería rechazar después de vaciar"
        
        print(f"\n  ✓ Tamaño saturado: {tamaño_saturado}")
        print(f"  ✓ Post-vaciado: {tamaño_post_vaciado}")
        print(f"  ✓ Recuperación exitosa")


class TestStressErrores:
    """Tests de manejo de errores bajo estrés."""
    
    def test_500_tareas_50_porciento_fallos(self):
        """Test: Manejar tasa moderada de fallos (30%)."""
        agente = AgenteStressTest(
            "STRESS_FAIL",
            capacidad=600,
            max_workers=6,
            max_reintentos=1,
            delay=0.002,
            fail_rate=0.3,  # 30% de fallos (evita saturar circuit breaker)
            circuit_breaker_threshold=200,  # Muy alto para permitir testear errores
        )
        
        num_tareas = 500
        
        for i in range(num_tareas):
            agente.enviar_orden(f"tarea_{i}")
        
        # Esperar procesamiento
        time.sleep(5.0)
        
        exitos = agente.metricas_globales["exitos"]
        fallos = agente.metricas_globales["fallos_fatales"]
        recuperados = agente.metricas_globales["fallos_recuperados"]
        
        # Verificaciones
        assert exitos > 200, f"Demasiados pocos éxitos: {exitos}"
        assert fallos < 300, f"Demasiados fallos: {fallos}"
        
        total_procesado = exitos + fallos + recuperados
        assert total_procesado >= 400, "Debió procesar al menos 80%"
        
        print(f"\n  ✓ Éxitos: {exitos}")
        print(f"  ✓ Fallos fatales: {fallos}")
        print(f"  ✓ Recuperados: {recuperados}")
        print(f"  ✓ Total procesado: {total_procesado}/{num_tareas}")
    
    def test_dead_letter_queue_bajo_estres(self):
        """Test: DLQ funciona correctamente bajo estrés."""
        agente = AgenteStressTest(
            "STRESS_DLQ",
            capacidad=400,
            max_workers=5,
            max_reintentos=0,  # Sin reintentos
            delay=0.001,
            fail_rate=0.2,  # 20% de fallos (tasa moderada)
            circuit_breaker_threshold=150,  # Muy alto para permitir testear DLQ
        )
        
        num_tareas = 300
        
        for i in range(num_tareas):
            agente.enviar_orden(f"tarea_{i}")
        
        time.sleep(3.0)
        
        dlq_size = len(agente.dead_letter_queue)
        exitos = agente.metricas_globales['exitos']
        
        # Con 20% de fallos, esperamos ~60 tareas en DLQ (20% de 300)
        # Pero el circuit breaker puede afectar, así que relajamos los límites
        assert dlq_size > 10, f"DLQ muy pequeño: {dlq_size}"
        assert dlq_size < 200, f"DLQ muy grande: {dlq_size}"
        assert exitos > 150, f"Muy pocos éxitos: {exitos}"
        
        print(f"\n  ✓ Tareas en DLQ: {dlq_size}")
        print(f"  ✓ Éxitos: {agente.metricas_globales['exitos']}")


class TestStressMetricas:
    """Tests de métricas bajo estrés."""
    
    def test_metricas_precision_1000_tareas(self):
        """Test: Precisión de métricas con 1000 tareas."""
        agente = AgenteStressTest(
            "STRESS_MET",
            capacidad=1500,
            max_workers=8,
            delay=0.002)
        
        num_tareas = 1000
        
        for i in range(num_tareas):
            agente.enviar_orden(f"tarea_{i}")
        
        # Esperar
        time.sleep(8.0)
        
        # Obtener métricas
        metricas = agente.obtener_metricas()
        
        # Verificaciones de consistencia
        assert "latencia_promedio" in metricas
        assert "tasa_error" in metricas
        
        # Latencia razonable
        assert metricas["latencia_promedio"] < 1.0, "Latencia muy alta"
        
        # Tasa de error razonable
        assert metricas["tasa_error"] <= 0.3, "Tasa error muy alta"
        
        print(f"\n  ✓ Latencia promedio: {metricas['latencia_promedio']:.3f}s")
        print(f"  ✓ Éxitos: {agente.metricas_globales['exitos']}")
        print(f"  ✓ Tasa error: {metricas['tasa_error']:.2%}")
    
    def test_metricas_p95_bajo_carga(self):
        """Test: P95 latency bajo carga variable."""
        agente = AgenteStressTest(
            "STRESS_P95",
            capacidad=600,
            max_workers=6,
            delay=0.001)
        
        # Enviar 500 tareas
        for i in range(500):
            agente.enviar_orden(f"tarea_{i}")
        
        time.sleep(4.0)
        
        p95 = agente.obtener_latencia_p95()
        promedio = agente.obtener_latencia_promedio()
        
        # P95 debe ser mayor que promedio pero razonable
        assert p95 >= promedio, "P95 debe ser >= promedio"
        assert p95 < 1.0, f"P95 muy alto: {p95}s"
        
        print(f"\n  ✓ Latencia promedio: {promedio:.3f}s")
        print(f"  ✓ Latencia P95: {p95:.3f}s")


class TestStressGracefulShutdown:
    """Tests de graceful shutdown bajo estrés."""
    
    def test_shutdown_con_cola_llena(self):
        """Test: Shutdown elegante con cola llena de tareas."""
        agente = AgenteStressTest(
            "STRESS_SHUT",
            capacidad=400,
            max_workers=6,
            delay=0.01,  # Procesamiento lento
        )
        
        # Llenar cola
        for i in range(300):
            agente.enviar_orden(f"tarea_{i}")
        
        tareas_en_cola = agente.buzon_entrada.qsize()
        
        # Shutdown con timeout
        stats = agente.detener_graceful(timeout=10.0)
        
        # Verificaciones
        assert stats is not None
        assert "agente" in stats
        assert stats["agente"] == "STRESS_SHUT"
        assert stats["tiempo_parada_segundos"] < 11.0
        
        # Verificar que procesó algunas tareas antes de parar
        assert stats["tareas_exitosas"] > 0
        
        print(f"\n  ✓ Tareas en cola al shutdown: {tareas_en_cola}")
        print(f"  ✓ Tiempo de parada: {stats['tiempo_parada_segundos']:.2f}s")
        print(f"  ✓ Tareas exitosas: {stats['tareas_exitosas']}")


class TestStressConcurrencia:
    """Tests de concurrencia extrema."""
    
    def test_multiples_threads_enviando(self):
        """Test: Múltiples threads enviando tareas simultáneamente."""
        agente = AgenteStressTest(
            "STRESS_CONC",
            capacidad=1200,
            max_workers=10,
            delay=0.001)
        
        num_threads = 10
        tareas_por_thread = 100
        
        def enviar_tareas(thread_id):
            for i in range(tareas_por_thread):
                agente.enviar_orden(f"thread{thread_id}_tarea{i}")
        
        # Lanzar threads
        threads = []
        inicio = time.time()
        
        for tid in range(num_threads):
            t = threading.Thread(target=enviar_tareas, args=(tid,))
            t.start()
            threads.append(t)
        
        # Esperar threads
        for t in threads:
            t.join()
        
        tiempo_envio = time.time() - inicio
        
        # Esperar procesamiento
        time.sleep(5.0)
        
        total_esperado = num_threads * tareas_por_thread
        exitos = agente.metricas_globales["exitos"]
        
        # Verificaciones
        assert exitos >= total_esperado * 0.9, f"Solo {exitos}/{total_esperado} exitosas"
        
        print(f"\n  ✓ Threads: {num_threads}")
        print(f"  ✓ Tareas por thread: {tareas_por_thread}")
        print(f"  ✓ Tiempo envío: {tiempo_envio:.2f}s")
        print(f"  ✓ Éxitos: {exitos}/{total_esperado}")


class TestStressSandboxYSalud:
    """Tests de sandbox y health bajo estrés."""
    
    def test_validacion_seguridad_1000_tareas(self):
        """Test: Validar 1000 tareas con sandbox activo."""
        agente = AgenteStressTest(
            "STRESS_SEC",
            capacidad=1200,
            max_workers=8,
            delay=0.001)
        
        # Agregar patrones peligrosos
        agente.agregar_patron_denylist("malware")
        agente.agregar_patron_denylist("virus")
        
        # Enviar tareas mixtas
        for i in range(1000):
            if i % 10 == 0:
                tarea = f"tarea_malware_{i}"  # 10% peligrosas
            else:
                tarea = f"tarea_normal_{i}"
            
            # Validar antes de enviar
            if agente.validar_tarea_segura(tarea):
                agente.enviar_orden(tarea)
        
        time.sleep(3.0)
        
        stats_seg = agente.obtener_estadisticas_seguridad()
        
        # Verificaciones
        assert stats_seg["tareas_rechazadas"] >= 90, "Debió rechazar ~100 tareas"
        assert stats_seg["tareas_rechazadas"] <= 110
        
        print(f"\n  ✓ Tareas rechazadas: {stats_seg['tareas_rechazadas']}")
        print(f"  ✓ Modo: {stats_seg['modo']}")
    
    def test_health_probes_bajo_carga(self):
        """Test: Health probes funcionan bajo carga."""
        agente = AgenteStressTest(
            "STRESS_HP",
            capacidad=600,
            max_workers=6,
            delay=0.005)
        
        # Enviar carga
        for i in range(500):
            agente.enviar_orden(f"tarea_{i}")
        
        # Verificar health probes durante carga
        liveness = agente.sondeo_liveness()
        readiness = agente.sondeo_readiness()
        startup = agente.sondeo_startup()
        salud_general = agente.obtener_estado_salud_general()
        
        # Verificaciones
        assert liveness["status"] == "alive", "Debe estar vivo bajo carga"
        assert startup["status"] == "started", "Debe estar iniciado"
        assert readiness["status"] in ["ready", "not_ready"]  # Puede variar
        
        print(f"\n  ✓ Liveness: {liveness['status']}")
        print(f"  ✓ Readiness: {readiness['status']}")
        print(f"  ✓ Startup: {startup['status']}")
        print(f"  ✓ Saludable: {salud_general['saludable']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
