<?php
declare(strict_types=1);

/**
 * Read-only status endpoint for the Proton-AI adapter.
 * It deliberately exposes no filesystem paths, secrets, or environment values.
 */
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function componentStatus(string $name, string $state, bool $ready): array
{
    return [
        'name' => $name,
        'state' => $state,
        'ready' => $ready,
    ];
}

function buildStatus(): array
{
    $checks = [
        componentStatus('php-web-adapter', 'prototype', true),
        componentStatus('neural-runtime', 'not-connected', false),
        componentStatus('terminal-core', 'separate-process', false),
    ];

    $readyCount = count(array_filter($checks, static fn(array $item): bool => $item['ready']));
    return [
        'name' => 'Proton-AI',
        'version' => '0.4.0',
        'status' => $readyCount === count($checks) ? 'ready' : 'prototype',
        'read_only' => true,
        'writes_data' => false,
        'components' => $checks,
        'summary' => [
            'components' => count($checks),
            'ready' => $readyCount,
            'pending' => count($checks) - $readyCount,
        ],
    ];
}

try {
    http_response_code(200);
    echo json_encode(
        buildStatus(),
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR
    );
} catch (JsonException $error) {
    http_response_code(500);
    echo '{"name":"Proton-AI","status":"error","message":"Unable to encode status"}';
}
