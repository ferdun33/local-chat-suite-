# chat_client.py - Клиент локального чата на Python (Tkinter GUI)
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import socket
import threading
import json
import base64
import os

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Локальный чат - Python")
        self.root.geometry("800x600")
        self.root.configure(bg="#2c3e50")
        
        self.nickname = None
        self.client_socket = None
        self.connected = False
        
        # Вход в чат
        self.login_frame = tk.Frame(root, bg="#2c3e50")
        self.login_frame.pack(expand=True)
        tk.Label(self.login_frame, text="Введите ваш ник:", bg="#2c3e50", fg="white", font=('Arial',14)).pack(pady=10)
        self.nick_entry = tk.Entry(self.login_frame, font=('Arial',12), width=30)
        self.nick_entry.pack(pady=5)
        tk.Button(self.login_frame, text="Подключиться", command=self.connect, bg="#3498db", fg="white").pack(pady=10)
        
        # Основной интерфейс чата (скрыт до подключения)
        self.chat_frame = tk.Frame(root, bg="#ecf0f1")
        self.text_area = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, height=20, font=('Arial',10))
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.text_area.config(state=tk.DISABLED)
        
        self.entry_frame = tk.Frame(self.chat_frame, bg="#ecf0f1")
        self.entry_frame.pack(fill=tk.X, padx=10, pady=5)
        self.msg_entry = tk.Entry(self.entry_frame, font=('Arial',11))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        tk.Button(self.entry_frame, text="Отправить", command=self.send_message, bg="#2ecc71", fg="white").pack(side=tk.RIGHT)
        tk.Button(self.entry_frame, text="📎 Файл", command=self.send_file, bg="#f39c12", fg="white").pack(side=tk.RIGHT, padx=5)
        tk.Button(self.entry_frame, text="👥 Пользователи", command=self.show_users, bg="#9b59b6", fg="white").pack(side=tk.RIGHT, padx=5)
        
        self.status_label = tk.Label(self.chat_frame, text="Не подключен", bg="#ecf0f1", fg="gray", anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=10, pady=2)
        
    def connect(self):
        nickname = self.nick_entry.get().strip()
        if not nickname:
            messagebox.showerror("Ошибка", "Введите ник")
            return
        self.nickname = nickname
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('127.0.0.1', 5555))
            # Ожидание запроса ника
            self.client_socket.recv(1024)
            self.client_socket.send(nickname.encode('utf-8'))
            self.connected = True
            self.login_frame.pack_forget()
            self.chat_frame.pack(fill=tk.BOTH, expand=True)
            self.status_label.config(text=f"Подключен как {nickname}")
            # Поток приема сообщений
            thread = threading.Thread(target=self.receive_messages, daemon=True)
            thread.start()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
    
    def receive_messages(self):
        while self.connected:
            try:
                msg = self.client_socket.recv(4096).decode('utf-8')
                if not msg:
                    break
                # Пробуем распарсить JSON (для приватных сообщений и файлов)
                if msg.startswith('{'):
                    data = json.loads(msg)
                    if data['type'] == 'private':
                        self.text_area.config(state=tk.NORMAL)
                        self.text_area.insert(tk.END, f"[→ Приват от {data['from']}]: {data['text']}\n", "private")
                        self.text_area.config(state=tk.DISABLED)
                        self.text_area.see(tk.END)
                    elif data['type'] == 'file':
                        # предложить сохранить файл
                        self.save_file_prompt(data['filename'], data['data'], data['from'])
                    else:
                        self.display_message(msg)
                else:
                    self.display_message(msg)
            except:
                break
        self.connected = False
        self.status_label.config(text="Отключен")
    
    def display_message(self, msg):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, msg + "\n")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)
    
    def send_message(self):
        text = self.msg_entry.get().strip()
        if not text:
            return
        # проверка на приватное сообщение: /w ник сообщение
        if text.startswith('/w '):
            parts = text.split(' ', 2)
            if len(parts) >= 3:
                target = parts[1]
                msg_text = parts[2]
                data = json.dumps({'type':'private','nickname':self.nickname,'target':target,'text':msg_text})
                self.client_socket.send(data.encode('utf-8'))
                self.display_message(f"[Вы -> {target} (приват)]: {msg_text}")
            else:
                self.display_message("[Ошибка] Используйте: /w ник сообщение")
        else:
            data = json.dumps({'type':'msg','nickname':self.nickname,'text':text})
            self.client_socket.send(data.encode('utf-8'))
            self.display_message(f"[{self.nickname}]: {text}")
        self.msg_entry.delete(0, tk.END)
    
    def send_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode('utf-8')
        data = json.dumps({'type':'file','nickname':self.nickname,'filename':filename,'data':file_data})
        self.client_socket.send(data.encode('utf-8'))
        self.display_message(f"[{self.nickname}] отправил файл: {filename}")
    
    def save_file_prompt(self, filename, data_b64, from_nick):
        answer = messagebox.askyesno("Получен файл", f"{from_nick} отправил файл '{filename}'. Сохранить?")
        if answer:
            filepath = filedialog.asksaveasfilename(defaultextension="", initialfile=filename)
            if filepath:
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(data_b64))
                self.display_message(f"[Файл сохранён: {filename}]")
    
    def show_users(self):
        # Запрос списка пользователей (можно реализовать через сервер)
        self.display_message("[Инфо] Список пользователей доступен через команду /users")
        # для полноты можно отправить запрос и получить ответ от сервера

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
