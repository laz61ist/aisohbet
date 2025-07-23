<?php
header('Content-Type: application/json');

// Veritabanı bağlantısı
function getDbConnection() {
    $host = 'localhost';
    $dbname = 'aisohbet_db';
    $user = 'root';
    $pass = ''; // XAMPP varsayılan şifresi boştur

    try {
        $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $user, $pass);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $pdo;
    } catch (PDOException $e) {
        // Veritabanı yoksa oluştur
        if ($e->getCode() == 1049) {
            try {
                $pdo = new PDO("mysql:host=$host;charset=utf8mb4", $user, $pass);
                $pdo->exec("CREATE DATABASE `$dbname` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;");
                $pdo->exec("USE `$dbname`;");

                // Tabloları oluştur
                $pdo->exec("
                    CREATE TABLE `chats` (
                      `id` int(11) NOT NULL AUTO_INCREMENT,
                      `title` varchar(255) NOT NULL,
                      `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                      PRIMARY KEY (`id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                ");

                $pdo->exec("
                    CREATE TABLE `messages` (
                      `id` int(11) NOT NULL AUTO_INCREMENT,
                      `chat_id` int(11) NOT NULL,
                      `role` varchar(50) NOT NULL,
                      `content` text NOT NULL,
                      `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                      PRIMARY KEY (`id`),
                      KEY `chat_id` (`chat_id`),
                      CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`chat_id`) REFERENCES `chats` (`id`) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                ");
                return $pdo;
            } catch (PDOException $ex) {
                http_response_code(500);
                die(json_encode(['error' => 'Veritabanı ve tablolar oluşturulamadı: ' . $ex->getMessage()]));
            }
        }
        http_response_code(500);
        die(json_encode(['error' => 'Veritabanı bağlantı hatası: ' . $e->getMessage()]));
    }
}

$action = $_GET['action'] ?? '';
$data = json_decode(file_get_contents('php://input'), true);
$pdo = getDbConnection();

switch ($action) {
    case 'getChats':
        $stmt = $pdo->query("SELECT id, title FROM chats ORDER BY created_at DESC");
        echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));
        break;

    case 'getMessages':
        $chatId = $data['chatId'] ?? 0;
        $stmt = $pdo->prepare("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY timestamp ASC");
        $stmt->execute([$chatId]);
        echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));
        break;

    case 'createChat':
        $title = $data['title'] ?? 'Yeni Sohbet';
        $stmt = $pdo->prepare("INSERT INTO chats (title) VALUES (?)");
        $stmt->execute([$title]);
        echo json_encode(['chatId' => $pdo->lastInsertId()]);
        break;

    case 'sendMessage':
        $chatId = $data['chatId'] ?? 0;
        $userMessage = $data['message'] ?? '';

        if (empty($chatId) || empty($userMessage)) {
            http_response_code(400);
            echo json_encode(['error' => 'Eksik parametreler.']);
            exit;
        }

        // 1. Kullanıcı mesajını veritabanına kaydet
        $stmt = $pdo->prepare("INSERT INTO messages (chat_id, role, content) VALUES (?, 'user', ?)");
        $stmt->execute([$chatId, $userMessage]);

        // 2. Son 10 mesajı (bağlam için) al
        $stmt = $pdo->prepare("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY timestamp DESC LIMIT 10");
        $stmt->execute([$chatId]);
        $history = array_reverse($stmt->fetchAll(PDO::FETCH_ASSOC)); // kronolojik sıraya koy

        // Python script'ine göndermek için veri hazırla
        $requestPayload = json_encode([
            'current_message' => $userMessage,
            'history' => $history
        ]);

        // 3. AI servisini çağır
        // Güvenlik için komut satırı argümanını base64 ile kodla
        $escaped_payload = base64_encode($requestPayload);
        $command = "python ai_service.py " . $escaped_payload;

        // Timeout ve hata yönetimi için proc_open kullanımı
        $descriptorspec = [
           0 => ["pipe", "r"],  // stdin
           1 => ["pipe", "w"],  // stdout
           2 => ["pipe", "w"]   // stderr
        ];
        $process = proc_open($command, $descriptorspec, $pipes);

        $aiResponseJson = null;
        $errorOutput = null;

        if (is_resource($process)) {
            // Script'e veri göndermiyoruz (stdin kapalı)
            fclose($pipes[0]);

            // Çıktıyı oku (timeout ile)
            $stdout_handle = $pipes[1];
            $stderr_handle = $pipes[2];
            stream_set_blocking($stdout_handle, false);
            stream_set_blocking($stderr_handle, false);

            $timeout = 30; // 30 saniye
            $start_time = time();

            while( (time() - $start_time) < $timeout && !feof($stdout_handle) && !feof($stderr_handle) ) {
                $aiResponseJson .= fgets($stdout_handle);
                $errorOutput .= fgets($stderr_handle);
                usleep(100000); // 0.1 saniye bekle
            }

            if( (time() - $start_time) >= $timeout){
                 $errorOutput = "Timeout: AI servisi 30 saniyeden uzun sürdü.";
                 proc_terminate($process); // işlemi sonlandır
            }

            fclose($stdout_handle);
            fclose($stderr_handle);
            proc_close($process);
        }

        if (!empty($errorOutput)) {
            $aiResponseJson = json_encode(['error' => "AI Servis Hatası: " . trim($errorOutput)]);
        }

        // 4. AI cevabını veritabanına kaydet
        $stmt = $pdo->prepare("INSERT INTO messages (chat_id, role, content) VALUES (?, 'ai', ?)");
        $stmt->execute([$chatId, $aiResponseJson]);

        // 5. AI cevabını frontend'e gönder
        echo $aiResponseJson;
        break;

    default:
        http_response_code(404);
        echo json_encode(['error' => 'Geçersiz eylem.']);
        break;
}
?>
