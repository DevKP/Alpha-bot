from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

bot = None

waiting_payments = {}

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()

        qs = {}
        path = self.path
        if '?' in path:
            path, tmp = path.split('?', 1)
            qs = parse_qs(tmp)

        with open('./payment_page{}'.format(path), 'rb') as page:
            self.wfile.write(page.read())

        puid = qs.get('PUID')
        if puid:
            user = waiting_payments.get(puid[0])
            if user:
                bot.send_message('-1001125742098', "*Чпоньк @{}*".format(user.username), parse_mode='Markdown')
                print(user)

def run():
  server_address = ('176.37.39.165', 80)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  httpd.serve_forever()