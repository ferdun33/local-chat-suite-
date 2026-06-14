// ChatForm.cs - Локальный чат на C# (встроенный сервер и клиент)
using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Windows.Forms;

public class ChatForm : Form
{
    private ListBox messageList;
    private TextBox inputBox;
    private Button sendBtn;
    private TcpListener server;
    private List<TcpClient> clients = new List<TcpClient>();
    private TcpClient client;
    private NetworkStream stream;
    private StreamReader reader;
    private StreamWriter writer;
    private string nickname;
    private bool isServer = false;

    public ChatForm()
    {
        Text = "Локальный чат C#";
        Size = new System.Drawing.Size(600, 450);
        messageList = new ListBox { Dock = DockStyle.Fill };
        inputBox = new TextBox { Dock = DockStyle.Bottom, Height = 30 };
        sendBtn = new Button { Text = "Отправить", Dock = DockStyle.Bottom, Height = 30 };
        sendBtn.Click += (s, e) => SendMessage();
        inputBox.KeyPress += (s, e) => { if (e.KeyChar == '\r') SendMessage(); };
        Controls.Add(messageList);
        Controls.Add(inputBox);
        Controls.Add(sendBtn);

        var result = MessageBox.Show("Запустить как сервер? (Да - сервер, Нет - клиент)", "Режим", MessageBoxButtons.YesNo);
        if (result == DialogResult.Yes)
        {
            isServer = true;
            StartServer();
            nickname = "Server";
            AppendMessage("Сервер запущен, ожидание клиентов...");
        }
        else
        {
            nickname = Microsoft.VisualBasic.Interaction.InputBox("Введите ник:", "Чат", "User" + new Random().Next(1000));
            ConnectToServer();
        }
    }

    private void StartServer()
    {
        server = new TcpListener(IPAddress.Any, 5555);
        server.Start();
        Thread acceptThread = new Thread(() => {
            while (true)
            {
                var client = server.AcceptTcpClient();
                clients.Add(client);
                var stream = client.GetStream();
                var reader = new StreamReader(stream);
                var writer = new StreamWriter(stream) { AutoFlush = true };
                string nick = reader.ReadLine();
                BroadcastMessage($"SERVER: {nick} присоединился");
                // запуск обработки
                Thread clientThread = new Thread(() => HandleClient(client, reader, writer, nick));
                clientThread.Start();
            }
        });
        acceptThread.IsBackground = true;
        acceptThread.Start();
    }

    private void HandleClient(TcpClient client, StreamReader reader, StreamWriter writer, string nick)
    {
        try
        {
            string line;
            while ((line = reader.ReadLine()) != null)
            {
                if (line.StartsWith("/w "))
                {
                    // приватная отправка
                    var parts = line.Split(' ', 3);
                    if (parts.Length >= 3)
                    {
                        SendPrivate(nick, parts[1], parts[2]);
                    }
                }
                else
                {
                    BroadcastMessage($"{nick}: {line}");
                }
            }
        }
        catch { }
        finally
        {
            clients.Remove(client);
            BroadcastMessage($"SERVER: {nick} покинул чат");
            client.Close();
        }
    }

    private void BroadcastMessage(string msg)
    {
        foreach (var c in clients)
        {
            try
            {
                var writer = new StreamWriter(c.GetStream()) { AutoFlush = true };
                writer.WriteLine(msg);
            }
            catch { }
        }
        AppendMessage(msg);
    }

    private void SendPrivate(string from, string target, string msg)
    {
        foreach (var c in clients)
        {
            try
            {
                var writer = new StreamWriter(c.GetStream()) { AutoFlush = true };
                var reader = new StreamReader(c.GetStream());
                // грубо, но для демо
            }
            catch { }
        }
    }

    private void ConnectToServer()
    {
        try
        {
            client = new TcpClient();
            client.Connect("127.0.0.1", 5555);
            stream = client.GetStream();
            writer = new StreamWriter(stream) { AutoFlush = true };
            reader = new StreamReader(stream);
            writer.WriteLine(nickname);
            Thread receiveThread = new Thread(() => {
                try
                {
                    string msg;
                    while ((msg = reader.ReadLine()) != null)
                    {
                        AppendMessage(msg);
                    }
                }
                catch { }
            });
            receiveThread.IsBackground = true;
            receiveThread.Start();
        }
        catch (Exception ex)
        {
            MessageBox.Show("Не удалось подключиться к серверу");
        }
    }

    private void SendMessage()
    {
        string msg = inputBox.Text.Trim();
        if (string.IsNullOrEmpty(msg)) return;
        if (isServer)
        {
            BroadcastMessage($"{nickname}: {msg}");
        }
        else
        {
            writer.WriteLine(msg);
            AppendMessage($"{nickname}: {msg}");
        }
        inputBox.Clear();
    }

    private void AppendMessage(string msg)
    {
        if (InvokeRequired)
        {
            Invoke(new Action(() => messageList.Items.Add(msg)));
        }
        else
        {
            messageList.Items.Add(msg);
        }
    }
}

static class Program
{
    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.Run(new ChatForm());
    }
}
