CREATE TABLE IF NOT EXISTS tracked_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    category TEXT,
    target_price TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracked_product_id INTEGER,
    product_id TEXT,
    store TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    current_price TEXT NOT NULL,
    original_price TEXT,
    discount_percent TEXT,
    url TEXT NOT NULL,
    image_url TEXT,
    collected_at TEXT NOT NULL,
    FOREIGN KEY (tracked_product_id) REFERENCES tracked_products(id)
);

CREATE INDEX IF NOT EXISTS idx_price_snapshots_lookup
ON price_snapshots(store, product_id, url, collected_at);

CREATE TABLE IF NOT EXISTS alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracked_product_id INTEGER,
    rule_type TEXT NOT NULL,
    threshold TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tracked_product_id) REFERENCES tracked_products(id)
);

CREATE TABLE IF NOT EXISTS alert_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_rule_id INTEGER,
    tracked_product_id INTEGER,
    store TEXT NOT NULL,
    title TEXT NOT NULL,
    current_price TEXT NOT NULL,
    url TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_rule_id) REFERENCES alert_rules(id),
    FOREIGN KEY (tracked_product_id) REFERENCES tracked_products(id)
);
