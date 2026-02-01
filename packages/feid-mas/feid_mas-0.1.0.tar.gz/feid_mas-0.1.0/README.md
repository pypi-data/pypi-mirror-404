# FEID - Framework para Multi-Agent Systems (MAS)

Framework ligero y **educativo** para construir sistemas multi‑agente en Python con setup mínimo y foco en prototipado rápido.

## ¿Para quién es?

- 🎓 **Educación**: enseñar MAS sin complejidad de JADE/infraestructura pesada.
- 🧪 **Investigación**: validar algoritmos rápidamente y reproducir resultados.
- 🤖 **Edge/IoT**: agentes en dispositivos con recursos limitados.
- 💡 **Prototipado**: validar arquitecturas MAS en días, no semanas.

## Lo que hace bien

✅ **Base MAS simple**: subclases mínimas y boilerplate bajo.
✅ **Multi‑protocolo**: FIPA ACL, KQML, JSON‑RPC, texto simple.
✅ **Percepción proactiva**: hook opcional para comportamiento autónomo.
✅ **Zero dependencies**: solo stdlib de Python.
✅ **Extensible**: handlers externos, logs rotativos, métricas básicas.
✅ **Resiliencia**: reintentos configurables, circuit breaker y Dead Letter Queue.
✅ **Testeado**: 131 tests pasando (incluye stress tests con 1k-5k tareas).

## Lo que NO intenta ser

❌ No es Celery/Airflow (no es orquestación ni broker).
❌ No compite con JADE como plataforma completa.
❌ Estado actual: **v0.1.0 experimental** (ideal para POC/educación/edge).

## Instalacion (editable para desarrollo)

```bash
pip install -e .
```

## Uso rapido

```python
from feid.agent import AgenteMaestroNASA, ExponentialBackoffStrategy

class MiAgente(AgenteMaestroNASA):
    def _trabajo_tecnico(self, tarea):
        return f"Procesado: {tarea}"

# Crear agente con opciones de resiliencia
agente = MiAgente(
    "productor",
    retry_strategy=ExponentialBackoffStrategy(),
    circuit_breaker_threshold=5,
    max_workers=4
)

# Enviar tarea con correlation ID (distributed tracing)
m_id = agente.enviar_orden(
    "procesar-datos",
    correlation_id="req-2024-001"
)

# Monitorear salud (incluye estado de circuit breaker y estrategia)
salud = agente.monitorear_salud()
```

## Documentación

- [Enterprise Features Guide](docs/enterprise_features.md) - Correlation IDs, Circuit Breaker, Retry Strategies
- [Handler Development](docs/handler_guide.md) - Integración con sistemas externos
- [Contributing](CONTRIBUTING.md) - Guía para contribuidores

## Ejemplos

Ver [examples/enterprise_demo.py](examples/enterprise_demo.py) para demostración completa de features.

```bash
python examples/enterprise_demo.py
```

## Estado
Proyecto experimental (v0.1.0). Ver [BACKLOG](BACKLOG.md) para roadmap y próximos pasos.

## Autor
**Leon Alberne Torres Restrepo**
- GitHub: [albernetr](https://github.com/albernetr)
- LinkedIn: [leon-alberne-torres-restrepo](https://www.linkedin.com/in/leon-alberne-torres-restrepo/)
- Email: albernetorres@gmail.com

## Disclaimer
Proyecto de desarrollo personal realizado en tiempo personal con equipos personales.
No afiliado ni respaldado por empleadores anteriores o actuales.
Proveido "como esta", sin garantias.

## Licencia
MIT License - Ver [LICENSE](LICENSE)
