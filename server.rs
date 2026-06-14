// server.rs - Асинхронный WebSocket сервер на Rust (tokio + tungstenite)
// Добавьте зависимости в Cargo.toml:
// [dependencies]
// tokio = { version = "1", features = ["full"] }
// tungstenite = "0.20"
// futures-util = "0.3"
// serde = { version = "1", features = ["derive"] }
// serde_json = "1"

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::net::{TcpListener, TcpStream};
use tungstenite::protocol::Message;
use tungstenite::accept;
use futures_util::{SinkExt, StreamExt};
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
enum ChatMessage {
    Join { nickname: String },
    Message { text: String, nickname: String },
    Private { target: String, text: String, from: String },
    File { filename: String, data: String, from: String },
    System { text: String },
    Users { users: Vec<String> },
}

type Clients = Arc<Mutex<HashMap<String, tokio::sync::mpsc::UnboundedSender<Message>>>>;

#[tokio::main]
async fn main() {
    let addr = "127.0.0.1:8080";
    let listener = TcpListener::bind(addr).await.expect("Failed to bind");
    println!("WebSocket сервер запущен на ws://{}", addr);
    let clients: Clients = Arc::new(Mutex::new(HashMap::new()));
    while let Ok((stream, _)) = listener.accept().await {
        let clients = clients.clone();
        tokio::spawn(handle_connection(stream, clients));
    }
}

async fn handle_connection(stream: TcpStream, clients: Clients) {
    let ws_stream = accept(stream).await.unwrap();
    let (mut sender, mut receiver) = ws_stream.split();
    let (tx, mut rx) = tokio::sync::mpsc::unbounded_channel();
    let mut nickname = String::new();
    // Задача отправки сообщений клиенту
    tokio::spawn(async move {
        while let Some(msg) = rx.recv().await {
            if sender.send(msg).await.is_err() { break; }
        }
    });
    // Прием сообщений от клиента
    while let Some(Ok(msg)) = receiver.next().await {
        if let Ok(text) = msg.to_text() {
            if let Ok(chat_msg) = serde_json::from_str::<ChatMessage>(text) {
                match chat_msg {
                    ChatMessage::Join { nickname: nick } => {
                        nickname = nick.clone();
                        clients.lock().await.insert(nickname.clone(), tx.clone());
                        broadcast_system(&clients, format!("{} присоединился", nickname).as_str()).await;
                        broadcast_users(&clients).await;
                    }
                    ChatMessage::Message { text, nickname: _ } => {
                        broadcast_message(&clients, &nickname, &text).await;
                    }
                    ChatMessage::Private { target, text, from: _ } => {
                        let mut clients_guard = clients.lock().await;
                        if let Some(target_tx) = clients_guard.get(&target) {
                            let _ = target_tx.send(Message::text(serde_json::to_string(&ChatMessage::Private { from: nickname.clone(), text: text.clone(), target: "".to_string() }).unwrap()));
                            let _ = tx.send(Message::text(serde_json::to_string(&ChatMessage::System { text: format!("[Вы -> {}]: {}", target, text) }).unwrap()));
                        } else {
                            let _ = tx.send(Message::text(serde_json::to_string(&ChatMessage::System { text: format!("Пользователь {} не найден", target) }).unwrap()));
                        }
                    }
                    ChatMessage::File { filename, data, from: _ } => {
                        broadcast_file(&clients, &nickname, &filename, &data).await;
                    }
                    _ => {}
                }
            }
        }
    }
    // удаление при разрыве
    clients.lock().await.remove(&nickname);
    broadcast_system(&clients, format!("{} покинул чат", nickname).as_str()).await;
    broadcast_users(&clients).await;
}

async fn broadcast_message(clients: &Clients, sender: &str, text: &str) {
    let msg = ChatMessage::Message { nickname: sender.to_string(), text: text.to_string() };
    let json = serde_json::to_string(&msg).unwrap();
    let clients_guard = clients.lock().await;
    for (_, tx) in clients_guard.iter() {
        let _ = tx.send(Message::text(json.clone()));
    }
}
async fn broadcast_system(clients: &Clients, text: &str) {
    let msg = ChatMessage::System { text: text.to_string() };
    let json = serde_json::to_string(&msg).unwrap();
    let clients_guard = clients.lock().await;
    for (_, tx) in clients_guard.iter() {
        let _ = tx.send(Message::text(json.clone()));
    }
}
async fn broadcast_users(clients: &Clients) {
    let users: Vec<String> = clients.lock().await.keys().cloned().collect();
    let msg = ChatMessage::Users { users };
    let json = serde_json::to_string(&msg).unwrap();
    let clients_guard = clients.lock().await;
    for (_, tx) in clients_guard.iter() {
        let _ = tx.send(Message::text(json.clone()));
    }
}
async fn broadcast_file(clients: &Clients, sender: &str, filename: &str, data: &str) {
    let msg = ChatMessage::File { from: sender.to_string(), filename: filename.to_string(), data: data.to_string() };
    let json = serde_json::to_string(&msg).unwrap();
    let clients_guard = clients.lock().await;
    for (nick, tx) in clients_guard.iter() {
        if nick != sender {
            let _ = tx.send(Message::text(json.clone()));
        }
    }
}
