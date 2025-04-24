# app.py
from flask import Flask, request, Response, abort
import requests
import ast

app = Flask(__name__)
RAPIDAPI_KEY = "87e8559442mshbf9de432bb5b1cfp191e31jsnf3bfe3fa5aac"

def safe_eval(expr: str) -> float:
    """
    Evaluate an arithmetic expression containing integers, +, -, *, /, and parentheses.
    Raises ValueError on any unsupported syntax.
    """
    node = ast.parse(expr, mode='eval')
    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp):
            l = _eval(n.left)
            r = _eval(n.right)
            if isinstance(n.op, ast.Add):   return l + r
            if isinstance(n.op, ast.Sub):   return l - r
            if isinstance(n.op, ast.Mult):  return l * r
            if isinstance(n.op, ast.Div):   return l / r
        if isinstance(n, ast.UnaryOp):
            v = _eval(n.operand)
            if isinstance(n.op, ast.UAdd):  return +v
            if isinstance(n.op, ast.USub):  return -v
        raise ValueError(f"Unsupported expression: {ast.dump(n)}")
    return _eval(node)

@app.route('/', methods=['GET'])
def index():
    params = request.args
    ops = {
        'queryAirportTemp':   handle_airport_temp,
        'queryStockPrice':    handle_stock_price,
        'queryEval':          handle_eval,
    }
    present = [k for k in ops if k in params]
    if len(present) != 1:
        abort(400, "Exactly one of queryAirportTemp, queryStockPrice or queryEval must be provided")
    key = present[0]
    try:
        result = ops[key](params[key])
    except requests.RequestException as e:
        abort(502, f"Upstream service error: {e}")
    except (IndexError, KeyError, ValueError) as e:
        abort(400, str(e))

    accept = request.headers.get('Accept', '')
    if 'application/xml' in accept or 'text/xml' in accept:
        body = f"<result>{result}</result>"
        mimetype = 'application/xml'
    else:
        body = str(result)
        mimetype = 'application/json'
    return Response(body, mimetype=mimetype)


def handle_airport_temp(iata: str) -> float:
    iata = iata.upper()
    if not (iata.isalpha() and len(iata) == 3):
        raise ValueError("IATA code must be three letters")
    r = requests.get(f"https://airport-data.com/api/ap_info.json?iata={iata}")
    info = r.json()
    lat, lon = info.get('latitude'), info.get('longitude')
    if lat is None or lon is None:
        raise ValueError(f"Airport {iata} not found")
    w = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={'latitude': lat, 'longitude': lon, 'current_weather': 'true', 'temperature_unit': 'celsius'}
    )
    weather = w.json().get('current_weather')
    if not weather or 'temperature' not in weather:
        raise ValueError("Weather data not available")
    return weather['temperature']


def handle_stock_price(symbol: str) -> float:
    symbol = symbol.upper()
    if not (1 <= len(symbol) <= 5 and symbol.isalnum()):
        raise ValueError("Stock symbol must be 1–5 alphanumeric characters")

    if not RAPIDAPI_KEY:
        raise ValueError("Missing RapidAPI key (set RAPIDAPI_KEY env-var)")
    url = f"https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/v2/get-summary"
    headers = {
        "x-rapidapi-key":  RAPIDAPI_KEY,
        "x-rapidapi-host": "apidojo-yahoo-finance-v1.p.rapidapi.com",
    }
    params = {"symbol": symbol, "region": "US"}

    resp = requests.get(url, params=params, headers=headers, timeout=5)
    
    stock_list = resp.json().get("marketSummaryAndSparkResponse", {}).get("result", [])
    if not stock_list:
        raise ValueError(f"Price for {symbol} not available")

    price_raw = (
        stock_list[0]
        .get("regularMarketPrice", {})
        .get("raw")
    )

    if price_raw is None:
        raise ValueError("Price not available")

    return float(price_raw)


def handle_eval(expr: str) -> float:
    return safe_eval(expr)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
