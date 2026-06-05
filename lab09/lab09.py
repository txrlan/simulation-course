import sys
import numpy as np
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QDoubleSpinBox,
    QSpinBox, QTextEdit, QFormLayout, QGroupBox, QAbstractSpinBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

UI_THEME = """
QMainWindow { background-color: #1e1e2e; }
QLabel { color: #cdd6f4; font-family: 'Segoe UI', Arial; font-size: 13px; font-weight: bold; }
QGroupBox { 
    border: 2px solid #89b4fa; border-radius: 6px; 
    color: #89b4fa; font-weight: bold; margin-top: 15px; padding-top: 10px;
}
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }
QPushButton { 
    background-color: #89b4fa; color: #1e1e2e; 
    border: none; padding: 12px; border-radius: 6px; font-weight: bold; font-size: 14px;
}
QPushButton:hover { background-color: #b4befe; }
QDoubleSpinBox, QSpinBox { 
    background-color: #313244; color: #cdd6f4; 
    border: 1px solid #585b70; border-radius: 4px; padding: 6px; font-size: 13px;
}
QDoubleSpinBox:focus, QSpinBox:focus { border: 1px solid #89b4fa; }
QTextEdit { 
    background-color: #181825; color: #a6e3a1; 
    border: 1px solid #45475a; border-radius: 6px; 
    font-size: 13px; font-family: 'Consolas', 'Courier New'; padding: 10px;
}
"""


def run_simulation(rate_in, rate_out, total_requests):
    success_count = 0
    fail_count = 0

    t_curr = 0.0
    system_free_at = 0.0

    for i in range(total_requests):
        if t_curr < system_free_at:
            delta_t_busy = np.random.exponential(2.0 / rate_in)
            potential_arrival = t_curr + delta_t_busy

            if potential_arrival < system_free_at:
                t_curr = potential_arrival
                fail_count += 1
            else:
                delta_t_free = np.random.exponential(1.0 / rate_in)
                t_curr = system_free_at + delta_t_free

                success_count += 1
                process_time = np.random.exponential(1.0 / rate_out)
                system_free_at = t_curr + process_time
        else:
            delta_t = np.random.exponential(1.0 / rate_in)
            t_curr += delta_t

            success_count += 1
            process_time = np.random.exponential(1.0 / rate_out)
            system_free_at = t_curr + process_time

    p0 = success_count / total_requests
    p1 = fail_count / total_requests
    return p0, p1

class StatisticsCanvas(FigureCanvasQTAgg):
    def __init__(self):
        fig = plt.Figure(figsize=(7, 6), facecolor='#1e1e2e')
        super().__init__(fig)
        self.axes = fig.add_subplot(111)

    def draw_bars(self, emp_data, theor_data, load_factor):
        self.axes.clear()
        self.axes.set_facecolor('#1e1e2e')

        categories = ['Свободен (P0)', 'Занят - Отказ (P1)']
        x_positions = np.arange(len(categories))
        bar_width = 0.35

        self.axes.bar(x_positions - bar_width / 2, emp_data, bar_width,
                      label='Моделирование', color='#89b4fa', edgecolor='#1e1e2e')
        self.axes.bar(x_positions + bar_width / 2, theor_data, bar_width,
                      label='Аналитика', color='#cba6f7', edgecolor='#1e1e2e', alpha=0.85)

        self.axes.set_title(f"Состояния системы (ρ = {load_factor:.2f})",
                            color='#89b4fa', fontsize=14, fontweight='bold', pad=15)
        self.axes.set_xticks(x_positions)
        self.axes.set_xticklabels(categories, color='#cdd6f4', fontsize=12, fontweight='bold')
        self.axes.tick_params(axis='y', colors='#cdd6f4')
        self.axes.legend(facecolor='#181825', edgecolor='#45475a', labelcolor='#cdd6f4')
        self.axes.grid(color='#45475a', linestyle='--', alpha=0.5, axis='y')

        self.draw()

class QueuingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Имитационное моделирование M/M/1/0")
        self.resize(1024, 680)
        self.setStyleSheet(UI_THEME)
        self.build_ui()
        self.execute_calculation() # автозапуск при открытии

    def build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        window_layout = QHBoxLayout(main_widget)

        # контейнер настроек
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(15)

        param_box = QGroupBox("Входные данные")
        form = QFormLayout()
        form.setSpacing(15)

        # создаем поля через вспомогательный метод
        self.input_lambda = self._create_input(5.0, 1000.0, is_float=True)
        self.input_mu = self._create_input(6.0, 1000.0, is_float=True)
        self.input_n = self._create_input(50000, 5000000, is_float=False)

        form.addRow("Поток заявок (λ):", self.input_lambda)
        form.addRow("Скорость обслуживания (μ):", self.input_mu)
        form.addRow("Размер выборки (N):", self.input_n)

        param_box.setLayout(form)
        settings_layout.addWidget(param_box)

        self.btn_calc = QPushButton("СТАРТ СИМУЛЯЦИИ")
        self.btn_calc.clicked.connect(self.execute_calculation)
        settings_layout.addWidget(self.btn_calc)

        self.text_report = QTextEdit()
        self.text_report.setReadOnly(True)
        settings_layout.addWidget(self.text_report)

        window_layout.addLayout(settings_layout, 2)

        self.plot_canvas = StatisticsCanvas()
        window_layout.addWidget(self.plot_canvas, 3)

    def _create_input(self, default_val, max_val, is_float):
        # фабрика полей
        box = QDoubleSpinBox() if is_float else QSpinBox()
        box.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        box.setMaximum(max_val)
        if is_float:
            box.setMinimum(0.01)
        else:
            box.setMinimum(100)
        box.setValue(default_val)
        return box

    def execute_calculation(self):
        # чтение параметров
        rate_lambda = self.input_lambda.value()
        rate_mu = self.input_mu.value()
        requests_count = self.input_n.value()

        # симуляция
        p0_emp, p1_emp = run_simulation(rate_lambda, rate_mu, requests_count)

        # расчет (эрланг)
        rho = rate_lambda / rate_mu
        p0_theor = 1.0 / (1.0 + 0.5 * rho)
        p1_theor = (rho * 0.5) / (1.0 + 0.5 * rho)

        throughput_theor = rate_lambda * p0_theor
        throughput_emp = rate_lambda * p0_emp

        self.plot_canvas.draw_bars(
            emp_data=[p0_emp, p1_emp],
            theor_data=[p0_theor, p1_theor],
            load_factor=rho
        )

        # отчетес
        report_lines = [
            "--- РЕЗУЛЬТАТЫ СИМУЛЯЦИИ M/M/1/0 ---",
            f"\nИнтенсивность нагрузки (ρ): {rho:.3f}\n",
            "СОСТОЯНИЕ P0 (СИСТЕМА СВОБОДНА):",
            f" Теоретически: {p0_theor:.4f}",
            f" Практически:  {p0_emp:.4f}",
            f" Погрешность:  {abs(p0_theor - p0_emp):.4f}\n",
            "СОСТОЯНИЕ P1 (СИСТЕМА ЗАНЯТА / ОТКАЗ):",
            f" Теоретически: {p1_theor:.4f}",
            f" Практически:  {p1_emp:.4f}",
            f" Погрешность:  {abs(p1_theor - p1_emp):.4f}\n",
            "АБСОЛЮТНАЯ ПРОПУСКНАЯ СПОСОБНОСТЬ (A):",
            f" Аналитика: {throughput_theor:.3f} з/ед.вр",
            f" Имитация:  {throughput_emp:.3f} з/ед.вр"
        ]
        self.text_report.setText("\n".join(report_lines))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueuingApp()
    window.show()
    sys.exit(app.exec())