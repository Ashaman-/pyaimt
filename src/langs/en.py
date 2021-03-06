# -*- coding: UTF-8 -*-

# If you change or add any strings in this file please contact the translators listed below
# Everything must be in UTF-8
# Look for language codes here - http://www.w3.org/WAI/ER/IG/ert/iso639.htm

class en: # English - James Bunton <mailto:james@delx.cjb.net>/Daniel Henninger <mailto:jadestorm@nc.rr.com>
	# Text that may get sent to the user. Useful for translations. Keep any %s symbols you see or you will have troubles later
	sessiongreeting = u"This is an experimental gateway, PyAIM-t. If you experience problems please contact Daniel Henninger <jadestorm@nc.rr.com>"
	authenticatetext = u"WARNING: Registration is a two-step process.  First, please enter your local username and your local password.  If you enter a valid username and password, you will get a 'Registration Successful' message.  Then, click Register again, and you will be prompted for your AIM username and password."
	registertext = u"Please type your AIM screen name into the username field and your password."
	notloggedin = u"Error. You must log into the transport before sending messages."
	notregistered = u"Sorry. You do not appear to be registered with this transport. Please register and try again. If you are having trouble registering please contact your Jabber administrator."
	waitforlogin = u"Sorry, this message cannot be delivered yet. Please try again when the transport has finished logging in."
	usernotonline = u"The user you specified is not currently online."
	groupchatinvite = u"You have been invited into a groupchat on the legacy service. You must join this room to switch into groupchat mode %s.\nIf you do not join this room you will not be able to participate in the groupchat, but you will still appear to have joined it to contacts on the AIM service."
	groupchatfailjoin1 = u"You did not join the groupchat room %s.\nThe following users were in the groupchat:"
	groupchatfailjoin2 = u"You have been removed from this room on the legacy service. The following was said before you were disconnected, while you appeared to be in the groupchat to the contacts on the legacy service."
	groupchatprivateerror = u"Sorry. You cannot send private messages to users in this groupchat. Please instead add the user to your contact list and message them that way."
	gatewaytranslator = u"Enter the user's AIM screen name."
	sessionnotactive = u"Your session with AIM is not active at this time."
	aimemailnotification = u"You have %d new message(s) at %s!\nCheck your mail at %s."
	searchnodataform = u"Use the enclosed form to search.  If your Jabber client does not support Data Forms, you will not be able to use this functionality."
	searchtitle = u"AIM Directory Search"
	searchinstructions = u"Fill in either the e-mail address field or any number of the other fields to search the AIM directory for matching users.  If the e-mail address is filled in, all other fields are ignored."
	sessionslimit = u"Sorry. You can't be connected to AIM because too many sessions active in this time. Try later or choose other gateway from list http://www.jabberes.org/servers/servers_by_gateway_aim.html"
	command_CommandList = u"PyAIMt Commands"
	command_Statistics = u"Statistics for PyAIMt"
	command_RosterRetrieval = u"Retrieve Roster Contents"
	command_ConnectUsers = u"Connect all registered users"
	command_Done = u"Command completed"
	command_NoSession = u"You must be logged in to use this command."
	command_ChangePassword = u"Change AIM password"
	command_ChangePassword_Instructions = u"Enter your current and new AIM passwords below."
	command_ChangePassword_NewPassword = u"New password"
	command_ChangePassword_NewPasswordAgain = u"New password (again)"
	command_ChangePassword_OldPassword = u"Current password"
	command_ChangePassword_Mismatch = u"New passwords entered do not match."
	command_ChangePassword_Failed = u"Password change failed.  Most likely this is due to the wrong current password being entered."
	command_EmailLookup = u"Look up AIM users via email"
	command_EmailLookup_Instructions = u"Enter an email address below to locate screen names associated with it."
	command_EmailLookup_Email = u"E-Mail address"
	command_EmailLookup_Results = u"These screen names matched the address provided:"
	command_ChangeEmail = u"Change registered e-mail address"
	command_ChangeEmail_Instructions = u"Enter your new e-mail address below.\nA confirmation message will be sent to your current address and,\nunless you cancel, your new address will take effect in 72 hours."
	command_ChangeEmail_Email = u"E-Mail address"
	command_FormatScreenName = u"Change format of screen name"
	command_FormatScreenName_Instructions = u"Enter format of screen name below.\nPlease be aware that only capitalization and spacing may be changed."
	command_FormatScreenName_FMTScreenName = u"Formatted ScreenName"
	command_ConfirmAccount = u"Confirm AIM account"
	command_ConfirmAccount_Complete = u"Account confirmation request completed.\nYou should receive email soon with instructions on how to proceed."
	command_ConfirmAccount_Failed = u"Unable to request confirmation at this time."
	command_AIMURITranslate = u"Translate an AIM URI"
	command_AIMURITranslate_Instructions = u"Enter an AIM URI and appropriate action will be taken based off the function of the URI."
	command_AIMURITranslate_URI = u"URI"
	command_AIMURITranslate_Failed = u"Unable to determine function of URI."
	command_UpdateMyVCard = u"Update my VCard"
	statistics_OnlineSessions = u"Online Users"
	statistics_Uptime = u"Uptime"
	statistics_IncomingMessages = u"Incoming Messages"
	statistics_OutgoingMessages = u"Outgoing Messages"
	statistics_TotalSessions = u"Total Sessions"
	statistics_MaxConcurrentSessions = u"Max Concurrent Sessions"
	statistics_MessageCount = u"Message Count"
	statistics_FailedMessageCount = u"Failed Message Count"
	statistics_AvatarCount = u"Avatar Count"
	statistics_FailedAvatarCount = u"Failed Avatar Count"
	statistics_OnlineSessions_Desc = u"The number of users currently connected to the service."
	statistics_Uptime_Desc = u"How long the service has been running, in seconds."
	statistics_IncomingMessages_Desc = u"How many messages have been transferred from the AIM network."
	statistics_OutgoingMessages_Desc = u"How many messages have been transferred to the AIM network."
	statistics_TotalSessions_Desc = u"The number of connections since the service started."
	statistics_MaxConcurrentSessions_Desc = u"The maximum number of users connected at any one time."
	statistics_MessageCount_Desc = u"How many messages have been transferred to and from the AIM network."
	statistics_FailedMessageCount_Desc = u"The number of messages that didn't make it to the AIM recipient and were bounced."
	statistics_AvatarCount_Desc = u"How many avatars have been transferred to and from the AIM network."
	statistics_FailedAvatarCount_Desc = u"The number of avatar transfers that have failed."
	chatroom_Exchanges = u"AIM Chatroom Exchanges"
en_US = en # en-US is the same as en, so are the others
en_AU = en
en_GB = en
