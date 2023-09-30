import requests
from datetime import datetime
# import config as config
from flask import Flask, jsonify, request

app = Flask(__name__)


def print_event_info(event):
    """Helper function to print event details and return True for use in list comprehension"""
    print(f"Event Details: \n"
          f"Subject Twitter Username: {event['subject'].get('username', 'N/A')}\n"
          f"Trader Twitter Username: {event['trader'].get('username', 'N/A')}\n"
          f"Is Buy: {event['isBuy']}\n"
          f"------------------------------")
    return True

def get_user_token_holdings(address):
    url = f"https://prod-api.kosetto.com/users/{address}/token-holdings"
    response = requests.get(url)
    data = response.json()

    # Extract token holdings for the user
    token_holdings = [
        {
            "address": user["address"],
            "twitterUsername": user["twitterUsername"],
            "balance": user["balance"]
        }
        for user in data["users"]
    ]

    return token_holdings

def get_eth_amounts_for_user(user_address):
    url = f"https://prod-api.kosetto.com/users/{user_address}/token/trade-activity"
    response = requests.get(url, headers=config.TRADING_ACTIVITY)
    
    if response.status_code != 200:
        print(f"Error fetching data for {user_address}. Status code: {response.status_code}")
        return []

    try:
        user_trades = response.json()['users']
    except ValueError:
        print(f"Invalid JSON response for {user_address}")
        return []

    eth_data = []
    for trade in user_trades:
        eth_amount = float(trade["ethAmount"]) / 1e18 if "ethAmount" in trade else None
        is_user_trade = trade["trader"].lower() == user_address.lower()

        eth_data.append({
            "ethAmount": eth_amount,
            "isUserTrade": is_user_trade,
            "createdAt": trade.get("createdAt"),
            "isBuy": trade.get("isBuy")
        })

    print(f"Retrieved {len(eth_data)} trade details for user {user_address}")
    
    return eth_data

def fetch_all_users_eth_data(address):
    tokens = get_user_token_holdings(address)

    data = []
    for token in tokens[:10]:
        token_address = token['address']
        print(f'Fetching data for purchase of {token["twitterUsername"]}')
        eth_amounts = get_eth_amounts_for_user(token_address)

        data.append({
            'token': token,
            'historical_prices': eth_amounts
        })

    print(f"Number of datasets generated for plotting: {len(data)}")
    return data

def create_scatter_plots(data):
    plots = []
    for person in data[:10]:  # Limit to the first 10 people
        
        # Extract the user's transactions
        transactions = person["historical_prices"][::-1]  # reverse the data

        # Convert timestamps into datetime format for annotations
        transaction_dates = [datetime.utcfromtimestamp(trade["createdAt"] / 1000).strftime('%Y-%m-%d %H:%M:%S') for trade in transactions]

        # Find the index of your purchase in the transactions list
        purchase_index = [idx for idx, trade in enumerate(transactions) if abs(trade["ethAmount"] - float(person['token']['balance'])) < 1e-8]

        # Set marker properties based on whether it's the user's trade or not
        marker_properties = dict(
            size=[15 if trade["isUserTrade"] else 6 for trade in transactions],
            color=['red' if idx in purchase_index else 'blue' for idx, trade in enumerate(transactions)]
        )

        # Create the plot
        plots.append(
            dcc.Graph(
                id=f'pnl-chart-{data.index(person)}',
                figure={
                    'data': [go.Scatter(
                        x=list(range(len(transactions))),
                        y=[trade["ethAmount"] for trade in transactions],
                        mode='lines+markers',
                        name=person["token"]["twitterUsername"],
                        marker=marker_properties,
                        text=transaction_dates,  # this will be displayed on hover
                        hoverinfo="x+y+text"    # display x, y, and text (date) on hover
                    )],
                    'layout': go.Layout(
                        title=f"ETH Amounts for {person['token']['twitterUsername']}",
                        xaxis=dict(title='Transaction Sequence #'),
                        yaxis=dict(title='ETH Amount')
                    )
                }
            )
        )
    return plots

# Fetch the data
# all_users_eth_data = fetch_all_users_eth_data("0x1Ec8b3B4CD301eC819Ed9925AfdFbae6B12e3F9b")

# Initialize Dash App
# app = dash.Dash(__name__)
# app.layout = html.Div(create_scatter_plots(all_users_eth_data))

# if __name__ == '__main__':
#     app.run_server(debug=True)

@app.route('/get_purchase_data/<address>', methods=['GET'])
def get_purchase_data(address):
    try:
        all_users_eth_data = fetch_all_users_eth_data(address)
        return jsonify(all_users_eth_data)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)

    