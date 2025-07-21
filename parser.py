import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import os
from tkinter import font as tkfont
import pyperclip
import re


class GCodeParserTk:
    def __init__(self, root):
        self.root = root
        self.root.title("G-code to Rapid Converter")
        self.root.geometry("800x725")
        self.root.minsize(600, 700)

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
            width=60,
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

        # Поля ввода
        self.create_labeled_entry(self.left_column, "Название процедуры:", "main", 0)
        self.create_labeled_entry(self.left_column, "Точка отсчёта:", "defaultPoint", 1)
        self.create_labeled_entry(self.left_column, "I/O сигнал:", "Spindle", 2)
        self.create_labeled_entry(self.right_column, "Инструмент:", "tool0", 0)
        self.create_labeled_entry(self.right_column, "Система координат:", "wobj0", 1)

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

        # Панель результатов с кнопкой копирования
        self.result_frame = ttk.LabelFrame(self.main_frame, padding=10)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок панели результатов с кнопкой копирования
        self.result_header = ttk.Frame(self.result_frame)
        self.result_header.pack(fill=tk.X)

        ttk.Label(
            self.result_header,
            text="Результат преобразования",
            font=('Helvetica', 10)
        ).pack(side=tk.LEFT)

        self.copy_btn = ttk.Button(
            self.result_header,
            text="📋 Копировать",
            command=self.copy_to_clipboard,
            width=10
        )
        self.copy_btn.pack(side=tk.RIGHT, padx=5)

        self.result_edit = scrolledtext.ScrolledText(
            self.result_frame,
            width=60,
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
        self.last_point = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.prev_circle_point = None

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabel', background='#f5f5f5')
        style.configure('TButton', padding=6, relief='flat', bordercolor='#ccc', borderwidth=1)
        style.map('TButton',
                  background=[('active', '#e6e6e6')],
                  bordercolor=[('active', '#adadad')])

        style.configure('TLabelframe', background='#f5f5f5', bordercolor='#ccc', borderwidth=1)
        style.configure('TLabelframe.Label', background='#f5f5f5')
        style.configure('TEntry', fieldbackground='white', bordercolor='#ccc', borderwidth=1, padding=5)

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=10)

    def create_labeled_entry(self, parent, label_text, default_value, pady_top):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(pady_top * 10, 0))

        label = ttk.Label(frame, text=label_text, width=20, anchor=tk.W)
        label.pack(side=tk.LEFT)

        entry = ttk.Entry(frame, width=15)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        entry.insert(0, default_value)

        if label_text == "Название процедуры:":
            self.proc_entry = entry
        elif label_text == "Точка отсчёта:":
            self.ref_entry = entry
        elif label_text == "I/O сигнал:":
            self.io_signal_entry = entry
        elif label_text == "Инструмент:":
            self.tool_entry = entry
        elif label_text == "Система координат:":
            self.wobj_entry = entry

    def copy_to_clipboard(self):
        """Копирует содержимое поля результата в буфер обмена"""
        content = self.result_edit.get("1.0", tk.END)
        if content.strip():
            pyperclip.copy(content)
            self.status_bar.config(text="Текст скопирован в буфер обмена")
        else:
            self.status_bar.config(text="Нет данных для копирования")

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
        io_signal = self.io_signal_entry.get()
        tool = self.tool_entry.get()
        wobj = self.wobj_entry.get()

        try:
            rapid_code = self.convert_to_rapid(gcode, proc_name, ref_point, io_signal, tool, wobj)
            self.result_edit.config(state='normal')
            self.result_edit.delete(1.0, tk.END)
            self.result_edit.insert(tk.END, rapid_code)
            self.result_edit.config(state='disabled')

            self.save_rapid_file(rapid_code, proc_name)
            self.status_bar.config(text="Конвертация успешно завершена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка конвертации:\n{str(e)}")
            self.status_bar.config(text="Ошибка конвертации")

    def parse_gcode_line(self, line):
        """Разбирает строку G-кода, разделяя команды даже без пробелов"""
        # Удаляем номер строки (если есть)
        if line[0] == 'N' and line[1].isdigit():
            line = line.split(' ', 1)[-1].strip()

        # Используем регулярное выражение для разделения команд
        pattern = r'([A-Z][-+]?\d*\.?\d*)'
        parts = re.findall(pattern, line)

        # Разделяем комбинированные команды (например "G1X10" -> "G1", "X10")
        commands = []
        for part in parts:
            # Ищем букву и следующие за ней цифры/знаки
            match = re.match(r'([A-Z])([-+]?\d*\.?\d*)', part)
            if match:
                cmd = match.group(1)
                value = match.group(2)
                commands.append(f"{cmd}{value}" if value else cmd)

        return commands

    def convert_to_rapid(self, gcode, proc_name, ref_point, io_signal, tool, wobj):
        lines = gcode.split('\n')
        rapid_commands = []
        self.last_point = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.last_rapid_command = ""
        self.prev_circle_point = None
        wobj_str = f",{wobj}" if wobj != "wobj0" else ""

        rapid_commands.append(f"GLOBAL PROC {proc_name}()")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Разбираем строку на отдельные команды
            commands = self.parse_gcode_line(line)

            # Обработка M05 (выключение)
            if "M05" in commands or "M5" in commands:
                rapid_commands.append(f"  SetDO {io_signal}, false")
                i += 1
                continue

            # Обработка M03 (включение)
            if "M03" in commands or "M3" in commands:
                rapid_commands.append(f"  SetDO {io_signal}, true")
                i += 1
                continue

            # Пропускаем другие M-коды
            if any(cmd in commands for cmd in ['G90', 'G71', 'M02', 'M30', 'G17']):
                i += 1
                continue

            # Обрабатываем команды перемещения
            move_cmd = None
            params = {}

            for cmd in commands:
                if cmd.startswith(('G00', 'G01', 'G0', 'G1', 'G02', 'G03', 'G2', 'G3')):
                    move_cmd = cmd
                elif cmd[0] in ['X', 'Y', 'Z', 'I', 'J']:
                    try:
                        params[cmd[0]] = float(cmd[1:])
                    except ValueError:
                        pass

            if not move_cmd and any(c in params for c in ['X', 'Y', 'Z']):
                # Если нет явной G-команды, но есть координаты - предполагаем G1
                move_cmd = 'G1'

            if move_cmd:
                # Обновляем текущую позицию
                for axis in ['X', 'Y', 'Z']:
                    if axis in params:
                        self.last_point[axis] = params[axis]

                # Преобразуем координаты
                x = self.last_point['X']
                y = self.last_point['Y']
                z = -self.last_point['Z']  # Инверсия Z

                def format_coord(coord):
                    s = f"{coord:.4f}".rstrip('0').rstrip('.') if '.' in f"{coord:.4f}" else f"{coord}"
                    return s

                x_str = format_coord(x)
                y_str = format_coord(y)
                z_str = format_coord(z)

                # Обработка круговой интерполяции (G02/G03)
                if move_cmd.startswith(('G02', 'G03', 'G2', 'G3')):
                    if self.prev_circle_point is None:
                        # Сохраняем первую точку дуги
                        self.prev_circle_point = {
                            'X': x_str,
                            'Y': y_str,
                            'Z': z_str
                        }
                        i += 1
                    else:
                        # Формируем команду MoveC из двух точек
                        start_point = f"Offs({ref_point},{self.prev_circle_point['X']},{self.prev_circle_point['Y']},{self.prev_circle_point['Z']})"
                        end_point = f"Offs({ref_point},{x_str},{y_str},{z_str})"

                        current_cmd = f"  MoveC {start_point},{end_point},v200,fine,{tool}{wobj_str}"
                        rapid_commands.append(current_cmd)
                        self.prev_circle_point = None
                        i += 1
                else:
                    # Линейное перемещение
                    current_cmd = f"  MoveL Offs({ref_point},{x_str},{y_str},{z_str}),v1000,fine,{tool}{wobj_str}"

                    if current_cmd != self.last_rapid_command:
                        rapid_commands.append(current_cmd)
                        self.last_rapid_command = current_cmd
                    i += 1
            else:
                i += 1

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
        self.io_signal_entry.delete(0, tk.END)
        self.io_signal_entry.insert(0, "Spindle")
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
        self.last_point = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.prev_circle_point = None
        self.status_bar.config(text="Готов к работе")


if __name__ == '__main__':
    root = tk.Tk()
    app = GCodeParserTk(root)
    root.mainloop()