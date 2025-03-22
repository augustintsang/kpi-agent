"""
Seed script to populate the database with mock sales and marketing data.
This creates realistic campaign data with anomalies for the agent to investigate.
"""
import os
import sys
import random
import datetime
from datetime import timedelta
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import execute_query, test_connection

# Load environment variables
load_dotenv()

# Constants for data generation
CAMPAIGN_COUNT = 10
ADS_PER_CAMPAIGN = 5
DAYS_OF_DATA = 30
USER_POOL_SIZE = 10000
DEVICES = ["desktop", "mobile", "tablet"]
PLATFORMS = ["facebook", "google", "instagram", "twitter", "linkedin"]
LOCATIONS = ["US", "UK", "CA", "AU", "DE", "FR", "JP", "BR", "IN", "MX"]
AD_TYPES = ["banner", "video", "text", "carousel", "native"]
CONVERSION_TYPES = ["purchase", "signup", "download", "lead", "pageview"]

# Anomaly settings - Campaign 5 will have a CTR drop after day 20
ANOMALY_CAMPAIGN = 5
ANOMALY_START_DAY = 20
CTR_DROP_FACTOR = 0.5  # 50% drop


def create_tables():
    """Create tables if they don't exist."""
    print("Creating tables...")
    
    # Read schema.sql file
    with open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r") as f:
        schema_sql = f.read()
    
    # Execute each statement
    for statement in schema_sql.split(";"):
        if statement.strip():
            execute_query(statement, fetch=False)
    
    print("Tables created successfully.")


def clear_existing_data():
    """Clear all existing data from tables."""
    print("Clearing existing data...")
    
    tables = [
        "daily_metrics", 
        "conversions", 
        "clicks", 
        "impressions", 
        "ads", 
        "campaigns"
    ]
    
    for table in tables:
        execute_query(f"DELETE FROM {table}", fetch=False)
    
    print("Data cleared successfully.")


def seed_campaigns():
    """Seed campaigns table with mock data."""
    print("Seeding campaigns...")
    
    campaigns = []
    today = datetime.date.today()
    
    for i in range(1, CAMPAIGN_COUNT + 1):
        start_date = today - timedelta(days=DAYS_OF_DATA)
        end_date = today + timedelta(days=random.randint(10, 30))
        
        campaign = {
            "name": f"Campaign {i}",
            "description": f"Test campaign {i} for sales analytics",
            "start_date": start_date,
            "end_date": end_date,
            "budget": random.uniform(5000, 50000),
            "status": random.choice(["active", "paused", "completed"]),
            "target_audience": random.choice(["male", "female", "young adults", "seniors", "professionals"])
        }
        campaigns.append(campaign)
        
        query = """
        INSERT INTO campaigns (name, description, start_date, end_date, budget, status, target_audience)
        VALUES (%(name)s, %(description)s, %(start_date)s, %(end_date)s, %(budget)s, %(status)s, %(target_audience)s)
        RETURNING campaign_id
        """
        result = execute_query(query, campaign)
        campaign["campaign_id"] = result[0][0]
    
    return campaigns


def seed_ads(campaigns):
    """Seed ads table with mock data."""
    print("Seeding ads...")
    
    ads = []
    for campaign in campaigns:
        for i in range(1, ADS_PER_CAMPAIGN + 1):
            ad = {
                "campaign_id": campaign["campaign_id"],
                "name": f"Ad {i} for {campaign['name']}",
                "description": f"Test ad {i} for {campaign['name']}",
                "creative_url": f"https://example.com/creatives/{campaign['campaign_id']}/ad{i}.jpg",
                "ad_type": random.choice(AD_TYPES)
            }
            ads.append(ad)
            
            query = """
            INSERT INTO ads (campaign_id, name, description, creative_url, ad_type)
            VALUES (%(campaign_id)s, %(name)s, %(description)s, %(creative_url)s, %(ad_type)s)
            RETURNING ad_id
            """
            result = execute_query(query, ad)
            ad["ad_id"] = result[0][0]
    
    return ads


def generate_performance_data(campaigns, ads):
    """Generate performance data including impressions, clicks, and conversions."""
    print("Generating performance data...")
    
    base_date = datetime.date.today() - timedelta(days=DAYS_OF_DATA)
    all_metrics = []
    
    for day in tqdm(range(DAYS_OF_DATA + 1)):
        current_date = base_date + timedelta(days=day)
        
        for campaign in campaigns:
            campaign_id = campaign["campaign_id"]
            campaign_ads = [ad for ad in ads if ad["campaign_id"] == campaign_id]
            
            for ad in campaign_ads:
                ad_id = ad["ad_id"]
                
                # Base metrics with some randomness
                base_impressions = random.randint(500, 2000)
                
                # Normal CTR range (1-5%)
                base_ctr = random.uniform(0.01, 0.05)
                
                # Conversion rate range (1-10% of clicks)
                base_cvr = random.uniform(0.01, 0.1)
                
                # Apply anomaly to Campaign 5 after day 20
                if campaign_id == ANOMALY_CAMPAIGN and day >= ANOMALY_START_DAY:
                    base_ctr *= CTR_DROP_FACTOR
                
                # Calculate derived metrics
                impressions = base_impressions
                clicks = int(impressions * base_ctr)
                conversions = int(clicks * base_cvr)
                spend = random.uniform(50, 200)
                
                # Safety checks
                clicks = min(clicks, impressions)
                conversions = min(conversions, clicks)
                
                # Calculate performance metrics
                ctr = clicks / impressions if impressions > 0 else 0
                cpc = spend / clicks if clicks > 0 else 0
                cvr = conversions / clicks if clicks > 0 else 0
                roas = (conversions * random.uniform(20, 100)) / spend if spend > 0 else 0
                
                # Create daily metric record
                metric = {
                    "date": current_date,
                    "campaign_id": campaign_id,
                    "ad_id": ad_id,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "spend": spend,
                    "ctr": ctr,
                    "cpc": cpc,
                    "cvr": cvr,
                    "roas": roas
                }
                all_metrics.append(metric)
    
    return all_metrics


def seed_daily_metrics(metrics):
    """Save the daily metrics to the database."""
    print("Saving daily metrics...")
    
    for metric in tqdm(metrics):
        query = """
        INSERT INTO daily_metrics 
        (date, campaign_id, ad_id, impressions, clicks, conversions, spend, ctr, cpc, cvr, roas)
        VALUES 
        (%(date)s, %(campaign_id)s, %(ad_id)s, %(impressions)s, %(clicks)s, %(conversions)s, 
         %(spend)s, %(ctr)s, %(cpc)s, %(cvr)s, %(roas)s)
        """
        execute_query(query, metric, fetch=False)


def generate_raw_events(metrics):
    """
    Generate individual impression, click, and conversion events
    based on the aggregated metrics.
    """
    print("Generating raw events...")
    
    for metric in tqdm(metrics):
        date = metric["date"]
        campaign_id = metric["campaign_id"]
        ad_id = metric["ad_id"]
        
        # Generate impression events
        for i in range(metric["impressions"]):
            timestamp = datetime.datetime.combine(
                date, 
                datetime.time(
                    hour=random.randint(0, 23),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
            )
            
            user_id = f"user_{random.randint(1, USER_POOL_SIZE)}"
            platform = random.choice(PLATFORMS)
            device = random.choice(DEVICES)
            location = random.choice(LOCATIONS)
            
            impression = {
                "ad_id": ad_id,
                "campaign_id": campaign_id,
                "user_id": user_id,
                "timestamp": timestamp,
                "platform": platform,
                "device": device,
                "location": location
            }
            
            query = """
            INSERT INTO impressions 
            (ad_id, campaign_id, user_id, timestamp, platform, device, location)
            VALUES 
            (%(ad_id)s, %(campaign_id)s, %(user_id)s, %(timestamp)s, %(platform)s, 
             %(device)s, %(location)s)
            RETURNING impression_id
            """
            
            result = execute_query(query, impression)
            impression_id = result[0][0]
            
            # Generate click events (based on CTR)
            if i < metric["clicks"]:
                # Add random delay for click (1-60 seconds)
                click_timestamp = timestamp + timedelta(seconds=random.randint(1, 60))
                
                click = {
                    "impression_id": impression_id,
                    "ad_id": ad_id,
                    "campaign_id": campaign_id,
                    "user_id": user_id,
                    "timestamp": click_timestamp,
                    "platform": platform,
                    "device": device,
                    "location": location
                }
                
                query = """
                INSERT INTO clicks 
                (impression_id, ad_id, campaign_id, user_id, timestamp, platform, device, location)
                VALUES 
                (%(impression_id)s, %(ad_id)s, %(campaign_id)s, %(user_id)s, %(timestamp)s, 
                 %(platform)s, %(device)s, %(location)s)
                RETURNING click_id
                """
                
                result = execute_query(query, click)
                click_id = result[0][0]
                
                # Generate conversion events (based on CVR)
                if i < metric["conversions"]:
                    # Add random delay for conversion (30-600 seconds)
                    conversion_timestamp = click_timestamp + timedelta(seconds=random.randint(30, 600))
                    conversion_type = random.choice(CONVERSION_TYPES)
                    conversion_value = random.uniform(10, 200)
                    
                    conversion = {
                        "click_id": click_id,
                        "ad_id": ad_id,
                        "campaign_id": campaign_id,
                        "user_id": user_id,
                        "conversion_type": conversion_type,
                        "conversion_value": conversion_value,
                        "timestamp": conversion_timestamp
                    }
                    
                    query = """
                    INSERT INTO conversions 
                    (click_id, ad_id, campaign_id, user_id, conversion_type, conversion_value, timestamp)
                    VALUES 
                    (%(click_id)s, %(ad_id)s, %(campaign_id)s, %(user_id)s, %(conversion_type)s, 
                     %(conversion_value)s, %(timestamp)s)
                    """
                    
                    execute_query(query, conversion, fetch=False)


def main():
    """Main function to seed the database."""
    parser = argparse.ArgumentParser(description="Seed the database with mock data")
    parser.add_argument("--delete", action="store_true", help="Delete existing data before seeding")
    parser.add_argument("--no-events", action="store_true", help="Skip generating individual events")
    args = parser.parse_args()
    
    # Test database connection
    if not test_connection():
        print("Database connection failed. Check your connection settings.")
        return
    
    # Create tables if they don't exist
    create_tables()
    
    # Clear existing data if requested
    if args.delete:
        clear_existing_data()
    
    # Seed campaigns
    campaigns = seed_campaigns()
    
    # Seed ads
    ads = seed_ads(campaigns)
    
    # Generate and save daily metrics
    metrics = generate_performance_data(campaigns, ads)
    seed_daily_metrics(metrics)
    
    # Generate individual events (optional)
    if not args.no_events:
        generate_raw_events(metrics)
    
    print("Database seeded successfully!")


if __name__ == "__main__":
    main() 