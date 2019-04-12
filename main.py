import os
import html
import base64
import string
import mimetypes

from synergistic import poller, broker

with open("./templates/search.html", 'r') as file:
    search_template = string.Template(file.read())
search_html = search_template.safe_substitute({'site_name': 'Search'})

broker_client = broker.Client("127.0.0.1", 8891, broker.Type.WEBAPP)


def handle_request(channel, msg_id, payload):
    endpoint = '.' + payload['endpoint']
    print(endpoint)
    if endpoint.startswith('./static/'):
        if not os.path.abspath(endpoint).startswith(os.getcwd()):
            broker_client.respond(msg_id, {'code': 403})
            return

        if not os.path.isfile(endpoint):
            broker_client.respond(msg_id, {'code': 404})
            return

        content_type = mimetypes.guess_type(endpoint)[0]

        bytes = 'image' in content_type
        text = ''
        with open(endpoint, 'rb' if bytes else 'r') as file:
            text = file.read()

        if bytes:
            text = base64.b64encode(text).decode()

        data = {'headers': {'Content-Type': content_type + '; charset=UTF-8'}, 'body': text, 'b64d': bytes}
        broker_client.respond(msg_id, data)

    elif 'search' in payload['body']:
        data = {'query': payload['body']['search'], 'msg_id': msg_id}
        broker_client.publish('search', data, return_results)

    elif 'crawl' in payload['body']:
        url = payload['body']['crawl']
        url = html.unescape(url)
        url = url.replace('%2F', '/').replace('%3A', ':')
        url = url.replace('https://', '')
        broker_client.publish('crawl', {'url': url})
        broker_client.respond(msg_id, {'body': search_html})

    elif endpoint == "./":
        broker_client.respond(msg_id, {'body': search_html})

    else:
        broker_client.respond(msg_id, {'code': 404})


def return_results(channel, msg_id, payload):
    with open("./templates/results.html", 'r') as file:
        text = file.read()

    template = string.Template(text)
    data = payload['results']

    results = ""
    for link in data:
        results += '<div class="results"><p class="result">' + link + '</p><p class="stats">' + link + '</p></div>'

    results_html = template.safe_substitute(
        {'site_name': 'Search', 'search': payload['query'], 'results': results})
    broker_client.respond(payload['msg_id'], {'body': results_html})


if __name__ == "__main__":
    poller = poller.Poll(catch_errors=False)

    poller.add_client(broker_client)
    broker_client.subscribe('request.*', handle_request)

    poller.serve_forever()
