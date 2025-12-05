# PredictionMarket

A Polymarket-style prediction market web application built with Flask. Users can create and bet on binary ("this or that") and over/under markets using virtual currency.

## Features

- **User Authentication**: Secure signup/login system with password hashing
- **Virtual Wallet**: Each user starts with $1,000 in virtual currency
- **Two Market Types**:
  - **Binary Markets**: Choose between two options (e.g., "NVidia vs Google")
  - **Over/Under Markets**: Bet on whether a value will be over or under a target (e.g., "TWiT length > 3.5 hours")
- **Real-time Sentiment**: Visual "tug of war" bar showing market sentiment based on betting volume
- **Market Creation**: Users can create their own prediction markets
- **Betting System**: Place bets on active markets with automatic balance management
- **Market Statistics**: View total volume, number of bets, and your position

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS (modern glassmorphism design), JavaScript
- **Security**: Werkzeug password hashing

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd /path/to/twitdemo
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python3 app.py
   ```

5. **Access the application**:
   Open your browser and navigate to: `http://127.0.0.1:5111`

## Database

The application uses SQLite with the following schema:

- **users**: User accounts with authentication and balance
- **markets**: Prediction markets (binary and over/under types)
- **bets**: User bets on markets

The database is automatically initialized on first run with two seed markets:
1. Binary market: "Who will win the AI chip race?" (NVidia vs Google)
2. Over/Under market: "Length of TWiT on Sunday" (> 3.5 hours)

## Usage

### Creating an Account

1. Navigate to the signup page
2. Choose a username and password
3. You'll automatically receive $1,000 to start betting

### Placing Bets

1. Log in to your account
2. Browse active markets on the dashboard
3. Click on a market to view details
4. Enter your bet amount and select an option
5. Confirm your bet (balance will be deducted automatically)

### Creating Markets

1. Click "Create Market" from the dashboard
2. Choose market type (Binary or Over/Under)
3. Fill in the required details:
   - **Binary**: Question and two options
   - **Over/Under**: Question, target value, and unit
4. Submit to create the market

## Project Structure

```
twitdemo/
├── app.py                      # Main Flask application
├── schema.sql                  # Database schema documentation
├── predictionmarket.db         # SQLite database (auto-generated)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── static/
│   └── style.css              # Application styling
├── templates/
│   ├── base.html              # Base template with navigation
│   ├── login.html             # Login page
│   ├── signup.html            # Signup page
│   ├── dashboard.html         # Main dashboard with market list
│   ├── market_detail.html     # Individual market view
│   └── create_market.html     # Market creation form
└── .venv/                     # Virtual environment (if created)
```

## Configuration

### Security

**IMPORTANT**: Before deploying to production, change the secret key in `app.py`:

```python
app.secret_key = 'your-secret-key-change-in-production'  # Change this!
```

Generate a secure secret key:
```python
import secrets
print(secrets.token_hex(32))
```

### Port Configuration

The application runs on port 5111 by default. To change this, modify the last line in `app.py`:

```python
app.run(debug=True, port=5111)  # Change port number here
```

## Development

### Debug Mode

Debug mode is enabled by default for development. Disable it in production:

```python
app.run(debug=False, port=5111)
```

### Database Reset

To reset the database and start fresh:

```bash
rm predictionmarket.db
python3 app.py  # Will recreate with seed data
```

## API Endpoints

- `GET /` - Home page (redirects to dashboard or login)
- `GET/POST /signup` - User registration
- `GET/POST /login` - User authentication
- `GET /logout` - User logout
- `GET /dashboard` - Main dashboard with active markets
- `GET /market/<id>` - Market detail page
- `GET/POST /create_market` - Market creation
- `POST /place_bet` - Place a bet on a market

## Future Enhancements

- Market resolution system
- User portfolio/history page
- Market search and filtering
- Real-time updates with WebSockets
- Payout calculations for resolved markets
- User leaderboard
- Market comments/discussion
- Mobile responsive design improvements

## License

This is a demo project for educational purposes.

## Support

For issues or questions, please refer to the code comments or create an issue in the project repository.
