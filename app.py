from __future__ import print_function
import json
import time
from random import choice
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.gen
import redis
import tornadoredis
import tornadoredis.pubsub
import sockjs.tornado


id = 1

# friend = {"1" : ["3", "2"], "2" : ["1"], "3" : ["1"]}

redis_client = redis.Redis()
subscriber = tornadoredis.pubsub.SockJSSubscriber(tornadoredis.Client())

#************************************************************************
db = redis.StrictRedis(host="localhost", port=6379, db=1)
friend_of_1 = db.lrange("friend:1", 0, db.llen("friend:1"))
friend_of_2 = db.lrange("friend:2", 0, db.llen("friend:2"))
friend_of_3 = db.lrange("friend:3", 0, db.llen("friend:3"))
friend = {"1":[], "2":[], "3":[]}
for i in range(3):
	friend_num = db.llen("friend:{}".format(str(i + 1)))
	friend_of_i = db.lrange("friend:{}".format(str(i + 1)), 0, db.llen("friend:{}".format(str(i + 1))))
	for j in range(friend_num):
		friend[str(i + 1)].append(friend_of_i[j].decode("utf-8"))

print(str(friend))
print(json.dumps(friend))
print("*******************************************")

#************************************************************************

class IndexPageHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("index.html");

class SendMessageHandler(tornado.web.RequestHandler):
	def _send_message(self, channel, msg, _from):
		msg = {'id' : '', 'msg': msg, 'from': _from}
		print("the channel is: ", channel)
		print('here1')
		msg = json.dumps(msg)
		print('here2')
		redis_client.publish(channel, msg)
		print('here3')

	def post(self):
		message = self.get_argument('message').strip()
		_from = self.get_argument('id').strip()
		self._send_message('private.{}'.format(_from), message, _from)


class MessageHandler(sockjs.tornado.SockJSConnection):		
	def on_open(self, request):
		global id
		self.id = id
		id += 1
		self.msg = 'begin<br>a'
		self.send(json.dumps({'id' : str(self.id), 'msg' : self.msg, 'from': ''}))
		subscriber.subscribe(['private.{}'.format(fri) for fri in friend[str(self.id)]], self)


	def on_close(self):
		self.msg += '<br>end!'
		self.send(json.dumps({'id': self.id, 'msg': self.msg}))

application = tornado.web.Application(
		[(r'/', IndexPageHandler),
		(r'/send', SendMessageHandler),] + 
		 sockjs.tornado.SockJSRouter(MessageHandler, '/getdata').urls
	)

if __name__ == '__main__':
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(8888)
	print('begin')
	tornado.ioloop.IOLoop.instance().start()

