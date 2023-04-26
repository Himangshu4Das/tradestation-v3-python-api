import http.server
import socketserver
import requests
import webbrowser


"""
    Get Auth0 auth-code through login from TradeStation.
    This code will later be used to generate refresh_code.
    """

# Replace the key/ client_id in the credentials.txt file.
with open('credentials.txt', 'r') as f:
    AUTH0_CLIENT_ID = f.readline().strip().split(': ')[-1]
print(AUTH0_CLIENT_ID)

# Replace AUTH0_SCOPE if required.
AUTH0_SCOPE = 'openid offline_access profile MarketData ReadAccount Trade Crypto Matrix OptionSpreads'

# Change the redirect_uri with any another port on localhost if required or set custom redirect_uri that you
# requested from TradeStation. Read more about redirect_uri and allowed default redirect_uri.
REDIRECT_URI = 'http://localhost:3000/'

# Generate the authorization URL
url = ('https://signin.tradestation.com/authorize?response_type=code&client_id={'
       '}&audience=https://api.tradestation.com&redirect_uri={}&scope={}').format(AUTH0_CLIENT_ID, REDIRECT_URI,
                                                                                  AUTH0_SCOPE)
print(url)

# Open the authorization URL in Chrome
webbrowser.open_new(url)

# Start the HTTP server to listen for the callback
class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        code = self.path.split('=')[-1]
        # Save the authorization code to a text file
        with open('auth_code.txt', 'w') as f:
            f.write(code)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes('<html><body>Authorization code saved to file.</body></html>', 'utf-8'))
        self.server.shutdown()


with socketserver.TCPServer(("", 3000), CallbackHandler) as httpd:
    httpd.serve_forever()

print("Authorization code saved to file.")
