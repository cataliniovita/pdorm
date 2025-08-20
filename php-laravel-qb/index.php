<?php
// Laravel Query Builder vulnerable example
// Mirrors php-pdo-emulate pattern: identifier interpolation + bound value

use Illuminate\Database\Capsule\Manager as Capsule;

require __DIR__ . '/vendor/autoload.php';

function json_response($data, int $status = 200): void {
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($data, JSON_PRETTY_PRINT);
}

$db = new Capsule();
$db->addConnection([
    'driver' => 'mysql',
    'host' => getenv('DB_HOST') ?: 'db',
    'database' => getenv('DB_NAME') ?: 'demo',
    'username' => getenv('DB_USER') ?: 'app',
    'password' => getenv('DB_PASS') ?: 'apppass',
    'charset' => 'utf8mb4',
    'collation' => 'utf8mb4_unicode_ci',
]);
$db->setAsGlobal();
$db->bootEloquent();

$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);

if ($uri === '/health') {
    try {
        Capsule::select('SELECT 1');
        json_response(['ok' => true]);
    } catch (Throwable $e) {
        json_response(['ok' => false, 'error' => $e->getMessage()], 500);
    }
    exit;
}

if ($uri === '/safe') {
    $name = $_GET['name'] ?? '';
    $col = $_GET['col'] ?? 'name';
    $allowed = ['id','name','color','price'];
    if (!in_array($col, $allowed, true)) {
        json_response(['error' => 'invalid column'], 400); exit;
    }
    // Safe: whitelist identifier; bind value
    $qb = Capsule::table('fruit')
        ->selectRaw("`$col` AS val")
        ->where('name', '=', $name);
    $sql = $qb->toSql();
    $bindings = $qb->getBindings();
    $rows = $qb->get();
    json_response(['sql' => $sql, 'bindings' => $bindings, 'rows' => $rows]);
    exit;
}

if ($uri === '/vuln') {
    $name = $_GET['name'] ?? '';
    $col = (string)($_GET['col'] ?? 'name');
    // VULN: naive backtick escaping of identifier + bound value in where
    $sanitized = str_replace('`', '``', $col);
    try {
        $qb = Capsule::table('fruit')
            ->selectRaw("`$sanitized` AS val")
            ->where('name', '=', $name); // value still bound by QB
        $sql = $qb->toSql();
        $bindings = $qb->getBindings();
        $rows = $qb->get();
        json_response(['sql' => $sql, 'bindings' => $bindings, 'rows' => $rows]);
    } catch (Throwable $e) {
        json_response(['error' => $e->getMessage()], 500);
    }
    exit;
}

json_response(['error' => 'not found'], 404);


