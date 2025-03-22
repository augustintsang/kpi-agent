# SalesIQ Agent

SalesIQ is an AI-powered CLI agent that uses [CrewAI](https://github.com/crewai/crewai) and Google's Gemini to investigate anomalies in sales and marketing data stored in PostgreSQL.

## Features

- 🕵️‍♀️ **Automatic Investigation**: Investigates marketing performance anomalies like CTR drops
- 🔍 **Schema Analysis**: Automatically analyzes database schema to understand data structure
- 📊 **SQL Generation**: Creates and executes optimal SQL queries to extract relevant data
- 🤖 **AI-Powered Analysis**: Uses Google's Gemini to summarize findings and identify root causes
- 📝 **Contextual Memory**: Maintains a scratchpad of actions and findings for transparent reasoning

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Google Gemini API key

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/salesiq-agent.git
cd salesiq-agent
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up your environment variables by copying the example file:

```bash
cp .env.example .env
```

4. Edit the `.env` file with your database credentials and API keys:

```
# Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# PostgreSQL Database Credentials
DB_NAME=salesiq
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432

# CrewAI Configuration
CREWAI_VERBOSE=True
```

## Database Setup

1. Create a PostgreSQL database:

```bash
createdb salesiq
```

2. Initialize the database schema:

```bash
psql -d salesiq -f db/schema.sql
```

3. Seed the database with mock data:

```bash
python -m db.seed
```

This will populate the database with sample marketing campaign data, including a simulated CTR drop anomaly in Campaign 5.

## Usage

### Basic Usage

Run the agent to investigate an anomaly:

```bash
python -m agent.run_agent "Investigate CTR drop for Campaign 5"
```

### Options

- `--output` or `-o`: Save the investigation results to a file
- `--verbose` or `-v`: Enable verbose output
- `--test-connection`: Test the database connection and exit
- `--context` or `-c`: Provide additional context (format: key1=value1,key2=value2)

### Examples

Test database connection:

```bash
python -m agent.run_agent --test-connection
```

Run an investigation with additional context:

```bash
python -m agent.run_agent "Investigate conversion rate changes for Campaign 3" --context timeframe=last_30_days,focus=mobile_devices
```

Save results to a file:

```bash
python -m agent.run_agent "Investigate CTR drop for Campaign 5" --output investigation_results.md
```

## Project Structure

```
salesiq-agent/
├── agent/
│   ├── config.py                # CrewAI agent configuration
│   ├── scratchpad.py            # In-memory memory log
│   └── run_agent.py             # CLI entrypoint
│
├── tools/
│   ├── run_sql.py               # Tool to execute SQL queries on PostgreSQL
│   ├── get_schema.py            # Tool to retrieve table schemas
│   └── summarizer.py            # Tool to summarize results using Gemini
│
├── db/
│   ├── schema.sql               # SQL script to define tables
│   ├── seed.py                  # Script to seed mock data into the database
│   └── connection.py            # PostgreSQL connection helper
│
├── prompts/
│   └── summarizer_prompt.txt    # Gemini prompt instructions for summarization
│
├── .env                         # API keys and DB credentials
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Testing

The seed script creates a simulated CTR drop anomaly in Campaign 5 after day 20. You can test the agent's ability to detect and analyze this anomaly with:

```bash
python -m agent.run_agent "Investigate CTR drop for Campaign 5"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [CrewAI](https://github.com/crewai/crewai) for the agent framework
- Google's Gemini API for language capabilities 