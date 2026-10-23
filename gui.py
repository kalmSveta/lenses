import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Импорт ваших функций
from read_recepy import *


class ConsoleRedirector:
    """Класс для перенаправления print() в текстовое поле Tkinter"""

    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        pass


def handle_universal_shortcuts(event):
    """
    Обработчик горячих клавиш по физическим кодам клавиш (keycode).
    Работает независимо от текущей раскладки (русской или английской).
    """
    if event.state & 4:
        if event.keycode == 86:  # Ctrl + V
            event.widget.event_generate("<<Paste>>")
            return "break"
        elif event.keycode == 67:  # Ctrl + C
            event.widget.event_generate("<<Copy>>")
            return "break"
        elif event.keycode == 88:  # Ctrl + X
            event.widget.event_generate("<<Cut>>")
            return "break"
        elif event.keycode == 65:  # Ctrl + A
            event.widget.event_generate("<<SelectAll>>")
            return "break"


def show_context_menu(event):
    """Отображение контекстного меню по правой кнопке мыши"""
    widget = event.widget
    context_menu = tk.Menu(root, tearoff=0)

    context_menu.add_command(label="Копировать",
                             command=lambda: widget.event_generate("<<Copy>>"))
    context_menu.add_command(label="Вставить",
                             command=lambda: widget.event_generate("<<Paste>>"))
    context_menu.add_command(label="Вырезать",
                             command=lambda: widget.event_generate("<<Cut>>"))
    context_menu.add_separator()
    context_menu.add_command(label="Выделить всё",
                             command=lambda: widget.event_generate(
                                 "<<SelectAll>>"))

    context_menu.tk_popup(event.x_root, event.y_root)


def add_standard_bindings(widget):
    """Привязка универсального обработчика клавиш и контекстного меню к виджету"""
    widget.bind("<Key>", handle_universal_shortcuts)
    widget.bind("<Button-3>", show_context_menu)


def validate_input_length(proposed_text):
    """Проверка длины текста в реальном времени (максимум 100 символов)"""
    if len(proposed_text) > 100:
        messagebox.showwarning("Ошибка ввода",
                               "Максимальная длина поля не может превышать 100 символов!")
        return False
    return True


def clear_entry(entry_widget):
    """Очистка поля ввода и возврат фокуса на него"""
    entry_widget.delete(0, tk.END)
    entry_widget.focus_set()


def select_input_folder():
    folder = filedialog.askdirectory(title="Выберите папку с входными файлами")
    if folder:
        normalized_path = os.path.normpath(folder)
        if len(normalized_path) > 100:
            messagebox.showerror("Ошибка",
                                 "Путь к выбранной папке превышает 100 символов!")
            return
        input_entry.delete(0, tk.END)
        input_entry.insert(0, normalized_path)


def select_output_folder():
    folder = filedialog.askdirectory(
        title="Выберите папку для сохранения результатов")
    if folder:
        normalized_path = os.path.normpath(folder)
        if len(normalized_path) > 100:
            messagebox.showerror("Ошибка",
                                 "Путь к выбранной папке превышает 100 символов!")
            return
        output_entry.delete(0, tk.END)
        output_entry.insert(0, normalized_path)


def start_processing():
    date_range = date_entry.get().strip()
    input_folder = input_entry.get().strip()
    output_folder = output_entry.get().strip()

    if not date_range or not input_folder or not output_folder:
        messagebox.showerror(
            "Ошибка", "Пожалуйста, заполните все поля и выберите папки!"
        )
        return

    # --- ПРОВЕРКА НАЛИЧИЯ ОБЯЗАТЕЛЬНЫХ ФАЙЛОВ ---
    required_files = [
        "РЕЦЕПТЫ.xlsx",
        "ТКЛ.xls",
        "МФКЛ.xls",
        "Справочник по контактным линзам.xlsx"
    ]

    missing_files = []
    for file_name in required_files:
        full_path = os.path.join(input_folder, file_name)
        if not os.path.exists(full_path):
            missing_files.append(file_name)

    if missing_files:
        error_msg = "В указанной входной папке не найдены следующие обязательные файлы:\n\n"
        for file in missing_files:
            error_msg += f"• {file}\n"
        error_msg += "\nПожалуйста, добавьте их в папку и повторите попытку."
        messagebox.showerror("Ошибка: Файлы не найдены", error_msg)
        return
    # ---------------------------------------------

    log_text.delete("1.0", tk.END)

    try:
        btn_start.config(state=tk.DISABLED)
        root.config(cursor="wait")
        root.update()

        # ПОЛУЧАЕМ ДАТЫ
        start_date, end_date = parse_date_range(date_range)

        # СНАЧАЛА ОБРАБОТАЕМ ТКЛ
        process_prescriptions(orders_file_path=input_folder,
                              prescription_file_path=input_folder,
                              handbook_file_path=input_folder,
                              lens_group='ТКЛ',
                              start_date=start_date,
                              end_date=end_date,
                              output_file_path=output_folder)

        # ПОТОМ ОБРАБОТАЕМ МФКЛ
        process_prescriptions(orders_file_path=input_folder,
                              prescription_file_path=input_folder,
                              handbook_file_path=input_folder,
                              lens_group='МФКЛ',
                              start_date=start_date,
                              end_date=end_date,
                              output_file_path=output_folder)

        messagebox.showinfo("Успех", "Обработка успешно завершена!")

    except Exception as e:
        print(f"\n[ОШИБКА] Произошел сбой: {str(e)}")
        messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")

    finally:
        btn_start.config(state=tk.NORMAL)
        root.config(cursor="")


# --- Создание главного окна ---
root = tk.Tk()
root.title("Отчетики")
root.geometry("620x510")

style = ttk.Style()
style.theme_use("vista")
style.configure("Clear.TButton", font=("Arial", 10, "bold"), width=2, padding=0)

vcmd = (root.register(validate_input_length), '%P')

main_frame = ttk.Frame(root, padding="15")
main_frame.pack(fill=tk.BOTH, expand=True)

# 1. Поле для ввода диапазона дат
ttk.Label(main_frame, text="Диапазон дат (ДД.ММ.ГГ-ДД.ММ.ГГ):").grid(
    row=0, column=0, sticky="w", pady=2
)
date_frame = ttk.Frame(main_frame)
date_frame.grid(row=1, column=0, columnspan=2, sticky="we", pady=5)

date_entry = ttk.Entry(date_frame, validate="key", validatecommand=vcmd)
date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
date_entry.insert(0, "01.01.26-31.12.26")
add_standard_bindings(date_entry)

btn_clear_date = ttk.Button(date_frame, text="×", style="Clear.TButton",
                            command=lambda: clear_entry(date_entry))
btn_clear_date.pack(side=tk.RIGHT, padx=(5, 0))

# 2. Поле выбора входной папки
ttk.Label(main_frame, text="Путь к папке с входными файлами:").grid(
    row=2, column=0, sticky="w", pady=2
)
input_frame = ttk.Frame(main_frame)
input_frame.grid(row=3, column=0, sticky="we", pady=5)

input_entry = ttk.Entry(input_frame, validate="key", validatecommand=vcmd)
input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
add_standard_bindings(input_entry)

btn_clear_input = ttk.Button(input_frame, text="×", style="Clear.TButton",
                             command=lambda: clear_entry(input_entry))
btn_clear_input.pack(side=tk.RIGHT, padx=(5, 0))

btn_input = ttk.Button(main_frame, text="Обзор...", command=select_input_folder)
btn_input.grid(row=3, column=1, padx=(10, 5), pady=5)

# 3. Поле выбора выходной папки
ttk.Label(main_frame, text="Путь к папке для сохранения:").grid(
    row=4, column=0, sticky="w", pady=2
)
output_frame = ttk.Frame(main_frame)
output_frame.grid(row=5, column=0, sticky="we", pady=5)

output_entry = ttk.Entry(output_frame, validate="key", validatecommand=vcmd)
output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
add_standard_bindings(output_entry)

btn_clear_output = ttk.Button(output_frame, text="×", style="Clear.TButton",
                              command=lambda: clear_entry(output_entry))
btn_clear_output.pack(side=tk.RIGHT, padx=(5, 0))

btn_output = ttk.Button(main_frame, text="Обзор...",
                        command=select_output_folder)
btn_output.grid(row=5, column=1, padx=(10, 5), pady=5)

# 4. Кнопка Запуска
btn_start = ttk.Button(main_frame, text="ЗАПУСТИТЬ", command=start_processing)
btn_start.grid(row=6, column=0, columnspan=2, pady=10, ipady=3)

# 5. СЕКЦИЯ ЛОГОВ
ttk.Label(main_frame, text="Ход выполнения программы:").grid(
    row=7, column=0, sticky="w", pady=5
)

log_frame = ttk.Frame(main_frame)
log_frame.grid(row=8, column=0, columnspan=2, sticky="nsew", pady=5)

log_text = tk.Text(
    log_frame,
    height=10,
    width=65,
    bg="#f0f0f0",
    fg="#333333",
    font=("Consolas", 10),
)
scrollbar = ttk.Scrollbar(log_frame, command=log_text.yview)
log_text.configure(yscrollcommand=scrollbar.set)

log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
add_standard_bindings(log_text)

main_frame.columnconfigure(0, weight=1)
main_frame.rowconfigure(8, weight=1)

sys.stdout = ConsoleRedirector(log_text)
sys.stderr = ConsoleRedirector(log_text)

root.mainloop()
