"""
Database layer for Meta Ads historical data storage
Stores snapshots every 6 hours for trend analysis
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MetaAdsDatabase:
    """SQLite database manager for Meta Ads snapshots"""
    
    def __init__(self, db_path: str = 'meta_ads_history.db'):
        self.db_path = db_path
        self.conn = None
    
    def get_connection(self):
        """Get or create database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def initialize_schema(self):
        """Create database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Snapshots table - stores metadata for each 6-hour checkpoint
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                snapshot_time TIMESTAMP NOT NULL,
                date_since TEXT NOT NULL,
                window_number INTEGER NOT NULL,
                account_balance REAL,
                account_balance_currency TEXT DEFAULT 'INR',
                campaigns_json TEXT,
                adsets_json TEXT,
                ads_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account_id, snapshot_time)
            )
        ''')
        
        # Campaign metrics - denormalized for easy querying
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                campaign_id TEXT NOT NULL,
                campaign_name TEXT NOT NULL,
                status TEXT,
                spend REAL DEFAULT 0,
                impressions INTEGER DEFAULT 0,
                reach INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                ctr REAL DEFAULT 0,
                conversions_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
            )
        ''')
        
        # AdSet metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS adset_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                campaign_id TEXT,
                adset_id TEXT NOT NULL,
                adset_name TEXT NOT NULL,
                status TEXT,
                spend REAL DEFAULT 0,
                impressions INTEGER DEFAULT 0,
                reach INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                ctr REAL DEFAULT 0,
                conversions_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
            )
        ''')
        
        # Ad metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ad_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                campaign_id TEXT,
                adset_id TEXT,
                ad_id TEXT NOT NULL,
                ad_name TEXT NOT NULL,
                status TEXT,
                spend REAL DEFAULT 0,
                impressions INTEGER DEFAULT 0,
                reach INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                ctr REAL DEFAULT 0,
                conversions_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
            )
        ''')
        
        # Claude analyses - stores AI insights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS claude_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                current_snapshot_id INTEGER NOT NULL,
                previous_snapshot_id INTEGER,
                prompt_text TEXT,
                analysis_text TEXT NOT NULL,
                model_used TEXT DEFAULT 'claude-sonnet-4-5',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
                FOREIGN KEY (previous_snapshot_id) REFERENCES snapshots(id) ON DELETE SET NULL
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_account_time ON snapshots(account_id, snapshot_time DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_date_window ON snapshots(date_since, window_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaign_metrics_snapshot ON campaign_metrics(snapshot_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_adset_metrics_snapshot ON adset_metrics(snapshot_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ad_metrics_snapshot ON ad_metrics(snapshot_id)')
        
        conn.commit()
        logger.info("Database schema initialized successfully")
    
    def save_snapshot(self, account_id: str, snapshot_data: Dict) -> int:
        """Save a snapshot and return snapshot_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO snapshots (
                account_id, snapshot_time, date_since, window_number,
                account_balance, campaigns_json, adsets_json, ads_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            account_id,
            snapshot_data['snapshot_time'],
            snapshot_data['date_since'],
            snapshot_data['window_number'],
            snapshot_data.get('balance', {}).get('balance', 0),
            json.dumps(snapshot_data.get('campaigns', [])),
            json.dumps(snapshot_data.get('adsets', [])),
            json.dumps(snapshot_data.get('ads', []))
        ))
        
        snapshot_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Saved snapshot {snapshot_id} for account {account_id}")
        return snapshot_id
    
    def get_latest_snapshot(self, account_id: str) -> Optional[Dict]:
        """Get the most recent snapshot for an account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM snapshots
            WHERE account_id = ?
            ORDER BY snapshot_time DESC
            LIMIT 1
        ''', (account_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_previous_snapshot(self, account_id: str, current_time: datetime) -> Optional[Dict]:
        """Get snapshot from 6 hours before current_time"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Look for snapshot approximately 6 hours ago (within 30 min window)
        target_time = current_time - timedelta(hours=6)
        time_window_start = target_time - timedelta(minutes=30)
        time_window_end = target_time + timedelta(minutes=30)
        
        cursor.execute('''
            SELECT * FROM snapshots
            WHERE account_id = ?
            AND snapshot_time BETWEEN ? AND ?
            ORDER BY ABS(CAST((julianday(?) - julianday(snapshot_time)) * 24 * 60 AS INTEGER))
            LIMIT 1
        ''', (account_id, time_window_start, time_window_end, target_time))
        
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Parse JSON fields
            result['campaigns'] = json.loads(result.get('campaigns_json', '[]'))
            result['adsets'] = json.loads(result.get('adsets_json', '[]'))
            result['ads'] = json.loads(result.get('ads_json', '[]'))
            return result
        return None
    
    def save_campaign_metrics(self, snapshot_id: int, campaigns: List[Dict]):
        """Save campaign-level metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for campaign in campaigns:
            cursor.execute('''
                INSERT INTO campaign_metrics (
                    snapshot_id, campaign_id, campaign_name, status,
                    spend, impressions, reach, clicks, ctr, conversions_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                campaign.get('campaign_id', ''),
                campaign.get('campaign_name', 'Unknown'),
                campaign.get('status', 'UNKNOWN'),
                float(campaign.get('spend', 0)),
                int(campaign.get('impressions', 0)),
                int(campaign.get('reach', 0)),
                int(campaign.get('clicks', 0)),
                float(campaign.get('ctr', 0)),
                json.dumps(campaign.get('parsed_actions', {}))
            ))
        
        conn.commit()
        logger.info(f"Saved {len(campaigns)} campaign metrics for snapshot {snapshot_id}")
    
    def save_adset_metrics(self, snapshot_id: int, adsets: List[Dict]):
        """Save adset-level metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for adset in adsets:
            cursor.execute('''
                INSERT INTO adset_metrics (
                    snapshot_id, campaign_id, adset_id, adset_name, status,
                    spend, impressions, reach, clicks, ctr, conversions_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                adset.get('campaign_id', ''),
                adset.get('adset_id', ''),
                adset.get('adset_name', 'Unknown'),
                adset.get('status', 'UNKNOWN'),
                float(adset.get('spend', 0)),
                int(adset.get('impressions', 0)),
                int(adset.get('reach', 0)),
                int(adset.get('clicks', 0)),
                float(adset.get('ctr', 0)),
                json.dumps(adset.get('parsed_actions', {}))
            ))
        
        conn.commit()
        logger.info(f"Saved {len(adsets)} adset metrics for snapshot {snapshot_id}")
    
    def save_ad_metrics(self, snapshot_id: int, ads: List[Dict]):
        """Save ad-level metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for ad in ads:
            cursor.execute('''
                INSERT INTO ad_metrics (
                    snapshot_id, campaign_id, adset_id, ad_id, ad_name, status,
                    spend, impressions, reach, clicks, ctr, conversions_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                ad.get('campaign_id', ''),
                ad.get('adset_id', ''),
                ad.get('ad_id', ''),
                ad.get('ad_name', 'Unknown'),
                ad.get('status', 'UNKNOWN'),
                float(ad.get('spend', 0)),
                int(ad.get('impressions', 0)),
                int(ad.get('reach', 0)),
                int(ad.get('clicks', 0)),
                float(ad.get('ctr', 0)),
                json.dumps(ad.get('parsed_actions', {}))
            ))
        
        conn.commit()
        logger.info(f"Saved {len(ads)} ad metrics for snapshot {snapshot_id}")
    
    def save_claude_analysis(self, current_snapshot_id: int, previous_snapshot_id: Optional[int], 
                            prompt: str, analysis: str, model: str = 'claude-sonnet-4-5'):
        """Save Claude AI analysis"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO claude_analyses (
                current_snapshot_id, previous_snapshot_id, prompt_text, analysis_text, model_used
            ) VALUES (?, ?, ?, ?, ?)
        ''', (current_snapshot_id, previous_snapshot_id, prompt, analysis, model))
        
        conn.commit()
        logger.info(f"Saved Claude analysis for snapshot {current_snapshot_id}")
    
    def cleanup_old_snapshots(self, days_to_keep: int = 30):
        """Delete snapshots older than specified days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cursor.execute('DELETE FROM snapshots WHERE snapshot_time < ?', (cutoff_date,))
        deleted_count = cursor.rowcount
        conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} snapshots older than {days_to_keep} days")
        return deleted_count
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
