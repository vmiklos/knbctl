#!/usr/bin/env python
#
#   knbctl
#  
#   Copyright (c) 2008 by Miklos Vajna <vmiklos@frugalware.org>
#  
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#  
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, 
#   USA.

import cgitb, cgi, os, time, Cookie, sha, urllib, base64, sys
from ConfigParser import ConfigParser
from xml.dom import minidom

cgitb.enable()

class Config:
	def __init__(self, nick, knbdir):
		self.attrs = ["nick", "realname", "keep", "server", "port", "channel", "owner"]
		os.chdir(knbdir)
		self.xml = minidom.parse("%s.xml" % nick)
		for i in self.attrs:
			setattr(self, i, self.xml.getElementsByTagName(i)[0].firstChild.toxml())
	def save(self):
		for i in self.attrs:
			self.xml.getElementsByTagName(i)[0].firstChild.data = getattr(self, i)
		sock = open("%s.xml" % self.nick, "w")
		sock.write("%s\n" % self.xml.toxml())
		sock.close()

		self.writeconfig()
		self.restart()

	def writeconfig(self):
		sock = open("%s.conf" % self.nick, "w")
		sock.write("""nick %s
realname %s
nicks %s
server %s %s
channel %s
""" % (self.nick, self.realname, self.keep, self.server, self.port, self.channel))
		sock.close()

		sock = open("%s.uf" % self.nick, "w")
		sock.write("%s\n" % self.owner)
		sock.close()

	def restart(self):
		try:
			sock = open("pid.%s" % self.nick, "r")
			pid = int(sock.read().strip())
			sock.close()
			os.kill(pid, 15)
		except OSError:
			pass
		os.system("./knb %s.conf >/dev/null 2>&1" % self.nick)

class Knbctl:
	def __init__(self):
		# our config
		c = ConfigParser()
		c.read("knbctl.config")
		self.username = c.get("knbctl", "username")
		self.password = c.get("knbctl", "password")
		self.nick = c.get("knbctl", "nick")
		self.knbdir = c.get("knbctl", "knbdir")

		# knb config
		self.config = Config(self.nick, self.knbdir)

		self.send(cgi.FieldStorage())
		self.receive()
	
	def cookie2dict(self):
		try:
			cookie = Cookie.SimpleCookie(os.environ["HTTP_COOKIE"])
			self.dict = eval(base64.decodestring(cookie['knbctl'].value))
		except Exception:
			self.dict = {}
	
	def dict2cookie(self):
		cookie = Cookie.SimpleCookie()
		cookie['knbctl'] = base64.encodestring(self.dict.__repr__()).replace('\n', '')
		print cookie
	
	def send(self, what):
		self.form = what
		self.cookie2dict()
		try:
			if self.dict['username'] != self.username or sha.sha(self.dict['password']).hexdigest() != self.password:
				self.__dumpheader()
				self.__dumplogin("post without password?!<br />")
				self.__dumpfooter()
				sys.exit(0)
			for i in self.config.attrs:
				setattr(self.config, i, self.form[i].value)
			self.config.save()
		except KeyError:
			return
	
	def receive(self):
		self.__handlecookies()
		self.__dumpheader()
		if len(self.password) and "password" not in self.dict.keys():
			self.__dumplogin()
		else:
			self.__dumpform()
		if "password" in self.dict.keys():
			self.__dumplogout()
		self.__dumpfooter()

	def __handlecookies(self):
		if "action" in self.form.keys() and self.form['action'].value == "login":
			if self.form['username'].value != self.username or sha.sha(self.form['password'].value).hexdigest() != self.password:
				self.__dumpheader()
				self.__dumplogin("wrong password! (%s)<br />" % sha.sha(self.form['password'].value).hexdigest())
				self.__dumpfooter()
				sys.exit(0)
			self.dict = {}
			self.dict['username'] = self.form['username'].value
			self.dict['password'] = self.form['password'].value
			self.dict2cookie()
		elif "action" in self.form.keys() and self.form['action'].value == "logout":
			self.dict = {}
			self.dict2cookie()
	
	def __dumpheader(self):
		print "Content-Type: text/html"
		print "Cache-Control: no-cache, must-revalidate"
		print "Pragma: no-cache"
		print
		print """<?xml version="1.0"?>"""
		print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
			"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
	
	def __dumplogin(self, errmsg=""):
		print """
		%s
		<form action="knbctl.py" method="post">
		username: <input type="text" name="username" value="" /><br/>
		password: <input type="password" name="password" value="" /><br/>
		<input type="hidden" name="action" value="login" />
		<input type="submit" value="login" />
		</form>""" % errmsg
	
	def __dumpfooter(self):
		pass

	def __dumpform(self):
		print """<form action="knbctl.py" method="post">"""
		for i in self.config.attrs:
			if i == "password":
				print """%s: <input type="password" name="%s" value="%s" /><br/>""" % (i, i, getattr(self.config, i))
			else:
				print """%s: <input type="text" name="%s" value="%s" /><br/>""" % (i, i, getattr(self.config, i))
		print """<input type="submit" value="save and restart bot" />
		</form>"""

	def __dumplogout(self):
		print """<form action="knbctl.py" method="post">
		<input type="hidden" name="action" value="logout" />
		<input type="submit" value="logout" />
		</form>"""

knbctl = Knbctl()
