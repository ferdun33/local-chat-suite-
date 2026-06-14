// server.js - WebSocket сервер для чата на Node.js (ws)
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });
let clients = new Map(); // socket -> nickname

wss.on('connection', (ws) => {
    ws.on('message', (data) => {
        const msg = JSON.parse(data);
        if (msg.type === 'join') {
            clients.set(ws, msg.nickname);
            broadcastSystem(`${msg.nickname} присоединился к чату`);
            broadcastUsers();
        } else if (msg.type === 'message') {
            broadcastMessage(msg.text, clients.get(ws));
        } else if (msg.type === 'private') {
            const targetNick = msg.target;
            let targetSocket = null;
            for (let [socket, nick] of clients.entries()) {
                if (nick === targetNick) targetSocket = socket;
            }
            if (targetSocket) {
                targetSocket.send(JSON.stringify({ type: 'private', from: clients.get(ws), text: msg.text }));
                ws.send(JSON.stringify({ type: 'private', from: 'Вы', text: `[${targetNick}]: ${msg.text}` }));
            } else {
                ws.send(JSON.stringify({ type: 'system', text: `Пользователь ${targetNick} не найден` }));
            }
        } else if (msg.type === 'file') {
            // рассылаем всем, кроме отправителя
            for (let [socket, nick] of clients.entries()) {
                if (socket !== ws) {
                    socket.send(JSON.stringify({ type: 'file', from: clients.get(ws), filename: msg.filename, data: msg.data }));
                }
            }
            ws.send(JSON.stringify({ type: 'system', text: `Файл ${msg.filename} отправлен` }));
        } else if (msg.type === 'getUsers') {
            const users = Array.from(clients.values());
            ws.send(JSON.stringify({ type: 'users', users: users }));
        }
    });
    ws.on('close', () => {
        const nickname = clients.get(ws);
        if (nickname) {
            clients.delete(ws);
            broadcastSystem(`${nickname} покинул чат`);
            broadcastUsers();
        }
    });
});

function broadcastMessage(text, senderNick) {
    const message = JSON.stringify({ type: 'message', nickname: senderNick, text: text });
    for (let client of clients.keys()) {
        client.send(message);
    }
}
function broadcastSystem(text) {
    for (let client of clients.keys()) {
        client.send(JSON.stringify({ type: 'system', text: text }));
    }
}
function broadcastUsers() {
    const users = Array.from(clients.values());
    const userMsg = JSON.stringify({ type: 'users', users: users });
    for (let client of clients.keys()) {
        client.send(userMsg);
    }
}
console.log("WebSocket сервер запущен на ws://localhost:8080");
