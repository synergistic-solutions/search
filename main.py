import os
import string
import html

from synergistic import poller, broker

with open("./templates/search.html", 'r') as file:
    text = file.read()

template = string.Template(text)
html_data = template.safe_substitute({'site_name': 'Search'})

broker_client = broker.client.Client("127.0.0.1", 8891, broker.Type.APPLICATION)


def handle_request(channel, msg_id, payload):
    endpoint = '.' + payload['endpoint']
    if endpoint.startswith('./static/'):
        if not os.path.abspath(endpoint).startswith(os.getcwd()):
            broker_client.respond(msg_id, {'code': 403})
            return

        if not os.path.isfile(endpoint):
            broker_client.respond(msg_id, {'code': 404})
            return

        data = {'headers': {'Content-Type': 'text/css; charset=UTF-8'}}
        with open(endpoint, 'r') as file:
            data['body'] = file.read()
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
        broker_client.respond(msg_id, {'body': html_data})

    else:
        broker_client.respond(msg_id, {'body': html_data})


def return_results(channel, msg_id, payload):
    with open("./templates/results.html", 'r') as file:
        text = file.read()

    template = string.Template(text)
    data = payload['results']

    links = []
    for link in data:
        links.append('<a href="http://' + link + '">' + link + '</a>')

    results_html = template.safe_substitute(
        {'site_name': 'Search', 'search': payload['query'], 'results': '<p></p>'.join(links)})
    broker_client.respond(payload['msg_id'], {'body': results_html})


if __name__ == "__main__":
    poller = poller.Poll(catch_errors=False)

    poller.add_client(broker_client)
    broker_client.subscribe('request.*', handle_request)

    poller.serve_forever()
