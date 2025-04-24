## Simple Flask Utility

This micro-service exposes three tiny utilities behind a single GET / endpoint:

Query parameter | What it does
|---|---|
queryAirportTemp | Returns the current air temperature (°C) at a given 3-letter IATA airport code.
queryStockPrice | Returns the latest regular-market price of a US-listed equity symbol.
queryEval | Safely evaluates a basic arithmetic expression and returns the numeric result.

> **Note**
Exactly **one** parameter must be supplied for every request.

## Quick Start

Clone & install:

```bash
git clone https://github.com/your-org/flask-utilities.git
cd flask-utilities
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

```
Export your RapidAPI key (only needed for stock quotes):

```bash
export RAPIDAPI_KEY='xxxxxxxxxxxxxxxxxxxxxxx'
```

Run the app:
```bash
python app.py            # listens on http://127.0.0.1:5000/
```

## Examples

#### Current temperature at Prague Airport (PRG) in XML

```bash
curl -H "Accept: application/xml" "http://localhost:5000/?queryAirportTemp=PRG"
```

Sample output:
```html
<result>14.7</result>
```

#### Latest price for Microsoft (MSFT)

```bash
curl "http://localhost:5000/?queryStockPrice=MSFT"
```

#### Evaluate an arithmetic expression

```bash
curl "http://localhost:5000/?queryEval=(7+5)*3-2/4"
```