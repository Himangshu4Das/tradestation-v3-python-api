import requests
import http.server
import socketserver
import requests
import webbrowser
from datetime import datetime, timedelta
import json

"""
    === IMPLEMENTATION OF TRADESTATION'S VERSION3 ENDPOINTS USING AUTH0 KEYS ===
    
    Only for HTTP requests.
    It would be better to use the HTTP streams directly from main scripts.
    Generate Auth0 Code using the Generate_AuthCode.py file first if refresh code has never been created.
    
    Auth0 code and refresh code should only be generated once since post refresh token generation, the expiry of 
    refresh token is set infinite. Refresh code expiry time can be changed by contacting TradeStation support.
    
    In case the expiry time of refresh is set ot a certain limit. You will have to generate auth code and refresh code post expiries."""


class CreateTSClient:

    def __init__(self, key: str, secret: str, redirect_uri='http://localhost:3000/'):
        """
        :param key: Your API client ID or key.
        :param secret: Your API secret key.
        :param redirect_uri: Specify a different port on localhost or custom redirect_uri if requested from TradeStation. Default port is 3000.
        """
        self.key = key
        self.secret = secret
        self.redirect_uri = redirect_uri
        self.token_url = 'https://signin.tradestation.com/oauth/token'

        # load access token
        with open('access_token.txt', 'r') as f:
            self.access_token = f.readline().strip()
            self.access_token_expiry = datetime.strptime(f.readline().strip(), '%Y-%m-%d %H:%M:%S')

    # ===================================== LOGINs ==================================================

    def fetch_refresh_token(self):
        """

        Fetches the refresh token.
        :return: refresh token and access token. Access token is ignored and recreated for simplicity.

        """
        print('=' * 25)
        # Read the authorization code from the text file
        with open('auth_code.txt', 'r') as f:
            auth_code = f.read()
        print(auth_code)

        # Send a POST request to the token endpoint to obtain a refresh token
        response = requests.post(
            self.token_url,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.key,
                'client_secret': self.secret
            }
        )
        try:
            ref_token = response.json()['refresh_token']
            ref_ac_token = response.json()['access_token']

            # Write the refresh token to a text file
            with open('refresh_token.txt', 'w') as f:
                f.write(ref_token)

            # Write the access token to a text file
            with open('refresh_access_token.txt', 'w') as f:
                f.write(ref_ac_token)

            # Print a success message
            print(f'Refresh token saved to refresh_token.txt')
            print(f'Refresh access token saved to refresh_access_token.txt')
            # Return refresh token and access token along with it
            return ref_token, ref_ac_token

        except Exception as e:
            print(e)
            print('Unable to fetch refresh token!')
        print('=' * 25)

    def fetch_access_token(self):
        """

        Get access token and expiry time of the same. Return it and save it in a text file.
        :return: Access token and expiry time in datetime format.

        """
        print('=' * 25)
        # Read the authorization code from the text file
        with open('refresh_token.txt', 'r') as f:
            ref_token = f.read()
        print(ref_token)
        # Send a POST request to the token endpoint to obtain a refresh token
        response = requests.post(
            self.token_url,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'refresh_token',
                'redirect_uri': self.redirect_uri,
                'client_id': self.key,
                'client_secret': self.secret,
                'refresh_token': ref_token
            }
        )
        self.access_token = response.json()['access_token']
        self.access_token_expiry = datetime.now() + timedelta(seconds=response.json()['expires_in'] - 60)
        self.access_token_expiry = self.access_token_expiry.strftime('%Y-%m-%d %H:%M:%S')

        # Write the access token and expiry time to a text file
        with open('access_token.txt', 'w') as f:
            f.write(self.access_token)
            f.write('\n')
            f.write(self.access_token_expiry)

        # Print a success message
        print(f'Access token saved to access_token.txt')
        print(self.access_token_expiry)
        self.access_token_expiry = datetime.strptime(self.access_token_expiry, '%Y-%m-%d %H:%M:%S')
        print('=' * 25)
        return self.access_token, self.access_token_expiry

    def get_saved_access_token(self):
        """
        Get previously stored access token and expiry datetime
        :return:
        """
        with open('access_token.txt', 'r') as f:
            self.access_token = f.readline().strip()
            self.access_token_expiry = f.readline().strip()

        return self.access_token, self.access_token_expiry

    # ======================================= MARKET DATA =======================================================

    def fetch_bars(self, symbol):
        """
        Get market data bars for specified ticker/ symbol
        eg. AAPL
        """
        bar_url = "https://api.tradestation.com/v3/marketdata/barcharts/{}".format(symbol)

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.request("GET", bar_url, headers=headers)

        return response.text

    def fetch_symbol_details(self, symbols):
        """
        Fetch details for the specified symbol or symbols.
        The symbol or symbols should be in a list.
        You can get details for a maximum of 50 symbols at a time.
        :param symbols: list or string of symbol or symbols.
        :return: Symbol details.

        """
        if isinstance(symbols, str):
            symbols = [symbols]

        sd_url = "https://api.tradestation.com/v3/marketdata/symbols/{}"
        symbol_str = ",".join(symbols)
        sd_url = sd_url.format(symbol_str)

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.request("GET", sd_url, headers=headers)

        return response.text

    def fetch_interests(self):
        """
        :return: Return interest rates of cryptocurrencies
        """
        url = "https://api.tradestation.com/v3/marketdata/crypto/interestrates"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request("GET", url, headers=headers)

        return response.text

    def fetch_opt_expirations(self, symbol):
        """
        Get expiration dates for specified underlying symbol.
        """
        bar_url = "https://api.tradestation.com/v3/marketdata/options/expirations/{}".format(symbol)

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.request("GET", bar_url, headers=headers)

        return response.text

    def fetch_opt_risk_reward(self, payload):
        """
        :param payload: Spread details with same strictly expirations.
        :return: Risk reward information such as:
                MaxGainIsInfinite, AdjustedMaxGain, MaxLossIsInfinite, AdjustedMaxLoss, BreakevenPoints
        payload example:
        payload = {
            "SpreadPrice": 0,
            "Legs": [
                {
                    "Symbol": "string",
                    "Quantity": 0,
                    "TradeAction": "BUY"
                }
            ]
        }
        """

        risk_reward_url = "https://api.tradestation.com/v3/marketdata/options/riskreward"

        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.request("POST", risk_reward_url, json=payload, headers=headers)
        return response.text

    def fetch_opt_strikes(self, symbol):
        """
        Fetch strike prices for an underlying.
        :return: collection of strikes.
        """
        bar_url = "https://api.tradestation.com/v3/marketdata/options/strikes/{}".format(symbol)

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.request("GET", bar_url, headers=headers)

        return response.text

    def fetch_spread_types(self):
        """
        Fetch spread types.
        """
        st_url = "https://api.tradestation.com/v3/marketdata/options/spreadtypes"

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.request("GET", st_url, headers=headers)

        return response.text

    def fetch_quotes(self, symbols):
        """
        Get quotes for specified symbols.
        The symbol or symbols should be in a list or string(allowed for single symbol).
        You can get details for a maximum of 50 symbols at a time.
        :param symbols: list or string of symbol or symbols.
        :return: Symbol details.

        """
        if isinstance(symbols, str):
            symbols = [symbols]

        q_url = "https://api.tradestation.com/v3/marketdata/quotes/{}"
        symbol_str = ",".join(symbols)
        q_url = q_url.format(symbol_str)

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.request("GET", q_url, headers=headers)

        return response.text

    # =========================================== BROKERAGE ===================================================
    def fetch_accounts(self, sim=True):
        """
        Fetch listed accounts.
        """
        if sim:
            acc_url = "https://sim-api.tradestation.com/v3/brokerage/accounts"
        else:
            acc_url = "https://api.tradestation.com/v3/brokerage/accounts"

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.request("GET", acc_url, headers=headers)

        return response.text

    def fetch_balances(self, accounts, sim=True):
        """
        Fetch account balances for one or multiple accounts if passed as list.
        :param accounts: account in string or accounts in list.
        :param sim: Sim set to True will access the simulator endpoints.
        :return: Account balances.
        """
        if sim:
            bal_url = "https://sim-api.tradestation.com/v3/brokerage/accounts/{}/balances"
        else:
            bal_url = "https://api.tradestation.com/v3/brokerage/accounts/{}/balances"

        if isinstance(accounts, str):
            accounts = [accounts]
        accounts_str = ", ".join(accounts)
        bal_url = bal_url.format(accounts_str)
        print(bal_url)

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request("GET", bal_url, headers=headers, timeout=20)

        return response.text

    def fetch_bod_balances(self, accounts, sim=True):
        """
        Fetch beginning of day balances for one or multiple accounts if passed as list.
        :param accounts: account in string or accounts in list.
        :param sim: Sim set to True will access the simulator endpoints.
        :return: Account balances.
        """
        if sim:
            bod_bal_url = "https://sim-api.tradestation.com/v3/brokerage/accounts/{}/bodbalances"
        else:
            bod_bal_url = "https://api.tradestation.com/v3/brokerage/accounts/{}/bodbalances"

        if isinstance(accounts, str):
            accounts = [accounts]
        accounts_str = ", ".join(accounts)
        bod_bal_url = bod_bal_url.format(accounts_str)

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request("GET", bod_bal_url, headers=headers, timeout=20)

        return response.text

    def fetch_hist_orders(self, accounts, since_date, sim=True):
        """
        Fetch orders for one or multiple accounts if passed as list.
        :param accounts: account in string or accounts in list.
        :param since_date: starting date for historical orders(string only with format YYYY-mm-dd).
        :param sim: Sim set to True will access the simulator endpoints.
        :return: Historical orders for given accounts and time range.
        """
        if sim:
            hist_orders_url = "https://sim-api.tradestation.com/v3/brokerage/accounts/{}/historicalorders"
        else:
            hist_orders_url = "https://api.tradestation.com/v3/brokerage/accounts/{}/historicalorders"

        if isinstance(accounts, str):
            accounts = [accounts]

        query = {"since": since_date}

        accounts_str = ", ".join(accounts)
        hist_orders_url = hist_orders_url.format(accounts_str)

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request("GET", hist_orders_url, headers=headers, params=query)

        return response.text

    def fetch_hist_orders_by_oid(self, accounts, since_date, o_id, sim=True):
        """
        Fetch order details for specified order IDs for one or multiple accounts if passed as list.
        :param accounts: account in string or accounts in list.
        :param since_date: starting date for historical orders(string only with format YYYY-mm-dd).
        :param sim: Sim set to True will access the simulator endpoints.
        :param o_id: list of order ID/s.
        :return: Historical orders for given accounts and time range.
        """
        if sim:
            hist_orders_oid_url = "https://sim-api.tradestation.com/v3/brokerage/accounts/{}/historicalorders/{}"
        else:
            hist_orders_oid_url = "https://api.tradestation.com/v3/brokerage/accounts/{}/historicalorders/{}"

        if isinstance(accounts, str):
            accounts = [accounts]

        if isinstance(o_id, str):
            o_id = [o_id]

        query = {"since": since_date}

        accounts_str = ", ".join(accounts)
        o_id_str = ", ".join(o_id)

        hist_orders_oid_url = hist_orders_oid_url.format(accounts_str, o_id_str)

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request("GET", hist_orders_oid_url, headers=headers, params=query)

        return response.text

    def fetch_positions(self, account, sim=True):
        """
        Fetch placed positions of the account

        :param account: Account number
        :param sim: Set to True to use the simulation account
        :return: Placed Positions
        """
        if sim:
            pos_url = "https://sim-api.tradestation.com/v3/brokerage/accounts/{}/positions".format(account)
        else:
            pos_url = "https://api.tradestation.com/v3/brokerage/accounts/{}/positions".format(account)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request("GET", pos_url, headers=headers, timeout=20)

        return response.text

    def fetch_orders(self, accounts, sim=True):
        """
        Fetch account orders for one or multiple accounts if passed as list.
        :param accounts: account in string or accounts in list.
        :param sim: Sim set to True will access the simulator endpoints.
        :return: Orders for given accounts.
        """
        if sim:
            orders_url = "https://sim-api.tradestation.com/v3/brokerage/accounts/{}/orders"
        else:
            orders_url = "https://api.tradestation.com/v3/brokerage/accounts/{}/orders"

        if isinstance(accounts, str):
            accounts = [accounts]
        accounts_str = ", ".join(accounts)
        orders_url = orders_url.format(accounts_str)
        print(orders_url)

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request("GET", orders_url, headers=headers, timeout=20)

        return response.text

    def fetch_orders_by_oid(self, accounts, o_id, sim=True):
        """
        Fetch order details for specified order IDs for one or multiple accounts if passed as list.
        :param accounts: account in string or accounts in list.
        :param sim: Sim set to True will access the simulator endpoints.
        :param o_id: list of order ID/s.
        :return: Orders for given accounts and order IDs.
        """
        if sim:
            orders_oid_url = "https://sim-api.tradestation.com/v3/brokerage/accounts/{}/orders/{}"
        else:
            orders_oid_url = "https://api.tradestation.com/v3/brokerage/accounts/{}/orders/{}"

        if isinstance(accounts, str):
            accounts = [accounts]

        if isinstance(o_id, str):
            o_id = [o_id]

        accounts_str = ", ".join(accounts)
        o_id_str = ", ".join(o_id)

        orders_oid_url = orders_oid_url.format(accounts_str, o_id_str)

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request("GET", orders_oid_url, headers=headers)

        return response.text

    def get_crypto_wallets(self, crypto_account):
        """
        Fetch information for specified cryptocurrency wallet.
        :param crypto_account: A Cryptocurrency wallet account ID.
        :return: Wallet information.
        """
        wallet_url = "https://api.tradestation.com/v3/brokerage/accounts/{}/wallets".format(crypto_account)

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request("GET", wallet_url, headers=headers)

        return response.text

    # =========================================== EXECUTION ===================================================
    def confirm_order(self, payload):
        """
        IMPORTANT : confirm_order only returns the estimated information for the intended order without it being placed.

        payload example:
        payload = {
            "AccountID": "123456782",
            "Symbol": "MSFT",
            "Quantity": "10",
            "OrderType": "Market",
            "TradeAction": "BUY",
            "TimeInForce": {"Duration": "DAY"},
            "Route": "Intelligent"
        }

        :param payload: Pass a dictionary imitating the order you wish to place. This will only estimate pricing and
        info. and not place any order. :return: Order estimated pricing, commision and other information.
        """
        confirm_url = "https://api.tradestation.com/v3/orderexecution/orderconfirm"

        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.request("POST", confirm_url, json=payload, headers=headers)

        return response.text

    def confirm_group_order(self, payload):
        """
        IMPORTANT : confirm_group_order only returns the estimated information for the intended order without it
        being placed. Fetch estimated information for a group of orders.

        payload example:
        payload = {
            "Type": "OCO",
            "Orders": [
                {
                    "AccountID": "123456782",
                    "Symbol": "MSFT",
                    "Quantity": "10",
                    "OrderType": "Limit",
                    "TradeAction": "BUY",
                    "LimitPrice": "230.00",
                    "Route": "Intelligent",
                    "TimeInForce": {"Duration": "DAY"}
                },
                {
                    "AccountID": "123456782",
                    "Symbol": "MSFT",
                    "Quantity": "10",
                    "OrderType": "StopMarket",
                    "TradeAction": "BUY",
                    "Route": "Intelligent",
                    "TimeInForce": {"Duration": "DAY"},
                    "AdvancedOptions": {"TrailingStop": {"Percent": "5.0"}}
                }
            ]
        }

        Type : Order types can be BRK, OCO and NORMAL

        Order Cancels Order (OCO) An OCO order is a group of orders whereby if one of the orders is filled or
        partially-filled, then all the other orders in the group are cancelled.

        Bracket OCO Orders A bracket order is a special instance of an OCO (Order Cancel Order). Bracket orders are
        used to exit an existing position. They are designed to limit loss and lock in profit by “bracketing” an
        order with a simultaneous stop and limit order.

        :param payload: Pass a dictionary imitating the group of orders you wish to place. This will only estimate
        pricing and information and won't place any order. :return: Order estimated pricing, commision and other
        information.
        """
        confirm_group_url = "https://api.tradestation.com/v3/orderexecution/orderconfirm"

        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.request("POST", confirm_group_url, json=payload, headers=headers)

        return response.text

    def place_orders(self, payload, sim=True):
        """

        payload example:
        payload = {
            "AccountID": "123456782",
            "Symbol": "MSFT",
            "Quantity": "10",
            "OrderType": "Market",
            "TradeAction": "BUY",
            "TimeInForce": {"Duration": "DAY"},
            "Route": "Intelligent"
        }

        :param sim: Set to true if the orders are to be placed in simulation account.
        :param payload: Order details to be placed.
        :return: Response.
        """

        if sim:
            place_order_url = "https://sim-api.tradestation.com/v3/orderexecution/orders"
        else:
            place_order_url = "https://api.tradestation.com/v3/orderexecution/orders"

        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.request("POST", place_order_url, json=payload, headers=headers)

        return response.text

    def place_group_orders(self, payload, sim=True):
        """

        payload example:
        payload = {
            "Type": "OCO",
            "Orders": [
                {
                    "AccountID": "123456782",
                    "Symbol": "MSFT",
                    "Quantity": "10",
                    "OrderType": "Limit",
                    "TradeAction": "BUY",
                    "LimitPrice": "230.00",
                    "Route": "Intelligent",
                    "TimeInForce": {"Duration": "DAY"}
                },
                {
                    "AccountID": "123456782",
                    "Symbol": "MSFT",
                    "Quantity": "10",
                    "OrderType": "StopMarket",
                    "TradeAction": "BUY",
                    "Route": "Intelligent",
                    "TimeInForce": {"Duration": "DAY"},
                    "AdvancedOptions": {"TrailingStop": {"Percent": "5.0"}}
                }
            ]
        }

        :param sim: Set to true if the orders are to be placed in simulation account.
        :param payload: Group order details to be placed.
        :return: Response.
        """

        if sim:
            place_group_order_url = "https://sim-api.tradestation.com/v3/orderexecution/ordergroups"
        else:
            place_group_order_url = "https://api.tradestation.com/v3/orderexecution/ordergroups"

        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.request("POST", place_group_order_url, json=payload, headers=headers)

        return response.text

    def replace_order(self, o_id, payload, sim=True):
        """
        Modify an active order that is not yet filled.

        payload example:
        payload = {
            "Quantity": "10",
            "OrderType": "Limit",
            "LimitPrice": "132.52"
        }

        :param o_id: OrderID you wish to update.
        :param payload: Changes for update ( Quantity, OrderType and LimitPrice)
        :param sim: Set to true if you need to work on simulation account.
        :return: Response.
        """

        if sim:
            replace_url = "https://sim-api.tradestation.com/v3/orderexecution/orders/{}".format(o_id)
        else:
            replace_url = "https://api.tradestation.com/v3/orderexecution/orders/{}".format(o_id)

        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.request("PUT", replace_url, json=payload, headers=headers)

        return response.text

    def cancel_order(self, o_id, sim=True):
        """
        Cancel an active order that is not yet filled.

        :param o_id: OrderID you wish to cancel.
        :param sim: Set to true if you need to work on simulation account.
        :return: Response.
        """

        if sim:
            cancel_url = "https://sim-api.tradestation.com/v3/orderexecution/orders/{}".format(o_id)
        else:
            cancel_url = "https://api.tradestation.com/v3/orderexecution/orders/{}".format(o_id)

        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.request("DELETE", cancel_url, headers=headers)

        return response.text

    def fetch_activation_triggers(self):
        """
        :return: List of valid activation trigger methods.
        """

        act_url = "https://api.tradestation.com/v3/orderexecution/activationtriggers"

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.request("GET", act_url, headers=headers)

        return response.text

    def fetch_routes(self):
        """
        :return: Fetch a list of available routes for placing an order.
        """
        routes_url = "https://api.tradestation.com/v3/orderexecution/routes"

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.request("GET", routes_url, headers=headers)

        return response.text
