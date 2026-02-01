from feid.agent import AgenteMaestroNASA


class AgenteDummy(AgenteMaestroNASA):
    def percibir_entorno(self):
        return None

    def _trabajo_tecnico(self, tarea):
        return f"ok:{tarea}"


def test_instanciacion_basica():
    agente = AgenteDummy("DUMMY")
    assert agente.nombre == "DUMMY"
