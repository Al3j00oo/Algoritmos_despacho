# Simulador de Algoritmos de Despacho

Simulador interactivo de algoritmos de planificación de procesos para la materia de Sistemas Operativos.

##  Demo

🔗 [https://despacho-gray-wood.reflex.run](https://despacho-gray-wood.reflex.run)

---

## ¿Qué hace?

Permite simular y comparar los principales algoritmos de despacho de procesos. El usuario ingresa los procesos con su tiempo de llegada, ráfaga y prioridad, elige el algoritmo y obtiene:

- Diagrama de Gantt interactivo
- Tiempo de espera y tiempo de retorno por proceso
- Promedios generales de la simulación

## Algoritmos implementados

| Algoritmo | Tipo |
|-----------|------|
| FIFO (First In, First Out) | No apropiativo |
| SJF (Shortest Job First) | No apropiativo |
| Prioridad | No apropiativo |
| Round Robin | Apropiativo (quantum configurable) |

---

## Tecnologías

- **[Reflex](https://reflex.dev/)** — Framework web full-stack en Python
- **[Plotly](https://plotly.com/python/)** — Gráficas interactivas (Diagrama de Gantt)
- **[Pydantic](https://docs.pydantic.dev/)** — Modelos de datos
- **[Reflex Hosting](https://reflex.dev/hosting)** — Despliegue en la nube

---

## ⚙️ Correr localmente

```bash
# Clonar el repositorio
git clone https://github.com/Al3j00oo/Algoritmos_despacho.git
cd Algoritmos_despacho

# Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Iniciar la aplicación
reflex run
```

La app estará disponible en `http://localhost:3000`
