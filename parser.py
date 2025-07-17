import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import os


class GCodeParserTk:
    def __init__(self, root):
        self.root = root
        self.root.title("G-code to Rapid Converter")
        self.root.geometry("900x800")

        # Основные виджеты
        self.gcode_label = tk.Label(root, text="Исходный G-code:")
        self.gcode_label.pack()

        self.gcode_edit = scrolledtext.ScrolledText(root, width=110, height=15)
        self.gcode_edit.pack()
        self.gcode_edit.insert(tk.END, "Вставьте G-code здесь или загрузите файл...")

        # Поля настроек
        self.settings_frame = tk.Frame(root)
        self.settings_frame.pack(pady=5, fill=tk.X)

        # Левая колонка
        self.left_column = tk.Frame(self.settings_frame)
        self.left_column.pack(side=tk.LEFT, padx=10)

        # Правая колонка
        self.right_column = tk.Frame(self.settings_frame)
        self.right_column.pack(side=tk.LEFT, padx=10)

        # Название процедуры
        self.proc_label = tk.Label(self.left_column, text="Название процедуры:")
        self.proc_label.pack(anchor='w')

        self.proc_entry = ttk.Entry(self.left_column)
        self.proc_entry.pack(fill=tk.X)
        self.proc_entry.insert(0, "main")

        # Точка отсчёта
        self.ref_label = tk.Label(self.left_column, text="Точка отсчёта:")
        self.ref_label.pack(anchor='w', pady=(5, 0))

        self.ref_entry = ttk.Entry(self.left_column)
        self.ref_entry.pack(fill=tk.X)
        self.ref_entry.insert(0, "defaultPoint")

        # Инструмент
        self.tool_label = tk.Label(self.right_column, text="Инструмент (Tool):")
        self.tool_label.pack(anchor='w')

        self.tool_entry = ttk.Entry(self.right_column)
        self.tool_entry.pack(fill=tk.X)
        self.tool_entry.insert(0, "tool0")

        # Система координат
        self.wobj_label = tk.Label(self.right_column, text="Система координат (Wobj):")
        self.wobj_label.pack(anchor='w', pady=(5, 0))

        self.wobj_entry = ttk.Entry(self.right_column)
        self.wobj_entry.pack(fill=tk.X)
        self.wobj_entry.insert(0, "wobj0")

        # Кнопки
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=5)

        self.load_btn = ttk.Button(self.button_frame, text="Загрузить файл", command=self.load_file)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.parse_btn = ttk.Button(self.button_frame, text="Конвертировать в Rapid", command=self.parse_gcode)
        self.parse_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(self.button_frame, text="Очистить", command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Результат
        self.result_label = tk.Label(root, text="Результат преобразования:")
        self.result_label.pack()

        self.result_edit = scrolledtext.ScrolledText(root, width=110, height=20, state='normal')
        self.result_edit.pack()
        self.result_edit.insert(tk.END, "Здесь будет отображен Rapid код...")
        self.result_edit.config(state='disabled')

        # Переменные для хранения состояния
        self.source_file_path = ""
        self.last_rapid_command = ""

    def load_file(self):
        filename = filedialog.askopenfilename(filetypes=[("G-code Files", "*.nc *.gcode *.txt"), ("All Files", "*.*")])
        if filename:
            try:
                self.source_file_path = filename
                with open(filename, 'r') as file:
                    self.gcode_edit.delete(1.0, tk.END)
                    self.gcode_edit.insert(tk.END, file.read())
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")

    def parse_gcode(self):
        gcode = self.gcode_edit.get(1.0, tk.END)
        if not gcode.strip():
            messagebox.showwarning("Предупреждение", "Поле G-code пусто!")
            return

        proc_name = self.proc_entry.get()
        ref_point = self.ref_entry.get()
        tool = self.tool_entry.get()
        wobj = self.wobj_entry.get()

        rapid_code = self.convert_to_rapid(gcode, proc_name, ref_point, tool, wobj)
        self.result_edit.config(state='normal')
        self.result_edit.delete(1.0, tk.END)
        self.result_edit.insert(tk.END, rapid_code)
        self.result_edit.config(state='disabled')

        # Сохраняем файл
        self.save_rapid_file(rapid_code, proc_name)

    def convert_to_rapid(self, gcode, proc_name, ref_point, tool, wobj):
        lines = gcode.split('\n')
        rapid_commands = []
        last_coords = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.last_rapid_command = ""

        # Формируем строку wobj для команд
        wobj_str = f",{wobj}" if wobj != "wobj0" else ""

        # Добавляем заголовок процедуры
        rapid_commands.append(f"GLOBAL PROC {proc_name}()")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Удаляем номер строки (если есть)
            if line[0] == 'N' and line[1].isdigit():
                line = line.split(' ', 1)[-1].strip()

            # Пропускаем команды, не связанные с перемещением
            if line.startswith(('G90', 'G71', 'M05', 'M03', 'M02', 'M30')):
                continue

            # Обрабатываем команды перемещения
            if line.startswith(('G00', 'G01', 'G0 ', 'G1 ', 'G02', 'G03', 'G2 ', 'G3 ')) or \
                    any(c in line for c in ['X', 'Y', 'Z']):

                parts = line.split()

                # Обновляем только указанные координаты
                for part in parts:
                    if part.startswith('X'):
                        last_coords['X'] = float(part[1:])
                    elif part.startswith('Y'):
                        last_coords['Y'] = float(part[1:])
                    elif part.startswith('Z'):
                        last_coords['Z'] = float(part[1:])

                # Преобразуем координаты (делим на 10 для перевода мм → см, инвертируем Z)
                x = last_coords['X'] / 10
                y = last_coords['Y'] / 10
                z = -last_coords['Z'] / 10  # Инверсия Z

                # Функция для точного форматирования координат
                def format_coord(coord):
                    # Преобразуем в строку и удаляем лишние нули
                    s = f"{coord:.4f}".rstrip('0').rstrip('.') if '.' in f"{coord:.4f}" else f"{coord}"
                    return s

                x_str = format_coord(x)
                y_str = format_coord(y)
                z_str = format_coord(z)

                # Формируем команду MoveL
                current_cmd = f"  MoveL Offs({ref_point},{x_str},{y_str},{z_str}),v1000,fine,{tool}{wobj_str}"

                # Пропускаем дубликаты команд
                if current_cmd != self.last_rapid_command:
                    rapid_commands.append(current_cmd)
                    self.last_rapid_command = current_cmd

        # Добавляем завершение процедуры
        rapid_commands.append("ENDPROC")
        rapid_commands.append("")

        return '\n'.join(rapid_commands)

    def save_rapid_file(self, rapid_code, proc_name):
        if not self.source_file_path:
            # Если файл не был загружен, сохраняем в текущую директорию
            save_path = os.path.join(os.getcwd(), f"{proc_name}.txt")
        else:
            # Формируем путь для сохранения
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


if __name__ == '__main__':
    root = tk.Tk()
    app = GCodeParserTk(root)
    root.mainloop()