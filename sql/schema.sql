CREATE DATABASE IF NOT EXISTS healthcare_DB;
USE healthcare_DB;




CREATE TABLE cluster_profiles (
    cluster_id              INT PRIMARY KEY,
    cluster_label            VARCHAR(50) NOT NULL,
    patient_count             INT CHECK(patient_count >= 0) DEFAULT 0,
    avg_age                   DECIMAL(5,2) NOT NULL CHECK(avg_age >= 0.00),
    avg_bmi                   DECIMAL(5,2) NOT NULL CHECK(avg_bmi >= 0.00),
    avg_risk_score            DECIMAL(5,2) DEFAULT 0.00,
    segment_size_pct          DECIMAL(5,2) DEFAULT 0.00,
    avg_annual_visits         DECIMAL(5,2) NOT NULL CHECK(avg_annual_visits >= 0),
    avg_billing_amount        DECIMAL(10,2) DEFAULT 0.00,
    avg_days_since_last_visit DECIMAL(6,2) DEFAULT 0.00,
    dominant_insurance_type   VARCHAR(30) DEFAULT 'None',
    dominant_condition        VARCHAR(50) DEFAULT 'Normal',
    recommendation            TEXT,
    updated_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE patients_clustered (
    patient_id              VARCHAR(20) PRIMARY KEY,
    age                      INT NOT NULL CHECK(age >= 0 AND age <= 100),
    gender                   VARCHAR(50) NOT NULL CHECK(gender IN ('Male','Female','Other')),
    state                    VARCHAR(100) DEFAULT 'Unknown',
    city                     VARCHAR(100) DEFAULT 'Unknown',
    height_cm                DECIMAL(5,2) DEFAULT 0.00 CHECK(height_cm >= 0),
    weight_kg                DECIMAL(5,2) DEFAULT 0.00 CHECK(weight_kg >= 0), 
    bmi                      DECIMAL(5,2) NOT NULL DEFAULT 0.00 CHECK(bmi >= 0.00),
    insurance_type           VARCHAR(100),
    primary_condition        VARCHAR(100) NOT NULL DEFAULT 'Normal',
    risk_score               DECIMAL(5,2) DEFAULT 0.00,
    num_chronic_conditions   INT CHECK(num_chronic_conditions >= 0),
    annual_visits             INT CHECK(annual_visits >= 0),
    avg_billing_amount        DECIMAL(10,2) DEFAULT 0.00 CHECK (avg_billing_amount >= 0.00),
    last_visit_date           DATE ,
    created_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    days_since_last_visit     INT NOT NULL CHECK(days_since_last_visit >= 0),
    preventive_care_flag      TINYINT DEFAULT 0 CHECK(preventive_care_flag IN (0,1)),
    cluster_id                INT,
    FOREIGN KEY (cluster_id) REFERENCES cluster_profiles(cluster_id) ON DELETE SET NULL 
);

CREATE INDEX index_patient_state ON patients_clustered(state);
CREATE INDEX index_patient_condition ON patients_clustered(primary_condition);
CREATE INDEX index_billing ON patients_clustered(avg_billing_amount);


CREATE VIEW patient_segment_summary AS
SELECT 
    p.cluster_id,
    cp.cluster_label,
    COUNT(*) as count,
    AVG(p.avg_billing_amount) as avg_billing
FROM patients_clustered p
JOIN cluster_profiles cp ON p.cluster_id = cp.cluster_id
GROUP BY p.cluster_id, cp.cluster_label;
