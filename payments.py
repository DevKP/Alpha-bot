from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from urllib.parse import quote_plus

bot = None

waiting_payments = {}
generated_payments = {}

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, type):
        self.send_response(200)
        self.send_header('Content-type', type)
        self.end_headers()

    def do_GET(self):
        if ".html" in self.path:
            self._set_headers('text/html')
        if ".css" in self.path:
            self._set_headers('text/css')

        qs = {}
        path = self.path
        if '?' in path:
            path, tmp = path.split('?', 1)
            qs = parse_qs(tmp)

        tuid = qs.get('TUID')
        if tuid:
            paymentid = generated_payments.get(tuid[0])
            if not paymentid:
                self.wfile.write(b"<html><head><title>Donate</title></head><body>Error</body></html>")
                return       

            with open('./payment_page{}'.format(path), 'rb') as page:
                page_content = bytes(page.read().decode('utf-8').format(successURL=quote_plus("http://alphaofftop.tk/payment1.html?PUID=" + paymentid)), "utf-8") 
                self.wfile.write(page_content)
            return

        with open('./payment_page{}'.format(path), 'rb') as page:
            self.wfile.write(page.read())

        puid = qs.get('PUID')
        if puid:
            message = waiting_payments.get(puid[0])
            if message:
                bot.send_message('-1001125742098', "*Большое спасибо {} {}(@{})!*".format(message.from_user.first_name,message.from_user.last_name,message.from_user.username), parse_mode='Markdown')
                print(user)
                waiting_payments.pop(puid[0])
                generated_payments.pop(str(message.from_user.id))

def run():
  server_address = ('176.37.39.165', 80)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  httpd.serve_forever()