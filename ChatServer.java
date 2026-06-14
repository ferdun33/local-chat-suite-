// ChatServer.java - Сервер чата на Java (ServerSocket)
import java.io.*;
import java.net.*;
import java.util.*;

public class ChatServer {
    private static Set<ClientHandler> clients = new HashSet<>();
    public static void main(String[] args) throws IOException {
        ServerSocket serverSocket = new ServerSocket(5555);
        System.out.println("Сервер запущен на порту 5555");
        while (true) {
            Socket socket = serverSocket.accept();
            ClientHandler handler = new ClientHandler(socket);
            clients.add(handler);
            handler.start();
        }
    }
    static void broadcast(String message, ClientHandler exclude) {
        for (ClientHandler client : clients) {
            if (client != exclude) {
                client.sendMessage(message);
            }
        }
    }
    static void removeClient(ClientHandler client) {
        clients.remove(client);
        broadcast("SERVER: " + client.getNickname() + " покинул чат", null);
    }
}

class ClientHandler extends Thread {
    private Socket socket;
    private BufferedReader in;
    private PrintWriter out;
    private String nickname;
    public ClientHandler(Socket socket) {
        this.socket = socket;
    }
    public void run() {
        try {
            in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            out = new PrintWriter(socket.getOutputStream(), true);
            out.println("NICK");
            nickname = in.readLine();
            System.out.println(nickname + " подключился");
            ChatServer.broadcast("SERVER: " + nickname + " присоединился к чату", this);
            String inputLine;
            while ((inputLine = in.readLine()) != null) {
                if (inputLine.startsWith("/w ")) {
                    String[] parts = inputLine.split(" ", 3);
                    if (parts.length >= 3) {
                        String target = parts[1];
                        String msg = parts[2];
                        sendPrivate(target, msg);
                    } else {
                        out.println("SYSTEM: Используйте /w ник сообщение");
                    }
                } else {
                    ChatServer.broadcast(nickname + ": " + inputLine, this);
                }
            }
        } catch (IOException e) {
            System.out.println("Ошибка: " + e.getMessage());
        } finally {
            try { socket.close(); } catch (IOException e) {}
            ChatServer.removeClient(this);
        }
    }
    private void sendPrivate(String target, String msg) {
        for (ClientHandler client : ChatServer.clients) {
            if (client.getNickname().equals(target)) {
                client.sendMessage("[Приват от " + nickname + "]: " + msg);
                this.sendMessage("[Приват для " + target + "]: " + msg);
                return;
            }
        }
        this.sendMessage("SYSTEM: Пользователь " + target + " не найден");
    }
    public void sendMessage(String msg) { out.println(msg); }
    public String getNickname() { return nickname; }
}
