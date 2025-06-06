from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from typing import List, Dict

app = FastAPI()

# Database connection 
def get_db_connection():
    return psycopg2.connect(
        dbname="bandit_db",
        user="bandit_user",
        password="Mike@PostgreSQL22",
        host="localhost",
        cursor_factory=RealDictCursor
    )

class MetricInput(BaseModel):
    experiment_id: str
    variant_id: str
    date: date
    impressions: int
    successes: int

class AllocationResponse(BaseModel):
    experiment_id: str
    date: date
    allocations: Dict[str, float]  # variant_id: percentage

@app.post("/metrics/")
async def add_metrics(metric: MetricInput):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO experiment_metrics 
                (experiment_id, variant_id, date, impressions, successes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (experiment_id, variant_id, date) 
                DO UPDATE SET 
                    impressions = EXCLUDED.impressions,
                    successes = EXCLUDED.successes
                """,
                (metric.experiment_id, metric.variant_id, 
                 metric.date, metric.impressions, metric.successes))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/allocations/{experiment_id}")
async def get_allocations(experiment_id: str, for_date: date):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get all variants for the experiment
            cursor.execute("""
                SELECT variant_id, is_control FROM variants 
                WHERE experiment_id = %s
                """, (experiment_id,))
            variants = cursor.fetchall()
            if not variants:
                raise HTTPException(
                    status_code=404, 
                    detail="Experiment or variants not found")
            
            # Get metrics for the last 30 days
            cursor.execute("""
                SELECT variant_id, SUM(impressions) as impressions, 
                       SUM(successes) as successes
                FROM experiment_metrics
                WHERE experiment_id = %s
                AND date >= %s - INTERVAL '30 days'
                GROUP BY variant_id
                """, (experiment_id, for_date))
            metrics = cursor.fetchall()
            
            # Prepare data for Thompson Sampling
            variant_data = {
                v['variant_id']: {
                    'impressions': 0,
                    'successes': 0,
                    'is_control': v['is_control']
                } for v in variants
            }
            
            for m in metrics:
                if m['variant_id'] in variant_data:
                    variant_data[m['variant_id']]['impressions'] = m['impressions']
                    variant_data[m['variant_id']]['successes'] = m['successes']
            
            # Thompson Sampling implementation
            allocations = thompson_sampling(variant_data)
            
            return AllocationResponse(
                experiment_id=experiment_id,
                date=for_date,
                allocations=allocations
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

def thompson_sampling(variant_data: Dict) -> Dict[str, float]:
    samples = {}
    for variant_id, data in variant_data.items():
        alpha = 1 + data['successes']
        beta = 1 + (data['impressions'] - data['successes'])
        samples[variant_id] = np.random.beta(alpha, beta)
    
    # Find the variant with the highest sample
    best_variant = max(samples.items(), key=lambda x: x[1])[0]
    
    # Calculate allocations
    total = sum(samples.values())
    allocations = {
        variant_id: (sample / total) * 100
        for variant_id, sample in samples.items()
    }
    
    return allocations