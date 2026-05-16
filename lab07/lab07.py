import tkinter as tk
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import csv
import threading
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class WeatherCTMCApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Модель погоды (Непрерывное время)")
        self.geometry("1600x900")
        self.configure(fg_color="#121212")

        self.running = False
        self.current_time = 0.0
        self.current_state = 0
        self.step_counter = 0

        self.history_times = [0.0]
        self.history_states = [0]
        self.time_spent = np.zeros(3)
        self.theo_probs = np.zeros(3)

        self.states = {0: "Ясно", 1: "Облачно", 2: "Пасмурно"}
        self.csv_file = "weather_report.csv"

        self.milestones = [10, 50, 200, 1000]
        self.reached_milestones = set()

        self.setup_ui()
        self.reset_data()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=450, fg_color="#1e1e1e", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Заголовок изменен на матрицу Q
        ctk.CTkLabel(self.sidebar, text="МАТРИЦА ИНТЕНСИВНОСТЕЙ (Q)",
                     font=("Helvetica", 15, "bold"), text_color="#ffffff").pack(pady=(30, 10))

        matrix_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        matrix_frame.pack(pady=10, padx=20)

        # Дефолтные интенсивности (сумма строк = 0)
        default_q = [[-0.4, 0.3, 0.1], [0.2, -0.5, 0.3], [0.1, 0.4, -0.5]]
        headers = ["Ясно", "Облачно", "Пасмурно"]

        for j, h in enumerate(headers):
            ctk.CTkLabel(matrix_frame, text=h, font=("Helvetica", 12), text_color="#aaaaaa").grid(row=0, column=j + 1,
                                                                                                  padx=8, pady=5)

        self.matrix_inputs = []
        for i in range(3):
            ctk.CTkLabel(matrix_frame, text=headers[i], font=("Helvetica", 12), text_color="#aaaaaa").grid(row=i + 1,
                                                                                                           column=0,
                                                                                                           padx=15,
                                                                                                           pady=5,
                                                                                                           sticky="e")
            row_entries = []
            for j in range(3):
                entry = ctk.CTkEntry(matrix_frame, width=70, height=35, fg_color="#2c2c2c", text_color="#ffffff",
                                     border_width=1, border_color="#444444", corner_radius=6, justify="center")
                entry.insert(0, str(default_q[i][j]))
                entry.grid(row=i + 1, column=j + 1, padx=6, pady=6)
                row_entries.append(entry)
            self.matrix_inputs.append(row_entries)

        self.most_prob_card = ctk.CTkFrame(self.sidebar, fg_color="#2c2c2c", corner_radius=8)
        self.most_prob_card.pack(pady=20, padx=30, fill="x")
        self.most_prob_lbl = ctk.CTkLabel(self.most_prob_card, text="Наиболее вероятно: ---",
                                          font=("Helvetica", 14, "bold"), text_color="#00ffcc")
        self.most_prob_lbl.pack(pady=10)

        ctk.CTkLabel(self.sidebar, text="КОНТРОЛЬНЫЕ ТОЧКИ:", font=("Helvetica", 13, "bold")).pack(pady=(10, 5))
        self.stats_box = ctk.CTkTextbox(self.sidebar, height=200, fg_color="#121212", text_color="#00ffcc",
                                        font=("Consolas", 12))
        self.stats_box.pack(pady=10, padx=30, fill="x")

        self.speed_slider = ctk.CTkSlider(self.sidebar, from_=0.0, to=0.5, width=280)
        self.speed_slider.set(0.05)
        self.speed_slider.pack(pady=10)

        self.start_btn = ctk.CTkButton(self.sidebar, text="СТАРТ", command=self.toggle_sim, fg_color="#ffffff",
                                       text_color="#111111", hover_color="#dddddd", font=("Helvetica", 15, "bold"),
                                       height=45)
        self.start_btn.pack(pady=(20, 10), padx=40, fill="x")

        self.reset_btn = ctk.CTkButton(self.sidebar, text="Сброс", command=self.full_reset, border_width=1,
                                       border_color="#555555", fg_color="transparent")
        self.reset_btn.pack(padx=40, fill="x")

        self.main_area = ctk.CTkFrame(self, fg_color="#121212", corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        self.header_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(10, 40))

        self.state_label = ctk.CTkLabel(self.header_frame, text="Ожидание...", font=("Helvetica", 45, "bold"),
                                        text_color="#ffffff")
        self.state_label.pack(side="left", padx=20)

        self.time_label = ctk.CTkLabel(self.header_frame, text="0.0 дн.", font=("Helvetica", 32), text_color="#888888")
        self.time_label.pack(side="right", padx=20)

        self.fig, (self.ax_line, self.ax_bar) = plt.subplots(1, 2, figsize=(13, 6), facecolor='#121212')
        self.fig.subplots_adjust(left=0.18, bottom=0.2, right=0.96, top=0.85, wspace=0.3)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_area)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.clean_axes()

    def calc_stationary(self, q):
        try:
            n = q.shape[0]
            a = q.T.copy()
            a[-1] = np.ones(n)
            b = np.zeros(n)
            b[-1] = 1
            res = np.linalg.solve(a, b)
            idx = np.argmax(res)
            self.most_prob_lbl.configure(text=f"Наиболее вероятно: {self.states[idx]} ({res[idx] * 100:.1f}%)")
            return res
        except:
            return np.array([0.33, 0.33, 0.34])

    def toggle_sim(self):
        if not self.running:
            q_mat = self.get_matrix()
            if q_mat is None or not np.allclose(q_mat.sum(axis=1), 0, atol=1e-3):
                tk.messagebox.showerror("Ошибка", "Сумма строки в матрице Q должна быть равна 0")
                return
            self.theo_probs = self.calc_stationary(q_mat)
            self.running = True
            self.start_btn.configure(text="СТОП")
            threading.Thread(target=self.run_model, daemon=True).start()
        else:
            self.running = False
            self.start_btn.configure(text="СТАРТ")

    def run_model(self):
        q_mat = self.get_matrix()
        while self.running:
            # Интенсивность выхода из состояния i
            q_i = -q_mat[self.current_state, self.current_state]

            if q_i <= 0:  # Защита, если оказались в поглощающем состоянии
                time.sleep(self.speed_slider.get())
                continue

            # Генерируем экспоненциально распределенное время пребывания
            tau = np.random.exponential(1.0 / q_i)

            # Вычисляем вероятности перехода (P_ij = Q_ij / -Q_ii)
            p_row = np.maximum(q_mat[self.current_state], 0)
            p_row[self.current_state] = 0  # Убираем вероятность остаться в самом себе
            p_row = p_row / np.sum(p_row)

            u = np.random.rand()
            acc = 0.0
            nxt = self.current_state
            for i in range(3):
                acc += p_row[i]
                if u <= acc:
                    nxt = i
                    break

            start_t = self.current_time
            self.time_spent[self.current_state] += tau
            self.current_time += tau

            for m in self.milestones:
                if self.current_time >= m and m not in self.reached_milestones:
                    self.record_milestone(m)
                    self.reached_milestones.add(m)

            self.current_state = nxt
            self.step_counter += 1
            self.history_times.append(self.current_time)
            self.history_states.append(self.current_state)

            self.after(0, self.draw_charts)

            with open(self.csv_file, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                # Теперь мы записываем 'tau' как длительность пребывания
                writer.writerow([self.step_counter, start_t, tau, self.current_state + 1,
                                 self.states[self.current_state]])

            time.sleep(self.speed_slider.get())

    def record_milestone(self, m_day):
        emp = self.time_spent / sum(self.time_spent)
        dev = np.mean(np.abs(emp - self.theo_probs)) * 100

        text = f"{m_day} ДНЕЙ\n"
        text += f"Опыт: {emp[0]:.3f}, {emp[1]:.3f}, {emp[2]:.3f}\n"
        text += f"Отклонение: {dev:.2f}%\n\n"

        self.stats_box.insert("end", text)
        self.stats_box.see("end")

    def draw_charts(self):
        self.time_label.configure(text=f"{self.current_time:.1f} дн.")  # Отображаем дробное время
        self.state_label.configure(text=self.states[self.current_state])

        self.ax_line.clear()
        self.ax_line.step(self.history_times[-40:], self.history_states[-40:], where='post', color='#00ffcc', lw=2)
        self.ax_line.set_yticks([0, 1, 2])
        self.ax_line.set_yticklabels(["Ясно", "Облачно", "Пасмурно"])
        self.ax_line.set_title("Динамика переходов", color="white", loc="left")

        self.ax_bar.clear()
        emp = self.time_spent / self.current_time if self.current_time > 0 else np.zeros(3)
        x = np.arange(3)
        self.ax_bar.bar(x - 0.17, emp, 0.34, color='#00ffcc', label='практика')
        self.ax_bar.bar(x + 0.17, self.theo_probs, 0.34, color='#444444', label='теория')
        self.ax_bar.set_xticks(x)
        self.ax_bar.set_xticklabels(["Ясно", "Облачно", "Пасмурно"])
        self.ax_bar.set_ylim(0, 1)
        self.ax_bar.legend(frameon=False, labelcolor="white")
        self.ax_bar.set_title("Распределение", color="white", loc="left")

        self.clean_axes()
        self.canvas.draw()

    def get_matrix(self):
        try:
            return np.array([[float(e.get()) for e in row] for row in self.matrix_inputs])
        except:
            return None

    def clean_axes(self):
        for ax in [self.ax_line, self.ax_bar]:
            ax.set_facecolor('#121212')
            ax.tick_params(colors='#888888', labelsize=10)
            for s in ax.spines.values(): s.set_visible(False)

    def reset_data(self):
        with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["шаг", "старт_день", "длительность", "код", "погода"])

    def full_reset(self):
        self.running = False
        self.current_time = 0.0
        self.time_spent = np.zeros(3)
        self.reached_milestones.clear()
        self.stats_box.delete("1.0", "end")
        self.history_times, self.history_states = [0.0], [0]
        self.reset_data()
        self.draw_charts()


if __name__ == "__main__":
    app = WeatherCTMCApp()
    app.mainloop()