-- AshFash database schema
-- Run: mysql -u root -p ashfash_db < app/db_schema.sql

CREATE TABLE IF NOT EXISTS categories (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    external_id   VARCHAR(100)                          NOT NULL UNIQUE,
    name          VARCHAR(255)                          NOT NULL,
    slug          VARCHAR(255)                          NOT NULL UNIQUE,
    parent_id     INT                                   NULL,
    gender        ENUM('women', 'men', 'unisex', 'kids') NULL,
    is_active     TINYINT(1)                            NOT NULL DEFAULT 1,
    display_order INT                                   NOT NULL DEFAULT 0,
    created_at    TIMESTAMP                             NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP                             NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS products (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    external_id        VARCHAR(100)                          NOT NULL UNIQUE,
    name               VARCHAR(500)                          NOT NULL,
    brand              VARCHAR(200)                          NULL,
    description        TEXT                                  NULL,
    external_url       VARCHAR(1000)                         NULL,
    primary_image_url  VARCHAR(1000)                         NULL,
    price_amount       DECIMAL(10, 2)                        NULL,
    price_currency     VARCHAR(5)                            NOT NULL DEFAULT 'USD',
    sale_price_amount  DECIMAL(10, 2)                        NULL,
    category_id        INT                                   NULL,
    gender             ENUM('women', 'men', 'unisex', 'kids') NULL,
    colour             VARCHAR(100)                          NULL,
    is_active          TINYINT(1)                            NOT NULL DEFAULT 1,
    raw_data           JSON                                  NULL,
    last_synced_at     TIMESTAMP                             NULL,
    view_count         INT                                   NOT NULL DEFAULT 0,
    created_at         TIMESTAMP                             NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP                             NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FULLTEXT INDEX ft_products_search (name, brand, description)
);

CREATE TABLE IF NOT EXISTS product_images (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    product_id    INT           NOT NULL,
    image_url     VARCHAR(1000) NOT NULL,
    is_primary    TINYINT(1)    NOT NULL DEFAULT 0,
    display_order INT           NOT NULL DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS product_sizes (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    product_id   INT         NOT NULL,
    size_label   VARCHAR(50) NOT NULL,
    is_available TINYINT(1)  NOT NULL DEFAULT 1,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sync_logs (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    sync_type          VARCHAR(50)                         NOT NULL,
    target_identifier  VARCHAR(200)                        NULL,
    status             ENUM('running', 'success', 'failed') NOT NULL DEFAULT 'running',
    records_fetched    INT                                 NOT NULL DEFAULT 0,
    records_inserted   INT                                 NOT NULL DEFAULT 0,
    records_updated    INT                                 NOT NULL DEFAULT 0,
    api_calls_used     INT                                 NOT NULL DEFAULT 0,
    error_message      TEXT                                NULL,
    started_at         TIMESTAMP                           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at       TIMESTAMP                           NULL
);

CREATE TABLE IF NOT EXISTS api_rate_tracker (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    month_year   CHAR(7)   NOT NULL UNIQUE,
    calls_used   INT       NOT NULL DEFAULT 0,
    calls_limit  INT       NOT NULL DEFAULT 500,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
