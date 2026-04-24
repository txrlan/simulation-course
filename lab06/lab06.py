import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import scipy.stats as stats
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# темная тема вконтакте
bg_color = "#2b2b2b"
fg_color = "#ffffff"
entry_bg = "#3c3f41"
entry_fg = "#ffffff"
btn_bg = "#4a4d50"
btn_active = "#5c5f61"
plot_bg = "#2b2b2b"
axis_color = "#ffffff"
readonly_bg = "#222222"
error_bg = "#5a1e1e"


class SimulationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("лаб06")
        self.geometry("950x600")
        self.minsize(850, 550)
        self.configure(bg=bg_color)

        self.apply_dark_style()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1, text=" Дискретная СВ ")
        self.notebook.add(self.tab2, text=" Нормальная СВ ")

        self.init_tab1()
        self.init_tab2()

    def apply_dark_style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', background=bg_color, foreground=fg_color, font=('Arial', 10))
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TEntry', fieldbackground=entry_bg, foreground=entry_fg, insertcolor=fg_color, borderwidth=1)
        style.configure('TButton', background=btn_bg, foreground=fg_color, borderwidth=1, focuscolor=btn_active)
        style.map('TButton', background=[('active', btn_active)])
        style.configure('TNotebook', background=bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background=entry_bg, foreground=fg_color, padding=[10, 5], borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', btn_active)], foreground=[('selected', fg_color)])

    def style_axis(self, ax):
        ax.set_facecolor(plot_bg)
        ax.tick_params(colors=axis_color)
        ax.xaxis.label.set_color(axis_color)
        ax.yaxis.label.set_color(axis_color)
        ax.title.set_color(axis_color)
        for spine in ax.spines.values():
            spine.set_edgecolor(axis_color)

    # дискретная св
    def init_tab1(self):
        left_frame = ttk.Frame(self.tab1, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        right_frame = ttk.Frame(self.tab1, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.p_vars = []
        for i in range(1, 5):
            ttk.Label(left_frame, text=f"Prob {i}:").grid(row=i - 1, column=0, sticky=tk.W, pady=8)
            var = tk.StringVar()
            var.trace_add("write", self.update_p5)
            ttk.Entry(left_frame, textvariable=var, width=15).grid(row=i - 1, column=1, pady=8)
            self.p_vars.append(var)

        ttk.Label(left_frame, text="Prob 5 (auto):").grid(row=4, column=0, sticky=tk.W, pady=8)
        self.p5_var = tk.StringVar()
        self.p5_entry = tk.Entry(left_frame, textvariable=self.p5_var, width=15, state='readonly',
                                 readonlybackground=readonly_bg, fg=fg_color, insertbackground=fg_color,
                                 highlightthickness=0, relief=tk.FLAT, font=('Arial', 10))
        self.p5_entry.grid(row=4, column=1, pady=8, ipady=3)

        ttk.Label(left_frame, text="Объем выборки (N):").grid(row=5, column=0, sticky=tk.W, pady=25)
        self.n_var_tab1 = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.n_var_tab1, width=15).grid(row=5, column=1, pady=25)

        ttk.Button(left_frame, text="Start", command=self.run_discrete).grid(row=6, column=0, columnspan=2, pady=10,
                                                                             ipadx=30, ipady=5)

        self.fig1 = Figure(figsize=(5, 4), dpi=100)
        self.fig1.patch.set_facecolor(plot_bg)
        self.ax1 = self.fig1.add_subplot(111)
        self.style_axis(self.ax1)

        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=right_frame)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        res_frame = ttk.Frame(right_frame)
        res_frame.pack(fill=tk.X, pady=10)

        self.lbl_stats1 = tk.Label(res_frame, text="Введите данные и нажмите start\n", font=("Arial", 11), bg=bg_color,
                                   fg=fg_color, justify=tk.LEFT)
        self.lbl_stats1.pack(anchor=tk.W)
        self.lbl_bool1 = tk.Label(res_frame, text="", font=("Arial", 11, "bold"), bg=bg_color)
        self.lbl_bool1.pack(anchor=tk.W)

    def update_p5(self, *args):
        # считаем пятую вероятность вычитая остальные из единицы
        try:
            total_p = sum(float(var.get()) for var in self.p_vars if var.get().replace('.', '', 1).isdigit())
            p5 = 1.0 - total_p
            self.p5_var.set(f"{p5:.4f}")
            # если сумма больше 1 = ошибка
            if p5 < 0:
                self.p5_entry.config(readonlybackground=error_bg)
            else:
                self.p5_entry.config(readonlybackground=readonly_bg)
        except ValueError:
            pass

    def run_discrete(self):
        try:
            probs = [float(var.get()) for var in self.p_vars]
            p5 = float(self.p5_var.get())
            probs.append(p5)
            n = int(self.n_var_tab1.get())

            if any(p < 0 for p in probs) or abs(sum(probs) - 1.0) > 1e-5:
                raise ValueError("Сумма вероятностей должна быть равна 1.")
            if n <= 0: raise ValueError("N должно быть > 0.")

            values = [1, 2, 3, 4, 5]

            # формулы теоретического среднего и дисперсии
            theor_mean = sum(v * p for v, p in zip(values, probs))
            theor_var = sum(((v - theor_mean) ** 2) * p for v, p in zip(values, probs))

            # генерация выборки методом обратного преобразования
            sample = []
            cdf = np.cumsum(probs)  # считаем кумулятивные отрезки
            for _ in range(n):
                u = random.random()  # равномерное число от 0 до 1
                for i, c in enumerate(cdf):
                    # в какой отрезок попало число
                    if u <= c:
                        sample.append(values[i])
                        break
            sample = np.array(sample)

            # считаем что получилось
            emp_mean = np.mean(sample)
            emp_var = np.var(sample)

            # процент ошибки
            error_mean = abs(emp_mean - theor_mean) / theor_mean * 100
            error_var = abs(emp_var - theor_var) / theor_var * 100 if theor_var > 0 else 0

            # подсчет частот для гистограммы
            unique, counts = np.unique(sample, return_counts=True)
            emp_freqs = np.zeros(5)
            for val, count in zip(unique, counts):
                emp_freqs[val - 1] = count

            # критерий хи2
            expected_freqs = np.array(probs) * n
            chi_squared = sum(
                ((emp_freqs[i] - expected_freqs[i]) ** 2) / expected_freqs[i] if expected_freqs[i] > 0 else 0 for i in
                range(5))

            df = len(probs) - 1
            chi_critical = stats.chi2.ppf(0.95, df)
            is_valid = chi_squared < chi_critical

            self.ax1.clear()
            self.style_axis(self.ax1)
            bars = self.ax1.bar(values, emp_freqs / n, color='#5c9ebf', edgecolor='#82c0df')
            self.ax1.set_xticks(values)
            self.ax1.set_title("Относительные частоты дискретной СВ")

            for bar in bars:
                yval = bar.get_height()
                self.ax1.text(bar.get_x() + bar.get_width() / 2, yval + 0.01, round(yval, 3), ha='center', va='bottom',
                              fontsize=9, color=fg_color)

            self.fig1.tight_layout()
            self.canvas1.draw()

            res_text = (f"Average: {emp_mean:.3f} (error = {error_mean:.2f}%)\n"
                        f"Variance: {emp_var:.3f} (error = {error_var:.2f}%)\n"
                        f"Chi-squared: {chi_squared:.2f} < {chi_critical:.3f} is ")
            self.lbl_stats1.config(text=res_text)
            self.lbl_bool1.config(text="true", fg="#5cae56") if is_valid else self.lbl_bool1.config(text="false",
                                                                                                    fg="#e06c75")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    # нормальная св
    def init_tab2(self):
        left_frame = ttk.Frame(self.tab2, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        right_frame = ttk.Frame(self.tab2, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(left_frame, text="Mean (мат. ожидание):").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.mean_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.mean_var, width=15).grid(row=0, column=1, pady=8)

        ttk.Label(left_frame, text="Variance (дисперсия):").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.var_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.var_var, width=15).grid(row=1, column=1, pady=8)

        ttk.Label(left_frame, text="Sample size (N):").grid(row=2, column=0, sticky=tk.W, pady=25)
        self.n_var_tab2 = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.n_var_tab2, width=15).grid(row=2, column=1, pady=25)

        ttk.Button(left_frame, text="Start", command=self.run_normal).grid(row=3, column=0, columnspan=2, pady=10,
                                                                           ipadx=30, ipady=5)

        self.fig2 = Figure(figsize=(5, 4), dpi=100)
        self.fig2.patch.set_facecolor(plot_bg)
        self.ax2 = self.fig2.add_subplot(111)
        self.style_axis(self.ax2)

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=right_frame)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        res_frame = ttk.Frame(right_frame)
        res_frame.pack(fill=tk.X, pady=10)

        self.lbl_stats2 = tk.Label(res_frame, text="Введите данные и нажмите Start\n", font=("Arial", 11), bg=bg_color,
                                   fg=fg_color, justify=tk.LEFT)
        self.lbl_stats2.pack(anchor=tk.W)
        self.lbl_bool2 = tk.Label(res_frame, text="", font=("Arial", 11, "bold"), bg=bg_color)
        self.lbl_bool2.pack(anchor=tk.W)

    def run_normal(self):
        try:
            theor_mean = float(self.mean_var.get())
            theor_var = float(self.var_var.get())
            n = int(self.n_var_tab2.get())

            if theor_var <= 0: raise ValueError("Дисперсия должна быть больше 0.")
            if n <= 0: raise ValueError("Объем выборки должен быть > 0.")

            std_dev = np.sqrt(theor_var)

            # генерация алгоритмом бокса мюллера
            sample = []
            # делим на 2 тк алгоритм делает сразу два числа за проход
            for _ in range((n + 1) // 2):
                u1, u2 = random.random(), random.random()

                # формулы бокса мюллера
                z0 = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
                z1 = np.sqrt(-2 * np.log(u1)) * np.sin(2 * np.pi * u2)

                # приводим стандартное распределение (m = 0 v = 1) к нашему умножая на ско и прибавляя среднее
                sample.append(z0 * std_dev + theor_mean)
                if len(sample) < n:  # если нечетное число N
                    sample.append(z1 * std_dev + theor_mean)

            sample = np.array(sample)

            # считаем выборочные среднее и дисперсию
            emp_mean = np.mean(sample)
            emp_var = np.var(sample)

            error_mean = abs(emp_mean - theor_mean) / abs(theor_mean) * 100 if theor_mean != 0 else abs(emp_mean) * 100
            error_var = abs(emp_var - theor_var) / theor_var * 100

            self.ax2.clear()
            self.style_axis(self.ax2)

            # плотность гистограммы
            counts, bins, patches = self.ax2.hist(sample, bins='auto', density=True, color='#6272a4',
                                                  edgecolor='#b0bfe6', alpha=0.9)

            # идеальная кривая
            x_axis = np.linspace(min(sample), max(sample), 100)
            y_axis = stats.norm.pdf(x_axis, theor_mean, std_dev)
            self.ax2.plot(x_axis, y_axis, color='#50fa7b', linewidth=2.5)
            self.ax2.set_title("Гистограмма и плотность норм. распределения")

            self.fig2.tight_layout()
            self.canvas2.draw()

            # хи2 для нормального
            obs_counts, _ = np.histogram(sample, bins=bins)
            expected_counts = []
            # считаем теоретические вероятности попадания в интервалы через функцию распределения
            for i in range(len(bins) - 1):
                p_interval = stats.norm.cdf(bins[i + 1], theor_mean, std_dev) - stats.norm.cdf(bins[i], theor_mean,
                                                                                               std_dev)
                expected_counts.append(p_interval * n)

            expected_counts = np.array(expected_counts)
            chi_squared = np.sum(
                (obs_counts - expected_counts) ** 2 / np.where(expected_counts == 0, 1e-10, expected_counts))

            # степени свободы
            df = len(bins) - 1 - 3
            if df < 1: df = 1

            chi_critical = stats.chi2.ppf(0.95, df)
            is_valid = chi_squared < chi_critical

            res_text = (f"Average: {emp_mean:.3f} (error = {error_mean:.2f}%)\n"
                        f"Variance: {emp_var:.3f} (error = {error_var:.2f}%)\n"
                        f"Chi-squared: {chi_squared:.2f} < {chi_critical:.3f} is ")
            self.lbl_stats2.config(text=res_text)
            self.lbl_bool2.config(text="true", fg="#5cae56") if is_valid else self.lbl_bool2.config(text="false",
                                                                                                    fg="#e06c75")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


if __name__ == "__main__":
    app = SimulationApp()
    app.mainloop()