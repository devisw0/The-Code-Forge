import yfinance as yf

def price(company:str):
    """
    A tool to get the current stock price for a given ticker symbol.

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., "AAPL").

    Returns:
        str: A string containing the current price or an error message.
    """

    ticker = yf.Ticker(company)
    current_price = ticker.info.get('currentPrice')
   
    if current_price:
        return f"The current price for {company} is {current_price}"
    else:
        return f"{company} is not a valid stock in yfinance"
    


def historical_data(company:str,period:str=None):
    """
    A tool to fetch historical stock data for a given ticker symbol.

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., "TSLA").
        period (str): The time period for the data (e.g., "1y", "6mo", "1d"). Default is "1y".

    Returns:
        str: A string of the historical data in CSV format or an error message.
    """
    try:

        ticker = yf.Ticker(company)
        history = ticker.history(period=period)
        if history.empty:
            return f"Error: No data found for ticker '{company}'. Please check the symbol and period."
            
            # Return the data as a clean, LLM-friendly CSV string
        return history.to_csv()

    except Exception as e:
            return f"Error: An unexpected error occurred. Details: {e}"
    



def get_option_dates(company: str):
    """
    A tool to get the upcoming option expiration dates for a given ticker symbol.

    Args:
        company (str): The stock ticker symbol (e.g., "AAPL").

    Returns:
        str: A string listing up to 10 upcoming option expiration dates, 
             or an error message.
    """
    try:
        stock = yf.Ticker(company)
        exp_dates = stock.options

        if exp_dates:
            # Correctly slice to get the first 10 dates
            upcoming_dates = exp_dates[:10]
            
            # Use an f-string to correctly insert the variable into the string
            return f"Found {len(upcoming_dates)} upcoming option dates for {company}: {upcoming_dates}"
        else:
            return f"No option dates found for '{company}'. The stock may not have options."

    except Exception as e:
        # This catches any other errors, like an invalid ticker
        return f"Error: Failed to process ticker '{company}'. It may not exist. Details: {e}"