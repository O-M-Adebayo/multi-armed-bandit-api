import database
from datetime import date, timedelta

def insert_test_data():
    conn = database.get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Insert experiment
            cursor.execute("""
                INSERT INTO experiments (experiment_id, name, description)
                VALUES ('homepage_ctr', 'Homepage CTR', 'Testing different homepage layouts')
                ON CONFLICT (experiment_id) DO NOTHING
            """)
            
            # Insert variants
            variants = [
                ('control', 'Homepage CTR', 'Original Layout', True),
                ('variant1', 'Homepage CTR', 'New Layout A', False),
                ('variant2', 'Homepage CTR', 'New Layout B', False)
            ]
            
            for variant_id, exp_id, name, is_control in variants:
                cursor.execute("""
                    INSERT INTO variants (variant_id, experiment_id, name, is_control)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (variant_id) DO NOTHING
                """, (variant_id, exp_id, name, is_control))
            
            # Insert metrics for last 30 days
            today = date.today()
            for i in range(30):
                day = today - timedelta(days=i)
                cursor.execute("""
                    INSERT INTO experiment_metrics 
                    (experiment_id, variant_id, date, impressions, successes)
                    VALUES (%s, 'control', %s, %s, %s)
                    ON CONFLICT (experiment_id, variant_id, date) DO NOTHING
                """, ('homepage_ctr', day, 1000, 120 + i))
                
                cursor.execute("""
                    INSERT INTO experiment_metrics 
                    (experiment_id, variant_id, date, impressions, successes)
                    VALUES (%s, 'variant1', %s, %s, %s)
                    ON CONFLICT (experiment_id, variant_id, date) DO NOTHING
                """, ('homepage_ctr', day, 1000, 150 + i))
                
                cursor.execute("""
                    INSERT INTO experiment_metrics 
                    (experiment_id, variant_id, date, impressions, successes)
                    VALUES (%s, 'variant2', %s, %s, %s)
                    ON CONFLICT (experiment_id, variant_id, date) DO NOTHING
                """, ('homepage_ctr', day, 1000, 130 + i))
            
            conn.commit()
            print("Test data inserted successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting test data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    insert_test_data()