import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import threading
import time
from datetime import datetime
import os

class NewellBrandsVoice:
    def __init__(self, master):
        self.master = master
        self.master.title("Call Monitoring - Newell Brands")
        self.master.geometry("1100x600")
        self.master.configure(bg="#F6F0FF")

        # Configuración para Render
        self.render_mode = os.environ.get('RENDER', 'False').lower() == 'true'
        if self.render_mode:
            self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # URL y parámetros de la API
        self.url = "https://reports.intouchcx.com/reports/lib/getRealtimeManagementFull.asp"
        self.payload = {
            'split': '3900,3901,3902,3903,3904,3905,3906,3907,3908,3909,3910,3911,3912,3913,3914,3915,3916,3917,3918,3919,3920,3921,3922,3923,3924,3925,3926,3927,3928,3929,3930,3931,3932,3933,3934,3935,3936,3937,3938,3939,3940,3941,3942,3943,3944,3945,3946,3947,3948,3949,3950,3951,3952,3953,3954,3955,3956,3957,3958,3959,3960,3961,3962,3963,3964,3965,3966,3967,3968,3969,3970,3971,3972,3973',
            'firstSortCol': 'FullName',
            'firstSortDir': 'ASC',
            'secondSortCol': 'FullName',
            'secondSortDir': 'ASC',
            'reason': 'all',
            'state': 'all',
            'timezone': '1',
            'altSL': '',
            'threshold': '180',
            'altSLThreshold': '0',
            'acdAlert': '',
            'acwAlert': '',
            'holdAlert': '',
            'slAlert': '',
            'asaAlert': ''
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/html, */*; q=0.01",
            "Referer": "https://reports.intouchcx.com/reports/custom/newellbrands/realtimemanagementfull.asp?threshold=180&tzoffset=est",
            "Origin": "https://reports.intouchcx.com"
        }

        # Tiempos predeterminados para las alertas
        self.alert_times = {
            "Long Call": 360,
            "Extended Lunch": 3600,
            "Long ACW": 120,
            "Extended Break": 900,
            "IT Issue": 30,
            "Long Hold": 120
        }

        # Variable global para manejar la actualización
        self.update_task = None
        self.running = True  # Flag para controlar las actualizaciones

        self.alert_list = []  # Lista para manejar las alertas
        self.aux_list = []    # Lista para manejar los AUX
        self.queue_list = []  # Lista para manejar las llamadas en cola
        self.total_calls_in_queue = 0  # Total de llamadas en cola

        # Lista de todas las skills disponibles
        self.all_skills = {
            '3900': 'Newell Brands EN (3900)',
            '3901': 'Newell Brands FR (3901)',
            '3902': 'Newell Brands Existing Order (3902)',
            '3903': 'Newell Brands EN (3903)',
            '3904': 'Newell Brands Existing Order EN (3904)',
            '3905': 'Newell Brands Place Order EN (3905)',
            '3906': 'Newell Brands Other Question EN (3906)',
            '3907': 'Newell Brands SP (3907)',
            '3908': 'Newell Brands Existing Order SP (3908)',
            '3909': 'Newell Brands Place Order SP (3909)',
            '3910': 'Newell Brands Other Question SP (3910)',
            '3911': 'Newell Brands Retail Express EN (3911)',
            '3912': 'Newell Brands Retail Express SP (3912)',
            '3913': 'Newell Brands CB EN (3913)',
            '3914': 'Newell Brands Existing Order CB EN (3914)',
            '3915': 'Newell Brands Place Order CB EN (3915)',
            '3916': 'Newell Brands Other CB EN (3916)',
            '3951': 'Newell Brands Escalation Sup (3951)',
            '3952': 'Newell Brands SP (3952)',
            '3953': 'Newell Brands Existing Order SP (3953)',
            '3954': 'Newell Brands Place Order EN (3954)',
            '3955': 'Newell Brands Other EN (3955)',
            '3956': 'Newell Brands Track Order SP (3956)',
            '3957': 'Newell Brands Place Order SP (3957)',
            '3958': 'Newell Brands Other SP (3958)',
            '3959': 'Newell Brands Retail Express EN (3959)',
            '3960': 'Newell Brands Retail Express SP (3960)',
            '3961': 'Newell Brands CB EN (3961)',
            '3962': 'Newell Brands Existing Order CB EN (3962)',
            '3963': 'Newell Brands Place Order CB EN (3963)',
            '3964': 'Newell Brands Retail Express CB EN (3964)',
            '3965': 'Newell Brands Other CB EN (3965)'
        }

        # Crear la interfaz gráfica
        self.create_interface()

        # Actualización automática de la tabla
        self.update_table()

    def time_to_seconds(self, time_str):
        try:
            parts = list(map(int, time_str.split(":")))
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:
                return parts[0] * 60 + parts[1]
            return 0
        except (ValueError, AttributeError):
            return 0

    def parse_queue_data(self, soup):
        data = []
        total_calls_in_queue = 0
        
        # Buscar todas las filas de datos en la tabla
        rows = soup.find_all('tr', class_='data')
        
        for row in rows:
            # Buscamos filas que contengan datos de skills
            skill_cell = row.find('td', colspan='3', class_='nowrap')
            if skill_cell and 'Skill Name' not in skill_cell.get_text():
                skill_name = skill_cell.get_text(strip=True)
                
                # Extraer el ID de skill (está entre paréntesis)
                skill_id = ""
                if "(" in skill_name and ")" in skill_name:
                    skill_id = skill_name.split("(")[-1].split(")")[0].strip()
                
                # Solo procesar si es una skill que conocemos
                if skill_id in self.all_skills:
                    # El siguiente td después del nombre de la skill es Calls in Queue
                    calls_in_queue_cell = skill_cell.find_next_sibling('td')
                    if calls_in_queue_cell:
                        calls_in_queue = calls_in_queue_cell.get_text(strip=True)
                        
                        # Buscamos las celdas de Staffed y Available
                        staffed_cell = calls_in_queue_cell
                        for _ in range(12):  # Avanzamos 12 celdas desde Calls in Queue
                            staffed_cell = staffed_cell.find_next_sibling('td')
                        
                        available_cell = staffed_cell.find_next_sibling('td')
                        
                        # Celda de Oldest Call (7 celdas después de Calls in Queue)
                        oldest_call_cell = calls_in_queue_cell
                        for _ in range(7):
                            oldest_call_cell = oldest_call_cell.find_next_sibling('td')
                        oldest_call = oldest_call_cell.get_text(strip=True) if oldest_call_cell else '00:00'
                        
                        # Celda de RT SL (15 celdas después de Calls in Queue)
                        rt_sl_cell = calls_in_queue_cell
                        for _ in range(15):
                            rt_sl_cell = rt_sl_cell.find_next_sibling('td')
                        rt_sl = rt_sl_cell.get_text(strip=True) if rt_sl_cell else '100.00%'
                        
                        # Solo procesar si calls_in_queue es un número
                        if calls_in_queue.isdigit():
                            calls_int = int(calls_in_queue)
                            total_calls_in_queue += calls_int
                            
                            data.append({
                                'skill_id': skill_id,
                                'skill_name': self.all_skills[skill_id],
                                'calls_in_queue': calls_in_queue,
                                'staffed': staffed_cell.get_text(strip=True) if staffed_cell else '0',
                                'available': available_cell.get_text(strip=True) if available_cell else '0',
                                'oldest_call': oldest_call,
                                'rt_sl': rt_sl
                            })
        
        return data, total_calls_in_queue

    def update_table(self):
        if not self.running:  # Si la aplicación está cerrando, no hacer nada
            return
            
        try:
            response = requests.post(self.url, data=self.payload, headers=self.headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Limpiar listas y tabla
                self.tree.delete(*self.tree.get_children())
                self.alert_list.clear()
                self.aux_list.clear()
                self.queue_list.clear()
                self.total_calls_in_queue = 0

                # Extraer datos de la tabla principal (agentes)
                rows = soup.find_all('tr', class_='data')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 9:
                        avaya_id = cols[0].text.strip()
                        full_name = cols[1].text.strip()
                        state = cols[2].text.strip().upper()
                        reason_code = cols[3].text.strip().upper()
                        active_call = cols[4].text.strip()
                        call_duration = cols[5].text.strip()
                        skill_name = cols[6].text.strip()
                        time_in_state = cols[7].text.strip()

                        call_duration_sec = self.time_to_seconds(call_duration)
                        time_in_state_sec = self.time_to_seconds(time_in_state)

                        # Check for AUX states
                        aux_codes = ["EMAIL 1", "EMAIL 2", "CSR LEVEL II", "QUALITY COACHING",
                                   "TL INTERN", "FLOOR SUPPORT", "CHAT", "BRAND SPECIALIST", "PERFORMANCE ANALYST",
                                    "BACK OFFICE", "TRAINING"]
                        if state == "AUX" and reason_code in aux_codes:
                            self.aux_list.append((reason_code, avaya_id, full_name, time_in_state))

                        alert = ""
                        alert_time = ""

                        if state == "ACD" and call_duration_sec > self.alert_times["Long Call"]:
                            alert = "Long Call"
                            alert_time = call_duration
                        elif "LUNCH" in reason_code and time_in_state_sec > self.alert_times["Extended Lunch"]:
                            alert = "Extended Lunch"
                            alert_time = time_in_state
                        elif state == "ACW" and time_in_state_sec > self.alert_times["Long ACW"]:
                            alert = "Long ACW"
                            alert_time = time_in_state
                        elif state == "AUX" and "BREAK" in reason_code and time_in_state_sec > self.alert_times["Extended Break"]:
                            alert = "Extended Break"
                            alert_time = time_in_state
                        elif state == "AUX" and "IT ISSUE" in reason_code and time_in_state_sec > self.alert_times["IT Issue"]:
                            alert = "IT Issue"
                            alert_time = time_in_state
                        elif state == "AUX" and "DEFAULT" in reason_code:
                            alert = "Default Detected"
                            alert_time = time_in_state
                        elif state == "OTHER (HOLD)" and time_in_state_sec > self.alert_times["Long Hold"]:
                            alert = "Long Hold"
                            alert_time = time_in_state

                        if alert:
                            self.alert_list.append((alert, avaya_id, full_name, alert_time))

                        # Alternar colores de las filas
                        if len(self.tree.get_children()) % 2 == 0:
                            self.tree.insert("", "end", values=(avaya_id, full_name, state, reason_code, active_call, call_duration, skill_name, time_in_state), tags=("even",))
                        else:
                            self.tree.insert("", "end", values=(avaya_id, full_name, state, reason_code, active_call, call_duration, skill_name, time_in_state), tags=("odd",))

                # Procesar datos de llamadas en cola
                queue_data, self.total_calls_in_queue = self.parse_queue_data(soup)
                
                # Asegurarse de que todas las skills estén representadas
                skills_in_data = {item['skill_id'] for item in queue_data}
                for skill_id, skill_name in self.all_skills.items():
                    if skill_id not in skills_in_data:
                        queue_data.append({
                            'skill_id': skill_id,
                            'skill_name': skill_name,
                            'calls_in_queue': "0",
                            'oldest_call': "00:00",
                            'rt_sl': "100.00%",
                            'staffed': "0",
                            'available': "0"
                        })
                
                # Ordenar por nombre de skill
                self.queue_list = sorted(queue_data, key=lambda x: x['skill_name'])

                # Mostrar notificación si hay llamadas en cola
                if self.total_calls_in_queue > 0:
                    # Mostrar notificación en la interfaz
                    if not hasattr(self, 'notification_label') or not self.notification_label.winfo_exists():
                        self.notification_label = tk.Label(
                            self.master,
                            text=f"¡{self.total_calls_in_queue} llamadas en cola! Haga clic en 'View Queue' para ver detalles.",
                            bg="red", fg="white", font=("Arial", 12, "bold"),
                            padx=10, pady=5
                        )
                        self.notification_label.place(relx=0.5, rely=0.25, anchor="center")
                else:
                    # Eliminar notificación si existe
                    if hasattr(self, 'notification_label') and self.notification_label.winfo_exists():
                        self.notification_label.destroy()
                        delattr(self, 'notification_label')

            else:
                messagebox.showerror("Error", f"Failed to fetch data: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Network error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            # En caso de error, asegurarse de que todas las skills estén representadas
            self.queue_list = []
            for skill_id, skill_name in self.all_skills.items():
                self.queue_list.append({
                    'skill_id': skill_id,
                    'skill_name': skill_name,
                    'calls_in_queue': "0",
                    'oldest_call': "00:00",
                    'rt_sl': "100.00%",
                    'staffed': "0",
                    'available': "0"
                })

        # Actualizar la tabla cada 15 segundos si la aplicación sigue corriendo
        if self.running:
            self.update_task = self.master.after(15000, self.update_table)

    def show_settings_window(self):
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Alert Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg="#F6F0FF")

        # Frame principal
        main_frame = tk.Frame(settings_window, bg="#F6F0FF")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        title_label = tk.Label(main_frame, text="Alert Settings",
                             font=("Arial", 16, "bold"), fg="black", bg="#F6F0FF")
        title_label.pack(pady=10)

        # Frame para los tiempos personalizados
        custom_frame = tk.Frame(main_frame, bg="#F6F0FF")
        custom_frame.pack(fill="x", pady=10)

        # Entradas para los tiempos personalizados
        self.custom_times = {}
        for alert, time in self.alert_times.items():
            row_frame = tk.Frame(custom_frame, bg="#F6F0FF")
            row_frame.pack(fill="x", pady=5)

            label = tk.Label(row_frame, text=f"{alert}:", font=("Arial", 12), bg="#F6F0FF")
            label.pack(side="left", padx=5)

            entry = tk.Entry(row_frame, font=("Arial", 12), width=10)
            entry.insert(0, str(time))
            entry.pack(side="right", padx=5)
            self.custom_times[alert] = entry

        # Botón para aplicar los cambios
        apply_button = tk.Button(main_frame, text="Aplicar",
                               command=lambda: self.apply_custom_times(settings_window),
                               bg="#6A0DAD", fg="white", font=("Arial", 12, "bold"))
        apply_button.pack(pady=10)

        # Botón para usar los tiempos predeterminados
        default_button = tk.Button(main_frame, text="Use Default Times",
                                 command=lambda: self.use_default_times(settings_window),
                                 bg="#6A0DAD", fg="white", font=("Arial", 12, "bold"))
        default_button.pack(pady=10)

    def apply_custom_times(self, settings_window):
        try:
            for alert, entry in self.custom_times.items():
                self.alert_times[alert] = int(entry.get())
            messagebox.showinfo("Success", "Custom times applied successfully!")
            settings_window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all fields.")

    def use_default_times(self, settings_window):
        self.alert_times = {
            "Long Call": 360,
            "Extended Lunch": 3600,
            "Long ACW": 120,
            "Extended Break": 900,
            "IT Issue": 30,
            "Long Hold": 120
        }
        messagebox.showinfo("Success", "Default times restored successfully!")
        settings_window.destroy()

    def show_alert_window(self):
        if hasattr(self, 'alert_window') and self.alert_window.winfo_exists():
            self.alert_window.lift()
            return
            
        self.alert_window = tk.Toplevel(self.master)
        self.alert_window.title("⚠️ ACTIVE ALERTS ⚠️")
        self.alert_window.geometry("600x500")
        self.alert_window.configure(bg="#FFB6C1")

        # Frame principal para el contenido
        self.main_frame = tk.Frame(self.alert_window, bg="#FFB6C1")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.title_label = tk.Label(self.main_frame, text="⚠️ ACTIVE ALERTS ⚠️",
                                  font=("Arial", 20, "bold"), fg="black", bg="#FFB6C1")
        self.title_label.pack(pady=10)

        # Frame para el contenido con scroll
        self.content_frame = tk.Frame(self.main_frame, bg="white", bd=2, relief="solid")
        self.content_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Canvas y scrollbar
        self.canvas = tk.Canvas(self.content_frame, bg="white")
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.canvas.yview)

        # Frame dentro del canvas
        self.alert_frame = tk.Frame(self.canvas, bg="white")

        # Configurar el canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Crear ventana en el canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.alert_frame, anchor="nw")

        # Función para actualizar las alertas
        def update_alerts():
            if not self.alert_window.winfo_exists():  # Si la ventana fue cerrada, no hacer nada
                return
                
            # Limpiar el contenido actual
            for widget in self.alert_frame.winfo_children():
                widget.destroy()

            # Mostrar las alertas actualizadas
            if not self.alert_list:
                no_alerts_label = tk.Label(self.alert_frame, text="No active alerts at the moment.",
                                         font=("Arial", 14, "italic"), fg="gray", bg="white")
                no_alerts_label.pack(pady=20)
            else:
                alert_dict = {}
                for alert, avaya_id, full_name, alert_time in self.alert_list:
                    if alert not in alert_dict:
                        alert_dict[alert] = []
                    alert_dict[alert].append(f"{avaya_id} - {full_name} ({alert_time})")

                for alert_type, users in alert_dict.items():
                    title = tk.Label(self.alert_frame, text=alert_type.upper(),
                                   font=("Arial", 16, "bold"), fg="red", bg="white")
                    title.pack(pady=5)

                    for user in users:
                        alert_label = tk.Label(self.alert_frame, text=user,
                                             font=("Arial", 12), bg="white")
                        alert_label.pack(anchor="w", padx=10)

            # Programar la próxima actualización si la ventana sigue abierta
            if self.alert_window.winfo_exists():
                self.alert_window.after(15000, update_alerts)

        # Llamar a la función de actualización por primera vez
        update_alerts()

        # Frame para el botón
        button_frame = tk.Frame(self.alert_window, bg="#FFB6C1")
        button_frame.pack(fill="x", pady=10)

        close_button = tk.Button(button_frame, text="Close",
                               font=("Arial", 12, "bold"), bg="red", fg="white",
                               command=self.alert_window.destroy)
        close_button.pack(pady=5)

        # Configurar el scroll
        def _on_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.itemconfig(self.canvas_frame, width=self.canvas.winfo_width())

        self.alert_frame.bind("<Configure>", _on_frame_configure)

        def _on_mousewheel(event):
            if self.alert_window.winfo_exists():
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _on_closing():
            self.canvas.unbind_all("<MouseWheel>")
            self.alert_window.destroy()

        self.alert_window.protocol("WM_DELETE_WINDOW", _on_closing)

    def show_aux_window(self):
        if hasattr(self, 'aux_window') and self.aux_window.winfo_exists():
            self.aux_window.lift()
            return
            
        self.aux_window = tk.Toplevel(self.master)
        self.aux_window.title("AUX Status")
        self.aux_window.geometry("600x500")
        self.aux_window.configure(bg="#FFB6C1")

        # Frame principal
        self.main_frame_aux = tk.Frame(self.aux_window, bg="#FFB6C1")
        self.main_frame_aux.pack(fill="both", expand=True, padx=20, pady=10)

        self.title_label_aux = tk.Label(self.main_frame_aux, text="AUX Status",
                                      font=("Arial", 20, "bold"), fg="black", bg="#FFB6C1")
        self.title_label_aux.pack(pady=10)

        # Frame para el contenido con scroll
        self.content_frame_aux = tk.Frame(self.main_frame_aux, bg="white", bd=2, relief="solid")
        self.content_frame_aux.pack(fill="both", expand=True, pady=(0, 10))

        # Canvas y scrollbar
        self.canvas_aux = tk.Canvas(self.content_frame_aux, bg="white")
        self.scrollbar_aux = ttk.Scrollbar(self.content_frame_aux, orient="vertical", command=self.canvas_aux.yview)

        # Frame dentro del canvas
        self.aux_frame = tk.Frame(self.canvas_aux, bg="white")

        # Configurar el canvas
        self.canvas_aux.configure(yscrollcommand=self.scrollbar_aux.set)
        self.canvas_aux.pack(side="left", fill="both", expand=True)
        self.scrollbar_aux.pack(side="right", fill="y")

        # Crear ventana en el canvas
        self.canvas_frame_aux = self.canvas_aux.create_window((0, 0), window=self.aux_frame, anchor="nw")

        # Función para actualizar el contenido de AUX
        def update_aux():
            if not self.aux_window.winfo_exists():  # Si la ventana fue cerrada, no hacer nada
                return
                
            # Limpiar el contenido actual
            for widget in self.aux_frame.winfo_children():
                widget.destroy()

            # Mostrar el contenido actualizado
            if not self.aux_list:
                no_aux_label = tk.Label(self.aux_frame, text="No agents in AUX status.",
                                      font=("Arial", 14, "italic"), fg="gray", bg="white")
                no_aux_label.pack(pady=20)
            else:
                aux_dict = {}
                for aux_type, avaya_id, full_name, time_in_state in self.aux_list:
                    if aux_type not in aux_dict:
                        aux_dict[aux_type] = []
                    aux_dict[aux_type].append(f"{avaya_id} - {full_name} ({time_in_state})")

                for aux_type, users in aux_dict.items():
                    title = tk.Label(self.aux_frame, text=aux_type,
                                   font=("Arial", 16, "bold"), fg="purple", bg="white")
                    title.pack(pady=5)

                    for user in users:
                        aux_label = tk.Label(self.aux_frame, text=user,
                                            font=("Arial", 12), bg="white")
                        aux_label.pack(anchor="w", padx=10)

            # Programar la próxima actualización si la ventana sigue abierta
            if self.aux_window.winfo_exists():
                self.aux_window.after(15000, update_aux)

        # Llamar a la función de actualización por primera vez
        update_aux()

        # Frame para el botón
        button_frame = tk.Frame(self.aux_window, bg="#FFB6C1")
        button_frame.pack(fill="x", pady=10)

        close_button = tk.Button(button_frame, text="Close",
                               font=("Arial", 12, "bold"), bg="red", fg="white",
                               command=self.aux_window.destroy)
        close_button.pack(pady=5)

        # Configurar el scroll
        def _on_frame_configure(event):
            self.canvas_aux.configure(scrollregion=self.canvas_aux.bbox("all"))
            self.canvas_aux.itemconfig(self.canvas_frame_aux, width=self.canvas_aux.winfo_width())

        self.aux_frame.bind("<Configure>", _on_frame_configure)

        def _on_mousewheel(event):
            if self.aux_window.winfo_exists():
                self.canvas_aux.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas_aux.bind_all("<MouseWheel>", _on_mousewheel)

        def _on_closing():
            self.canvas_aux.unbind_all("<MouseWheel>")
            self.aux_window.destroy()

        self.aux_window.protocol("WM_DELETE_WINDOW", _on_closing)

    def show_queue_window(self):
        if hasattr(self, 'queue_window') and self.queue_window.winfo_exists():
            self.queue_window.lift()
            return
            
        self.queue_window = tk.Toplevel(self.master)
        self.queue_window.title("Calls in Queue")
        self.queue_window.geometry("800x600")
        self.queue_window.configure(bg="#FFB6C1")

        # Frame principal
        self.main_frame_queue = tk.Frame(self.queue_window, bg="#FFB6C1")
        self.main_frame_queue.pack(fill="both", expand=True, padx=20, pady=10)

        self.title_label_queue = tk.Label(self.main_frame_queue, text="Active Calls in Queue",
                                        font=("Arial", 20, "bold"), fg="black", bg="#FFB6C1")
        self.title_label_queue.pack(pady=10)

        # Frame para el contenido con scroll
        self.content_frame_queue = tk.Frame(self.main_frame_queue, bg="white", bd=2, relief="solid")
        self.content_frame_queue.pack(fill="both", expand=True, pady=(0, 10))

        # Crear tabla para mostrar las skills y sus llamadas en cola
        columns = ("Skill Name", "Calls in Queue", "Oldest Call", "Staffed", "Available")
        self.queue_tree = ttk.Treeview(self.content_frame_queue, columns=columns, show="headings", height=20)

        # Configurar columnas
        self.queue_tree.heading("Skill Name", text="Skill Name")
        self.queue_tree.heading("Calls in Queue", text="Calls in Queue")
        self.queue_tree.heading("Oldest Call", text="Oldest Call")
        self.queue_tree.heading("Staffed", text="Staffed")
        self.queue_tree.heading("Available", text="Available")

        self.queue_tree.column("Skill Name", width=250, anchor="w")
        self.queue_tree.column("Calls in Queue", width=100, anchor="center")
        self.queue_tree.column("Oldest Call", width=100, anchor="center")
        self.queue_tree.column("Staffed", width=80, anchor="center")
        self.queue_tree.column("Available", width=80, anchor="center")

        # Scrollbar
        self.scrollbar_queue = ttk.Scrollbar(self.content_frame_queue, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=self.scrollbar_queue.set)

        # Empaquetar
        self.queue_tree.pack(side="left", fill="both", expand=True)
        self.scrollbar_queue.pack(side="right", fill="y")

        # Función para actualizar la tabla de llamadas en cola
        def update_queue():
            if not self.queue_window.winfo_exists():  # Si la ventana fue cerrada, no hacer nada
                return
                
            # Limpiar la tabla
            for row in self.queue_tree.get_children():
                self.queue_tree.delete(row)

            # Filtrar para mostrar solo skills con llamadas en cola
            filtered_queue_list = [skill for skill in self.queue_list if int(skill['calls_in_queue']) > 0]

            if not filtered_queue_list:
                # Si no hay llamadas en cola, mostrar un mensaje
                self.queue_tree.insert("", "end", values=("No calls currently in queue for any skill.", "", "", "", ""))
            else:
                # Llenar la tabla con datos filtrados
                for skill in filtered_queue_list:
                    values = (
                        skill['skill_name'],
                        skill['calls_in_queue'],
                        skill['oldest_call'],
                        skill['staffed'],
                        skill['available']
                    )
                    self.queue_tree.insert("", "end", values=values, tags=("has_calls",))

            # Programar la próxima actualización si la ventana sigue abierta
            if self.queue_window.winfo_exists():
                self.queue_window.after(15000, update_queue)

        # Llamar a la función de actualización por primera vez
        update_queue()

        # Configurar tag para filas resaltadas
        self.queue_tree.tag_configure("has_calls", background="#ffcccc")

        # Frame para el botón
        button_frame = tk.Frame(self.queue_window, bg="#FFB6C1")
        button_frame.pack(fill="x", pady=10)

        close_button = tk.Button(button_frame, text="Close",
                               font=("Arial", 12, "bold"), bg="red", fg="white",
                               command=self.queue_window.destroy)
        close_button.pack(pady=5)

    def create_interface(self):
        # Logo de Newell Brands
        canvas = tk.Canvas(self.master, width=250, height=100, bg="#F6F0FF", highlightthickness=0)
        canvas.place(relx=0.5, rely=0.12, anchor="center")

        # Función para dibujar un rectángulo con esquinas redondeadas
        def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
            points = [
                x1 + radius, y1,
                x2 - radius, y1,
                x2, y1,
                x2, y1 + radius,
                x2, y2 - radius,
                x2, y2,
                x2 - radius, y2,
                x1 + radius, y2,
                x1, y2,
                x1, y2 - radius,
                x1, y1 + radius,
                x1, y1,
                x1 + radius, y1
            ]
            return canvas.create_polygon(points, **kwargs, smooth=True)

        # Dibujar el logo con esquinas redondeadas
        create_rounded_rectangle(canvas, 10, 30, 240, 90, radius=20, fill="#0056A7", outline="black", width=2)
        canvas.create_text(125, 60, text="Newell Brands", font=("Arial", 18, "bold"), fill="white")

        # Texto "IntouchCX" en la esquina superior izquierda
        intouch_label = tk.Label(
            self.master,
            text="IntouchCX",
            font=("Arial", 35, "bold"),
            fg="#6A0DAD",
            bg="#F6F0FF",
            padx=10,
            pady=5
        )
        intouch_label.place(relx=0.02, rely=0.095, anchor="nw")

        # Botón para cambiar al dashboard de colas
        queue_dashboard_button = tk.Button(
            self.master,
            text="Switch to Queue Dashboard",
            command=self.open_queue_dashboard,
            bg="#6A0DAD",
            fg="white",
            font=("Arial", 12, "bold")
        )
        queue_dashboard_button.place(relx=0.98, rely=0.095, anchor="ne")

        # Resto de la interfaz (tabla, botones, etc.)
        frame_table = tk.Frame(self.master, bg="#F6F0FF")
        frame_table.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.6)

        columns = ("Avaya ID", "Full Name", "State", "Reason Code", "Active Call", "Call Duration", "Skill Name", "Time in State")
        self.tree = ttk.Treeview(frame_table, columns=columns, show="headings")

        # Configurar columnas
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        # Configurar colores alternados para las filas
        self.tree.tag_configure("even", background="#DAC8FF")
        self.tree.tag_configure("odd", background="#D0B5FF")

        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(expand=True, fill="both")

        # Frame para los botones
        button_frame = tk.Frame(self.master, bg="#F6F0FF")
        button_frame.place(relx=0.5, rely=0.9, anchor="center")

        # Botón de alertas
        alert_button = tk.Button(button_frame, text="View Alerts", command=self.show_alert_window,
                               bg="#6A0DAD", fg="white", font=("Arial", 12, "bold"))
        alert_button.pack(side="left", padx=5)

        # Botón de AUX
        aux_button = tk.Button(button_frame, text="View AUX Status", command=self.show_aux_window,
                             bg="#6A0DAD", fg="white", font=("Arial", 12, "bold"))
        aux_button.pack(side="left", padx=5)

        # Botón de Queue
        queue_button = tk.Button(button_frame, text="View Queue", command=self.show_queue_window,
                               bg="#6A0DAD", fg="white", font=("Arial", 12, "bold"))
        queue_button.pack(side="left", padx=5)

        # Botón de configuración
        settings_button = tk.Button(button_frame, text="Settings", command=self.show_settings_window,
                                  bg="#6A0DAD", fg="white", font=("Arial", 12, "bold"))
        settings_button.pack(side="left", padx=5)

    def open_queue_dashboard(self):
        self.master.withdraw()  # Ocultar la ventana actual
        queue_root = tk.Toplevel()
        queue_root.protocol("WM_DELETE_WINDOW", lambda: self.close_queue_dashboard(queue_root))
        QueueDashboard(queue_root, self)

    def close_queue_dashboard(self, queue_root):
        queue_root.destroy()
        self.master.deiconify()  # Mostrar nuevamente la ventana principal

    def on_closing(self):
        """Método para manejar el cierre de la aplicación"""
        self.running = False  # Detener las actualizaciones
        if self.update_task:
            self.master.after_cancel(self.update_task)
        self.master.destroy()


class QueueDashboard:
    def __init__(self, root, agent_app):
        self.root = root
        self.agent_app = agent_app
        self.root.title("Queue Monitoring Dashboard")
        self.root.geometry("1400x800")
        self.root.configure(bg='#6a0dad')
        self.running = True
        self.highlight_labels = {}

        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # General style configurations
        self.style.configure(".", background='#6a0dad', foreground='white')

        # Treeview styles
        self.style.configure("Treeview", 
                           font=('Arial', 10), 
                           rowheight=25,
                           background='#d8bfd8',
                           fieldbackground='#d8bfd8',
                           foreground='black')
        self.style.configure("Treeview.Heading", 
                           font=('Arial', 10, 'bold'),
                           background='#9370db',
                           foreground='white',
                           relief='flat')
        self.style.map("Treeview.Heading", 
                      background=[('active', '#ba55d3')])
        
        # Label styles
        self.style.configure("Header.TLabel", 
                           font=('Arial', 18, 'bold'),
                           background='#6a0dad',
                           foreground='white')
        self.style.configure("Info.TLabel", 
                           font=('Arial', 10),
                           background='#6a0dad',
                           foreground='white')

        # Button styles
        self.style.configure("Toggle.TButton",
                           font=('Arial', 10, 'bold'),
                           background='#9370db',
                           foreground='white',
                           borderwidth=1,
                           relief='raised')
        self.style.map("Toggle.TButton",
                      background=[('pressed', '#8a2be2'),
                                 ('active', '#ba55d3'),
                                 ('disabled', '#cccccc')],
                      foreground=[('pressed', 'white'),
                                 ('active', 'white'),
                                 ('disabled', '#666666')])

        # Main container
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with logo and title
        header_frame = tk.Frame(self.main_frame, bg='#6a0dad')
        header_frame.pack(fill=tk.X, pady=(0, 20))

        left_header = tk.Frame(header_frame, bg='#6a0dad')
        left_header.pack(side=tk.LEFT, padx=10, pady=5)
        intouch_logo = tk.Label(left_header, 
                              text="IntouchCX", 
                              font=('Arial', 18, 'bold'),
                              bg='#6a0dad',
                              fg='white')
        intouch_logo.pack(side=tk.LEFT)

        center_header = tk.Frame(header_frame, bg='#6a0dad')
        center_header.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Label(center_header, 
                 text="Queue Monitoring Dashboard", 
                 style="Header.TLabel").pack(pady=5)

        right_header = tk.Frame(header_frame, bg='#6a0dad')
        right_header.pack(side=tk.RIGHT, padx=10, pady=5)

        # Botón para regresar al dashboard principal
        back_button = tk.Button(
            right_header,
            text="Back to Agent Dashboard",
            command=self.open_agent_dashboard,
            bg="#9370db",
            fg="white",
            font=("Arial", 10, "bold")
        )
        back_button.pack(side=tk.LEFT, padx=5)

        # Botón para copiar datos
        copy_button = tk.Button(
            right_header,
            text="Copy SLA Data",
            command=self.copy_sla_data,
            bg="#9370db",
            fg="white",
            font=("Arial", 10, "bold")
        )
        copy_button.pack(side=tk.LEFT, padx=5)

        newell_frame = tk.Frame(right_header, 
                             bg='#0056A7', 
                             width=120,
                             height=60)
        newell_frame.pack_propagate(0)
        newell_frame.pack(side=tk.RIGHT)
        newell_label = tk.Label(newell_frame, 
                             text="Newell", 
                             font=('Arial', 16, 'bold'),
                             bg='#0056A7',
                             fg='white')
        newell_label.pack(expand=True)

        # Control panel
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 20))

        button_container = ttk.Frame(control_frame)
        button_container.pack(side=tk.LEFT, padx=20)
        self.main_view_button = ttk.Button(
            button_container, 
            text="Main View", 
            style="Toggle.TButton",
            command=lambda: self.toggle_view('main')
        )
        self.main_view_button.pack(side=tk.LEFT)
        self.agents_view_button = ttk.Button(
            button_container, 
            text="Agents View", 
            style="Toggle.TButton",
            command=lambda: self.toggle_view('agents')
        )
        self.agents_view_button.pack(side=tk.LEFT, padx=5)

        # Column configurations for different views
        self.column_configs = {
            'main': [
                ('skill_name', 'Skill Name', 180, tk.W),
                ('calls_in_queue', 'Calls in Queue', 100, tk.CENTER),
                ('offered', 'Offered', 80, tk.CENTER),
                ('answered', 'Answered', 80, tk.CENTER),
                ('transfers', 'Transfers', 80, tk.CENTER),
                ('true_abn', 'True Abn', 80, tk.CENTER),
                ('short_abn', 'Short Abn', 80, tk.CENTER),
                ('oldest_call', 'Oldest Call', 100, tk.CENTER),
                ('max_delay', 'Max Delay', 100, tk.CENTER),
                ('asa', 'ASA', 80, tk.CENTER),
                ('aqt', 'AQT', 80, tk.CENTER),
                ('service_level', 'Service Level %', 120, tk.CENTER),
                ('rt_sl', 'RT SL %', 100, tk.CENTER)
            ],
            'agents': [
                ('skill_name', 'Skill Name', 180, tk.W),
                ('staffed', 'Staffed', 80, tk.CENTER),
                ('available', 'Available', 80, tk.CENTER),
                ('acw', 'ACW', 80, tk.CENTER),
                ('acd', 'ACD', 80, tk.CENTER),
                ('aux', 'AUX', 80, tk.CENTER),
                ('other', 'Other', 80, tk.CENTER)
            ]
        }

        all_columns = []
        for view in self.column_configs.values():
            all_columns.extend([col[0] for col in view])
        all_columns = list(dict.fromkeys(all_columns))

        # Contenedor principal para el Treeview y scrollbar
        tree_container = tk.Frame(self.main_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(tree_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        self.tree = ttk.Treeview(
            tree_container,
            columns=all_columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        # Configurar todas las columnas
        self.configure_all_columns()

        self.current_view = 'main'
        self.toggle_view('main')

        # Configurar tags para las filas
        self.tree.tag_configure('normal', background='#DAC8FF')
        self.tree.tag_configure('alternate', background='#D0B5FF')
        self.tree.tag_configure('calls_warning', background='#E66F6F')  # Light red for calls in queue
        self.tree.tag_configure('sl_warning', background='#CE2424')     # Medium red for SLA < 80%
        self.tree.tag_configure('both_warning', background='#660002', foreground='white')  # Dark red for both

        # Frame para los highlights (superpuesto al Treeview)
        self.highlight_frame = tk.Frame(tree_container)
        self.highlight_frame.place(in_=self.tree, relx=0, rely=0, relwidth=1, relheight=1)
        self.highlight_frame.lower(self.tree)  # Colocar detrás del Treeview

        self.current_data = []
        self.start_auto_refresh()
        self.refresh_data()

        # Configurar eventos para actualizar highlights
        self.tree.bind("<Configure>", self.update_highlights)
        self.tree.bind("<MouseWheel>", self.on_mousewheel)

    def copy_sla_data(self):
        """Copy the current SLA data to clipboard in the requested format"""
        try:
            # Get skills with SLA below 80%
            low_sla_skills = []
            for skill in self.current_data:
                try:
                    sl_value = float(skill.get('service_level', '0%').rstrip('%'))
                    if sl_value < 80:
                        skill_name = skill.get('skill_name', '')
                        sl_percent = skill.get('service_level', '0%')
                        low_sla_skills.append(f"{skill_name} = {sl_percent}")
                except ValueError:
                    continue
            
            # Prepare the text to copy
            if low_sla_skills:
                text_to_copy = (
                    "Voice - Queue\n\n"
                    "Team, this is our current SLA view and listed you'll find the impacted skills so far:\n\n"
                    + "\n".join([f"- {skill}" for skill in low_sla_skills]) + 
                    "\n\nThe other skills are on target."
                )
            else:
                text_to_copy = (
                    "Voice - Queue\n\n"
                    "All skills are currently meeting SLA targets (80% or above)"
                )
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(text_to_copy)
            
            # Show toast notification
            self.show_toast("SLA data copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy data: {str(e)}")

    def show_toast(self, message):
        """Show a temporary toast notification"""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.geometry(f"+{self.root.winfo_rootx()+50}+{self.root.winfo_rooty()+50}")
        
        label = tk.Label(toast, text=message, bg="#4CAF50", fg="white", padx=20, pady=10)
        label.pack()
        
        # Auto-close after 3 seconds
        toast.after(3000, toast.destroy)

    def on_mousewheel(self, event):
        self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.update_highlights()
        return "break"

    def update_highlights(self, event=None):
        for item_id, label in self.highlight_labels.items():
            if self.tree.exists(item_id):
                bbox = self.tree.bbox(item_id, column='#2')
                if bbox:
                    x, y, width, height = bbox
                    label.place(x=x, y=y, width=width, height=height)

    def configure_all_columns(self):
        for view in self.column_configs.values():
            for col_id, heading, width, anchor in view:
                self.tree.heading(col_id, text=heading)
                self.tree.column(col_id, width=width, anchor=anchor)

    def toggle_view(self, view_name):
        if view_name == self.current_view:
            return
        self.current_view = view_name
        
        for col in self.tree['columns']:
            self.tree.column(col, width=0, stretch=False)
        
        for col_id, _, width, _ in self.column_configs[view_name]:
            self.tree.column(col_id, width=width, stretch=True)
        
        if view_name == 'main':
            self.main_view_button.state(['pressed', 'disabled'])
            self.agents_view_button.state(['!pressed', '!disabled'])
        else:
            self.main_view_button.state(['!pressed', '!disabled'])
            self.agents_view_button.state(['pressed', 'disabled'])
        
        self.display_current_data()

    def display_current_data(self):
        if not hasattr(self, 'running') or not self.running:
            return
            
        for label in self.highlight_labels.values():
            label.destroy()
        self.highlight_labels = {}
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for i, row_data in enumerate(self.current_data):
            # Crear una copia para modificar los datos de visualización
            display_data = row_data.copy()
            
            # Verificar si hay llamadas en cola y estamos en vista principal
            calls_in_queue = display_data.get('calls_in_queue', '0')
            has_calls = calls_in_queue.isdigit() and int(calls_in_queue) > 0
            
            if has_calls and self.current_view == 'main':
                display_data['calls_in_queue'] = f"⚠️{calls_in_queue}⚠️"
            
            if self.current_view == 'main':
                values = [
                    display_data.get('skill_name', ''),
                    display_data.get('calls_in_queue', ''),
                    display_data.get('offered', ''),
                    display_data.get('answered', ''),
                    display_data.get('transfers', ''),
                    display_data.get('true_abn', ''),
                    display_data.get('short_abn', ''),
                    display_data.get('oldest_call', ''),
                    display_data.get('max_delay', ''),
                    display_data.get('asa', ''),
                    display_data.get('aqt', ''),
                    display_data.get('service_level', ''),
                    display_data.get('rt_sl', '')
                ]
                values.extend([''] * (len(self.tree['columns']) - len(values)))
            else:
                values = [''] * len(self.tree['columns'])
                for j, (col_id, _, _, _) in enumerate(self.column_configs['agents']):
                    col_index = self.tree['columns'].index(col_id)
                    values[col_index] = display_data.get(col_id, '')

            # Determinar el tag apropiado
            try:
                sl_value = float(display_data.get('service_level', '0').rstrip('%'))
                low_sla = sl_value < 80
            except ValueError:
                low_sla = False
                
            if self.current_view == 'main':
                if has_calls and low_sla:
                    tag = 'both_warning'
                elif has_calls:
                    tag = 'calls_warning'
                elif low_sla:
                    tag = 'sl_warning'
                else:
                    tag = 'alternate' if i % 2 else 'normal'
            else:
                tag = 'alternate' if i % 2 else 'normal'

            item = self.tree.insert('', tk.END, values=values, tags=(tag,))
            
            # Solo para la vista principal y si hay llamadas en cola
            if has_calls and self.current_view == 'main':
                highlight = tk.Label(
                    self.highlight_frame, 
                    text=calls_in_queue,
                    font=('Arial', 10, 'bold'),
                    background="#CE2424",
                    foreground="white",
                    bd=0
                )
                self.highlight_labels[item] = highlight
                    
        self.update_highlights()

    def refresh_data(self):
        try:
            if not self.root.winfo_exists():
                return
                
            self.root.config(cursor="wait")
            self.root.update()
            
            html_content = self.fetch_api_data()
            self.process_data(html_content)
        except Exception as e:
            if self.root.winfo_exists():
                messagebox.showerror("Error", f"Failed to load data: {str(e)}")
        finally:
            if self.root.winfo_exists():
                self.root.config(cursor="")

    def process_data(self, html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            self.current_data = []
            rows = soup.find_all('tr', class_='data')[2:]
            
            for row in rows:
                cells = row.find_all('td')
                if not cells or len(cells) < 19:
                    continue
                
                try:
                    skill_info = cells[0]
                    strong_tag = skill_info.find('strong')
                    if not strong_tag:
                        continue
                        
                    skill_name = strong_tag.text.strip()
                    skill_id = cells[0].text.strip().split('(')[-1].split(')')[0].strip()
                    
                    row_data = {
                        'skill_name': f"{skill_name} ({skill_id})",
                        'calls_in_queue': cells[1].text.strip() if len(cells) > 1 else '',
                        'offered': cells[2].text.strip() if len(cells) > 2 else '',
                        'answered': cells[3].text.strip() if len(cells) > 3 else '',
                        'transfers': cells[4].text.strip() if len(cells) > 4 else '',
                        'true_abn': cells[5].text.strip() if len(cells) > 5 else '',
                        'short_abn': cells[6].text.strip() if len(cells) > 6 else '',
                        'oldest_call': cells[7].text.strip() if len(cells) > 7 else '',
                        'max_delay': cells[8].text.strip() if len(cells) > 8 else '',
                        'asa': cells[9].text.strip() if len(cells) > 9 else '',
                        'aqt': cells[10].text.strip() if len(cells) > 10 else '',
                        'service_level': cells[11].text.strip() if len(cells) > 11 else '0%',
                        'rt_sl': cells[12].text.strip() if len(cells) > 12 else '',
                        'staffed': cells[13].text.strip() if len(cells) > 13 else '',
                        'available': cells[14].text.strip() if len(cells) > 14 else '',
                        'acw': cells[15].text.strip() if len(cells) > 15 else '',
                        'acd': cells[16].text.strip() if len(cells) > 16 else '',
                        'aux': cells[17].text.strip() if len(cells) > 17 else '',
                        'other': cells[18].text.strip() if len(cells) > 18 else ''
                    }
                    self.current_data.append(row_data)
                except (IndexError, AttributeError) as e:
                    print(f"Error processing row: {str(e)}")
                    continue
                    
            self.display_current_data()
        except Exception as e:
            raise Exception(f"Error processing data: {str(e)}")

    def fetch_api_data(self):
        try:
            url = "https://reports.intouchcx.com/reports/lib/getRealtimeManagementFull.asp"
            payload = {
                "split": "3900,3901,3902,3903,3904,3905,3906,3907,3908,3909,3910,3911,3912,3913,3914,3915,3916,3917,3918,3919,3920,3921,3922,3923,3924,3925,3926,3927,3928,3929,3930,3931,3932,3933,3934,3935,3936,3937,3938,3939,3940,3941,3942,3943,3944,3945,3946,3947,3948,3949,3950,3951,3952,3953,3954,3955,3956,3957,3958,3959,3960,3961,3962,3963,3964,3965,3966,3967,3968,3969,3970,3971,3972,3973",
                "firstSortCol": "FullName",
                "firstSortDir": "ASC",
                "secondSortCol": "FullName",
                "secondSortDir": "ASC",
                "reason": "all",
                "state": "all",
                "timezone": "1",
                "altSL": "",
                "threshold": "180",
                "altSLThreshold": "0",
                "acdAlert": "",
                "acwAlert": "",
                "holdAlert": "",
                "slAlert": "",
                "asaAlert": ""
            }
            headers = {
                "Accept": "text/html, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://reports.intouchcx.com/reports/custom/newellbrands/realtimemanagementfull.asp?threshold=180&tzoffset=est"
            }
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch data: {str(e)}")

    def start_auto_refresh(self):
        def refresh_loop():
            while self.running:
                time.sleep(15)
                try:
                    if self.root.winfo_exists():
                        self.root.after(0, self.refresh_data)
                except:
                    break
                    
        thread = threading.Thread(target=refresh_loop, daemon=True)
        thread.start()

    def open_agent_dashboard(self):
        if self.agent_app.master.winfo_exists():
            self.running = False
            for label in self.highlight_labels.values():
                label.destroy()
            self.highlight_labels = {}
            self.root.destroy()
            self.agent_app.master.deiconify()


if __name__ == "__main__":
    root = tk.Tk()
    app = NewellBrandsVoice(root)
    
    # Configurar el manejo de cierre para Render
    if os.environ.get('RENDER', 'False').lower() == 'true':
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()