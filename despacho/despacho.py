"""
Simulador de Algoritmos de Despacho — Sistemas Operativos
Algoritmos: FIFO · SJF · Prioridad · Round Robin

Integración:
    import scheduling
    app = rx.App(theme=rx.theme(appearance="dark"))
    app.add_page(scheduling.index, route="/", title="Scheduler — SO")
"""

import reflex as rx
import plotly.graph_objects as go
from typing import List
from pydantic import BaseModel

# ─── Paleta de colores por proceso ──────────────────────────────────────────
PROCESS_COLORS = [
    "#00FFA3", "#00C8FF", "#FF6B9D", "#FFB347",
    "#A78BFA", "#FDE68A", "#6EE7B7", "#FB923C",
    "#F472B6", "#34D399",
]

ALGORITHM_OPTIONS = ["FIFO", "SJF", "Prioridad", "Round Robin"]


# ─── Modelos ─────────────────────────────────────────────────────────────────
class Process(BaseModel):
    pid: str
    arrival: int
    burst: int
    priority: int


class ScheduleResult(BaseModel):
    pid: str
    arrival: int
    burst: int
    priority: int
    start: int       
    finish: int      
    waiting: int
    turnaround: int


class TimeSegment(BaseModel):
    pid: str
    start: int
    end: int


# ─── Estado ──────────────────────────────────────────────────────────────────
class SchedulerState(rx.State):
    processes: List[Process] = []
    algorithm: str = "FIFO"
    quantum: str = "2"

    # Formulario
    new_pid: str = ""
    new_arrival: str = "0"
    new_burst: str = "1"
    new_priority: str = "1"

    # Resultados
    results: List[ScheduleResult] = []
    timeline: List[TimeSegment] = []
    has_results: bool = False
    error_msg: str = ""

    # ── Setters ──────────────────────────────────────────────────────────────
    def set_algorithm(self, v: str):
        self.algorithm = v
        self.has_results = False

    def set_quantum(self, v: str):  self.quantum = v
    def set_pid(self, v: str):      self.new_pid = v
    def set_arrival(self, v: str):  self.new_arrival = v
    def set_burst(self, v: str):    self.new_burst = v
    def set_priority(self, v: str): self.new_priority = v

    # ── Agregar proceso ───────────────────────────────────────────────────────
    def add_process(self):
        self.error_msg = ""
        pid = self.new_pid.strip()
        if not pid:
            self.error_msg = "El nombre del proceso no puede estar vacio."
            return
        try:
            arrival  = int(self.new_arrival)
            burst    = int(self.new_burst)
            priority = int(self.new_priority)
        except ValueError:
            self.error_msg = "Los campos numericos deben ser enteros."
            return
        if burst <= 0:
            self.error_msg = "El tiempo de rafaga debe ser mayor a 0."
            return
        if arrival < 0:
            self.error_msg = "El tiempo de llegada no puede ser negativo."
            return
        if any(p.pid == pid for p in self.processes):
            self.error_msg = f"Ya existe un proceso llamado '{pid}'."
            return

        self.processes = self.processes + [
            Process(pid=pid, arrival=arrival, burst=burst, priority=priority)
        ]
        self.new_pid = ""
        self.new_arrival = "0"
        self.new_burst = "1"
        self.new_priority = "1"

    def remove_process(self, pid: str):
        self.processes = [p for p in self.processes if p.pid != pid]
        self.has_results = False

    def clear_all(self):
        self.processes = []
        self.results = []
        self.timeline = []
        self.has_results = False
        self.error_msg = ""
        self.new_pid = ""
        self.new_arrival = "0"
        self.new_burst = "1"
        self.new_priority = "1"

    # ── Ejecutar ──────────────────────────────────────────────────────────────
    def run_scheduler(self):
        self.error_msg = ""
        if not self.processes:
            self.error_msg = "Agrega al menos un proceso antes de ejecutar."
            return

        procs = [(p.pid, p.arrival, p.burst, p.priority) for p in self.processes]

        if self.algorithm == "FIFO":
            segments, results = self._fifo(procs)
        elif self.algorithm == "SJF":
            segments, results = self._sjf(procs)
        elif self.algorithm == "Prioridad":
            segments, results = self._priority_sched(procs)
        else:
            try:
                q = int(self.quantum)
                if q <= 0:
                    raise ValueError
            except ValueError:
                self.error_msg = "El quantum debe ser un entero mayor a 0."
                return
            segments, results = self._round_robin(procs, q)

        self.timeline = [TimeSegment(**s) for s in segments]
        self.results  = [ScheduleResult(**r) for r in results]
        self.has_results = True

    # ── FIFO ──────────────────────────────────────────────────────────────────
    def _fifo(self, procs):
        ordered = sorted(procs, key=lambda x: (x[1], x[0]))
        return self._run_nonpreemptive(ordered)

    # ── SJF (no apropiativo) ──────────────────────────────────────────────────
    def _sjf(self, procs):
        remaining = list(procs)
        current, segments, results = 0, [], []
        while remaining:
            avail = [p for p in remaining if p[1] <= current]
            if not avail:
                current = min(p[1] for p in remaining)
                avail = [p for p in remaining if p[1] <= current]
            chosen = min(avail, key=lambda x: (x[2], x[1], x[0]))
            remaining.remove(chosen)
            seg = self._make_segment(chosen, current)
            segments.append(seg)
            results.append(self._make_result(chosen, seg["start"], seg["end"]))
            current = seg["end"]
        return segments, results

    # ── Prioridad (no apropiativo) ────────────────────────────────────────────
    def _priority_sched(self, procs):
        remaining = list(procs)
        current, segments, results = 0, [], []
        while remaining:
            avail = [p for p in remaining if p[1] <= current]
            if not avail:
                current = min(p[1] for p in remaining)
                avail = [p for p in remaining if p[1] <= current]
            chosen = min(avail, key=lambda x: (x[3], x[1], x[0]))
            remaining.remove(chosen)
            seg = self._make_segment(chosen, current)
            segments.append(seg)
            results.append(self._make_result(chosen, seg["start"], seg["end"]))
            current = seg["end"]
        return segments, results

    # ── Round Robin ───────────────────────────────────────────────────────────
    def _round_robin(self, procs, q: int):
        queue_order = sorted(procs, key=lambda x: (x[1], x[0]))
        remaining   = {p[0]: p[2] for p in procs}
        proc_map    = {p[0]: p for p in procs}
        first_start = {}
        last_finish = {}

        ready   = []
        arrived = list(queue_order)
        current = 0
        segments = []

        # Cargar procesos que llegan en t=0
        to_load = [p for p in arrived if p[1] <= current]
        for p in to_load:
            ready.append(p[0])
            arrived.remove(p)

        while ready or arrived:
            if not ready:
                current = arrived[0][1]
                to_load = [p for p in arrived if p[1] <= current]
                for p in to_load:
                    ready.append(p[0])
                    arrived.remove(p)

            pid    = ready.pop(0)
            exec_t = min(q, remaining[pid])
            start  = current
            end    = current + exec_t

            if pid not in first_start:
                first_start[pid] = start
            last_finish[pid] = end

            segments.append({"pid": pid, "start": start, "end": end})
            remaining[pid] -= exec_t
            current = end

            # Nuevos procesos que llegaron durante este quantum
            to_load = [p for p in arrived if p[1] <= current]
            for p in to_load:
                ready.append(p[0])
                arrived.remove(p)

            # Si no termino, vuelve al final de la cola
            if remaining[pid] > 0:
                ready.append(pid)

        # Calcular resultados agregados por proceso
        results = []
        for p in procs:
            pid, arrival, burst, priority = p
            finish     = last_finish[pid]
            turnaround = finish - arrival
            waiting    = turnaround - burst
            results.append({
                "pid": pid, "arrival": arrival, "burst": burst,
                "priority": priority, "start": first_start[pid],
                "finish": finish, "waiting": waiting, "turnaround": turnaround,
            })
        return segments, results

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _run_nonpreemptive(self, ordered):
        current, segments, results = 0, [], []
        for p in ordered:
            seg = self._make_segment(p, current)
            segments.append(seg)
            results.append(self._make_result(p, seg["start"], seg["end"]))
            current = seg["end"]
        return segments, results

    def _make_segment(self, p, current_time):
        pid, arrival, burst, _ = p
        start = max(current_time, arrival)
        return {"pid": pid, "start": start, "end": start + burst}

    def _make_result(self, p, start, finish):
        pid, arrival, burst, priority = p
        return {
            "pid": pid, "arrival": arrival, "burst": burst, "priority": priority,
            "start": start, "finish": finish,
            "waiting": start - arrival,
            "turnaround": finish - arrival,
        }

    # ── Vars computadas ───────────────────────────────────────────────────────
    @rx.var
    def process_count(self) -> int:
        return len(self.processes)

    @rx.var
    def show_quantum(self) -> bool:
        return self.algorithm == "Round Robin"

    @rx.var
    def avg_waiting(self) -> str:
        if not self.results:
            return "-"
        return f"{sum(r.waiting for r in self.results) / len(self.results):.2f}"

    @rx.var
    def avg_turnaround(self) -> str:
        if not self.results:
            return "-"
        return f"{sum(r.turnaround for r in self.results) / len(self.results):.2f}"

    @rx.var
    def gantt_figure(self) -> go.Figure:
        if not self.timeline:
            return go.Figure()

        # Orden de aparicion de procesos
        pid_order = []
        seen = set()
        for seg in self.timeline:
            if seg.pid not in seen:
                pid_order.append(seg.pid)
                seen.add(seg.pid)
        color_map = {pid: PROCESS_COLORS[i % len(PROCESS_COLORS)]
                     for i, pid in enumerate(pid_order)}

        fig = go.Figure()
        added_legend = set()

        for seg in self.timeline:
            color    = color_map[seg.pid]
            show_leg = seg.pid not in added_legend
            added_legend.add(seg.pid)
            width = seg.end - seg.start

            fig.add_trace(go.Bar(
                name=seg.pid,
                x=[width],
                y=[seg.pid],
                base=[seg.start],
                orientation="h",
                marker=dict(color=color,
                            line=dict(color="#0D0D1A", width=2),
                            opacity=0.9),
                text=seg.pid if width >= 1 else "",
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="#0D0D1A", size=12,
                              family="'JetBrains Mono', monospace"),
                showlegend=show_leg,
                legendgroup=seg.pid,
                hovertemplate=(
                    f"<b>{seg.pid}</b><br>"
                    f"Inicio: {seg.start} → Fin: {seg.end}<br>"
                    f"Duracion: {width}"
                    "<extra></extra>"
                ),
            ))

        tick_max = max(seg.end for seg in self.timeline)
        fig.update_layout(
            barmode="overlay",
            xaxis=dict(
                title="Tiempo",
                range=[0, tick_max + 1],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.07)",
                tickmode="linear",
                dtick=1,
                tickfont=dict(color="#8888AA",
                              family="'JetBrains Mono', monospace"),
                title_font=dict(color="#8888AA"),
                zeroline=True,
                zerolinecolor="rgba(255,255,255,0.12)",
            ),
            yaxis=dict(
                title="",
                autorange="reversed",
                tickfont=dict(color="#CCCCDD",
                              family="'JetBrains Mono', monospace", size=13),
                showgrid=False,
                categoryorder="array",
                categoryarray=list(reversed(pid_order)),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(color="#CCCCDD",
                          family="'JetBrains Mono', monospace", size=12),
                bgcolor="rgba(0,0,0,0)",
            ),
            height=max(240, len(pid_order) * 54 + 110),
            margin=dict(l=10, r=20, t=40, b=50),
            plot_bgcolor="#12122A",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="'JetBrains Mono', monospace"),
        )
        return fig


# ─── Estilos compartidos ─────────────────────────────────────────────────────
CARD_STYLE = {
    "background": "rgba(255,255,255,0.04)",
    "border": "1px solid rgba(255,255,255,0.09)",
    "border_radius": "12px",
    "padding": "1.5rem",
    "width": "100%",
    "backdrop_filter": "blur(8px)",
}

LABEL_STYLE = {
    "color": "#7777AA",
    "font_size": "0.72rem",
    "font_weight": "600",
    "letter_spacing": "0.08em",
    "text_transform": "uppercase",
    "font_family": "'JetBrains Mono', monospace",
    "margin_bottom": "4px",
}

INPUT_STYLE = {
    "background": "rgba(255,255,255,0.05)",
    "border": "1px solid rgba(255,255,255,0.12)",
    "color": "#E8E8FF",
    "font_family": "'JetBrains Mono', monospace",
    "font_size": "0.9rem",
    "border_radius": "8px",
    "_placeholder": {"color": "#44447A"},
    "_focus": {
        "outline": "none",
        "border_color": "#00FFA3",
        "box_shadow": "0 0 0 3px rgba(0,255,163,0.12)",
    },
    "width": "100%",
}


# ─── Componentes ─────────────────────────────────────────────────────────────
def section_title(text: str, color: str = "#00FFA3") -> rx.Component:
    return rx.text(text, style={
        "color": color,
        "font_size": "0.78rem",
        "font_weight": "700",
        "letter_spacing": "0.12em",
        "text_transform": "uppercase",
        "font_family": "'JetBrains Mono', monospace",
        "margin_bottom": "1rem",
    })


def th_cell(text: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.text(text, style={
            "color": "#7777AA",
            "font_size": "0.72rem",
            "font_weight": "700",
            "letter_spacing": "0.08em",
            "text_transform": "uppercase",
            "font_family": "'JetBrains Mono', monospace",
        })
    )


def process_row(process: Process) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(process.pid,
            style={"color": "#00FFA3", "font_family": "'JetBrains Mono', monospace",
                   "font_weight": "700"})),
        rx.table.cell(rx.text(process.arrival,
            style={"color": "#CCCCDD", "font_family": "'JetBrains Mono', monospace"})),
        rx.table.cell(rx.text(process.burst,
            style={"color": "#CCCCDD", "font_family": "'JetBrains Mono', monospace"})),
        rx.table.cell(rx.text(process.priority,
            style={"color": "#CCCCDD", "font_family": "'JetBrains Mono', monospace"})),
        rx.table.cell(
            rx.button(
                rx.icon("x", size=14),
                on_click=SchedulerState.remove_process(process.pid),
                style={
                    "background": "rgba(255,80,80,0.12)",
                    "border": "1px solid rgba(255,80,80,0.25)",
                    "color": "#FF6B6B",
                    "border_radius": "6px",
                    "padding": "2px 8px",
                    "cursor": "pointer",
                    "_hover": {"background": "rgba(255,80,80,0.25)"},
                },
            )
        ),
        style={"_hover": {"background": "rgba(255,255,255,0.03)"}},
    )


def result_row(result: ScheduleResult) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(result.pid,
            style={"color": "#00FFA3", "font_weight": "700",
                   "font_family": "'JetBrains Mono', monospace"})),
        rx.table.cell(rx.text(result.arrival,
            style={"color": "#AAAACC", "font_family": "'JetBrains Mono', monospace"})),
        rx.table.cell(rx.text(result.burst,
            style={"color": "#AAAACC", "font_family": "'JetBrains Mono', monospace"})),
        rx.table.cell(rx.text(result.priority,
            style={"color": "#AAAACC", "font_family": "'JetBrains Mono', monospace"})),
        rx.table.cell(rx.text(result.start,
            style={"color": "#CCCCDD", "font_family": "'JetBrains Mono', monospace"})),
        rx.table.cell(rx.text(result.finish,
            style={"color": "#CCCCDD", "font_family": "'JetBrains Mono', monospace"})),
        rx.table.cell(
            rx.box(
                rx.text(result.waiting, style={"color": "#0D0D1A", "font_weight": "700",
                    "font_family": "'JetBrains Mono', monospace", "font_size": "0.85rem"}),
                style={"background": "#00C8FF", "border_radius": "6px",
                       "padding": "2px 10px", "display": "inline-block"},
            )
        ),
        rx.table.cell(
            rx.box(
                rx.text(result.turnaround, style={"color": "#0D0D1A", "font_weight": "700",
                    "font_family": "'JetBrains Mono', monospace", "font_size": "0.85rem"}),
                style={"background": "#A78BFA", "border_radius": "6px",
                       "padding": "2px 10px", "display": "inline-block"},
            )
        ),
        style={"_hover": {"background": "rgba(255,255,255,0.03)"}},
    )


def algorithm_bar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text("Algoritmo", style=LABEL_STYLE),
                rx.select(
                    ALGORITHM_OPTIONS,
                    value=SchedulerState.algorithm,
                    on_change=SchedulerState.set_algorithm,
                    style={
                        "background": "rgba(255,255,255,0.05)",
                        "border": "1px solid rgba(255,255,255,0.15)",
                        "color": "#E8E8FF",
                        "font_family": "'JetBrains Mono', monospace",
                        "border_radius": "8px",
                        "min_width": "180px",
                    },
                ),
                spacing="1",
            ),
            # Campo Quantum — solo visible en Round Robin
            rx.cond(
                SchedulerState.show_quantum,
                rx.vstack(
                    rx.text("Quantum (Q)", style=LABEL_STYLE),
                    rx.input(
                        value=SchedulerState.quantum,
                        on_change=SchedulerState.set_quantum,
                        type="number",
                        style={**INPUT_STYLE, "max_width": "110px"},
                    ),
                    spacing="1",
                ),
                rx.box(),
            ),
            rx.spacer(),
            rx.button(
                rx.icon("play", size=17),
                "Ejecutar Simulacion",
                on_click=SchedulerState.run_scheduler,
                style={
                    "background": rx.cond(
                        SchedulerState.process_count > 0,
                        "linear-gradient(135deg, #7C3AED, #00C8FF)",
                        "rgba(255,255,255,0.06)",
                    ),
                    "color": rx.cond(
                        SchedulerState.process_count > 0, "#FFFFFF", "#44447A"
                    ),
                    "font_weight": "700",
                    "font_family": "'JetBrains Mono', monospace",
                    "font_size": "0.9rem",
                    "border_radius": "10px",
                    "padding": "10px 22px",
                    "cursor": rx.cond(
                        SchedulerState.process_count > 0, "pointer", "not-allowed"
                    ),
                    "border": "none",
                    "transition": "all 0.15s ease",
                    "_hover": rx.cond(
                        SchedulerState.process_count > 0,
                        {"opacity": "0.88", "transform": "translateY(-1px)",
                         "box_shadow": "0 4px 20px rgba(124,58,237,0.4)"},
                        {},
                    ),
                },
            ),
            align="end",
            width="100%",
            spacing="4",
        ),
        style=CARD_STYLE,
    )


def input_form() -> rx.Component:
    return rx.box(
        section_title("Agregar Proceso"),
        rx.grid(
            rx.vstack(
                rx.text("PID / Nombre", style=LABEL_STYLE),
                rx.input(placeholder="P1", value=SchedulerState.new_pid,
                         on_change=SchedulerState.set_pid, style=INPUT_STYLE),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Llegada", style=LABEL_STYLE),
                rx.input(placeholder="0", value=SchedulerState.new_arrival,
                         on_change=SchedulerState.set_arrival, type="number",
                         style=INPUT_STYLE),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Rafaga", style=LABEL_STYLE),
                rx.input(placeholder="1", value=SchedulerState.new_burst,
                         on_change=SchedulerState.set_burst, type="number",
                         style=INPUT_STYLE),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Prioridad", style=LABEL_STYLE),
                rx.input(placeholder="1", value=SchedulerState.new_priority,
                         on_change=SchedulerState.set_priority, type="number",
                         style=INPUT_STYLE),
                spacing="1",
            ),
            columns="4",
            spacing="4",
            width="100%",
        ),
        rx.cond(
            SchedulerState.error_msg != "",
            rx.box(
                rx.hstack(
                    rx.icon("triangle-alert", size=14, color="#FF6B6B"),
                    rx.text(SchedulerState.error_msg, style={
                        "color": "#FF6B6B", "font_size": "0.85rem",
                        "font_family": "'JetBrains Mono', monospace",
                    }),
                    spacing="2", align="center",
                ),
                style={
                    "background": "rgba(255,80,80,0.08)",
                    "border": "1px solid rgba(255,80,80,0.25)",
                    "border_radius": "8px",
                    "padding": "10px 14px",
                    "margin_top": "12px",
                },
            ),
            rx.box(),
        ),
        rx.hstack(
            rx.button(
                rx.icon("plus", size=15),
                "Agregar Proceso",
                on_click=SchedulerState.add_process,
                style={
                    "background": "linear-gradient(135deg, #00FFA3, #00C8FF)",
                    "color": "#0D0D1A",
                    "font_weight": "700",
                    "font_family": "'JetBrains Mono', monospace",
                    "font_size": "0.85rem",
                    "border_radius": "8px",
                    "padding": "8px 18px",
                    "cursor": "pointer",
                    "border": "none",
                    "_hover": {"opacity": "0.88", "transform": "translateY(-1px)"},
                    "transition": "all 0.15s ease",
                },
            ),
            rx.button(
                rx.icon("trash-2", size=15),
                "Limpiar todo",
                on_click=SchedulerState.clear_all,
                style={
                    "background": "rgba(255,255,255,0.06)",
                    "color": "#8888AA",
                    "font_family": "'JetBrains Mono', monospace",
                    "font_size": "0.85rem",
                    "border": "1px solid rgba(255,255,255,0.1)",
                    "border_radius": "8px",
                    "padding": "8px 18px",
                    "cursor": "pointer",
                    "_hover": {"background": "rgba(255,255,255,0.1)", "color": "#CCCCDD"},
                    "transition": "all 0.15s ease",
                },
            ),
            spacing="3",
            margin_top="1rem",
        ),
        style=CARD_STYLE,
    )


def process_table() -> rx.Component:
    return rx.cond(
        SchedulerState.process_count > 0,
        rx.box(
            section_title("Cola de Procesos"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        th_cell("PID"), th_cell("Llegada"),
                        th_cell("Rafaga"), th_cell("Prioridad"), th_cell(""),
                        style={"border_bottom": "1px solid rgba(255,255,255,0.08)"},
                    )
                ),
                rx.table.body(rx.foreach(SchedulerState.processes, process_row)),
                width="100%",
            ),
            style=CARD_STYLE,
        ),
        rx.box(),
    )


def gantt_section() -> rx.Component:
    return rx.box(
        section_title("Diagrama de Gantt", color="#00C8FF"),
        rx.box(
            rx.plotly(data=SchedulerState.gantt_figure, width="100%"),
            style={"border_radius": "8px", "overflow": "hidden"},
        ),
        style=CARD_STYLE,
    )


def stats_row() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text("T. Espera Promedio", style=LABEL_STYLE),
            rx.text(SchedulerState.avg_waiting, style={
                "color": "#00C8FF", "font_size": "2rem", "font_weight": "800",
                "font_family": "'JetBrains Mono', monospace", "line_height": "1",
            }),
            rx.text("unidades de tiempo", style={
                "color": "#44447A", "font_size": "0.75rem",
                "font_family": "'JetBrains Mono', monospace", "margin_top": "4px",
            }),
            style={**CARD_STYLE, "flex": "1"},
        ),
        rx.box(
            rx.text("T. Retorno Promedio", style=LABEL_STYLE),
            rx.text(SchedulerState.avg_turnaround, style={
                "color": "#A78BFA", "font_size": "2rem", "font_weight": "800",
                "font_family": "'JetBrains Mono', monospace", "line_height": "1",
            }),
            rx.text("unidades de tiempo", style={
                "color": "#44447A", "font_size": "0.75rem",
                "font_family": "'JetBrains Mono', monospace", "margin_top": "4px",
            }),
            style={**CARD_STYLE, "flex": "1"},
        ),
        rx.box(
            rx.text("Procesos Totales", style=LABEL_STYLE),
            rx.text(SchedulerState.process_count, style={
                "color": "#00FFA3", "font_size": "2rem", "font_weight": "800",
                "font_family": "'JetBrains Mono', monospace", "line_height": "1",
            }),
            rx.text("en la simulacion", style={
                "color": "#44447A", "font_size": "0.75rem",
                "font_family": "'JetBrains Mono', monospace", "margin_top": "4px",
            }),
            style={**CARD_STYLE, "flex": "1"},
        ),
        spacing="4",
        width="100%",
    )


def results_table() -> rx.Component:
    return rx.box(
        section_title("Resultados por Proceso", color="#A78BFA"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    th_cell("PID"), th_cell("Llegada"), th_cell("Rafaga"),
                    th_cell("Prioridad"), th_cell("1er Inicio"), th_cell("Fin"),
                    th_cell("T. Espera"), th_cell("T. Retorno"),
                    style={"border_bottom": "1px solid rgba(255,255,255,0.08)"},
                )
            ),
            rx.table.body(rx.foreach(SchedulerState.results, result_row)),
            width="100%",
        ),
        style=CARD_STYLE,
    )


def results_section() -> rx.Component:
    return rx.cond(
        SchedulerState.has_results,
        rx.vstack(
            gantt_section(),
            stats_row(),
            results_table(),
            spacing="4",
            width="100%",
        ),
        rx.box(),
    )


# ─── Pagina principal ────────────────────────────────────────────────────────
def index() -> rx.Component:
    return rx.box(
        rx.html("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&display=swap');
  body { background: #0D0D1A !important; }
  .grid-bg {
    background-image:
      linear-gradient(rgba(0,255,163,0.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,163,0.035) 1px, transparent 1px);
    background-size: 40px 40px;
  }
</style>
"""),
        rx.box(
            rx.vstack(
                rx.box(
                    rx.text("Algoritmos de Despacho", style={
                        "font_family": "'JetBrains Mono', monospace",
                        "font_size": "clamp(2rem, 5vw, 3.5rem)",
                        "font_weight": "800",
                        "background": "linear-gradient(135deg, #00FFA3 0%, #00C8FF 50%, #A78BFA 100%)",
                        "background_clip": "text",
                        "-webkit-background-clip": "text",
                        "color": "transparent",
                        "letter_spacing": "-0.02em",
                        "line_height": "1",
                        "justify_content": "center",
                    }),
                    rx.text(
                        "Simulador de Algoritmos de Despacho - Sistemas Operativos",
                        style={
                            "color": "#7777AA",
                            "font_family": "'JetBrains Mono', monospace",
                            "font_size": "0.85rem",
                            "letter_spacing": "0.06em",
                            "margin_top": "6px",
                        },
                    ),
                    style={"text_align": "center", "margin_bottom": "2.5rem"},
                ),
                algorithm_bar(),
                input_form(),
                process_table(),
                results_section(),
                spacing="4",
                width="100%",
            ),
            class_name="grid-bg",
            style={
                "max_width": "960px",
                "margin": "0 auto",
                "padding": "3rem 1.5rem",
                "min_height": "100vh",
            },
        ),
        style={"background": "#0D0D1A", "min_height": "100vh"},
    )


# ─── App ─────────────────────────────────────────────────────────────────────
app = rx.App(theme=rx.theme(appearance="dark"))
app.add_page(index, route="/", title="Scheduler - SO")