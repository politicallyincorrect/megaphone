#!/usr/bin/env python
#coding: utf-8

from Queue import Queue, Empty
q = Queue()
from Tkinter import *
from threading import Thread
import tkMessageBox
import irc.client
import time
import json
import random
import webbrowser

#4chon Megaphone - based very loosely off of http://en.wikipedia.org/wiki/Megaphone_desktop_tool
#Unlike that one, it allows 4chon users to report new action alerts.
#People who can report are channel operators in #4idf on irc.datnode.net
#Join there for more information.

#Only requires Python 2.x, Tkinter and irclib. All other imports are in the stdlib.

class IRCC(irc.client.SimpleIRCClient):
	def __init__(self, megaphone): 
		self.nick = "`4IDF"+''.join(random.choice("0123456789ABCDEF") for x in xrange(0,5))
		self.megaphone = megaphone
		irc.client.SimpleIRCClient.__init__(self)

	def on_welcome(self, connection, event):
		connection.join("#4idf")

	def on_pubmsg(self, connection, event):
		if event.arguments[0].startswith("@ACTION"): #Is this an action?
			list_of_args = event.arguments[0].split() 
			if "@URL" in list_of_args:
				url_index = list_of_args.index("@URL")
				url = list_of_args[url_index+1]
			else:
				url_index = len(event.arguments[0])-1
				url = None
			
			action = ' '.join(list_of_args[1:url_index])

			self.action = (event.arguments[0], event.source.nick, url, action) #If so, store it.
			connection.whois([event.source.nick]) #Do a WHOIS to verify that the caller is an op. 
		else:
			q.put(['normalmessage',(event.arguments[0], event.source.nick)])

	def on_whoischannels(self, connection, event):
		channels = event.arguments[1].split() #These are the channels the caller is in.
		if u'@#4idf' in channels: #Is he an op in #4idf?
			q.put(['action',self.action]) #If so, send the action to megaphone.

class Megaphone(Frame):
	def __init__(self, root):
		Frame.__init__(self, root)
		self.pack()
		self.label = Label(self)
		self.label.config(text="4chon.net/new",foreground="blue")
		self.label.pack()
		self.text = Text(self)
		self.text.pack()
		self.text.config(state=DISABLED)
		self._update()

	def _update(self):
		try: 
			msg = q.get(False)
			if msg[0] == 'normalmessage': self._normalmessage(msg[1])
			else: self._action(msg[1])
		except Empty: 
			pass
		finally: self.after(100, self._update)		

	def _text_message_handler(self,message):
		self.text.config(state=NORMAL)
		self.text.insert(END,message.encode('utf-8'))
		self.text.config(state=DISABLED)
		self.text.yview(END) # Scroll to bottom

	def _action(self,action):
		self._text_message_handler(u"Nick: {0}, URL: {1}, Action Text: {2}\n\n".format(action[1],action[2],action[3]))
		result = tkMessageBox.askyesno("New action alert from {0}".format(action[1]),action[3])
		if result and action[2] is not None:
			webbrowser.open(action[2])

	def _normalmessage(self,message):
		self._text_message_handler(u"<{1}> {0}\n".format(message[0],message[1]))

#		for k in self.text.configure().keys():
#			print k, ':', self.text.cget(k)

root = Tk()
root.title("4chon Megaphone")
app = Megaphone(root)

c = IRCC(app)
c.connect("irc.datnode.net", 6667, c.nick)
def irc_listen(c):
	c.start()
t = Thread(target=irc_listen, args=(c,))
t.daemon = True
t.start()
app.mainloop()

