import tkinter as tk
from tkinter import ttk
import numpy as np
from scipy.stats import poisson

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PoissonSimulationApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("lab08")
        self.root.geometry("1050x650")
        self.root.configure(bg="#f0f0f0")

        self.left_frame = ttk.Frame(self.root, padding="10")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.right_frame = ttk.Frame(self.root, padding="10")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.rate_lambda = tk.DoubleVar(value=5.0)
        self.time_t = tk.DoubleVar(value=2.0)
        self.experiments_count = tk.IntVar(value=10000)

        self._build_controls()
        self._build_plot_area()

        self.run_experiment()

    def _build_controls(self):
        ttk.Label(self.left_frame, text="Интенсивность λ (заявок/сек):", font=("Segoe UI", 10, "bold")).pack(
            anchor=tk.W, pady=(10, 2))
        ttk.Spinbox(self.left_frame, from_=0.1, to=50.0, increment=0.5, textvariable=self.rate_lambda,
                    font=("Segoe UI", 10)).pack(fill=tk.X, pady=(0, 15))

        ttk.Label(self.left_frame, text="Интервал времени time_t (сек):", font=("Segoe UI", 10, "bold")).pack(
            anchor=tk.W, pady=(0, 2))
        ttk.Spinbox(self.left_frame, from_=0.1, to=20.0, increment=0.5, textvariable=self.time_t,
                    font=("Segoe UI", 10)).pack(fill=tk.X, pady=(0, 15))

        ttk.Label(self.left_frame, text="Количество экспериментов N:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W,
                                                                                                           pady=(0, 2))
        ttk.Spinbox(self.left_frame, from_=100, to=100000, increment=1000, textvariable=self.experiments_count,
                    font=("Segoe UI", 10)).pack(fill=tk.X, pady=(0, 20))

        self.btn_simulate = tk.Button(self.left_frame, text="СМОДЕЛИРОВАТЬ ПОТОК", bg="#4CAF50", fg="black",
                                      font=("Segoe UI", 11, "bold"), relief=tk.FLAT, command=self.run_experiment)
        self.btn_simulate.pack(fill=tk.X, ipady=8, pady=(0, 20))

        ttk.Label(self.left_frame, text="Результаты и Вывод:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.output_text = tk.Text(self.left_frame, height=12, width=35, font=("Segoe UI", 10), wrap=tk.WORD,
                                   bg="#ffffff", fg="black", relief=tk.SOLID, borderwidth=1)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def _build_plot_area(self):
        self.fig, self.ax = plt.subplots(facecolor="#f0f0f0")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def run_experiment(self):
        current_lambda = self.rate_lambda.get()
        current_t = self.time_t.get()
        total_exp = self.experiments_count.get()

        expected_requests = current_lambda * current_t

        # массив для сохранения числа событий в каждом эксперименте
        simulated_counts = np.zeros(total_exp, dtype=int)

        # генерация заявок через экспоненциальные интервалы
        for idx in range(total_exp):
            time_accumulator = 0.0
            events_registered = 0

            # пока не вышли за рамки current_t, прибавляем случайный шаг и считаем события
            while (time_accumulator := time_accumulator + np.random.exponential(1.0 / current_lambda)) <= current_t:
                events_registered += 1

            simulated_counts[idx] = events_registered

        calc_mean = np.mean(simulated_counts)
        calc_var = np.var(simulated_counts)

        self._update_plot(simulated_counts, expected_requests, current_t)
        self._update_report(expected_requests, calc_mean, calc_var)

    def _update_plot(self, simulated_counts, expected_requests, current_t):
        self.ax.clear()
        self.ax.set_facecolor("white")
        self.ax.grid(color="#d3d3d3", linestyle=":", linewidth=1.5)

        max_events = max(simulated_counts) if len(simulated_counts) > 0 else int(expected_requests * 2)
        hist_bins = np.arange(-0.5, max_events + 1.5, 1)

        self.ax.hist(simulated_counts, bins=hist_bins, density=True, color="#64b5f6", edgecolor="#1976d2", alpha=0.75,
                     label="Модель (Гистограмма)")

        x_points = np.arange(0, max_events + 1)
        y_points = poisson.pmf(x_points, expected_requests)
        self.ax.plot(x_points, y_points, "s--", color="#d32f2f", linewidth=2, markersize=5.5,
                     label=f"Теория (λT = {expected_requests:.1f})")

        self.ax.set_title(f"Распределение числа заявок на сервере за time_t = {current_t}с", fontsize=6)
        self.ax.set_xlabel("Количество поступивших заявок", fontsize=6)
        self.ax.set_ylabel("Относительная частота / Вероятность", fontsize=6)
        self.ax.legend(fontsize=6)

        self.fig.tight_layout()
        self.canvas.draw()

    def _update_report(self, expected_requests, calc_mean, calc_var):
        # анализ разницы между математическим ожиданием и дисперсией
        difference = abs(calc_mean - calc_var)

        report_text = (
            f"Теоретическое ожидание (λT): {expected_requests:.3f}\n"
            f"Эмпирическое среднее: {calc_mean:.3f}\n"
            f"Эмпирическая дисперсия: {calc_var:.3f}\n\n"
            f"ВЫВОД:\n"
        )

        # проверка ключевого свойства простейшего потока
        if difference < max(0.5, expected_requests * 0.1):
            report_text += "Среднее значение и дисперсия практически равны. Эмпирическое распределение соответствует теоретическому распределению Пуассона."
        else:
            report_text += "Обнаружено расхождение между средним и дисперсией. Рекомендуется увеличить количество экспериментов total_exp."

        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, report_text)
        self.output_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = PoissonSimulationApp(root)
    root.mainloop()