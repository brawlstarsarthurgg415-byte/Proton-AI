<?php
declare(strict_types=1);

// Minimal read-only health endpoint for a future Proton web adapter.
header('Content-Type: application/json; charset=utf-8');
echo json_encode([
    'name' => 'Proton-AI',
    'component' => 'php-web-adapter',
    'status' => 'prototype',
    'writes_data' => false,
], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
