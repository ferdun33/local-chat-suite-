<?php
// chat.php - Простейший чат на PHP (обмен через файл)
session_start();
$chatFile = 'chat_log.txt';
$usersFile = 'users.txt';
$maxLines = 200;

// Обработка AJAX запросов
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_SERVER['HTTP_X_REQUESTED_WITH'])) {
    header('Content-Type: application/json');
    $action = $_POST['action'] ?? '';
    if ($action === 'send') {
        $nick = $_SESSION['nick'] ?? 'Anon';
        $msg = htmlspecialchars($_POST['message']);
        $line = date('H:i:s') . " [$nick]: $msg" . PHP_EOL;
        $lines = file($chatFile, FILE_IGNORE_NEW_LINES) ?: [];
        array_unshift($lines, trim($line));
        if (count($lines) > $maxLines) $lines = array_slice($lines, 0, $maxLines);
        file_put_contents($chatFile, implode(PHP_EOL, $lines));
        echo json_encode(['status'=>'ok']);
    } elseif ($action === 'poll') {
        $lastCount = (int)$_POST['lastCount'];
        $lines = file($chatFile, FILE_IGNORE_NEW_LINES) ?: [];
        $newLines = array_slice($lines, 0, $maxLines);
        if (count($newLines) > $lastCount) {
            $new = array_slice($newLines, 0, $lastCount - count($newLines));
            echo json_encode(['messages'=>array_reverse($new), 'count'=>count($newLines)]);
        } else {
            echo json_encode(['messages'=>[], 'count'=>count($newLines)]);
        }
    } elseif ($action === 'login') {
        $nick = $_POST['nick'];
        $_SESSION['nick'] = $nick;
        // обновить список пользователей
        $users = file($usersFile, FILE_IGNORE_NEW_LINES) ?: [];
        if (!in_array($nick, $users)) {
            $users[] = $nick;
            file_put_contents($usersFile, implode(PHP_EOL, $users));
        }
        echo json_encode(['status'=>'ok']);
    } elseif ($action === 'users') {
        $users = file($usersFile, FILE_IGNORE_NEW_LINES) ?: [];
        echo json_encode(['users'=>$users]);
    }
    exit;
}
// При первом входе
if (!isset($_SESSION['nick'])) {
    echo '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Чат PHP</title></head><body>
    <form method="post" action=""><input type="text" name="nick" placeholder="Ваш ник" required><button>Войти</button></form></body></html>';
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['nick'])) {
        session_start();
        $_SESSION['nick'] = $_POST['nick'];
        header('Location: chat.php');
    }
    exit;
}
$nick = $_SESSION['nick'];
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Чат на PHP</title>
    <style>
        body { font-family: Arial; background: #1e2a3a; margin:0; padding:20px; }
        .chat { max-width: 800px; margin:auto; background: white; border-radius: 16px; overflow: hidden; }
        .messages { height: 500px; overflow-y: auto; background: #fef9e8; padding: 10px; display: flex; flex-direction: column-reverse; }
        .msg { padding: 5px 10px; border-bottom: 1px solid #ddd; }
        .input-area { display: flex; padding: 10px; background: #ecf0f1; }
        .input-area input { flex:1; padding: 8px; border-radius: 20px; border:1px solid #ccc; }
        .input-area button { margin-left: 10px; padding: 8px 20px; background: #2ecc71; border: none; border-radius: 20px; color:white; cursor:pointer; }
        .sidebar { position: fixed; right: 20px; top: 20px; background: #2c3e50; color: white; padding: 10px; border-radius: 10px; width: 150px; }
    </style>
</head>
<body>
<div class="sidebar" id="usersList">Пользователи:<br></div>
<div class="chat">
    <div class="messages" id="messages"></div>
    <div class="input-area">
        <input type="text" id="messageInput" placeholder="Введите сообщение... /w ник сообщение для приватного">
        <button id="sendBtn">Отправить</button>
    </div>
</div>
<script>
    let lastCount = 0;
    let nickname = "<?= htmlspecialchars($nick) ?>";
    function loadMessages() {
        fetch('chat.php', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'},
            body: 'action=poll&lastCount=' + lastCount
        }).then(res => res.json()).then(data => {
            if (data.messages && data.messages.length) {
                const container = document.getElementById('messages');
                for (let msg of data.messages) {
                    const div = document.createElement('div');
                    div.className = 'msg';
                    div.innerText = msg;
                    container.appendChild(div);
                }
                lastCount = data.count;
            }
            setTimeout(loadMessages, 1000);
        });
    }
    function sendMessage() {
        let msg = document.getElementById('messageInput').value;
        if (!msg) return;
        fetch('chat.php', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'},
            body: 'action=send&message=' + encodeURIComponent(msg)
        }).then(() => {
            document.getElementById('messageInput').value = '';
            loadMessages(); // immediate refresh
        });
    }
    function loadUsers() {
        fetch('chat.php', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'},
            body: 'action=users'
        }).then(res => res.json()).then(data => {
            let html = 'Пользователи:<br>';
            data.users.forEach(u => html += u + '<br>');
            document.getElementById('usersList').innerHTML = html;
        });
    }
    document.getElementById('sendBtn').onclick = sendMessage;
    document.getElementById('messageInput').addEventListener('keypress', (e) => { if(e.key === 'Enter') sendMessage(); });
    loadMessages();
    setInterval(loadUsers, 5000);
    loadUsers();
</script>
</body>
</html>
