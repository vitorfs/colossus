-- KumoMTA Production Configuration
local kumo = require 'kumo'

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
        max_segment_duration = '1 minute',
    }
end)

kumo.on('get_egress_source', function(source_name)
    return kumo.make_egress_source {
        name = source_name,
    }
end)

kumo.on('get_queue_config', function(domain, tenant, campaign, routing_domain)
    return kumo.make_queue_config {
        max_age = '24 hours',
        retry_interval = '5 minutes',
        max_retry_interval = '20 minutes',
    }
end)

-- РЕАЛЬНАЯ ОТПРАВКА ПИСЕМ (а не только тестирование)
kumo.on('smtp_server_message_received', function(msg)
    msg:set_meta('queue', 'default')
end)
