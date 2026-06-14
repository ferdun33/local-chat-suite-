// main.go - Чат на Go с WebSocket (gorilla/websocket)
package main

import (
    "encoding/json"
    "log"
    "net/http"
    "sync"

    "github.com/gorilla/websocket"
)

type Message struct {
    Type     string `json:"type"`
    Nickname string `json:"nickname,omitempty"`
    Text     string `json:"text,omitempty"`
    Target   string `json:"target,omitempty"`
    Filename string `json:"filename,omitempty"`
    Data     string `json:"data,omitempty"`
    From     string `json:"from,omitempty"`
    Users    []string `json:"users,omitempty"`
}

var clients = make(map[*websocket.Conn]string)
var mu sync.Mutex
var upgrader = websocket.Upgrader{
    CheckOrigin: func(r *http.Request) bool { return true },
}

func broadcastSystem(msg string) {
    mu.Lock()
    defer mu.Unlock()
    for conn := range clients {
        conn.WriteJSON(Message{Type: "system", Text: msg})
    }
}

func broadcastUsers() {
    mu.Lock()
    defer mu.Unlock()
    var users []string
    for _, nick := range clients {
        users = append(users, nick)
    }
    for conn := range clients {
        conn.WriteJSON(Message{Type: "users", Users: users})
    }
}

func handleWebSocket(w http.ResponseWriter, r *http.Request) {
    conn, err := upgrader.Upgrade(w, r, nil)
    if err != nil {
        log.Print(err)
        return
    }
    defer conn.Close()
    var nickname string
    for {
        var msg Message
        err := conn.ReadJSON(&msg)
        if err != nil {
            break
        }
        if msg.Type == "join" {
            nickname = msg.Nickname
            mu.Lock()
            clients[conn] = nickname
            mu.Unlock()
            broadcastSystem(nickname + " присоединился к чату")
            broadcastUsers()
        } else if msg.Type == "message" {
            broadcastMessage(msg.Text, nickname)
        } else if msg.Type == "private" {
            targetNick := msg.Target
            mu.Lock()
            var targetConn *websocket.Conn
            for conn2, nick := range clients {
                if nick == targetNick {
                    targetConn = conn2
                    break
                }
            }
            mu.Unlock()
            if targetConn != nil {
                targetConn.WriteJSON(Message{Type: "private", From: nickname, Text: msg.Text})
                conn.WriteJSON(Message{Type: "private", From: "Вы", Text: "[" + targetNick + "]: " + msg.Text})
            } else {
                conn.WriteJSON(Message{Type: "system", Text: "Пользователь " + targetNick + " не найден"})
            }
        } else if msg.Type == "file" {
            mu.Lock()
            for conn2 := range clients {
                if conn2 != conn {
                    conn2.WriteJSON(Message{Type: "file", From: nickname, Filename: msg.Filename, Data: msg.Data})
                }
            }
            mu.Unlock()
            conn.WriteJSON(Message{Type: "system", Text: "Файл отправлен"})
        } else if msg.Type == "getUsers" {
            broadcastUsers()
        }
    }
    // clean up
    mu.Lock()
    delete(clients, conn)
    mu.Unlock()
    if nickname != "" {
        broadcastSystem(nickname + " покинул чат")
        broadcastUsers()
    }
}

func broadcastMessage(text, sender string) {
    mu.Lock()
    defer mu.Unlock()
    for conn := range clients {
        conn.WriteJSON(Message{Type: "message", Nickname: sender, Text: text})
    }
}

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        http.ServeFile(w, r, "chat.html") // используем тот же HTML, что и в JS версии
    })
    http.HandleFunc("/ws", handleWebSocket)
    log.Println("Сервер запущен на http://localhost:8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
