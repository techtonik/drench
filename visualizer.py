import txws
import json
from Queue import Queue
from collections import namedtuple
from twisted.web import http
from twisted.internet import protocol, reactor, endpoints
import pudb


download_file = namedtuple('download_file', 'path bits')


def init_state(t_dict):
    pass


class BitClient(protocol.Protocol):
    message_list = []
    '''
    Responsible for grabbing TCP connection to BitTorrent client.
    Gets callback on dataReceived initiating a broadcast to all
    websockets
    '''
    def dataReceived(self, data):
        print 'received some data:' + '\n\t' + data
        self.message_list.append(data)
        if WebSocket.websockets:
            WebSocket.broadcast(data)


class MyRequestHandler(http.Request):
    script = open('client.js').read()
    resources = {
        '/': '''<script src="http://d3js.org/d3.v3.js" charset="utf-8">
                    </script>
                <script>{}</script><h1>O hai</h1>'''.format(script)
    }

    def process(self):
        print 'process got called'
        self.setHeader('Content-Type', 'text/html')
        if self.path in self.resources:
            self.write(self.resources[self.path])
        else:
            self.setResponseCode(http.NOT_FOUND,
                                 'Sorry, dogg. We dont have those here')
        self.finish()


class MyHTTP(http.HTTPChannel):
    print 'MyHTTP initialized'
    requestFactory = MyRequestHandler


class MyHTTPFactory(http.HTTPFactory):
    def buildProtocol(self, addr):
        http_protocol = MyHTTP()
        return http_protocol


# TODO -- make a new queue for each client

class WebSocket(protocol.Protocol):
    websockets = []

    @classmethod
    def add_socket(self, ws):
        print 'adding a websocket'
        WebSocket.websockets.append(ws)

    @classmethod
    def broadcast(self, message):
        for ws in WebSocket.websockets:
            ws.message_queue.put(message)
            ws.send_all_messages()

    def connectionMade(self):
        self.message_queue = Queue()
        for i in range(len(BitClient.message_list)):
            self.message_queue.put(BitClient.message_list[i])
        self.send_all_messages()

    def send_all_messages(self):
        print 'SENDING ALL MESSAGES'
        while not self.message_queue.empty():
                self.transport.write(self.message_queue.get())


class MyWSFactory(protocol.Factory):
    def buildProtocol(self, addr):
        print 'building a WebSocket object'
        ws = WebSocket()
        WebSocket.add_socket(ws)
        print WebSocket.websockets
        return ws

point = endpoints.TCP4ClientEndpoint(reactor, "127.0.0.1", 8035)
bit_client = BitClient()
d = endpoints.connectProtocol(point, bit_client)
reactor.listenTCP(8000, MyHTTPFactory())
reactor.listenTCP(8001, txws.WebSocketFactory(MyWSFactory()))
reactor.run()
