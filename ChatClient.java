// ChatClient.java - Клиент чата на Java (Swing)
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.net.Socket;

public class ChatClient extends JFrame {
    private JTextArea textArea;
    private JTextField inputField;
    private PrintWriter out;
    private BufferedReader in;
    private String nickname;
    public ChatClient() {
        setTitle("Локальный чат - Java");
        setSize(500, 400);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        textArea = new JTextArea();
        textArea.setEditable(false);
        add(new JScrollPane(textArea), BorderLayout.CENTER);
        inputField = new JTextField();
        inputField.addActionListener(e -> sendMessage());
        add(inputField, BorderLayout.SOUTH);
        // подключение
        nickname = JOptionPane.showInputDialog("Введите ник:");
        if (nickname == null) System.exit(0);
        try {
            Socket socket = new Socket("127.0.0.1", 5555);
            in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            out = new PrintWriter(socket.getOutputStream(), true);
            // ожидание запроса ника
            String serverMsg = in.readLine();
            if ("NICK".equals(serverMsg)) {
                out.println(nickname);
            }
            new Thread(this::receiveMessages).start();
        } catch (IOException e) {
            JOptionPane.showMessageDialog(this, "Ошибка подключения");
            System.exit(1);
        }
        setVisible(true);
    }
    private void receiveMessages() {
        try {
            String msg;
            while ((msg = in.readLine()) != null) {
                final String m = msg;
                SwingUtilities.invokeLater(() -> textArea.append(m + "\n"));
            }
        } catch (IOException e) {}
    }
    private void sendMessage() {
        String msg = inputField.getText().trim();
        if (msg.isEmpty()) return;
        out.println(msg);
        inputField.setText("");
    }
    public static void main(String[] args) {
        new ChatClient();
    }
}
