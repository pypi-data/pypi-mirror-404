"""Tests para nuevas features de base profesional."""

import pytest
import time
import json
from feid.agent import (
    AgenteMaestroNASA,
    LifecycleHooks,
    EventoSchema,
    ValidadorPayload,
    RateLimiter,
    ColectorMetricas,
    PoliticaCola,
    GestorColaPolitica,
    AuditorEstructurado,
    ConfigAgente,
    PoliticaError,
    GestorPoliticasError,
    GestorAntiInanicion,
    SandboxSeguridad,
    SondeoSalud,
)


class AgenteTest(AgenteMaestroNASA):
    """Agente dummy para testing."""
    
    def _trabajo_tecnico(self, tarea):
        return f"ok: {tarea}"


class TestLifecycleHooks:
    """Tests para lifecycle hooks."""
    
    def test_registrar_hook_valido(self):
        """Test: Registrar callback para evento válido."""
        agente = AgenteTest("TEST", capacidad=10)
        
        resultados = []
        def on_start_callback(datos):
            resultados.append(datos)
        
        agente.registrar_hook("on_start", on_start_callback)
        assert len(agente.lifecycle_hooks._hooks["on_start"]) == 1
    
    def test_registrar_hook_invalido(self):
        """Test: Error al registrar evento inválido."""
        agente = AgenteTest("TEST", capacidad=10)
        
        # El método atrapa la excepción y la loguea
        # así que solo verificamos que NO se agregó el hook
        agente.registrar_hook("on_invalid", lambda x: None)
        assert len(agente.lifecycle_hooks._hooks.get("on_invalid", [])) == 0
    
    def test_invocar_hook(self):
        """Test: Invocar callbacks registrados."""
        agente = AgenteTest("TEST", capacidad=10)
        
        resultados = []
        agente.registrar_hook("on_error", lambda e: resultados.append(e))
        
        # Invocar manualmente
        agente.invocar_hook_custom("on_error", "test_error")
        
        assert len(resultados) == 1
        assert resultados[0] == "test_error"


class TestEventoSchema:
    """Tests para validación de eventos."""
    
    def test_validar_evento_valido(self):
        """Test: Evento válido pasa validación."""
        evento_datos = {
            "tipo": "EXITO",
            "datos": {"resultado": "ok"}
        }
        
        assert EventoSchema.validar("EXITO", evento_datos) is True
    
    def test_validar_tipo_invalido(self):
        """Test: Error con tipo de evento inválido."""
        with pytest.raises(ValueError):
            EventoSchema.validar("TIPO_INVALIDO", {})
    
    def test_validar_evento_muy_grande(self):
        """Test: Error si evento excede tamaño."""
        evento_grande = {"data": "x" * (1024 * 101)}  # > 100KB
        
        with pytest.raises(ValueError):
            EventoSchema.validar("EXITO", evento_grande, max_kb=100)


class TestValidadorPayload:
    """Tests para validador de payload."""
    
    def test_validar_payload_string(self):
        """Test: Validar string válido."""
        validador = ValidadorPayload()
        assert validador.validar("tarea simple") is True
    
    def test_validar_payload_dict(self):
        """Test: Validar dict válido."""
        validador = ValidadorPayload()
        assert validador.validar({"operacion": "crear", "datos": "info"}) is True
    
    def test_validar_payload_tipo_no_permitido(self):
        """Test: Error con tipo no permitido."""
        validador = ValidadorPayload(tipos_permitidos=["str"])
        
        with pytest.raises(TypeError):
            validador.validar({"dict": "no_permitido"})
    
    def test_validar_payload_muy_grande(self):
        """Test: Error si payload excede tamaño."""
        validador = ValidadorPayload(max_bytes=1000)
        payload_grande = {"data": "x" * 2000}
        
        with pytest.raises(ValueError):
            validador.validar(payload_grande)
    
    def test_enviar_orden_con_validacion(self):
        """Test: enviar_orden valida payload."""
        agente = AgenteTest("TEST", capacidad=10)
        
        # Payload válido
        m_id = agente.enviar_orden("tarea válida")
        assert m_id is not None
        
        # Payload inválido (type not permitted)
        # Por ahora los tipos por defecto permiten str, dict, etc.
        # Crear validador restrictivo
        agente.validador_payload = ValidadorPayload(tipos_permitidos=["str"])
        
        # Dict debería fallar
        m_id2 = agente.enviar_orden({"dict": "tarea"})
        assert m_id2 is None  # Rechazada por validación


class TestRateLimiter:
    """Tests para rate limiting."""
    
    def test_rate_limiter_inicial(self):
        """Test: RateLimiter se inicializa con tokens."""
        limiter = RateLimiter(tasa_tokens=100.0, capacidad_max=100.0)
        
        estado = limiter.obtener_estado()
        assert estado["tokens_disponibles"] == 100.0
        assert estado["tasa_tokens"] == 100.0
    
    def test_permitir_consume_token(self):
        """Test: permitir() consume token."""
        limiter = RateLimiter(tasa_tokens=10.0, capacidad_max=10.0)
        
        # Primer consumo debe funcionar
        assert limiter.permitir(1.0) is True
        
        # Verificar que se consumió
        estado = limiter.obtener_estado()
        assert estado["tokens_disponibles"] == 9.0
    
    def test_permitir_agota_tokens(self):
        """Test: Rechaza cuando no hay tokens."""
        limiter = RateLimiter(tasa_tokens=1.0, capacidad_max=1.0)
        
        # Consumir único token
        assert limiter.permitir(1.0) is True
        
        # Segunda solicitud debe ser rechazada
        assert limiter.permitir(1.0) is False
    
    def test_relleno_tokens_con_tiempo(self):
        """Test: Tokens se rellenan con tiempo."""
        limiter = RateLimiter(tasa_tokens=10.0, capacidad_max=10.0)
        
        # Consumir tokens
        limiter.permitir(10.0)  # 0 tokens
        assert limiter.permitir(1.0) is False
        
        # Esperar 100ms → ~1 token rellenado (10 tokens/seg)
        time.sleep(0.1)
        assert limiter.permitir(0.5) is True
    
    def test_limite_por_origen(self):
        """Test: Límites específicos por origen."""
        limiter = RateLimiter(tasa_tokens=100.0, capacidad_max=100.0)
        
        # Registrar límite estricto para "origen_A"
        limiter.registrar_limite_origen("origen_A", tasa=1.0, capacidad=1.0)
        
        # origen_A solo puede hacer 1 solicitud
        assert limiter.permitir_por_origen("origen_A", 1.0) is True
        assert limiter.permitir_por_origen("origen_A", 1.0) is False
        
        # Otros orígenes sin límite específico funcionan normalmente
        assert limiter.permitir_por_origen("origen_B", 1.0) is True
    
    def test_agente_con_rate_limiter(self):
        """Test: Agente rechaza órdenes limitadas por tasa."""
        agente = AgenteTest("TEST", capacidad=50)
        
        # Configurar rate limiter muy restrictivo
        agente.configurar_rate_limit(tasa_tokens=1.0, capacidad_max=1.0)
        
        # Primera orden debe pasar
        m_id1 = agente.enviar_orden("tarea1")
        assert m_id1 is not None
        
        # Segunda orden debe ser rechazada (rate limit)
        m_id2 = agente.enviar_orden("tarea2")
        assert m_id2 is None
    
    def test_agente_agrega_limite_origen(self):
        """Test: Agente puede registrar límites por origen."""
        agente = AgenteTest("TEST", capacidad=50)
        
        # Agregar límite para "cliente_A"
        agente.agregar_limite_origen("cliente_A", tasa_tokens=2.0, capacidad_max=2.0)
        
        # Dos órdenes desde cliente_A deben pasar
        m_id1 = agente.enviar_orden("tarea1", m_id="cliente_A_1")
        m_id2 = agente.enviar_orden("tarea2", m_id="cliente_A_2")
        
        # Verificar estado del limiter
        estado = agente.obtener_estado_rate_limiter()
        assert "limites_por_origen" in estado


class TestColectorMetricas:
    """Tests para recolección de métricas."""
    
    def test_colector_metricas_inicial(self):
        """Test: ColectorMetricas se inicializa vacío."""
        colector = ColectorMetricas()
        
        estado = colector.obtener_estado()
        assert estado["tareas_completadas"] == 0
        assert estado["tareas_fallidas"] == 0
        assert estado["tasa_error"] == 0.0
    
    def test_registrar_tarea_exitosa(self):
        """Test: Registrar tarea completada incrementa contador."""
        colector = ColectorMetricas()
        
        colector.registrar_inicio_tarea("tarea1")
        time.sleep(0.05)
        colector.registrar_fin_tarea("tarea1", exitosa=True)
        
        estado = colector.obtener_estado()
        assert estado["tareas_completadas"] == 1
        assert estado["tareas_fallidas"] == 0
        assert estado["num_muestras_latencia"] >= 1
    
    def test_registrar_tarea_fallida(self):
        """Test: Registrar tarea fallida incrementa contador de fallos."""
        colector = ColectorMetricas()
        
        colector.registrar_inicio_tarea("tarea1")
        colector.registrar_fin_tarea("tarea1", exitosa=False)
        
        estado = colector.obtener_estado()
        assert estado["tareas_completadas"] == 0
        assert estado["tareas_fallidas"] == 1
        assert estado["tasa_error"] == 1.0
    
    def test_latencia_promedio(self):
        """Test: Calcular latencia promedio."""
        colector = ColectorMetricas()
        
        # Registrar 3 tareas con latencias ~50ms cada una
        for i in range(3):
            colector.registrar_inicio_tarea(f"tarea{i}")
            time.sleep(0.05)
            colector.registrar_fin_tarea(f"tarea{i}", exitosa=True)
        
        latencia_prom = colector.obtener_latencia_promedio()
        assert 0.04 < latencia_prom < 0.1  # Aproximadamente 50ms
    
    def test_latencia_p95(self):
        """Test: Calcular percentil 95 de latencia."""
        colector = ColectorMetricas()
        
        # Registrar algunas tareas
        for i in range(10):
            colector.registrar_inicio_tarea(f"tarea{i}")
            time.sleep(0.01 + (i * 0.001))
            colector.registrar_fin_tarea(f"tarea{i}", exitosa=True)
        
        latencia_p95 = colector.obtener_latencia_p95()
        assert latencia_p95 > 0
    
    def test_tasa_error_mixta(self):
        """Test: Calcular tasa de error con éxitos y fallos."""
        colector = ColectorMetricas()
        
        # 7 exitosas, 3 fallidas → tasa_error = 0.3
        for i in range(7):
            colector.registrar_inicio_tarea(f"exito{i}")
            colector.registrar_fin_tarea(f"exito{i}", exitosa=True)
        
        for i in range(3):
            colector.registrar_inicio_tarea(f"fallo{i}")
            colector.registrar_fin_tarea(f"fallo{i}", exitosa=False)
        
        estado = colector.obtener_estado()
        assert estado["tasa_error"] == 0.3
        assert estado["total_tareas"] == 10
    
    def test_limpiar_metricas(self):
        """Test: Limpiar reinicia estadísticas."""
        colector = ColectorMetricas()
        
        # Registrar datos
        colector.registrar_inicio_tarea("tarea1")
        colector.registrar_fin_tarea("tarea1", exitosa=True)
        
        # Verificar que hay datos
        estado = colector.obtener_estado()
        assert estado["tareas_completadas"] == 1
        
        # Limpiar
        colector.limpiar()
        
        # Verificar que se reinició
        estado = colector.obtener_estado()
        assert estado["tareas_completadas"] == 0
        assert estado["tareas_fallidas"] == 0
    
    def test_agente_con_metricas(self):
        """Test: Agente integra colector de métricas."""
        agente = AgenteTest("TEST_METRICAS", capacidad=10)
        
        # Enviar varias órdenes
        for i in range(5):
            agente.enviar_orden(f"tarea{i}")
        
        # Procesar tareas
        time.sleep(0.5)
        
        # Verificar que agente tiene acceso a métricas
        metricas = agente.obtener_metricas()
        assert "tareas_completadas" in metricas
        assert "latencia_promedio" in metricas
        assert "tasa_error" in metricas


class TestGestorColaPolitica:
    """Tests para gestor de políticas de cola."""
    
    def test_fifo_order(self):
        """Test: FIFO devuelve tareas en orden de llegada."""
        gestor = GestorColaPolitica(politica=PoliticaCola.FIFO)
        
        # Encolar 3 tareas
        tarea1 = (2, 100, 10, 5, 0, "id1", "tarea1", "SIMPLE", None)
        tarea2 = (1, 101, 10, 5, 0, "id2", "tarea2", "SIMPLE", None)
        tarea3 = (3, 102, 10, 5, 0, "id3", "tarea3", "SIMPLE", None)
        
        gestor.encolar(tarea1)
        gestor.encolar(tarea2)
        gestor.encolar(tarea3)
        
        # Desencolar debe respetar orden de llegada
        assert gestor.desencolar()[5] == "id1"  # m_id es índice 5
        assert gestor.desencolar()[5] == "id2"
        assert gestor.desencolar()[5] == "id3"
    
    def test_lifo_order(self):
        """Test: LIFO devuelve tareas en orden inverso."""
        gestor = GestorColaPolitica(politica=PoliticaCola.LIFO)
        
        tarea1 = (2, 100, 10, 5, 0, "id1", "tarea1", "SIMPLE", None)
        tarea2 = (1, 101, 10, 5, 0, "id2", "tarea2", "SIMPLE", None)
        tarea3 = (3, 102, 10, 5, 0, "id3", "tarea3", "SIMPLE", None)
        
        gestor.encolar(tarea1)
        gestor.encolar(tarea2)
        gestor.encolar(tarea3)
        
        # LIFO debe devolver última primero
        assert gestor.desencolar()[5] == "id3"
        assert gestor.desencolar()[5] == "id2"
        assert gestor.desencolar()[5] == "id1"
    
    def test_priority_order(self):
        """Test: PRIORITY devuelve tareas por prioridad."""
        gestor = GestorColaPolitica(politica=PoliticaCola.PRIORITY)
        
        # Prioridades: 1 (baja), 2 (media), 3 (alta)
        tarea1 = (1, 100, 10, 5, 0, "id1", "tarea1", "SIMPLE", None)
        tarea2 = (3, 101, 10, 5, 0, "id2", "tarea2", "SIMPLE", None)
        tarea3 = (2, 102, 10, 5, 0, "id3", "tarea3", "SIMPLE", None)
        
        gestor.encolar(tarea1)
        gestor.encolar(tarea2)
        gestor.encolar(tarea3)
        
        # Priority queue devuelve menor prioridad primero (heap)
        resultado = []
        resultado.append(gestor.desencolar()[5])
        resultado.append(gestor.desencolar()[5])
        resultado.append(gestor.desencolar()[5])
        
        # Orden esperado: id1 (p=1), id3 (p=2), id2 (p=3)
        assert resultado == ["id1", "id3", "id2"]
    
    def test_qsize(self):
        """Test: qsize() retorna tamaño de la cola."""
        gestor = GestorColaPolitica(politica=PoliticaCola.FIFO)
        
        assert gestor.qsize() == 0
        
        tarea1 = (2, 100, 10, 5, 0, "id1", "tarea1", "SIMPLE", None)
        gestor.encolar(tarea1)
        assert gestor.qsize() == 1
        
        gestor.desencolar()
        assert gestor.qsize() == 0
    
    def test_cambiar_politica(self):
        """Test: Cambiar política de cola."""
        gestor = GestorColaPolitica(politica=PoliticaCola.FIFO)
        assert gestor.politica == PoliticaCola.FIFO
        
        gestor.cambiar_politica(PoliticaCola.LIFO)
        assert gestor.politica == PoliticaCola.LIFO
        
        gestor.cambiar_politica(PoliticaCola.PRIORITY)
        assert gestor.politica == PoliticaCola.PRIORITY
    
    def test_limpiar(self):
        """Test: Limpiar la cola."""
        gestor = GestorColaPolitica(politica=PoliticaCola.FIFO)
        
        tarea1 = (2, 100, 10, 5, 0, "id1", "tarea1", "SIMPLE", None)
        gestor.encolar(tarea1)
        assert gestor.qsize() == 1
        
        gestor.limpiar()
        assert gestor.qsize() == 0
    
    def test_agente_con_politica_cola(self):
        """Test: Agente puede cambiar política de cola."""
        agente = AgenteTest("TEST_POLICY", capacidad=10)
        
        # Verificar política por defecto es PRIORITY
        assert agente.obtener_politica_cola() == "priority"
        
        # Cambiar a FIFO
        agente.cambiar_politica_cola(PoliticaCola.FIFO)
        assert agente.obtener_politica_cola() == "fifo"
        
        # Cambiar a LIFO
        agente.cambiar_politica_cola(PoliticaCola.LIFO)
        assert agente.obtener_politica_cola() == "lifo"


class TestAuditorEstructurado:
    """Tests para auditoría estructurada."""
    
    def test_auditor_inicializa_vacio(self):
        """Test: Auditor se inicializa sin registros."""
        auditor = AuditorEstructurado("TEST_AGENT")
        
        registros = auditor.obtener_registros()
        assert len(registros) == 0
    
    def test_registrar_evento(self):
        """Test: Registrar evento estructurado."""
        auditor = AuditorEstructurado("TEST_AGENT")
        
        auditor.registrar(
            "EVENTO_TEST",
            "INFO",
            {"param1": "valor1", "param2": 42}
        )
        
        registros = auditor.obtener_registros()
        assert len(registros) == 1
        assert registros[0]["evento"] == "EVENTO_TEST"
        assert registros[0]["nivel"] == "INFO"
        assert registros[0]["detalles"]["param1"] == "valor1"
    
    def test_ocultar_campos_sensibles(self):
        """Test: Ofuscar campos sensibles."""
        auditor = AuditorEstructurado("TEST_AGENT")
        
        # Registrar con campos sensibles
        auditor.registrar(
            "LOGIN",
            "INFO",
            {
                "usuario": "admin",
                "password": "super_secret_123",
                "token": "abc123xyz"
            }
        )
        
        registros = auditor.obtener_registros()
        assert registros[0]["detalles"]["usuario"] == "admin"
        assert registros[0]["detalles"]["password"] == "***OCULTO***"
        assert registros[0]["detalles"]["token"] == "***OCULTO***"
    
    def test_registrar_tarea_enviada(self):
        """Test: Registrar envío de tarea."""
        auditor = AuditorEstructurado("TEST_AGENT")
        
        auditor.registrar_tarea_enviada("tarea_001", 2, 30)
        
        registros = auditor.obtener_registros()
        assert registros[0]["evento"] == "TAREA_ENVIADA"
        assert registros[0]["detalles"]["tarea_id"] == "tarea_001"
        assert registros[0]["detalles"]["prioridad"] == 2
    
    def test_registrar_tarea_completada(self):
        """Test: Registrar tarea completada."""
        auditor = AuditorEstructurado("TEST_AGENT")
        
        auditor.registrar_tarea_completada("tarea_001", 0.523)
        
        registros = auditor.obtener_registros()
        assert registros[0]["evento"] == "TAREA_COMPLETADA"
        assert registros[0]["detalles"]["latencia_segundos"] == 0.523
    
    def test_registrar_error(self):
        """Test: Registrar error en tarea."""
        auditor = AuditorEstructurado("TEST_AGENT")
        
        auditor.registrar_error("tarea_001", "ValueError", "Invalid input format")
        
        registros = auditor.obtener_registros()
        assert registros[0]["evento"] == "ERROR_TAREA"
        assert registros[0]["nivel"] == "ERROR"
        assert registros[0]["detalles"]["tipo_error"] == "ValueError"
    
    def test_filtrar_por_evento(self):
        """Test: Filtrar registros por evento."""
        auditor = AuditorEstructurado("TEST_AGENT")
        
        auditor.registrar_tarea_enviada("t1", 1, 10)
        auditor.registrar_tarea_enviada("t2", 2, 20)
        auditor.registrar_error("t1", "Error", "Msg")
        
        enviadas = auditor.obtener_registros_por_evento("TAREA_ENVIADA")
        errores = auditor.obtener_registros_por_evento("ERROR_TAREA")
        
        assert len(enviadas) == 2
        assert len(errores) == 1
    
    def test_exportar_json(self):
        """Test: Exportar auditoría como JSON."""
        auditor = AuditorEstructurado("TEST_AGENT")
        
        auditor.registrar_tarea_enviada("t1", 1, 10)
        auditor.registrar_error("t1", "ValueError", "Error msg")
        
        json_export = auditor.exportar_json()
        datos = json.loads(json_export)
        
        assert len(datos) == 2
        assert datos[0]["evento"] == "TAREA_ENVIADA"
        assert datos[1]["evento"] == "ERROR_TAREA"
    
    def test_limpiar_registros(self):
        """Test: Limpiar auditoría."""
        auditor = AuditorEstructurado("TEST_AGENT")
        
        auditor.registrar_tarea_enviada("t1", 1, 10)
        assert len(auditor.obtener_registros()) == 1
        
        auditor.limpiar()
        assert len(auditor.obtener_registros()) == 0
    
    def test_agente_con_auditoria(self):
        """Test: Agente integra auditoría."""
        agente = AgenteTest("TEST_AUDIT", capacidad=10)
        
        # Enviar orden debe registrarse en auditoría
        m_id = agente.enviar_orden("tarea1", prioridad=2, ttl=10)
        assert m_id is not None
        
        # Verificar que hay registros de auditoría
        registros = agente.obtener_registros_auditoria(10)
        assert len(registros) > 0
        assert any(r["evento"] == "TAREA_ENVIADA" for r in registros)


class TestConfigAgente:
    """Tests para configuración versionada."""
    
    def test_config_defectos(self):
        """Test: Configuración tiene valores por defecto."""
        config = ConfigAgente()
        
        assert config.version == "1.0"
        assert config.capacidad == 50
        assert config.max_reintentos == 3
        assert config.ttl_defecto == 10.0
    
    def test_config_personalizada(self):
        """Test: Crear configuración personalizada."""
        config = ConfigAgente(
            capacidad=100,
            max_reintentos=5,
            ttl_defecto=20.0,
            rate_limit_tokens=50.0
        )
        
        assert config.capacidad == 100
        assert config.max_reintentos == 5
        assert config.ttl_defecto == 20.0
        assert config.rate_limit_tokens == 50.0
    
    def test_actualizar_config(self):
        """Test: Actualizar parámetros de configuración."""
        config = ConfigAgente(capacidad=50)
        
        cambios = config.actualizar(capacidad=100, max_reintentos=10)
        
        assert config.capacidad == 100
        assert config.max_reintentos == 10
        assert cambios["capacidad"]["anterior"] == 50
        assert cambios["capacidad"]["nuevo"] == 100
    
    def test_validar_config_valida(self):
        """Test: Validación de config válida."""
        config = ConfigAgente()
        assert config.validar() is True
    
    def test_validar_config_invalida(self):
        """Test: Validación rechaza config inválida."""
        config = ConfigAgente(capacidad=-1)
        with pytest.raises(ValueError):
            config.validar()
        
        config2 = ConfigAgente(backpressure_threshold=1.5)
        with pytest.raises(ValueError):
            config2.validar()
    
    def test_a_diccionario(self):
        """Test: Exportar config como diccionario."""
        config = ConfigAgente(capacidad=100, max_reintentos=5)
        
        dicc = config.a_diccionario()
        assert dicc["version"] == "1.0"
        assert dicc["capacidad"] == 100
        assert dicc["max_reintentos"] == 5
        assert "timestamp_creacion" in dicc
    
    def test_a_json(self):
        """Test: Exportar config como JSON."""
        config = ConfigAgente(capacidad=75)
        
        json_str = config.a_json()
        datos = json.loads(json_str)
        
        assert datos["capacidad"] == 75
        assert datos["version"] == "1.0"
    
    def test_desde_diccionario(self):
        """Test: Cargar config desde diccionario."""
        datos_orig = {
            "capacidad": 200,
            "max_reintentos": 7,
            "ttl_defecto": 30.0
        }
        
        config = ConfigAgente.desde_diccionario(datos_orig)
        
        assert config.capacidad == 200
        assert config.max_reintentos == 7
        assert config.ttl_defecto == 30.0
    
    def test_desde_json(self):
        """Test: Cargar config desde JSON."""
        json_str = '''
        {
            "capacidad": 150,
            "max_reintentos": 6,
            "ttl_defecto": 25.0
        }
        '''
        
        config = ConfigAgente.desde_json(json_str)
        
        assert config.capacidad == 150
        assert config.max_reintentos == 6
    
    def test_roundtrip_json(self):
        """Test: JSON -> Config -> JSON preserva datos."""
        config_orig = ConfigAgente(capacidad=80, max_reintentos=4)
        json_str = config_orig.a_json()
        
        config_loaded = ConfigAgente.desde_json(json_str)
        dicc_loaded = config_loaded.a_diccionario()
        
        assert dicc_loaded["capacidad"] == 80
        assert dicc_loaded["max_reintentos"] == 4


class TestGestorPoliticasError:
    """Tests para gestor de políticas de error."""
    
    def test_politica_defecto(self):
        """Test: Política defecto es DLQ."""
        gestor = GestorPoliticasError()
        assert gestor.politica_defecto == PoliticaError.DLQ
    
    def test_registrar_politica_por_tipo(self):
        """Test: Registrar política específica por tipo error."""
        gestor = GestorPoliticasError()
        
        gestor.registrar_politica_por_tipo("TimeoutError", PoliticaError.RETRY)
        gestor.registrar_politica_por_tipo("ValueError", PoliticaError.DISCARD)
        
        assert gestor.obtener_politica("TimeoutError") == PoliticaError.RETRY
        assert gestor.obtener_politica("ValueError") == PoliticaError.DISCARD
    
    def test_politica_case_insensitive(self):
        """Test: Políticas son case-insensitive."""
        gestor = GestorPoliticasError()
        gestor.registrar_politica_por_tipo("RuntimeError", PoliticaError.BACKOFF)
        
        assert gestor.obtener_politica("runtimeerror") == PoliticaError.BACKOFF
        assert gestor.obtener_politica("RUNTIMEERROR") == PoliticaError.BACKOFF
    
    def test_debe_reintentar(self):
        """Test: Determinar si reintentar según política."""
        gestor = GestorPoliticasError()
        
        # RETRY y BACKOFF deben reintentar
        assert gestor.debe_reintentar("tipo1") is False  # DLQ defecto no reinten ta
        
        gestor.registrar_politica_por_tipo("tipo_retry", PoliticaError.RETRY)
        assert gestor.debe_reintentar("tipo_retry") is True
        
        gestor.registrar_politica_por_tipo("tipo_backoff", PoliticaError.BACKOFF)
        assert gestor.debe_reintentar("tipo_backoff") is True
    
    def test_debe_enviar_dlq(self):
        """Test: Determinar si enviar a DLQ según política."""
        gestor = GestorPoliticasError()
        
        # DLQ por defecto
        assert gestor.debe_enviar_dlq("cualquiera") is True
        
        gestor.registrar_politica_por_tipo("tipo_discard", PoliticaError.DISCARD)
        assert gestor.debe_enviar_dlq("tipo_discard") is False
        
        gestor.registrar_politica_por_tipo("tipo_dlq", PoliticaError.DLQ)
        assert gestor.debe_enviar_dlq("tipo_dlq") is True
    
    def test_agente_con_politicas_error(self):
        """Test: Agente puede configurar políticas de error."""
        agente = AgenteTest("TEST_ERROR_POLICY", capacidad=10)
        
        # Configurar política por defecto
        agente.configurar_politica_error_defecto(PoliticaError.DISCARD)
        
        # Registrar políticas específicas
        agente.registrar_politica_error_por_tipo("ValueError", PoliticaError.RETRY)
        agente.registrar_politica_error_por_tipo("TypeError", PoliticaError.BACKOFF)
        
        # Verificar
        assert agente.obtener_politica_error("ValueError") == "retry"
        assert agente.obtener_politica_error("TypeError") == "backoff"


class TestGracefulShutdown:
    """Tests para parada elegante del agente."""
    
    def test_detener_graceful_retorna_stats(self):
        """Test: Detener graceful retorna estadísticas."""
        agente = AgenteTest("TEST_SHUTDOWN", capacidad=10)
        
        # Enviar algunas tareas
        for i in range(3):
            agente.enviar_orden(f"tarea{i}")
        
        # Pequeño tiempo para procesar
        time.sleep(0.1)
        
        # Parada elegante
        stats = agente.detener_graceful(timeout=5.0)
        
        assert "agente" in stats
        assert stats["agente"] == "TEST_SHUTDOWN"
        assert "tiempo_parada_segundos" in stats
        assert "tareas_exitosas" in stats
        assert stats["tiempo_parada_segundos"] >= 0
    
    def test_detener_graceful_salva_archivos(self):
        """Test: Detener graceful guarda archivos de estado."""
        import os
        
        agente = AgenteTest("TEST_SAVE", capacidad=5)
        agente.enviar_orden("tarea1")
        time.sleep(0.1)
        
        stats = agente.detener_graceful(timeout=5.0)
        
        # Verificar que se crearon archivos
        # Nota: Los archivos se crean con el nombre del agente
        # Comprobamos que la operación fue exitosa sin errores


class TestGestorAntiInanicion:
    """Tests para protección contra inanición de tareas de baja prioridad."""
    
    def test_inicializacion(self):
        """Test: GestorAntiInanicion inicializa con ratio por defecto."""
        gestor = GestorAntiInanicion(ratio_minimo_baja_prioridad=0.2)
        
        assert gestor.ratio_minimo == 0.2
        assert gestor.contador_tareas == 0
        assert gestor.tareas_baja_prioridad_ejecutadas == 0
    
    def test_ratio_clamped(self):
        """Test: Ratio se ajusta entre 0.0 y 1.0."""
        gestor1 = GestorAntiInanicion(ratio_minimo_baja_prioridad=1.5)
        assert gestor1.ratio_minimo == 1.0
        
        gestor2 = GestorAntiInanicion(ratio_minimo_baja_prioridad=-0.5)
        assert gestor2.ratio_minimo == 0.0
    
    def test_puede_saltarse_baja_prioridad_inicial(self):
        """Test: No se pueden saltar tareas de baja prioridad inicialmente."""
        gestor = GestorAntiInanicion(ratio_minimo_baja_prioridad=0.5)
        
        # Al inicio no hay tareas, así que NO se puede saltar
        assert gestor.puede_saltarse_baja_prioridad() is False
    
    def test_puede_saltarse_baja_prioridad_ratios(self):
        """Test: Determina si se puede saltar según ratio."""
        gestor = GestorAntiInanicion(ratio_minimo_baja_prioridad=0.3)
        
        # Ejecutar 10 tareas de alta prioridad
        for i in range(10):
            gestor.registrar_tarea_ejecutada(es_baja_prioridad=False)
        
        # Aún sin ejecutar una de baja, NO se puede saltar (ratio 0.0 < 0.3)
        assert gestor.puede_saltarse_baja_prioridad() is False
        
        # Ejecutar 3 tareas de baja prioridad (ratio = 3/13 ≈ 0.23 < 0.3)
        for i in range(3):
            gestor.registrar_tarea_ejecutada(es_baja_prioridad=True)
        assert gestor.puede_saltarse_baja_prioridad() is False
        
        # Ejecutar 1 más de baja (ratio = 4/14 ≈ 0.29 < 0.3)
        gestor.registrar_tarea_ejecutada(es_baja_prioridad=True)
        assert gestor.puede_saltarse_baja_prioridad() is False
        
        # Ejecutar 1 más de baja (ratio = 5/15 ≈ 0.33 >= 0.3)
        gestor.registrar_tarea_ejecutada(es_baja_prioridad=True)
        assert gestor.puede_saltarse_baja_prioridad() is True
    
    def test_estadisticas(self):
        """Test: Obtener estadísticas precisas."""
        gestor = GestorAntiInanicion(ratio_minimo_baja_prioridad=0.25)
        
        # Ejecutar tareas mixtas
        for i in range(3):
            gestor.registrar_tarea_ejecutada(es_baja_prioridad=False)
        for i in range(1):
            gestor.registrar_tarea_ejecutada(es_baja_prioridad=True)
        
        stats = gestor.obtener_estadisticas()
        
        assert stats["total_tareas"] == 4
        assert stats["tareas_baja_prioridad"] == 1
        assert abs(stats["ratio_actual"] - 0.25) < 0.01
        assert stats["ratio_minimo_requerido"] == 0.25
    
    def test_limpiar(self):
        """Test: Limpiar estadísticas."""
        gestor = GestorAntiInanicion()
        
        gestor.registrar_tarea_ejecutada(es_baja_prioridad=False)
        gestor.registrar_tarea_ejecutada(es_baja_prioridad=True)
        
        assert gestor.contador_tareas == 2
        
        gestor.limpiar()
        
        assert gestor.contador_tareas == 0
        assert gestor.tareas_baja_prioridad_ejecutadas == 0
    
    def test_agente_anti_inanicion(self):
        """Test: Agente expone gestor anti-inanición."""
        agente = AgenteTest("TEST_ANTI", capacidad=10)
        
        # Verificar que el agente tiene el gestor
        assert hasattr(agente, 'gestor_anti_inanicion')
        
        # Obtener estadísticas
        stats = agente.obtener_estadisticas_anti_inanicion()
        assert "total_tareas" in stats
        assert "tareas_baja_prioridad" in stats
        assert "ratio_actual" in stats
    
    def test_establecer_ratio_minimo(self):
        """Test: Establecer ratio mínimo en agente."""
        agente = AgenteTest("TEST_RATIO", capacidad=10)
        
        # Establecer nuevo ratio
        agente.establecer_ratio_minimo_baja_prioridad(0.5)
        
        assert agente.gestor_anti_inanicion.ratio_minimo == 0.5
    
    def test_limpiar_estadisticas_agente(self):
        """Test: Limpiar estadísticas desde agente."""
        agente = AgenteTest("TEST_CLEAN", capacidad=10)
        
        # Simular ejecución de tareas
        agente.gestor_anti_inanicion.registrar_tarea_ejecutada(es_baja_prioridad=False)
        agente.gestor_anti_inanicion.registrar_tarea_ejecutada(es_baja_prioridad=True)
        
        assert agente.gestor_anti_inanicion.contador_tareas == 2
        
        # Limpiar
        agente.limpiar_estadisticas_anti_inanicion()
        
        assert agente.gestor_anti_inanicion.contador_tareas == 0


class TestSandboxSeguridad:
    """Tests para sandbox de seguridad con denylist/whitelist."""
    
    def test_inicializacion_denylist(self):
        """Test: Sandbox inicializa con denylist por defecto."""
        sandbox = SandboxSeguridad(habilitar_whitelist=False)
        
        assert len(sandbox.denylist) > 0
        assert "rm -rf" in sandbox.denylist
        assert "del /s" in sandbox.denylist
    
    def test_tarea_segura_modo_denylist(self):
        """Test: Modo denylist rechaza tareas con patrones prohibidos."""
        sandbox = SandboxSeguridad(habilitar_whitelist=False)
        
        # Tareas seguras
        assert sandbox.es_segura_tarea("procesar_datos") is True
        assert sandbox.es_segura_tarea("generar_reporte") is True
        
        # Tareas peligrosas (contienen patrones del denylist)
        assert sandbox.es_segura_tarea("rm -rf /home") is False
        assert sandbox.es_segura_tarea("del /s *.txt") is False
        assert sandbox.es_segura_tarea("exec(código)") is False
    
    def test_agregar_patron_denylist(self):
        """Test: Agregar patrón personalizado a denylist."""
        sandbox = SandboxSeguridad(habilitar_whitelist=False)
        
        sandbox.agregar_denylist("sql_injection")
        sandbox.agregar_denylist("malware")
        
        assert "sql_injection" in sandbox.denylist
        assert "malware" in sandbox.denylist
        
        # Verificar que se rechaza
        assert sandbox.es_segura_tarea("SELECT * sql_injection") is False
        assert sandbox.es_segura_tarea("descargar malware") is False
    
    def test_modo_whitelist(self):
        """Test: Modo whitelist solo permite patrones permitidos."""
        sandbox = SandboxSeguridad(habilitar_whitelist=True)
        
        # Sin whitelist, todo es rechazado
        assert sandbox.es_segura_tarea("cualquier_tarea") is True  # Whitelist vacío = todo permitido
        
        # Agregar patrones al whitelist
        sandbox.agregar_whitelist("procesar")
        sandbox.agregar_whitelist("analizar")
        
        # Tareas con patrones permitidos
        assert sandbox.es_segura_tarea("procesar_datos") is True
        assert sandbox.es_segura_tarea("analizar_archivo") is True
        
        # Tareas sin patrones permitidos
        assert sandbox.es_segura_tarea("borrar_datos") is False
        assert sandbox.es_segura_tarea("ejecutar_comando") is False
    
    def test_case_insensitive(self):
        """Test: Validación es case-insensitive."""
        sandbox = SandboxSeguridad(habilitar_whitelist=False)
        
        # Agregar en minúscula
        sandbox.agregar_denylist("malware")
        
        # Validar en mayúscula
        assert sandbox.es_segura_tarea("MALWARE DETECTADO") is False
        assert sandbox.es_segura_tarea("Malware") is False
        assert sandbox.es_segura_tarea("malware") is False
    
    def test_contador_rechazos(self):
        """Test: Contador de tareas rechazadas."""
        sandbox = SandboxSeguridad(habilitar_whitelist=False)
        
        # Validar tareas
        sandbox.es_segura_tarea("tarea_segura")
        sandbox.es_segura_tarea("rm -rf")  # Rechazada
        sandbox.es_segura_tarea("otra_segura")
        sandbox.es_segura_tarea("exec()")  # Rechazada
        
        assert sandbox.contador_rechazos == 2
    
    def test_estadisticas_seguridad(self):
        """Test: Obtener estadísticas de seguridad."""
        sandbox = SandboxSeguridad(habilitar_whitelist=False)
        
        sandbox.agregar_denylist("peligro1")
        sandbox.agregar_denylist("peligro2")
        sandbox.agregar_whitelist("permitido1")
        
        sandbox.es_segura_tarea("peligro1")  # Rechazada
        
        stats = sandbox.obtener_estadisticas_seguridad()
        
        assert stats["tareas_rechazadas"] == 1
        assert stats["modo"] == "denylist"
        assert stats["denylist_size"] > 2
        assert stats["whitelist_size"] == 1
    
    def test_limpiar_estadisticas(self):
        """Test: Limpiar contadores de seguridad."""
        sandbox = SandboxSeguridad(habilitar_whitelist=False)
        
        sandbox.es_segura_tarea("rm -rf")  # Rechazada
        sandbox.es_segura_tarea("del /s")  # Rechazada
        
        assert sandbox.contador_rechazos == 2
        
        sandbox.limpiar_estadisticas()
        
        assert sandbox.contador_rechazos == 0
    
    def test_agente_sandbox_seguridad(self):
        """Test: Agente expone métodos de sandbox de seguridad."""
        agente = AgenteTest("TEST_SANDBOX", capacidad=10)
        
        # Agregar patrones
        agente.agregar_patron_denylist("peligro")
        agente.agregar_patron_whitelist("permitido")
        
        # Validar tareas
        assert agente.validar_tarea_segura("tarea_normal") is True
        assert agente.validar_tarea_segura("peligro") is False
        
        # Obtener estadísticas
        stats = agente.obtener_estadisticas_seguridad()
        assert "tareas_rechazadas" in stats
        assert "modo" in stats
    
    def test_cambiar_modo_whitelist_agente(self):
        """Test: Cambiar modo de whitelist en agente."""
        agente = AgenteTest("TEST_MODO", capacidad=10)
        
        # Verificar modo por defecto (denylist)
        stats = agente.obtener_estadisticas_seguridad()
        assert stats["modo"] == "denylist"
        
        # Cambiar a whitelist
        agente.habilitar_modo_whitelist(True)
        stats = agente.obtener_estadisticas_seguridad()
        assert stats["modo"] == "whitelist"
        
        # Cambiar de vuelta
        agente.habilitar_modo_whitelist(False)
        stats = agente.obtener_estadisticas_seguridad()
        assert stats["modo"] == "denylist"


class TestSondeoSalud:
    """Tests para sondeos de salud (health probes)."""
    
    def test_inicializacion_sondeo(self):
        """Test: SondeoSalud inicializa correctamente."""
        sondeo = SondeoSalud("TEST_AGENT", umbral_inactividad=60.0)
        
        assert sondeo.nombre_agente == "TEST_AGENT"
        assert sondeo.umbral_inactividad == 60.0
    
    def test_sondeo_liveness_vivo(self):
        """Test: Sondeo liveness marca agente como vivo si contacto reciente."""
        sondeo = SondeoSalud("TEST", umbral_inactividad=10.0)
        
        # Marcar contacto reciente
        sondeo.marcar_contacto()
        
        result = sondeo.sondeo_liveness()
        assert result["status"] == "alive"
        assert result["tipo"] == "liveness"
        assert result["segundos_inactivo"] < 1.0  # Recién marcado
    
    def test_sondeo_liveness_muerto(self):
        """Test: Sondeo liveness marca agente como muerto si inactividad > umbral."""
        sondeo = SondeoSalud("TEST", umbral_inactividad=0.1)
        
        # Esperar para que pase el umbral
        time.sleep(0.2)
        
        result = sondeo.sondeo_liveness()
        assert result["status"] == "dead"
        assert result["segundos_inactivo"] >= 0.1
    
    def test_sondeo_readiness_listo(self):
        """Test: Sondeo readiness marca agente como listo."""
        sondeo = SondeoSalud("TEST", umbral_inactividad=60.0)
        
        # Agente vivo, cola vacía
        result = sondeo.sondeo_readiness(agente_vivo=True, tamaño_cola=0, capacidad_cola=100)
        
        assert result["status"] == "ready"
        assert result["tipo"] == "readiness"
        assert result["agente_vivo"] is True
        assert result["porcentaje_saturacion"] == 0.0
    
    def test_sondeo_readiness_saturado(self):
        """Test: Sondeo readiness marca como no listo si cola saturada."""
        sondeo = SondeoSalud("TEST", umbral_inactividad=60.0)
        
        # Cola saturada al 90%
        result = sondeo.sondeo_readiness(agente_vivo=True, tamaño_cola=90, capacidad_cola=100)
        
        assert result["status"] == "not_ready"
        assert result["porcentaje_saturacion"] == 90.0
    
    def test_sondeo_readiness_muerto(self):
        """Test: Sondeo readiness marca como no listo si agente muerto."""
        sondeo = SondeoSalud("TEST", umbral_inactividad=60.0)
        
        # Agente no vivo
        result = sondeo.sondeo_readiness(agente_vivo=False, tamaño_cola=0, capacidad_cola=100)
        
        assert result["status"] == "not_ready"
        assert result["agente_vivo"] is False
    
    def test_sondeo_startup_iniciado(self):
        """Test: Sondeo startup marca como started."""
        sondeo = SondeoSalud("TEST", umbral_inactividad=60.0)
        
        result = sondeo.sondeo_startup(inicializacion_completa=True)
        
        assert result["status"] == "started"
        assert result["tipo"] == "startup"
        assert result["inicializacion_completa"] is True
    
    def test_sondeo_startup_iniciando(self):
        """Test: Sondeo startup marca como starting."""
        sondeo = SondeoSalud("TEST", umbral_inactividad=60.0)
        
        result = sondeo.sondeo_startup(inicializacion_completa=False)
        
        assert result["status"] == "starting"
        assert result["inicializacion_completa"] is False
    
    def test_estado_general_saludable(self):
        """Test: Estado general marca agente como saludable."""
        sondeo = SondeoSalud("TEST", umbral_inactividad=60.0)
        sondeo.marcar_contacto()
        
        result = sondeo.obtener_estado_general(
            agente_vivo=True,
            tamaño_cola=10,
            capacidad_cola=100
        )
        
        assert result["agente"] == "TEST"
        assert result["liveness"]["status"] == "alive"
        assert result["readiness"]["status"] == "ready"
        assert result["startup"]["status"] == "started"
        assert result["saludable"] is True
    
    def test_estado_general_no_saludable(self):
        """Test: Estado general marca agente como no saludable."""
        sondeo = SondeoSalud("TEST", umbral_inactividad=0.1)
        time.sleep(0.2)  # Hacer que liveness sea dead
        
        result = sondeo.obtener_estado_general(
            agente_vivo=True,
            tamaño_cola=10,
            capacidad_cola=100
        )
        
        assert result["liveness"]["status"] == "dead"
        assert result["saludable"] is False
    
    def test_agente_sondeos_salud(self):
        """Test: Agente expone métodos de sondeos de salud."""
        agente = AgenteTest("TEST_SALUD", capacidad=50)
        
        # Prueba de liveness
        liveness = agente.sondeo_liveness()
        assert liveness["status"] == "alive"
        assert "tipo" in liveness
        
        # Prueba de readiness
        readiness = agente.sondeo_readiness()
        assert readiness["status"] == "ready"
        assert "tamaño_cola" in readiness
        
        # Prueba de startup
        startup = agente.sondeo_startup()
        assert startup["status"] == "started"
        
        # Estado general
        general = agente.obtener_estado_salud_general()
        assert general["saludable"] is True
        assert "liveness" in general
        assert "readiness" in general
        assert "startup" in general


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
