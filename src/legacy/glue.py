# Copyright 2004-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import imgmanip
import utils
from twisted.words.xish.domish import Element
from twisted.internet import protocol, reactor, defer, task
from tlib import oscar
from tlib import socks5, sockserror
from twisted.python import log
import groupchat
import aimt
import config
from debug import LogEvent, INFO, WARN, ERROR
import sys, warnings, pprint
import lang
import os.path
import re
import time
import binascii
import avatar
import md5

# The name of the transport
name = "AIM Transport"

# The transport's version
version = "0.8.0.1"

# URL of the transport's web site
url = "http://pyaimt.googlecode.com"

# This should be set to the identity of the gateway
id = "aim"

if not config.disableAvatars:
	# Load the default AIM and ICQ avatars
	f = open(os.path.join("data", "defaultAIMAvatar.png"))
	defaultAIMAvatarData = f.read()
	f.close()
	defaultAIMAvatar = avatar.AvatarCache().setAvatar(defaultAIMAvatarData)

	f = open(os.path.join("data", "defaultICQAvatar.png"))
	defaultICQAvatarData = f.read()
	f.close()
	defaultICQAvatar = avatar.AvatarCache().setAvatar(defaultICQAvatarData)

	defaultAvatar = defaultAIMAvatar
	defaultAvatarData = defaultAIMAvatarData
else:
	defaultAvatar = None
	defaultAvatarData = None

# This function should return true if the JID is a group JID, false otherwise
def isGroupJID(jid):
	#if (jid[0] == "#" or jid[0] == "%"):
	if jid.find(config.confjid) > 0:
		return True
	else:
		return False

# This function translates an AIM screen name to a JID
def aim2jid(aimid):
	if aimid:
		retstr = aimid.lower().replace(' ', '')
		return retstr.replace('@', '%') + "@" + config.jid
	else:
		return config.jid

# This function translates a JID to an AIM screen name
def jid2aim(jid):
	return unicode(jid[:jid.find('@')].replace('%','@'))

# This function translates an AIM chat room to a groupchat JID
def aim2jidGroup(chatid, userid=None, exchange=None):
	retstr = chatid.replace(' ', '_')
	retstr = retstr.replace('@', '')
	if exchange:
		retstr = retstr + "%" + str(exchange)
	retstr = retstr + "@" + config.confjid
	if userid:
		retstr = retstr + "/" + userid
	return retstr

# This function translates a groupchat JID to an AIM chat room
def jid2aimGroup(jid):
	exchange = 4
	groupid = unicode(jid[0:jid.find('@')].replace('_',' '))
	if groupid.find('%') != -1:
		exchange = int(groupid[groupid.find('%')+1:])
		groupid = groupid[:groupid.find('%')]
	if jid.find('/') != -1:
		userid = unicode(jid[jid.find('/'):])
	else:
		userid = None
	return (groupid,userid,exchange)

# This function is called to handle legacy id translation to a JID
translateAccount = aim2jid



############################################################################
# This class handles most interaction with AIM chatrooms
############################################################################
class LegacyGroupchat(groupchat.BaseGroupchat):
	def __init__(self, session, resource, ID=None, existing=False, switchboardSession=None):
		groupchat.BaseGroupchat.__init__(self, session, resource, ID)
		groupid,userid,exchange = jid2aimGroup(self.roomJID())
		LogEvent(INFO, self.session.jabberID)
		self.session.legacycon.createChat(groupid,exchange)

	def removeMe(self):
		groupid,userid,exchange = jid2aimGroup(self.roomJID())
		LogEvent(INFO, self.session.jabberID)
		self.session.legacycon.leaveChat(groupid)
		groupchat.BaseGroupchat.removeMe(self)
		utils.mutilateMe(self)

	def sendLegacyMessage(self, message, noerror):
		groupid,userid,exchange = jid2aimGroup(self.roomJID())
		LogEvent(INFO, self.session.jabberID)
		self.session.legacycon.sendChat(groupid, message)
	
	def sendContactInvite(self, contactJID):
		groupid,userid,exchange = jid2aimGroup(self.roomJID())
		contactid = jid2aim(contactJID)
		LogEvent(INFO, self.session.jabberID)
		self.session.legacycon.sendInvite(groupid, contactid)



############################################################################
# This class handles most interaction with AIM
############################################################################
class LegacyConnection:
	""" A glue class that connects to the legacy network """
	def __init__(self, username, password, session):
		import buddies

		self.username = username
		self.password = password
		self.session = session
		self.legacyList = buddies.BuddyList(self.session)
		self.savedShow = None
		self.savedFriendly = None
		self.savedURL = None
		self.reactor = reactor
		self.deferred = defer.Deferred()
		self.deferred.addErrback(self.errorCallback)
		hostport = (config.aimServer, config.aimPort)
		LogEvent(INFO, self.session.jabberID, "Creating")
		if config.socksProxyServer and config.socksProxyPort:
			self.oa = aimt.OA
			self.creator = socks5.ProxyClientCreator(self.reactor, self.oa, self.username, self.password, self, deferred=self.deferred, icq=0)
			LogEvent(INFO, self.session.jabberID, "Connect via socks proxy")
			self.creator.connectSocks5Proxy(config.aimServer, config.aimPort, config.socksProxyServer, config.socksProxyPort, "AIMCONN")
		else:
			self.oa = aimt.OA
			self.creator = protocol.ClientCreator(self.reactor, self.oa, self.username, self.password, self, deferred=self.deferred, icq=0)
			LogEvent(INFO, self.session.jabberID, "Connect via direct tcp")
			self.creator.connectTCP(*hostport)

		LogEvent(INFO, self.session.jabberID, "Created!")

	def removeMe(self):
		from glue import aim2jid
		LogEvent(INFO, self.session.jabberID)
		try:
			self.bos.stopKeepAlive()
			self.bos.disconnect()
		except AttributeError:
			pass
		self.legacyList.removeMe()
		self.legacyList = None
		self.session = None
		utils.mutilateMe(self)

	def jidRes(self, resource):
		to = self.session.jabberID
		if resource:
			to += "/" + resource
		return to

	def highestResource(self):
		""" Returns highest priority resource """
		return self.session.highestResource()

	def setURL(self, URL=None):
		LogEvent(INFO, self.session.jabberID, "setURL %s" % URL)
		try:
			self.bos.setURL(utils.utf8encode(URL))
		except AttributeError:
			#self.alertUser(lang.get("sessionnotactive", config.jid)
			pass

	def sendMessage(self, target, resource, message, noerror, xhtml, autoResponse=0):
		LogEvent(INFO, self.session.jabberID)
		from glue import jid2aim
		try:
			self.session.pytrans.serviceplugins['Statistics'].stats['OutgoingMessages'] += 1
			self.session.pytrans.serviceplugins['Statistics'].sessionUpdate(self.session.jabberID, 'OutgoingMessages', 1)
			scrnname = jid2aim(target)
			wantIcon = 0
			if self.bos.requesticon.has_key(scrnname):
				LogEvent(INFO, self.session.jabberID, "Going to ask for target's icon.")
				wantIcon = 1
				del self.bos.requesticon[scrnname]
			offline = 1
			try:
				if self.legacyList.ssicontacts[scrnname]['presence'] != "unavailable":                       
					offline = 0
			except: 
				# well then they're online in some way
				pass

			iconSum = None
			iconLen = None
			iconStamp = None
			if hasattr(self, "myavatar"):
				iconSum = oscar.getIconSum(self.myavatar)
				iconLen = len(self.myavatar)
				iconStamp = time.time()
				LogEvent(INFO, self.session.jabberID, "Going to send info about our icon, length %d, cksum %d" % (iconLen, iconSum))

			LogEvent(INFO, self.session.jabberID)
			if scrnname[0].isdigit():
				encoding = "iso-8859-1"
				charset = "iso-8859-1"
				if self.legacyList.hasCapability(scrnname, "unicode"):
					encoding = "utf-16be"
					charset = "unicode"
				LogEvent(INFO, self.session.jabberID, "Encoding %r" % encoding)
				self.bos.sendMessage(scrnname, [[message,charset]], offline=offline, wantIcon=wantIcon, autoResponse=autoResponse, iconSum=iconSum, iconLen=iconLen, iconStamp=iconStamp)
				self.session.sendArchive(target, self.session.jabberID, message)
			else:
				if xhtml and not config.disableXHTML:
					xhtml = utils.xhtml_to_aimhtml(xhtml)
					self.bos.sendMessage(scrnname, xhtml, wantIcon=wantIcon, autoResponse=autoResponse, iconSum=iconSum, iconLen=iconLen, iconStamp=iconStamp)
					self.session.sendArchive(target, self.session.jabberID, message)
				else:
					htmlized = oscar.html(message)
					self.bos.sendMessage(scrnname, htmlized, wantIcon=wantIcon, autoResponse=autoResponse, iconSum=iconSum, iconLen=iconLen, iconStamp=iconStamp)
					self.session.sendArchive(target, self.session.jabberID, message)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def newResourceOnline(self, resource):
		from glue import aim2jid
		LogEvent(INFO, self.session.jabberID)
		try:
			for c in self.legacyList.ssicontacts.keys( ):
				LogEvent(INFO, self.session.jabberID, "Resending buddy %r" % c)
				jid = aim2jid(c)
				show = self.legacyList.ssicontacts[c]['show']
				status = self.legacyList.ssicontacts[c]['status']
				ptype = self.legacyList.ssicontacts[c]['presence']
				url = self.legacyList.ssicontacts[c]['url']
				#FIXME, needs to be contact based updatePresence
				self.session.sendPresence(to=self.session.jabberID, fro=jid, show=show, status=status, ptype=ptype, url=url)
		except AttributeError:
			return

	def setAway(self, awayMessage=None):
		LogEvent(INFO, self.session.jabberID)
		try:
			self.bos.awayResponses = {}
			self.bos.setAway(utils.xmlify(awayMessage))
		except AttributeError:
			#self.alertUser(lang.get("sessionnotactive", config.jid))
			pass

	def setBack(self, backMessage=None):
		LogEvent(INFO, self.session.jabberID)
		try:
			self.bos.awayResponses = {}
			self.bos.setBack(utils.utf8encode(backMessage))
		except AttributeError:
			#self.alertUser(lang.get("sessionnotactive", config.jid))
			pass

	def sendShowStatus(self, jid=None):
		if not self.session: return
		if not jid:
			jid = self.jabberID
		self.session.sendPresence(to=jid, fro=config.jid, show=self.savedShow, status=self.savedFriendly)
	
 	def setStatus(self, nickname, show, friendly, url=None):
		LogEvent(INFO, self.session.jabberID)

		if show=="away" and not friendly:
			friendly="Away"
		elif show=="dnd" and not friendly:
			friendly="Do Not Disturb"
		elif show=="xa" and not friendly:
			friendly="Extended Away"
		elif show=="chat" and not friendly:
			friendly="Free to Chat"

		self.savedShow = show
		self.savedFriendly = friendly
		self.savedURL = url

		if not self.session.ready:
			return

		if not show or show == "online" or show == "Online" or show == "chat":
			self.setBack(friendly)
			self.setURL(url)
			self.session.sendPresence(to=self.session.jabberID, fro=config.jid, show=None, url=url)
		else:
			self.setAway(friendly)
			self.setURL(url)
			self.session.sendPresence(to=self.session.jabberID, fro=config.jid, show=show, status=friendly, url=url)

	def setProfile(self, profileMessage=None):
		LogEvent(INFO, self.session.jabberID)
		try:
			self.bos.setProfile(profileMessage)
		except AttributeError:
			#self.alertUser(lang.get("sessionnotactive", config.jid))
			pass

        def buildFriendly(self, status):
		friendly = self.jabberID[:self.jabberID.find('@')]
		if status and len(status) > 0:
			friendly += " - "
			friendly += status
		if len(friendly) > 127:
			friendly = friendly[:124] + "..."
		return friendly

	def sendTypingNotify(self, type, dest):
		from tlib.oscar import MTN_FINISH, MTN_IDLE, MTN_BEGIN
		from glue import jid2aim
		try:
			username = jid2aim(dest)
			LogEvent(INFO, self.session.jabberID)
			if type == "begin":
				self.bos.sendTypingNotification(username, MTN_BEGIN)
			elif type == "idle":
				self.bos.sendTypingNotification(username, MTN_IDLE)
			elif type == "finish":
				self.bos.sendTypingNotification(username, MTN_FINISH)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))
	
	def userTypingNotification(self, dest, resource, composing):
		LogEvent(INFO, self.session.jabberID)
		if composing:
			self.sendTypingNotify("begin", dest)
		else:
			self.sendTypingNotify("finish", dest)

	def chatStateNotification(self, dest, resource, state):
		LogEvent(INFO, self.session.jabberID)
		if state == "composing":
			self.sendTypingNotify("begin", dest)
		elif state == "paused" or state == "inactive":
			self.sendTypingNotify("idle", dest)
		elif state == "active" or state == "gone":
			self.sendTypingNotify("finish", dest)

	def jabberVCardRequest(self, vcard, user):
		LogEvent(INFO, self.session.jabberID)
		return self.getvCard(vcard, user)

	def getvCardNotInList(self, vcard, jid):
		try:
			LogEvent(INFO, self.session.jabberID)
		except AttributeError:
			pass

		user = jid.split('@')[0]
		return self.getvCard(vcard, user)

	def createChat(self, chatroom, exchange):
		LogEvent(INFO, self.session.jabberID)
		try:
			self.bos.createChat(chatroom, exchange).addCallback(self.bos.createdRoom)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def leaveChat(self, chatroom):
		LogEvent(INFO, self.session.jabberID)
		try:
			for c in self.bos.chats:
				if c.name == chatroom:
					c.leaveChat()
					self.bos.chats.remove(c)
					break
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def sendChat(self, chatroom, message):
		LogEvent(INFO, self.session.jabberID)
		try:
			for c in self.bos.chats:
				#debug.log("Checking chat %s" % (c.name))
				if c.name.lower() == chatroom.lower():
					c.sendMessage(message)
					#debug.log("Found chat and sent message.")
					break
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def sendInvite(self, chatroom, contact):
		LogEvent(INFO, self.session.jabberID)
		try:
			for c in self.bos.chats:
				if c.name.lower() == chatroom.lower():
					self.bos.sendInvite(contact, c)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def resourceOffline(self, resource):
		from glue import aim2jid
		LogEvent(INFO, self.session.jabberID)
		try:
			show = None
			status = None
			ptype = "unavailable"
			for c in self.legacyList.ssicontacts.keys( ):
				LogEvent(INFO, self.session.jabberID, "Sending offline %r" % c)
				jid = aim2jid(c)

				self.session.sendPresence(to=self.session.jabberID+"/"+resource, fro=jid, ptype=ptype, show=show, status=status)
			self.session.sendPresence(to=self.session.jabberID+"/"+resource, fro=config.jid, ptype=ptype, show=show, status=status)
		except AttributeError:
			return

	def updateAvatar(self, av=None):
		""" Called whenever a new avatar needs to be set. Instance of avatar.Avatar is passed """
		if config.disableAvatars: return
		imageData = ""
		if av:
			imageData = av.getImageData()
		else:
			if not config.disableDefaultAvatar:
				global defaultAvatarData
				imageData = defaultAvatarData
			else:
				imageData = None

		self.changeAvatar(imageData)

	def changeAvatar(self, imageData):
		if config.disableAvatars: return
		if imageData:
			try:
				self.myavatar = imgmanip.convertToJPG(imageData)
				self.myavatarlen = len(self.myavatar)
				m=md5.new()
				m.update(self.myavatar)
				self.myavatarsum = m.digest()
				self.myavatarstamp = time.time()
			except:
				LogEvent(INFO, self.session.jabberID, "Unable to convert avatar to JPEG")
				return
		if hasattr(self, "bos") and self.session.ready:
			if not imageData:
				if hasattr(self, "myavatar"):
					del self.myavatar
				if len(self.bos.ssiiconsum) > 0:
					self.bos.startModifySSI()
					for i in self.bos.ssiiconsum:
						LogEvent(INFO, self.session.jabberID, "Removing icon %s (u:%d g:%d)" % (i.name, i.buddyID, i.groupID))
						de = self.bos.delItemSSI(i)
					self.bos.endModifySSI()
				return
			if len(self.bos.ssiiconsum) > 0 and self.bos.ssiiconsum[0]:
				LogEvent(INFO, self.session.jabberID, "Replacing existing icon")
				self.bos.ssiiconsum[0].updateIcon(imageData)
				self.bos.startModifySSI()
				self.bos.modifyItemSSI(self.bos.ssiiconsum[0])
				self.bos.endModifySSI()
			else:
				LogEvent(INFO, self.session.jabberID, "Adding new icon")
				newBuddySum = oscar.SSIIconSum()
				newBuddySum.updateIcon(imageData)
				self.bos.startModifySSI()
				self.bos.addItemSSI(newBuddySum)
				self.bos.endModifySSI()

	def doSearch(self, form, iq):
		LogEvent(INFO, self.session.jabberID)
		#TEST self.bos.sendInterestsRequest()
		email = utils.getDataFormValue(form, "email")
		first = utils.getDataFormValue(form, "first")
		middle = utils.getDataFormValue(form, "middle")
		last = utils.getDataFormValue(form, "last")
		maiden = utils.getDataFormValue(form, "maiden")
		nick = utils.getDataFormValue(form, "nick")
		address = utils.getDataFormValue(form, "address")
		city = utils.getDataFormValue(form, "city")
		state = utils.getDataFormValue(form, "state")
		zip = utils.getDataFormValue(form, "zip")
		country = utils.getDataFormValue(form, "country")
		interest = utils.getDataFormValue(form, "interest")
		try:
			d = defer.Deferred()
			self.bos.sendDirectorySearch(email=email, first=first, middle=middle, last=last, maiden=maiden, nickname=nick, address=address, city=city, state=state, zip=zip, country=country, interest=interest).addCallback(self.gotSearchResults, iq, d).addErrback(self.gotSearchError, d)
			return d
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def gotSearchResults(self, results, iq, d):
		LogEvent(INFO, self.session.jabberID)
		from glue import aim2jid

		x = None
		for query in iq.elements():
			if query.name == "query":
				for child in query.elements():
					if child.name == "x":
						x = child
						break
				break

		if x:
			for r in results:
				if r.has_key("screenname"):
					r["jid"] = aim2jid(r["screenname"])
				else:
					r["jid"] = "Unknown"
				item = x.addElement("item")
				for k in ["jid","first","middle","last","maiden","nick","email","address","city","state","country","zip","region"]:
					item.addChild(utils.makeDataFormElement(None, k, value=r.get(k,None)))
		d.callback(iq)

	def gotSearchError(self, error, d):
		LogEvent(INFO, self.session.jabberID)
		#d.callback(vcard)

	def getvCard(self, vcard, user):
		LogEvent(INFO, self.session.jabberID)
		try:
			d = defer.Deferred()
			self.bos.getProfile(user).addCallback(self.gotvCard, user, vcard, d).addErrback(self.gotnovCard, user, vcard, d)
			return d
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def gotvCard(self, profile, user, vcard, d):
		from glue import aim2jid

		LogEvent(INFO, self.session.jabberID)

		cutprofile = oscar.dehtml(profile)
		nickname = vcard.addElement("NICKNAME")
		nickname.addContent(utils.xmlify(user))
		jabberid = vcard.addElement("JABBERID")
		jabberid.addContent(aim2jid(user))
		desc = vcard.addElement("DESC")
		desc.addContent(utils.xmlify(cutprofile))

		d.callback(vcard)

	def gotnovCard(self, profile, user, vcard, d):
		from glue import aim2jid
		LogEvent(INFO, self.session.jabberID)

		nickname = vcard.addElement("NICKNAME")
		nickname.addContent(user)
		jabberid = vcard.addElement("JABBERID")
		jabberid.addContent(aim2jid(user))
		desc = vcard.addElement("DESC")
		desc.addContent("User is not online.")

		d.callback(vcard)

	def aim2uhandle(self, aimid):
		retstr = aimid.replace(' ','')
		return retstr.lower()

	def updatePresence(self, userHandle, ptype): # Convenience
		from glue import aim2jid
		to = aim2jid(userHandle)
		self.session.sendPresence(to=self.session.jabberID, fro=to, ptype=ptype)

	def addContact(self, userHandle):
		LogEvent(INFO, self.session.jabberID)
		def cb(arg=None):
			self.updatePresence(userHandle, "subscribed")

		try:
			for g in self.bos.ssigroups:
				for u in g.users:
					aimHandle = self.aim2uhandle(u.name)
					if aimHandle == userHandle:
						if not u.authorizationRequestSent and not u.authorized:
							self.bos.sendAuthorizationRequest(userHandle, "Please authorize me!")
							u.authorizationRequestSent = True
							return
						else:
							cb()
							return

			savethisgroup = None
			groupName = "PyAIM-t Buddies"
			for g in self.bos.ssigroups:
				if g.name == groupName:
					LogEvent(INFO, self.session.jabberID, "Located group %s" % (g.name))
					savethisgroup = g

			if savethisgroup is None:
				LogEvent(INFO, self.session.jabberID, "Adding new group")
				newGroupID = self.generateGroupID()
				newGroup = oscar.SSIGroup(groupName, newGroupID, 0)
				self.bos.startModifySSI()
				self.bos.addItemSSI(newGroup)
				self.bos.endModifySSI()
				savethisgroup = newGroup
				self.bos.ssigroups.append(newGroup)

			group = self.findGroupByName(groupName)
			newUserID = self.generateBuddyID(group.groupID)
			newUser = oscar.SSIBuddy(userHandle, group.groupID, newUserID)
			savethisgroup.addUser(newUserID, newUser)

			LogEvent(INFO, self.session.jabberID, "Adding item to SSI")
			self.bos.startModifySSI()
			self.bos.addItemSSI(newUser)
			self.bos.modifyItemSSI(savethisgroup)
			self.bos.endModifySSI()

			self.legacyList.updateSSIContact(userHandle)
			self.updatePresence(userHandle, "subscribe")
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def removeContact(self, userHandle):
		LogEvent(INFO, self.session.jabberID)
		try:
			def cb(arg=None):
				self.updatePresence(userHandle, "unsubscribed")

			savetheseusers = []

			if userHandle in self.bos.authorizationRequests:
				self.bos.sendAuthorizationResponse(userHandle, False, "")
				self.bos.authorizationRequests.remove(userHandle)

			for g in self.bos.ssigroups:
				for u in g.users:
					aimHandle = self.aim2uhandle(u.name)
					LogEvent(INFO, self.session.jabberID, "Comparing %s and %s" % (aimHandle, userHandle))
					if aimHandle == userHandle:
						LogEvent(INFO, self.session.jabberID, "Located user %s" % (u.name))
						savetheseusers.append(u)

			if len(savetheseusers) == 0:
				LogEvent(INFO, self.session.jabberID, "Did not find user")
				return

			self.bos.startModifySSI()
			for u in savetheseusers:
				LogEvent(INFO, self.session.jabberID, "Removing %s (u:%d g:%d) from group %s"%(u.name, u.buddyID, u.groupID, u.group.name))
				de = self.bos.delItemSSI(u)
				de.addCallback(self.SSIItemDeleted, u)
			de.addCallback(cb)
			self.bos.endModifySSI()
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def authContact(self, userHandle):
		LogEvent(INFO, self.session.jabberID)
		try:
			if userHandle in self.bos.authorizationRequests:
				self.bos.sendAuthorizationResponse(userHandle, True, "OK")
				self.bos.authorizationRequests.remove(userHandle)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def deauthContact(self, userHandle):
		LogEvent(INFO, self.session.jabberID)
		# I don't recall why these are the same
		self.authContact(userHandle)

	def SSIItemDeleted(self, x, user):
		c = 0
		for g in self.bos.ssigroups:
			c += 1
			for u in g.users:
				if u.buddyID == user.buddyID and u.groupID == user.groupID:
					g.users.remove(u)
					del g.usersToID[u]

	def errorCallback(self, result):
		try:
			LogEvent(INFO, self.session.jabberID)
			errmsg = result.getErrorMessage()
			errmsgs = errmsg.split("'")
			message = "Authentication Error!" 
			if errmsgs[1]:
				message = message+"\n"+errmsgs[1]
			if errmsgs[3]:
				message = message+"\n"+errmsgs[3]
			self.alertUser(message)
			self.session.removeMe()
		except:
			pass

	def findGroupByID(self, groupID):
		for x in self.bos.ssigroups:
			if x.groupID == groupID:
				return x

	def findGroupByName(self, groupName):
		for x in self.bos.ssigroups:
			if x.name == groupName:
				return x

	def generateGroupID(self):
		pGroupID = len(self.bos.ssigroups)
		while True:
			pGroupID += 1
			found = False
			for x in self.bos.ssigroups:
				if pGroupID == x.groupID:
					found = True
					break
			if not found: break
		return pGroupID

	def generateBuddyID(self, groupID):
		group = self.findGroupByID(groupID)
		pBuddyID = len(group.users)
		while True: # If all integers are taken we got a bigger problems
			pBuddyID += 1
			found = False
			for x in group.users:
				if pBuddyID == x.buddyID:
					found = True
					break
			if not found: break
		return pBuddyID

	def alertUser(self, message):
		tmpjid = config.jid
		if self.session.registeredmunge:
			tmpjid = tmpjid + "/registered"
		self.session.sendMessage(to=self.session.jabberID, fro=tmpjid, body=message, mtype="error")
