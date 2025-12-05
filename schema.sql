-- PredictionMarket Database Schema
-- SQLite Database for Polymarket Clone

-- Users Table
-- Stores user authentication and wallet balance
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    balance REAL DEFAULT 1000.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Markets Table
-- Supports both Binary and Over/Under market types
CREATE TABLE IF NOT EXISTS markets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    market_type TEXT NOT NULL CHECK(market_type IN ('binary', 'over_under')),
    
    -- For Binary markets (e.g., "NVidia vs Google")
    option_a TEXT,
    option_b TEXT,
    
    -- For Over/Under markets (e.g., "TWiT length > 3.5 hours")
    target_value REAL,
    unit TEXT,
    
    -- Market status and resolution
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'resolved', 'cancelled')),
    resolution TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Bets Table
-- Records all bets placed by users
CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    market_id INTEGER NOT NULL,
    
    -- Option chosen: 'option_a', 'option_b', 'over', or 'under'
    option TEXT NOT NULL,
    
    amount REAL NOT NULL CHECK(amount > 0),
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (market_id) REFERENCES markets(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_bets_market ON bets(market_id);
CREATE INDEX IF NOT EXISTS idx_bets_user ON bets(user_id);
CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status);

-- Seed Data (TWiT and NVidia markets)
-- These will be inserted by the Flask app on first launch

-- Example Binary Market:
-- INSERT INTO markets (question, market_type, option_a, option_b)
-- VALUES ('Who will win the AI chip race?', 'binary', 'NVidia', 'Google');

-- Example Over/Under Market:
-- INSERT INTO markets (question, market_type, target_value, unit)
-- VALUES ('Length of TWiT on Sunday', 'over_under', 3.5, 'hours');
