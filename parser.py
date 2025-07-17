import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import os
from tkinter import font as tkfont


class GCodeParserTk:
    def __init__(self, root):
        self.root = root
        self.root.title("G-code to Rapid Converter")
        self.root.geometry("800x700")
        self.root.minsize(800, 700)

        # Настройка стилей
        self.setup_styles()

        # Основной контейнер
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        self.header = ttk.Label(
            self.main_frame,
            text="Конвертер G-code в Rapid",
            font=('Helvetica', 14, 'bold')
        )
        self.header.pack(pady=(0, 15))

        # Панель с G-code
        self.gcode_frame = ttk.LabelFrame(self.main_frame, text=" Исходный G-code ", padding=10)
        self.gcode_frame.pack(fill=tk.BOTH, expand=True)

        self.gcode_edit = scrolledtext.ScrolledText(
            self.gcode_frame,
            width=100,
            height=15,
            font=('Consolas', 10),
            padx=5,
            pady=5,
            wrap=tk.NONE
        )
        self.gcode_edit.pack(fill=tk.BOTH, expand=True)
        self.gcode_edit.insert(tk.END, "Вставьте G-code здесь или загрузите файл...")

        # Панель настроек
        self.settings_frame = ttk.Frame(self.main_frame)
        self.settings_frame.pack(fill=tk.X, pady=10)

        # Левая колонка настроек
        self.left_column = ttk.Frame(self.settings_frame)
        self.left_column.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        # Правая колонка настроек
        self.right_column = ttk.Frame(self.settings_frame)
        self.right_column.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        # Поля ввода (уменьшенная ширина)
        self.create_labeled_entry(self.left_column, "Название процедуры:", "main", 0, width=20)
        self.create_labeled_entry(self.left_column, "Точка отсчёта:", "defaultPoint", 1, width=20)
        self.create_labeled_entry(self.right_column, "Инструмент:", "tool0", 0, width=20)
        self.create_labeled_entry(self.right_column, "Система координат:", "wobj0", 1, width=20)

        # Панель кнопок
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=5)

        self.load_btn = ttk.Button(
            self.button_frame,
            text="Загрузить файл",
            command=self.load_file
        )
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.parse_btn = ttk.Button(
            self.button_frame,
            text="Конвертировать",
            command=self.parse_gcode
        )
        self.parse_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(
            self.button_frame,
            text="Очистить",
            command=self.clear_all
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Панель результатов
        self.result_frame = ttk.LabelFrame(self.main_frame, text=" Результат преобразования ", padding=10)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        self.result_edit = scrolledtext.ScrolledText(
            self.result_frame,
            width=100,
            height=15,
            font=('Consolas', 10),
            padx=5,
            pady=5,
            wrap=tk.NONE,
            state='disabled'
        )
        self.result_edit.pack(fill=tk.BOTH, expand=True)
        self.result_edit.insert(tk.END, "Здесь будет отображен Rapid код...")

        # Статус бар
        self.status_bar = ttk.Label(
            self.main_frame,
            text="Готов к работе",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        self.status_bar.pack(fill=tk.X, pady=(5, 0))

        # Переменные состояния
        self.source_file_path = ""
        self.last_rapid_command = ""

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Настройка скруглённых углов
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabel', background='#f5f5f5')
        style.configure('TButton', padding=6, relief='flat', bordercolor='#ccc', borderwidth=1)
        style.map('TButton',
                  background=[('active', '#e6e6e6')],
                  bordercolor=[('active', '#adadad')])

        # Скруглённые углы для LabelFrame
        style.configure('TLabelframe', background='#f5f5f5', bordercolor='#ccc', borderwidth=1)
        style.configure('TLabelframe.Label', background='#f5f5f5')

        # Стиль для Entry
        style.configure('TEntry', fieldbackground='white', bordercolor='#ccc', borderwidth=1, padding=5)

        # Шрифты
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=10)

    def create_labeled_entry(self, parent, label_text, default_value, pady_top, width=20):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(pady_top * 10, 0))

        label = ttk.Label(frame, text=label_text, width=width, anchor=tk.W)
        label.pack(side=tk.LEFT)

        entry = ttk.Entry(frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        entry.insert(0, default_value)

        # Сохраняем ссылки на важные поля
        if label_text == "Название процедуры:":
            self.proc_entry = entry
        elif label_text == "Точка отсчёта:":
            self.ref_entry = entry
        elif label_text == "Инструмент:":
            self.tool_entry = entry
        elif label_text == "Система координат:":
            self.wobj_entry = entry

    def load_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("G-code Files", "*.nc *.gcode *.txt"), ("All Files", "*.*")],
            title="Выберите файл G-code"
        )
        if filename:
            try:
                self.source_file_path = filename
                with open(filename, 'r') as file:
                    self.gcode_edit.delete(1.0, tk.END)
                    self.gcode_edit.insert(tk.END, file.read())
                self.status_bar.config(text=f"Загружен файл: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
                self.status_bar.config(text="Ошибка загрузки файла")

    def parse_gcode(self):
        gcode = self.gcode_edit.get(1.0, tk.END)
        if not gcode.strip():
            messagebox.showwarning("Предупреждение", "Поле G-code пусто!")
            return

        proc_name = self.proc_entry.get()
        ref_point = self.ref_entry.get()
        tool = self.tool_entry.get()
        wobj = self.wobj_entry.get()

        try:
            rapid_code = self.convert_to_rapid(gcode, proc_name, ref_point, tool, wobj)
            self.result_edit.config(state='normal')
            self.result_edit.delete(1.0, tk.END)
            self.result_edit.insert(tk.END, rapid_code)
            self.result_edit.config(state='disabled')

            self.save_rapid_file(rapid_code, proc_name)
            self.status_bar.config(text="Конвертация успешно завершена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка конвертации:\n{str(e)}")
            self.status_bar.config(text="Ошибка конвертации")

    def convert_to_rapid(self, gcode, proc_name, ref_point, tool, wobj):
        lines = gcode.split('\n')
        rapid_commands = []
        last_coords = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.last_rapid_command = ""

        wobj_str = f",{wobj}" if wobj != "wobj0" else ""

        rapid_commands.append(f"GLOBAL PROC {proc_name}()")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line[0] == 'N' and line[1].isdigit():
                line = line.split(' ', 1)[-1].strip()

            if line.startswith(('G90', 'G71', 'M05', 'M03', 'M02', 'M30')):
                continue

            if line.startswith(('G00', 'G01', 'G0 ', 'G1 ', 'G02', 'G03', 'G2 ', 'G3 ')) or \
                    any(c in line for c in ['X', 'Y', 'Z']):

                parts = line.split()

                for part in parts:
                    if part.startswith('X'):
                        last_coords['X'] = float(part[1:])
                    elif part.startswith('Y'):
                        last_coords['Y'] = float(part[1:])
                    elif part.startswith('Z'):
                        last_coords['Z'] = float(part[1:])

                x = last_coords['X'] / 10
                y = last_coords['Y'] / 10
                z = -last_coords['Z'] / 10

                def format_coord(coord):
                    s = f"{coord:.4f}".rstrip('0').rstrip('.') if '.' in f"{coord:.4f}" else f"{coord}"
                    return s

                x_str = format_coord(x)
                y_str = format_coord(y)
                z_str = format_coord(z)

                current_cmd = f"  MoveL Offs({ref_point},{x_str},{y_str},{z_str}),v1000,fine,{tool}{wobj_str}"

                if current_cmd != self.last_rapid_command:
                    rapid_commands.append(current_cmd)
                    self.last_rapid_command = current_cmd

        rapid_commands.append("ENDPROC")
        rapid_commands.append("")

        return '\n'.join(rapid_commands)

    def save_rapid_file(self, rapid_code, proc_name):
        if not self.source_file_path:
            save_path = os.path.join(os.getcwd(), f"{proc_name}.txt")
        else:
            dirname = os.path.dirname(self.source_file_path)
            save_path = os.path.join(dirname, f"{proc_name}.txt")

        try:
            with open(save_path, 'w') as file:
                file.write(rapid_code)
            messagebox.showinfo("Успех", f"Файл успешно сохранен:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def clear_all(self):
        self.gcode_edit.delete(1.0, tk.END)
        self.proc_entry.delete(0, tk.END)
        self.proc_entry.insert(0, "main")
        self.ref_entry.delete(0, tk.END)
        self.ref_entry.insert(0, "defaultPoint")
        self.tool_entry.delete(0, tk.END)
        self.tool_entry.insert(0, "tool0")
        self.wobj_entry.delete(0, tk.END)
        self.wobj_entry.insert(0, "wobj0")
        self.result_edit.config(state='normal')
        self.result_edit.delete(1.0, tk.END)
        self.result_edit.insert(tk.END, "Здесь будет отображен Rapid код...")
        self.result_edit.config(state='disabled')
        self.source_file_path = ""
        self.last_rapid_command = ""
        self.status_bar.config(text="Готов к работе")


if __name__ == '__main__':
    root = tk.Tk()
    app = GCodeParserTk(root)
    root.mainloop()