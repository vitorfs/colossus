-- KumoMTA Production Configuration с правильной обработкой доменов
local kumo = require 'kumo'

-- ВКЛЮЧАЕМ ПОДРОБНОЕ ЛОГИРОВАНИЕ ДЛЯ ДИАГНОСТИКИ
kumo.set_diagnostic_log_filter 'kumod=debug,kumo_server_memory=info'

kumo.on('init', function()
    kumo.define_spool {
        name = 'meta',
        path = '/var/spool/kumomta/meta',
        kind = 'RocksDB',
    }

    kumo.define_spool {
        name = 'data',
        path = '/var/spool/kumomta/data',
        kind = 'RocksDB',
    }

    -- SMTP Listener для приема от Django
    kumo.start_esmtp_listener {
        listen = '0.0.0.0:25',
        hostname = 'sugarsending.com',
        relay_hosts = { '127.0.0.1', '172.16.0.0/12', '192.168.0.0/16' },
    }

    kumo.start_http_listener {
        listen = '0.0.0.0:8000',
        trusted_hosts = { '127.0.0.1', '172.16.0.0/12' },
    }

    kumo.configure_local_logs {
        log_dir = '/var/log/kumomta',
        max_segment_duration = '10 seconds',
    }
end)

-- Настройка egress source
kumo.on('get_egress_source', function(source_name)
    print(string.format('DEBUG: get_egress_source called with source_name=%s', source_name))
    return kumo.make_egress_source {
        name = source_name,
        ehlo_domain = 'sugarsending.com',
    }
end)

-- Настройка egress pool
kumo.on('get_egress_pool', function(pool_name)
    print(string.format('DEBUG: get_egress_pool called with pool_name=%s', pool_name))
    return kumo.make_egress_pool {
        name = pool_name,
        entries = {
            { name = 'default-source' }
        }
    }
end)

-- Конфигурация очередей
kumo.on('get_queue_config', function(domain, tenant, campaign, routing_domain)
    print(string.format('DEBUG: get_queue_config called for domain=%s, tenant=%s', domain, tenant or 'nil'))
    return kumo.make_queue_config {
        max_age = '24 hours',
        retry_interval = '5 minutes',
        max_retry_interval = '20 minutes',
        egress_pool = 'default-pool',
    }
end)

-- Функция настройки путей доставки
kumo.on('get_egress_path_config', function(domain, source_name, site_name)
    print(string.format('DEBUG: get_egress_path_config called for domain=%s, source=%s, site=%s',
        domain, source_name, site_name))
    return kumo.make_egress_path {
        connection_limit = 10,
        max_message_rate = '100/hr',
        enable_tls = 'Opportunistic',
        smtp_port = 25,
    }
end)

-- ИСПРАВЛЕННАЯ обработка принятых писем
kumo.on('smtp_server_message_received', function(msg)
    local recipient_domain = msg:recipient().domain
    print(string.format('DEBUG: Message received from %s to %s (domain: %s)',
        msg:from_header().email,
        msg:recipient().email,
        recipient_domain))

    -- НЕ устанавливаем queue в 'default'!
    -- KumoMTA автоматически использует домен получателя
    -- msg:set_meta('queue', 'default') -- УБИРАЕМ ЭТУ СТРОКУ!
end)
