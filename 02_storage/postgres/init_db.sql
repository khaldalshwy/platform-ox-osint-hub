-- تفعيل إضافة نظم المعلومات الجغرافية PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. جدول المصادر المرصودة
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- news_site, telegram, twitter, ais_feed, sensor
    url_or_channel TEXT,
    credibility_score FLOAT DEFAULT 0.5,
    country VARCHAR(100),
    language VARCHAR(10) DEFAULT 'ar',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. جدول الأحداث والمنشورات المرصودة
CREATE TABLE IF NOT EXISTS osint_events (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    raw_content TEXT,
    cleaned_content TEXT,
    source_id INT REFERENCES sources(id) ON DELETE SET NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    event_category VARCHAR(100), -- أمني، بحري، سياسي، كوارث، شائعات
    sentiment_score FLOAT, -- من -1.0 إلى +1.0
    sentiment_label VARCHAR(20), -- إيجابي، سلبي، محايد
    urgency_level VARCHAR(20) DEFAULT 'روتينية', -- قصوى، متوسطة، روتينية
    fact_check_status VARCHAR(50) DEFAULT 'قيد التحقق', -- مؤكد، غير مؤكد، شائعة، مضلل
    latitude FLOAT,
    longitude FLOAT,
    location_geom GEOMETRY(Point, 4326),
    location_name VARCHAR(255),
    raw_data_url TEXT, -- رابط الملف في MinIO
    raw_hash VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_events_geom ON osint_events USING GIST (location_geom);
CREATE INDEX IF NOT EXISTS idx_events_published_at ON osint_events (published_at);
CREATE INDEX IF NOT EXISTS idx_events_category ON osint_events (event_category);

-- 3. جدول تتبع حركة السفن (AIS Tracks)
CREATE TABLE IF NOT EXISTS ais_vessels (
    mmsi INT PRIMARY KEY,
    vessel_name VARCHAR(255),
    imo_number INT,
    vessel_type VARCHAR(100), -- ناقلة نفط، حاويات، سفينة صيد، عسكرية
    flag_country VARCHAR(100),
    destination VARCHAR(255),
    eta TIMESTAMP WITH TIME ZONE,
    current_latitude FLOAT,
    current_longitude FLOAT,
    current_geom GEOMETRY(Point, 4326),
    speed_knots FLOAT,
    course_degrees FLOAT,
    nav_status VARCHAR(100),
    last_signal_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessels_geom ON ais_vessels USING GIST (current_geom);

-- 4. جدول سجل مسارات السفن التاريخي
CREATE TABLE IF NOT EXISTS ais_history (
    id BIGSERIAL PRIMARY KEY,
    mmsi INT REFERENCES ais_vessels(mmsi) ON DELETE CASCADE,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    geom GEOMETRY(Point, 4326),
    speed_knots FLOAT,
    course_degrees FLOAT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ais_history_geom ON ais_history USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_ais_history_mmsi ON ais_history (mmsi);

-- 5. جدول الكيانات المستخرجة (الأشخاص، المنظمات، الأماكن)
CREATE TABLE IF NOT EXISTS extracted_entities (
    id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- PERSON, ORG, GPE, WEAPON, VESSEL
    confidence_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. جدول شبكة العلاقات بين الكيانات والأحداث
CREATE TABLE IF NOT EXISTS entity_relationships (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES osint_events(id) ON DELETE CASCADE,
    entity_id INT REFERENCES extracted_entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100), -- مشارك، مستهدف، موقع، مصدر
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
