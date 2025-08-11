<?php
// Same app as emulated variant, but container sets PDO_EMULATE=0
declare(strict_types=1);

function json_response($data, int $status = 200): void {
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($data, JSON_PRETTY_PRINT);
}

function get_pdo(): PDO {
    $host = getenv('DB_HOST') ?: 'db';
    $db   = getenv('DB_NAME') ?: 'demo';
    $user = getenv('DB_USER') ?: 'app';
    $pass = getenv('DB_PASS') ?: 'apppass';
    $dsn = "mysql:host={$host};dbname={$db};charset=utf8mb4";
    $pdo = new PDO($dsn, $user, $pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    ]);
    $emulate = getenv('PDO_EMULATE');
    $emulate = $emulate !== false ? (bool)intval($emulate) : false; // default false here
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, $emulate);
    return $pdo;
}

function route(): void {
    $uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
    if ($uri === '/health') {
        $pdo = get_pdo();
        $ok = $pdo->getAttribute(PDO::ATTR_EMULATE_PREPARES) ? 'emulate' : 'native';
        json_response([ 'ok' => true, 'pdo' => $ok ]);
        return;
    }
    if ($uri === '/safe') { safe_handler(); return; }
    if ($uri === '/vuln') { vuln_handler(); return; }
    json_response([ 'error' => 'not found' ], 404);
}

function safe_handler(): void {
    $pdo = get_pdo();
    $name = $_GET['name'] ?? '';
    $col = $_GET['col'] ?? 'name';
    $allowed = ['id', 'name', 'color', 'price'];
    if (!in_array($col, $allowed, true)) { json_response(['error' => 'invalid column'], 400); return; }
    $sql = "SELECT `$col` FROM fruit WHERE name = :name";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([':name' => $name]);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    json_response(['mode' => $pdo->getAttribute(PDO::ATTR_EMULATE_PREPARES) ? 'emulate' : 'native', 'rows' => $rows]);
}

function vuln_handler(): void {
    $pdo = get_pdo();
    $name = $_GET['name'] ?? '';
    $col = $_GET['col'] ?? 'name';
    $sanitized = str_replace('`', '``', (string)$col);
    $sql = "SELECT `{$sanitized}` FROM fruit WHERE name = ?";
    try {
        $stmt = $pdo->prepare($sql);
        $stmt->execute([$name]);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        json_response(['mode' => $pdo->getAttribute(PDO::ATTR_EMULATE_PREPARES) ? 'emulate' : 'native', 'query' => $sql, 'rows' => $rows]);
    } catch (Throwable $e) {
        json_response(['mode' => $pdo->getAttribute(PDO::ATTR_EMULATE_PREPARES) ? 'emulate' : 'native', 'query' => $sql, 'error' => $e->getMessage()], 500);
    }
}

route();


