-- Create database if it doesn't exist
-- Run this command separately: CREATE DATABASE salesiq;

-- Create campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    budget DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'paused', 'completed', 'draft')),
    target_audience VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create ads table
CREATE TABLE IF NOT EXISTS ads (
    ad_id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(campaign_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    creative_url VARCHAR(255),
    ad_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create impressions table
CREATE TABLE IF NOT EXISTS impressions (
    impression_id SERIAL PRIMARY KEY,
    ad_id INTEGER REFERENCES ads(ad_id),
    campaign_id INTEGER REFERENCES campaigns(campaign_id),
    user_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL,
    platform VARCHAR(50),
    device VARCHAR(50),
    location VARCHAR(100)
);

-- Create clicks table
CREATE TABLE IF NOT EXISTS clicks (
    click_id SERIAL PRIMARY KEY,
    impression_id INTEGER REFERENCES impressions(impression_id),
    ad_id INTEGER REFERENCES ads(ad_id),
    campaign_id INTEGER REFERENCES campaigns(campaign_id),
    user_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL,
    platform VARCHAR(50),
    device VARCHAR(50),
    location VARCHAR(100)
);

-- Create conversions table
CREATE TABLE IF NOT EXISTS conversions (
    conversion_id SERIAL PRIMARY KEY,
    click_id INTEGER REFERENCES clicks(click_id),
    ad_id INTEGER REFERENCES ads(ad_id),
    campaign_id INTEGER REFERENCES campaigns(campaign_id),
    user_id VARCHAR(100),
    conversion_type VARCHAR(50),
    conversion_value DECIMAL(12, 2),
    timestamp TIMESTAMP NOT NULL
);

-- Create daily_metrics table for aggregated data
CREATE TABLE IF NOT EXISTS daily_metrics (
    metric_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    campaign_id INTEGER REFERENCES campaigns(campaign_id),
    ad_id INTEGER REFERENCES ads(ad_id),
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    spend DECIMAL(12, 2) DEFAULT 0,
    ctr DECIMAL(8, 6),
    cpc DECIMAL(8, 6),
    cvr DECIMAL(8, 6),
    roas DECIMAL(8, 6)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_impressions_campaign_id ON impressions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_clicks_campaign_id ON clicks(campaign_id);
CREATE INDEX IF NOT EXISTS idx_conversions_campaign_id ON conversions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_campaign_id ON daily_metrics(campaign_id);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);

-- Add comments for documentation
COMMENT ON TABLE campaigns IS 'Marketing campaigns';
COMMENT ON TABLE ads IS 'Advertisements within campaigns';
COMMENT ON TABLE impressions IS 'Ad impressions/views';
COMMENT ON TABLE clicks IS 'Ad clicks';
COMMENT ON TABLE conversions IS 'Conversions resulting from ad clicks';
COMMENT ON TABLE daily_metrics IS 'Aggregated daily performance metrics'; 