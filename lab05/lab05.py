import time
import tkinter as tk
from tkinter import ttk, messagebox

class LCG:
    def __init__(self, seed=1):
        self.m, self.a, self.c = 2 ** 64, 6364136223846793005, 1442695040888963407
        self.state = seed

    def get_value(self):
        self.state = (self.a * self.state + self.c) % self.m
        return self.state / self.m

# настройки шара
PROBS_8BALL = [0.15, 0.10, 0.25, 0.10, 0.10, 0.15, 0.05, 0.10]
ANSWERS_8BALL = ["Бесспорно", "Определённо да", "Возможно", "Шансы 50 на 50",
                 "Спроси позже", "Сомнительно", "Маловероятно", "Точно нет"]

def validate_probabilities():
    if len(PROBS_8BALL) != 8 or round(sum(PROBS_8BALL), 5) != 1.0:
        raise ValueError("Ошибка: Шар должен содержать ровно 8 вероятностей с суммой 1.0!")

def roll_dice(probs, rng):
    r = rng.get_value()
    for i, p in enumerate(probs):
        r -= p
        if r <= 0: return i
    return len(probs) - 1

class RandomEventsApp:
    def __init__(self, root):
        self.root, self.rng = root, LCG(int(time.time()))
        root.title("Моделирование событий")
        root.geometry("500x350")

        nb = ttk.Notebook(root)
        nb.pack(fill='both', expand=True, padx=10, pady=10)

        # да / нет
        t1 = ttk.Frame(nb, padding=20)
        nb.add(t1, text="Скажи 'Да' или 'Нет'")

        ttk.Label(t1, text="Введите вопрос:").pack()
        self.q1 = ttk.Entry(t1, width=40)
        self.q1.pack(pady=(0, 10))

        ttk.Label(t1, text="Вероятность 'ДА' (0.0 - 1.0):").pack()
        self.prob_yes_entry = ttk.Entry(t1, width=10)
        self.prob_yes_entry.insert(0, "0.5")
        self.prob_yes_entry.pack(pady=(0, 10))

        self.res1 = ttk.Label(t1, text="?", font=("Arial", 35, "bold"), foreground="blue")
        self.res1.pack(pady=10)

        ttk.Button(t1, text="Ответить", command=self.generate_yn).pack(pady=5)

        #  вкладка
        t2 = ttk.Frame(nb, padding=20)
        nb.add(t2, text="Шар (8 ответов)")

        ttk.Label(t2, text="Введите вопрос шару:").pack()
        self.q2 = ttk.Entry(t2, width=40)
        self.q2.pack(pady=(0, 10))

        self.res2 = ttk.Label(t2, text="Потряси шар", font=("Arial", 20, "bold"), foreground="purple")
        self.res2.pack(pady=20)

        ttk.Button(t2, text="Потрясти", command=self.generate_8ball).pack(pady=5)

    def generate_yn(self):
        if not self.q1.get().strip(): return messagebox.showwarning("Внимание", "Введите вопрос!")
        try:
            p_yes = float(self.prob_yes_entry.get().replace(',', '.'))
            if not (0.0 <= p_yes <= 1.0): raise ValueError
        except ValueError:
            return messagebox.showerror("Ошибка", "Число от 0.0 до 1.0!")

        ans = ["ДА", "НЕТ"][roll_dice([p_yes, 1.0 - p_yes], self.rng)]
        self.res1.config(text=ans, foreground="green" if ans == "ДА" else "red")

    def generate_8ball(self):
        if not self.q2.get().strip(): return messagebox.showwarning("Внимание", "Введите вопрос!")
        self.res2.config(text=ANSWERS_8BALL[roll_dice(PROBS_8BALL, self.rng)])

if __name__ == "__main__":
    try:
        validate_probabilities()
        root = tk.Tk()
        RandomEventsApp(root)
        root.mainloop()
    except Exception as e:
        tk.Tk().withdraw()
        messagebox.showerror("Ошибка настройки", str(e))