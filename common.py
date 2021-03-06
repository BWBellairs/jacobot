import urllib.request
import urllib.parse
import urllib.error
import re
import time
import os
import json

from config import adminHostmasks, ownerHostmasks

class ShowHelpException(Exception):
	pass

def GetGlobals():
	return globals()

def CheckOwner(hostmask):
	host = hostmask.split("!")[-1]
	return host in ownerHostmasks

def CheckAdmin(hostmask):
	host = hostmask.split("!")[-1]
	return host in adminHostmasks or CheckOwner(hostmask)

messageQueue = []
def Send(msg):
	messageQueue.append(msg)

def SendMessage(target, msg):
	msg = msg[:450]
	if re.match(".*moo+$", msg):
		msg = msg + "."
	Send("PRIVMSG %s :%s\n" % (target, msg))

def SendNotice(target, msg):
	msg = msg[:450]
	Send("NOTICE %s :%s\n" % (target, msg))

rateLimit = False
def SetRateLimiting(rateLimiting):
	global rateLimit
	rateLimit = rateLimiting

def DoRateLimiting():
	global rateLimit
	return rateLimit

currentChannel = None
def SetCurrentChannel(channel):
	global currentChannel
	currentChannel = channel

def GetCurrentChannel():
	global currentChannel
	return currentChannel

plugin = ""
def RegisterMod(name):
	global plugin
	name = name.split(".")[-1]
	commands[name] = []
	plugin = name

commands = {}
def command(name, minArgs = 0, owner = False, admin = False, rateLimit = False):
	def real_command(func):
		def call_func(username, hostmask, channel, text):
			if owner and not CheckOwner(hostmask):
				SendNotice(username, "This command is owner only")
				return
			if admin and not CheckAdmin(hostmask):
				SendNotice(username, "This command is admin only")
				return
			if len(text) < minArgs:
				SendNotice(username, "Usage: %s" % func.__doc__)
				return
			if rateLimit and len(messageQueue) > 2:
				SendNotice(username, "This command has been rate limited")
				return
			return func(username, hostmask, channel, text)
		call_func.__doc__ = func.__doc__
		commands[plugin].append((name, call_func))
		return call_func
	return real_command

def GetPage(url, cookies = None, headers = None, removeTags = False, getredirect=False):
	try:
		if cookies:
			req = urllib.request.Request(url, data=urllib.parse.urlencode(headers).encode("utf-8") if headers else None, headers={'Cookie':cookies.encode("utf-8")})
		else:
			req = urllib.request.Request(url, data=urllib.parse.urlencode(headers).encode("utf-8") if headers else None)
		data = urllib.request.urlopen(req, timeout=10)
		page = data.read().decode("utf-8", errors="replace")
		url = data.geturl()
		if removeTags:
			return re.sub("<.*?>", "", page)
		return url if getredirect else page
	except urllib.error.URLError:
	#except IOError:
		return None

# Functions for saving / storing data in a "database" (really a json file stored on disk)
data = {}
lastData = {}
initialized = {}
def StoreData(plugin, key, value):
	if plugin not in initialized:
		InitializeData(plugin)
	if plugin not in data:
		data[plugin] = {}
	if plugin not in lastData:
		lastData[plugin] = 0
	node = data[plugin]
	for k in key.split(".")[:-1]:
		if not k in node:
			node[k] = {}
		node = node[k]
	node[key.split(".")[-1]] = value
	
	lastData[plugin] = time.time()

def WriteAllData(force = False):
	for plugin in data:
		if not force and plugin in lastData and time.time() - lastData[plugin] > 65:
			continue
		if not os.path.isdir("data"):
			os.mkdir("data")
		f = open(os.path.join("data", "{0}.json".format(plugin)), "w")
		json.dump(data[plugin], f)
		f.close()

def InitializeData(plugin):
	try:
		f = open(os.path.join("data", "{0}.json".format(plugin)))
	except FileNotFoundError:
		return
	try:
		data[plugin] = json.load(f)
		f.close()
	except json.decoder.JSONDecodeError:
		f.close()
		os.rename(os.path.join("data", "{0}.json".format(plugin)), os.path.join("data", "{0}-backup-{1}.json".format(plugin, int(time.time()))))
	initialized[plugin] = True

def GetData(plugin, key):
	if plugin not in initialized:
		InitializeData(plugin)
	if plugin not in data:
		return None

	node = data[plugin]
	for k in key.split("."):
		if not k in node:
			return None
		node = node[k]
	return node

settings = {}
# Functions for loading settings. If the settings file doesn't exist it is created with default values
def AddSetting(plugin, setting, default):
	if plugin not in settings:
		settings[plugin] = {}
	
	settings[plugin][setting] = default

def LoadSettings(plugin):
	if not os.path.isdir("settings"):
		os.mkdir("settings")
	try:
		f = open(os.path.join("settings", "{0}.json".format(plugin)))
		foundSettings = json.load(f)
		for (k,v) in foundSettings.items():
			if k in settings[plugin]:
				settings[plugin][k] = v
		f.close()
	except FileNotFoundError:
		pass

	f = open(os.path.join("settings", "{0}.json".format(plugin)), "w")
	json.dump(settings[plugin], f, indent="\t")
	f.close()

def GetSetting(plugin, setting):
	return settings[plugin][setting]
