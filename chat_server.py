# chat_server.py - Сервер локального чата на Python (сокеты, threading)
import socket
import threading
import json
import time

class ChatServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.clients = []
        self.nicknames = []
        print(f"[SERVER] Запущен на {host}:{port}")

    def broadcast(self, message, sender_socket=None):
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    self.remove_client(client)

    def remove_client(self, client):
        if client in self.clients:
            idx = self.clients.index(client)
            self.clients.remove(client)
            nickname = self.nicknames.pop(idx)
            self.broadcast(f"[SERVER] {nickname} покинул чат")
            print(f"[SERVER] {nickname} отключился")

    def handle_client(self, client):
        while True:
            try:
                msg = client.recv(1024).decode('utf-8')
                if not msg:
                    break
                data = json.loads(msg)
                if data['type'] == 'msg':
                    formatted = f"[{data['nickname']}]: {data['text']}"
                    print(formatted)
                    self.broadcast(formatted, client)
                elif data['type'] == 'private':
                    target_nick = data['target']
                    # найти клиента по нику
                    for i, nick in enumerate(self.nicknames):
                        if nick == target_nick:
                            self.clients[i].send(json.dumps({'type':'private','from':data['nickname'],'text':data['text']}).encode())
                            break
                elif data['type'] == 'file':
                    # отправка файла (base64)
                    self.broadcast(f"[FILE] {data['nickname']} отправил файл: {data['filename']}", client)
                    for i, nick in enumerate(self.nicknames):
                        if nick == data['nickname']: continue
                        self.clients[i].send(json.dumps({'type':'file','from':data['nickname'],'filename':data['filename'],'data':data['data']}).encode())
            except:
                self.remove_client(client)
                break

    def start(self):
        while True:
            client, addr = self.server.accept()
            print(f"[SERVER] Подключен {addr}")
            client.send("NICK".encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            self.nicknames.append(nickname)
            self.clients.append(client)
            self.broadcast(f"[SERVER] {nickname} присоединился к чату")
            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.start()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
