import sys
import math
import heapq
import numpy as np
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QDoubleSpinBox,
    QSpinBox, QTextEdit, QGridLayout, QGroupBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

UI_THEME = """
QMainWindow { background-color: #1e1e2e; }
QLabel { color: #cdd6f4; font-weight: bold; font-size: 13px; }
QGroupBox { border: 1px solid #45475a; border-radius: 8px; margin-top: 15px; background-color: #181825; color: #89b4fa; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; }
QPushButton { background-color: #89b4fa; color: #1e1e2e; border: none; padding: 12px; border-radius: 6px; font-weight: bold; font-size: 14px; }
QPushButton:hover { background-color: #b4befe; }
QDoubleSpinBox, QSpinBox { background-color: #313244; color: #cdd6f4; border: 1px solid #585b70; border-radius: 4px; padding: 6px; font-weight: bold; }
QTextEdit { background-color: #11111b; color: #a6e3a1; border: 1px solid #45475a; border-radius: 8px; font-size: 13px; font-family: 'Consolas', monospace; padding: 10px; }
"""

# типы событий
EV_ARRIVAL = 0
EV_DEPARTURE = 1
EV_DROPOUT = 2

class Event:
    def __init__(self, time, event_type, req_id):
        self.time = time
        self.type = event_type
        self.req_id = req_id  # ID заявки

    def __lt__(self, other):
        return self.time < other.time


class SimulationEngine:
    def __init__(self, arrival_rate, service_rate, num_servers, queue_capacity, max_wait_time, total_requests):
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.num_servers = num_servers
        self.queue_capacity = queue_capacity
        self.max_wait_time = max_wait_time
        self.total_requests = total_requests

        self.max_sys_capacity = num_servers + queue_capacity
        self.events = []
        self.queue = []  # массив с ID заявок

        self.free_servers = num_servers
        self.in_system = 0

        self.served_count = 0
        self.rejected_count = 0
        self.dropped_count = 0

        self.state_times = {i: 0.0 for i in range(self.max_sys_capacity + 1)}

    def simulate(self):
        heapq.heappush(self.events, Event(0.0, EV_ARRIVAL, 1))
        req_count = 1

        prev_time = 0.0
        current_time = 0.0

        while self.events:
            event = heapq.heappop(self.events)
            current_time = event.time
            req_id = event.req_id

            # учет времени нахождения системы в состояниях
            self.state_times[self.in_system] += (current_time - prev_time)
            prev_time = current_time

            if event.type == EV_ARRIVAL:
                # генерируем следующую заявку
                if req_count < self.total_requests:
                    next_arrival = current_time + np.random.exponential(1.0 / self.arrival_rate)
                    req_count += 1
                    heapq.heappush(self.events, Event(next_arrival, EV_ARRIVAL, req_count))

                # судьба прибывшей заявки
                if self.free_servers > 0:
                    self.in_system += 1
                    self.free_servers -= 1
                    proc_time = np.random.exponential(1.0 / self.service_rate)
                    heapq.heappush(self.events, Event(current_time + proc_time, EV_DEPARTURE, req_id))

                elif len(self.queue) < self.queue_capacity:
                    self.in_system += 1
                    self.queue.append(req_id)
                    # запускаем таймер ожидания
                    dropout_time = current_time + self.max_wait_time
                    heapq.heappush(self.events, Event(dropout_time, EV_DROPOUT, req_id))
                else:
                    self.rejected_count += 1

            elif event.type == EV_DEPARTURE:
                self.in_system -= 1
                self.served_count += 1

                # прибор освободился, берем первую заявку из очереди
                if self.queue:
                    next_req_id = self.queue.pop(0)
                    proc_time = np.random.exponential(1.0 / self.service_rate)
                    heapq.heappush(self.events, Event(current_time + proc_time, EV_DEPARTURE, next_req_id))
                else:
                    self.free_servers += 1

            elif event.type == EV_DROPOUT:
                # если заявка всё ещё в очереди, то она удалится
                try:
                    self.queue.remove(req_id)
                    self.dropped_count += 1
                    self.in_system -= 1
                except ValueError:
                    pass

        p_empirical = {k: v / current_time for k, v in self.state_times.items()}
        return p_empirical, current_time

    def calculate_theory(self):
        rho = self.arrival_rate / self.service_rate
        p_theor = {}

        fact_c = math.factorial(self.num_servers)
        sum0 = sum((rho ** k) / math.factorial(k) for k in range(self.num_servers + 1))
        sum1 = sum((rho ** (self.num_servers + i)) / (fact_c * (self.num_servers ** i)) for i in range(1, self.queue_capacity + 1))

        p_theor[0] = 1.0 / (sum0 + sum1)
        for k in range(1, self.num_servers + 1):
            p_theor[k] = (rho ** k / math.factorial(k)) * p_theor[0]
        for i in range(1, self.queue_capacity + 1):
            p_theor[self.num_servers + i] = (rho ** (self.num_servers + i) / (fact_c * (self.num_servers ** i))) * p_theor[0]

        return p_theor

class QueuingLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("СМО: Многоканальная с очередью и нетерпеливостью")
        self.resize(1100, 750)
        self.setStyleSheet(UI_THEME)

        self.params_config = {
            "arrival_rate": ("Интенсивность потока (λ):", float, 0.1, 1000.0, 10.0, 0.5),
            "service_rate": ("Скорость обслуживания (μ):", float, 0.1, 1000.0, 3.0, 0.5),
            "num_servers": ("Количество приборов (c):", int, 1, 100, 3, 1),
            "queue_capacity": ("Мест в очереди (K):", int, 0, 1000, 10, 1),
            "max_wait_time": ("Предел ожидания (T):", float, 0.1, 1000.0, 2.0, 0.5),
            "total_requests": ("Объем выборки (N):", int, 1000, 5000000, 20000, 5000)
        }
        self.inputs = {}
        self.build_ui()
        self.run_simulation()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        left_panel = QVBoxLayout()
        group_params = QGroupBox("Параметры модели")
        grid = QGridLayout(group_params)

        for row, (key, (label, val_type, min_v, max_v, def_v, step)) in enumerate(self.params_config.items()):
            box = QDoubleSpinBox() if val_type == float else QSpinBox()
            box.setRange(min_v, max_v)
            box.setValue(def_v)
            box.setSingleStep(step)
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(box, row, 1)
            self.inputs[key] = box

        left_panel.addWidget(group_params)

        self.btn_run = QPushButton("СТАРТ СИМУЛЯЦИИ")
        self.btn_run.clicked.connect(self.run_simulation)
        left_panel.addWidget(self.btn_run)

        self.results_log = QTextEdit()
        self.results_log.setReadOnly(True)
        left_panel.addWidget(self.results_log)

        self.canvas = FigureCanvas(plt.Figure(figsize=(8, 6), facecolor='#1e1e2e'))

        layout.addLayout(left_panel, 1)
        layout.addWidget(self.canvas, 2)

    def run_simulation(self):
        self.btn_run.setEnabled(False)
        self.btn_run.setText("ВЫЧИСЛЕНИЕ...")
        QApplication.processEvents()

        vals = {key: box.value() for key, box in self.inputs.items()}

        engine = SimulationEngine(**vals)
        p_emp, total_time = engine.simulate()
        p_theor = engine.calculate_theory()

        max_states = vals["num_servers"] + vals["queue_capacity"]
        labels = [f"{i}" for i in range(max_states + 1)]
        emp_vals = [p_emp.get(i, 0.0) for i in range(max_states + 1)]
        theor_vals = [p_theor.get(i, 0.0) for i in range(max_states + 1)]

        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        ax.set_facecolor('#181825')

        x = np.arange(len(labels))
        ax.plot(x, theor_vals, color='#89b4fa', linestyle='--', linewidth=2, label='Теория (Идеальная очередь)')
        ax.plot(x, emp_vals, color='#a6e3a1', marker='o', linewidth=2, markersize=5, label='Имитация (С нетерпеливостью)')

        ax.set_title(f"Вероятности состояний (ρ = {vals['arrival_rate'] / vals['service_rate']:.2f})", color='#cdd6f4', pad=15, weight='bold')
        ax.set_xlabel("Число заявок в системе (k)", color='#cdd6f4')
        ax.set_ylabel("Вероятность (p_k)", color='#cdd6f4')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, color='#cdd6f4')
        ax.tick_params(axis='y', colors='#cdd6f4')
        ax.grid(color='#45475a', linestyle='-', linewidth=0.5)
        for spine in ax.spines.values(): spine.set_color('#45475a')
        ax.legend(facecolor='#11111b', edgecolor='#45475a', labelcolor='#cdd6f4')
        self.canvas.draw()

        n = vals["total_requests"]
        served = engine.served_count
        rejected = engine.rejected_count
        dropped = engine.dropped_count

        report = (
            "=== РЕЗУЛЬТАТЫ СИМУЛЯЦИИ ===\n\n"
            f"Сгенерировано заявок: {n}\n"
            f"Время симуляции: {total_time:.1f} ед.\n\n"
            "--- СУДЬБА ЗАЯВОК ---\n"
            f"Обслужено:    {served} ({(served / n) * 100:.1f}%)\n"
            f"Отказ (мест нет): {rejected} ({(rejected / n) * 100:.1f}%)\n"
            f"Ушли из очереди:  {dropped} ({(dropped / n) * 100:.1f}%)\n\n"
            "--- СРАВНЕНИЕ ПРОСТОЯ (P0) ---\n"
            f"P0 (Теория Эрланга): {p_theor.get(0, 0):.4f}\n"
            f"P0 (Имитация):       {p_emp.get(0, 0):.4f}\n"
        )
        self.results_log.setText(report)
        self.btn_run.setText("СТАРТ СИМУЛЯЦИИ")
        self.btn_run.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = QueuingLabWindow()
    w.show()
    sys.exit(app.exec())