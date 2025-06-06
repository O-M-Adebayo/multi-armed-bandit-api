import database
from psycopg2 import sql, errors

SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id VARCHAR(50) PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE variants (
    variant_id VARCHAR(50) PRIMARY KEY,
    experiment_id VARCHAR(50) REFERENCES experiments(experiment_id),
    name TEXT NOT NULL,
    is_control BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE experiment_metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) REFERENCES experiments(experiment_id),
    variant_id VARCHAR(50) REFERENCES variants(variant_id),
    date DATE NOT NULL,
    impressions INTEGER NOT NULL CHECK (impressions >= 0),
    successes INTEGER NOT NULL CHECK (successes >= 0 AND successes <= impressions),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (experiment_id, variant_id, date)
);

CREATE INDEX idx_experiment_metrics_experiment ON experiment_metrics(experiment_id);
CREATE INDEX idx_experiment_metrics_variant ON experiment_metrics(variant_id);
CREATE INDEX idx_experiment_metrics_date ON experiment_metrics(date);
"""

def initialize_db():
    conn = None
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # Split into separate statements for better error reporting
            statements = [s.strip() for s in SQL_SCHEMA.split(';') if s.strip()]
            
            # This is much better to prevent my code crashing
            for statement in statements:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    print(f"Skipping statement due to error: {statement[:50]}...\nError: {e}")
                    conn.rollback()
                    continue
            
        conn.commit()
        print("Database initialized successfully!")
    
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        if conn:
            conn.rollback()
        raise  # Re-raise after logging
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_db()