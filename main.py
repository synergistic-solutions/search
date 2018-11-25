import string

from synergistic import poller, server
import indexer


with open("./templates/search.html", 'r') as file:
    text = file.read()

template = string.Template(text)
html = template.safe_substitute({'site_name': 'Search'})

index = indexer.Indexer()


class Handler(server.http.Handler):

    def handle_message(self, message):
        message = message.decode('utf-8')
        method, endpoint, headers, body = self.parse(message)
        print(method, endpoint, body)

        if endpoint.startswith('/static'):
            with open("." + endpoint, 'r') as file:
                data = file.read()
            self.respond(message=data, headers={'Content-Type': 'text/css; charset=UTF-8'})
        elif 'search' in body:
            data = index.search(body['search'])

            with open("./templates/results.html", 'r') as file:
                text = file.read()

            template = string.Template(text)

            links = []
            for link in data:
                links.append('<a href="http://' + link + '">' + link + '</a>')

            results_html = template.safe_substitute({'site_name': 'Search', 'search': body['search'], 'results': '<p></p>'.join(links)})

            self.respond(message=results_html)
        else:
            self.respond(message=html)
        self.close()


if __name__ == "__main__":
    poller = poller.Poll(catch_errors=False)

    http_server = server.http.Server(handler=Handler)

    index.index("example.com", "example web site test")
    index.index("stallman.org", "Richard Stallman's web site")
    index.index("wikipedia.com", "wiki wikipedia site")
    index.index("youtube.com", "youtube video site")
    index.index("google.com", "search engine")
    index.index("google.co.uk", "search engine uk")
    index.index("twitter.com", "twitter social network")
    index.index("brookes.ac.uk", "brookes")
    index.index("moodle.brookes.ac.uk", "brookes moodle")
    index.index("brookes.ac.uk/students/careers/", "brookes careers")

    poller.add_server(http_server)

    poller.serve_forever()
