import server
import poller
import string


class Handler(server.http.Handler):

    def handle_message(self, message):
        message = message.decode('utf-8')
        method, endpoint, headers, body = self.parse(message)

        print(method, endpoint)

        with open("./templates/search.html", 'r') as file:
            text = file.read()

        template = string.Template(text)
        html = template.safe_substitute({'site_name': 'Search'})

        self.respond(message=html)
        self.close()


if __name__ == "__main__":
    poller = poller.Poll(catch_errors=False)

    http_server = server.http.Server(handler=Handler)
    poller.add_server(http_server)

    poller.serve_forever()
