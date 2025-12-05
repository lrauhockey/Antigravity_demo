from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'  # Change this in production!

DATABASE = 'predictionmarket.db'

# Database helper functions
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema and seed data"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL DEFAULT 1000.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            market_type TEXT NOT NULL CHECK(market_type IN ('binary', 'over_under')),
            option_a TEXT,
            option_b TEXT,
            target_value REAL,
            unit TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'resolved', 'cancelled')),
            resolution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            market_id INTEGER NOT NULL,
            option TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (market_id) REFERENCES markets(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_market ON bets(market_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_user ON bets(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status)')
    
    # Seed data if markets table is empty
    cursor.execute('SELECT COUNT(*) FROM markets')
    if cursor.fetchone()[0] == 0:
        # Binary Market: NVidia vs Google
        cursor.execute('''
            INSERT INTO markets (question, market_type, option_a, option_b)
            VALUES (?, ?, ?, ?)
        ''', ('Who will win the AI chip race?', 'binary', 'NVidia', 'Google'))
        
        # Over/Under Market: TWiT length
        cursor.execute('''
            INSERT INTO markets (question, market_type, target_value, unit)
            VALUES (?, ?, ?, ?)
        ''', ('Length of TWiT on Sunday', 'over_under', 3.5, 'hours'))
    
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_user_balance():
    """Get current user's balance"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return user['balance'] if user else 0

# Helper function to calculate market sentiment
def get_market_sentiment(market_id):
    """Calculate sentiment percentages for a market"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get market type
    cursor.execute('SELECT market_type FROM markets WHERE id = ?', (market_id,))
    market = cursor.fetchone()
    if not market:
        return None
    
    market_type = market['market_type']
    
    # Get total bets by option
    cursor.execute('''
        SELECT option, SUM(amount) as total
        FROM bets
        WHERE market_id = ?
        GROUP BY option
    ''', (market_id,))
    
    bets = cursor.fetchall()
    conn.close()
    
    if not bets:
        # No bets yet, return 50/50
        if market_type == 'binary':
            return {'option_a': 50.0, 'option_b': 50.0}
        else:
            return {'over': 50.0, 'under': 50.0}
    
    # Calculate totals
    totals = {bet['option']: bet['total'] for bet in bets}
    grand_total = sum(totals.values())
    
    if grand_total == 0:
        if market_type == 'binary':
            return {'option_a': 50.0, 'option_b': 50.0}
        else:
            return {'over': 50.0, 'under': 50.0}
    
    # Calculate percentages
    if market_type == 'binary':
        option_a_total = totals.get('option_a', 0)
        option_b_total = totals.get('option_b', 0)
        return {
            'option_a': round((option_a_total / grand_total) * 100, 1),
            'option_b': round((option_b_total / grand_total) * 100, 1)
        }
    else:
        over_total = totals.get('over', 0)
        under_total = totals.get('under', 0)
        return {
            'over': round((over_total / grand_total) * 100, 1),
            'under': round((under_total / grand_total) * 100, 1)
        }

def get_market_stats(market_id):
    """Get statistics for a market"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total volume
    cursor.execute('SELECT SUM(amount) as total FROM bets WHERE market_id = ?', (market_id,))
    result = cursor.fetchone()
    total_volume = result['total'] if result['total'] else 0
    
    # Total bets count
    cursor.execute('SELECT COUNT(*) as count FROM bets WHERE market_id = ?', (market_id,))
    total_bets = cursor.fetchone()['count']
    
    # User's position (if logged in)
    user_position = 0
    if 'user_id' in session:
        cursor.execute('''
            SELECT SUM(amount) as total 
            FROM bets 
            WHERE market_id = ? AND user_id = ?
        ''', (market_id, session['user_id']))
        result = cursor.fetchone()
        user_position = result['total'] if result['total'] else 0
    
    conn.close()
    
    return {
        'total_volume': total_volume,
        'total_bets': total_bets,
        'user_position': user_position
    }

# Routes
@app.route('/')
def index():
    """Home page - redirect to dashboard or login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('signup.html')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists.', 'danger')
            conn.close()
            return render_template('signup.html')
        
        # Create user with $1,000 starting balance
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash, balance)
            VALUES (?, ?, 1000.0)
        ''', (username, password_hash))
        conn.commit()
        
        user_id = cursor.lastrowid
        conn.close()
        
        # Log user in
        session['user_id'] = user_id
        session['username'] = username
        flash(f'Welcome {username}! You have been given $1,000 to start betting.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing all active markets"""
    balance = get_user_balance()
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user balance
    cursor.execute('SELECT balance FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    balance = user['balance']
    
    # Get all active markets
    cursor.execute('SELECT * FROM markets WHERE status = ? ORDER BY created_at DESC', ('active',))
    markets = cursor.fetchall()
    conn.close()
    
    # Enrich markets with sentiment and stats
    enriched_markets = []
    for market in markets:
        market_dict = dict(market)
        market_dict['sentiment'] = get_market_sentiment(market['id'])
        market_dict['stats'] = get_market_stats(market['id'])
        enriched_markets.append(market_dict)
    
    return render_template('dashboard.html', markets=enriched_markets, balance=balance)

@app.route('/market/<int:market_id>')
@login_required
def market_detail(market_id):
    balance = get_user_balance()
    """Market detail page"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get market
    cursor.execute('SELECT * FROM markets WHERE id = ?', (market_id,))
    market = cursor.fetchone()
    
    if not market:
        flash('Market not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get user balance
    cursor.execute('SELECT balance FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    balance = user['balance']
    
    conn.close()
    
    # Get sentiment and stats
    market_dict = dict(market)
    market_dict['sentiment'] = get_market_sentiment(market_id)
    market_dict['stats'] = get_market_stats(market_id)
    
    return render_template('market_detail.html', market=market_dict, balance=balance)

@app.route('/create_market', methods=['GET', 'POST'])
@login_required
def create_market():
    """Create a new market"""
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        market_type = request.form.get('market_type')
        
        if not question or not market_type or market_type not in ['binary', 'over_under']:
            flash('Invalid market parameters.', 'danger')
            return render_template('create_market.html', balance=get_user_balance())
        
        conn = get_db()
        cursor = conn.cursor()
        
        if market_type == 'binary':
            option_a = request.form.get('option_a', '').strip()
            option_b = request.form.get('option_b', '').strip()
            
            if not option_a or not option_b:
                flash('Both options are required for binary markets.', 'danger')
                conn.close()
                return render_template('create_market.html', balance=get_user_balance())
            
            cursor.execute('''
                INSERT INTO markets (question, market_type, option_a, option_b)
                VALUES (?, ?, ?, ?)
            ''', (question, market_type, option_a, option_b))
        else:
            target_value = request.form.get('target_value', type=float)
            unit = request.form.get('unit', '').strip()
            
            if not target_value or not unit:
                flash('Target value and unit are required for over/under markets.', 'danger')
                conn.close()
                return render_template('create_market.html', balance=get_user_balance())
            
            cursor.execute('''
                INSERT INTO markets (question, market_type, target_value, unit)
                VALUES (?, ?, ?, ?)
            ''', (question, market_type, target_value, unit))
        
        conn.commit()
        conn.close()
        
        flash('Market created successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # GET request
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    balance = user['balance']
    conn.close()
    
    return render_template('create_market.html', balance=balance)

@app.route('/place_bet', methods=['POST'])
@login_required
def place_bet():
    """Place a bet on a market"""
    market_id = request.form.get('market_id', type=int)
    option = request.form.get('option')
    amount = request.form.get('amount', type=float)
    
    if not market_id or not option or not amount or amount <= 0:
        flash('Invalid bet parameters.', 'danger')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check user balance
    cursor.execute('SELECT balance FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if user['balance'] < amount:
        flash('Insufficient balance.', 'danger')
        conn.close()
        return redirect(url_for('market_detail', market_id=market_id))
    
    # Verify market exists and is active
    cursor.execute('SELECT * FROM markets WHERE id = ? AND status = ?', (market_id, 'active'))
    market = cursor.fetchone()
    
    if not market:
        flash('Market not found or not active.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Validate option based on market type
    valid_options = []
    if market['market_type'] == 'binary':
        valid_options = ['option_a', 'option_b']
    else:
        valid_options = ['over', 'under']
    
    if option not in valid_options:
        flash('Invalid betting option.', 'danger')
        conn.close()
        return redirect(url_for('market_detail', market_id=market_id))
    
    # Place bet
    cursor.execute('''
        INSERT INTO bets (user_id, market_id, option, amount)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], market_id, option, amount))
    
    # Update user balance
    cursor.execute('''
        UPDATE users SET balance = balance - ? WHERE id = ?
    ''', (amount, session['user_id']))
    
    conn.commit()
    conn.close()
    
    flash(f'Bet placed successfully! ${amount:.2f} on {option.replace("_", " ").title()}.', 'success')
    return redirect(url_for('market_detail', market_id=market_id))

if __name__ == '__main__':
    # Initialize database on startup
    if not os.path.exists(DATABASE):
        init_db()
        print("Database initialized with seed data.")
    else:
        # Ensure tables exist even if DB file exists
        init_db()
    
    # Run on port 5111
    app.run(debug=True, port=5111)
