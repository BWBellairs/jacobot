import html.parser
import json
import time
import re
from common import *
from datetime import datetime
from time import sleep
RegisterMod(__name__)

ipbans = ("31.48.60.79", "109.146.200.33", "5.80.87.176")
def Parse(raw, text):
    if len(text) >= 8 and text[0] == ":StewieGriffin!~Stewie@Powder/Bot/StewieGriffin" and text[1] == "PRIVMSG" and text[2] == "#powder-info" and text[3] == ":New" and text[4] == "registration:":
        if text[7].strip("[]") in ipbans:
            BanUser(text[5][:-1], "1", "p", "Automatic ip ban")
    match = re.match("^:StewieGriffinSub!(Stewie|jacksonmj3)@2a01:7e00::f03c:91ff:fedf:890f PRIVMSG #powder-saves :Warning: LCRY, Percentage: ([0-9.]+), http://tpt.io/~([0-9]+)$", raw)
    if match:
        saveID = match.group(3)
        info = GetSaveInfo(saveID)
        if info:
            elementCount = {}
            for element in info["ElementCount"]:
                elementCount[element["Name"]] = int(element["Count"])
            if "LCRY" in elementCount and elementCount["LCRY"] > 75000:
                LCRYpercent = float(elementCount["LCRY"]) / (sum(elementCount.values()))
                if LCRYpercent > .9:
                    #SendMessage("jacob1", "demoting save ID %s, %s" % (saveID, LCRYpercent))
                    if not PromotionLevel(match.group(3), -1):
                        SendMessage("+#powder-saves", "Error demoting save ID %s" % (match.group(3)))
                    else:
                        SendMessage("+#powder-saves", "Demoted save ID %s" % (match.group(3)))

seenReports = {}
def AlwaysRun(channel):
    global seenReports
    now = datetime.now()
    if now.minute == 30 and now.second ==  0:
        reportlist = ReportsList()
        if reportlist == None:
            SendMessage("#powder-info", "Error fetching reports")
            sleep(1)
            return
        reportlistunseen = [report for report in reportlist if seenReports.get(report[1]) != int(report[0])]
        for report in reportlistunseen:
            if seenReports.get(report[1]) and report[0] > seenReports.get(report[1]):
                report = (int(report[0]) - seenReports.get(report[1]), report[1], report[2])
        if len(reportlist):
            SendMessage("#powder-info", u"There are \u0002%s unread reports\u0002: " % (len(reportlist)) + ", ".join(["http://tpt.io/~%s#Reports %s" % (report[1], report[0]) for report in reportlist]))
            PrintReportList("#powder-info", reportlistunseen)
        seenReports = {}
        for report in reportlist:
            seenReports[report[1]] = int(report[0])

        #if len(reportlist):
        #    SendMessage("#powder-info", "Report list: " + ", ".join(["http://tpt.io/~%s#Reports %s" % (report[1], report[0]) for report in reportlist]))
        #else:
        #    SendMessage("#powder-info", "Test: No reports")

        convolist = GetConvoList()
        for convo in convolist:
            SendMessage("jacob1", "Conversation: {0} by {1} ({2} messages)".format(convo["Subject"], convo["MostRecent"], convo["MessageCount"]))
        sleep(1)

#Generic useful functions
def GetTPTSessionInfo(line):
    with open("passwords.txt") as f:
        return f.readlines()[line].strip()

def GetUserID(username):
	page = GetPage("http://powdertoy.co.uk/User.json?Name={}".format(username))
	thing = page.find("\"ID\":")
	return page[thing+5:page.find(",", thing)]

#Ban / Unban Functions
def BanUser(username, time, timeunits, reason):
    try:
        userID = int(username)
    except:
        userID = GetUserID(username)
    if userID < 0 or userID == 1 or userID == 38642:
        return
    data = {"BanUser":str(userID).strip("="), "BanReason":reason, "BanTime":time, "BanTimeSpan":timeunits}
    GetPage("http://powdertoy.co.uk/User/Moderation.html?ID=%s&Key=%s" % (userID, GetTPTSessionInfo(1)), GetTPTSessionInfo(0), data)

def UnbanUser(username):
    try:
        userID = int(username)
    except:
        userID = GetUserID(username)
    if userID < 0:
	    return
    data = {"UnbanUser":str(userID).strip("=")}
    GetPage("http://powdertoy.co.uk/User/Moderation.html?ID=%s&Key=%s" % (userID, GetTPTSessionInfo(1)), GetTPTSessionInfo(0), data)

#Functions to get info from TPT
def GetPostInfo(postID):
    page = GetPage("http://tpt.io/.%s" % postID)
    match = re.search("<div class=\"Comment\">(.+?<div id=\"MessageContainer-%s\" class=\"Message\">.+?)</li>" % postID, page, re.DOTALL)
    matchinfo = filter(None, re.split("[ \n\t]*<.+?>[ \n\t]*", match.group(1)))
    #"[ \n\t]*</?div.+?>[ \n\t+]*"
    print(matchinfo)

def GetSaveInfo(saveID):
    try:
        page = GetPage("http://powdertoythings.co.uk/Powder/Saves/ViewDetailed.json?ID=%s" % saveID)
        info = json.loads(page)
        return info
    except Exception:
        return None

def FormatDate(unixtime):
    timestruct = time.localtime(unixtime)
    strftime = time.strftime("%a %b %d %Y %I:%M:%S%p", timestruct)
    return strftime

def FormatSaveInfo(info):
    elementCount = {}
    for element in info["ElementCount"]:
        elementCount[element["Name"]] = element["Count"]
    elementCountSorted = sorted(elementCount.items(), key=lambda x: x[1], reverse=True)

    mainline = "Save is \x0302%s\x03 (ID:%s) by \x0305%s\x03. Has %s upvotes, %s downvotes, %s views, and %s comments. Created in TPT version %s." % (info["Name"], info["ID"], info["Username"], info["ScoreUp"], info["ScoreDown"], info["Views"], info["Comments"], info["PowderVersion"])
    dateline = "Uploaded on \x0303%s\x03. Updated %s time%s: [%s]" % (FormatDate(info["FirstPublishTime"]), len(info["BumpTimes"]), "" if len(info["BumpTimes"]) == 1 else "s", ", ".join([FormatDate(i) for i in info["BumpTimes"]]))
    descriptionline = "Description: \x0303%s\x03. Tags: [%s]" % (info["Description"], ", ".join(info["Tags"]))
    elementline = "Element Counts: %s" % (", ".join(["\x02%s\x02: %s" % (element[0], element[1]) for element in elementCountSorted]))
    return "%s\n%s\n%s\n%s" % (mainline, dateline, descriptionline, elementline)

#Moderation functions
def HidePost(postID, remove, reason):
    data = {"Hide_Reason":reason,"Hide_Hide":"Hide Post"}
    if remove:
        data["Hide_Remove"] = "1"
    GetPage("http://powdertoy.co.uk/Discussions/Thread/HidePost.html?Post=%s&Key=%s" % (postID, GetTPTSessionInfo(1)), GetTPTSessionInfo(0), data)

def UnhidePost(postID):
    GetPage("http://powdertoy.co.uk/Discussions/Thread/UnhidePost.html?Post=%s&Key=%s" % (postID, GetTPTSessionInfo(1)), GetTPTSessionInfo(0))

def LockThread(threadID, reason):
    GetPage("http://powdertoy.co.uk/Discussions/Thread/Moderation.html?Thread=%s" % (threadID), GetTPTSessionInfo(0), {"Moderation_Lock":"Lock Thread", "Moderation_LockReason":reason})

def UnlockThread(threadID):
    GetPage("http://powdertoy.co.uk/Discussions/Thread/Moderation.html?Thread=%s" % (threadID), GetTPTSessionInfo(0), {"Moderation_Unlock":"Unlock"})

def PromotionLevel(saveID, level):
    if level >= -2 and level <= 2:
        GetPage("http://powdertoy.co.uk/Browse/View.html?ID=%s&Key=%s" % (saveID, GetTPTSessionInfo(1)), GetTPTSessionInfo(0), {"PromoState":str(level)})
        return True
    return False

def SaveReports(ID):
    page = GetPage("http://powdertoy.co.uk/Reports/View.html?ID=%s" % ID, GetTPTSessionInfo(0))
    reports = re.findall('<div class="Message">([^<]+)<div class="Clear">', page)
    usernames = re.findall('<a href="/User.html\?ID=[0-9]+">([^<]+)</a>', page)[1:] #ignore "My Profile"
    return list(zip(usernames, reports))

def ReportsList():
    page = GetPage("http://powdertoy.co.uk/Reports.html", GetTPTSessionInfo(0))
    if page:
        matches = re.findall('ReportsCount">([0-9]+)</span>\t\t<span class="SaveName">\t\t\t<a href="/Reports/View.html\?ID=([0-9]+)" target="_blank">\t\t\t\t([^\t]+)\t\t\t</a>\t\t</span> by\t\t<span class="SaveAuthor">([^<]+)<', page)
    else:
        return None
    for match in matches:
        match = (int(match[0]), match[1], match[2])
    return matches

#Prints reports on a save (reporter and report text)
def PrintReports(channel, reportlist):
    h = html.parser.HTMLParser()
    for report in reportlist:
        reporter = report[0]
        text = h.unescape(report[1])
        for match in re.findall("((~|ID:?|id:?)? ?([0-9]+))", text):
            if len(match[0]) > 3:
                text = text.replace(match[0], "http://tpt.io/~"+match[2])
        SendMessage(channel, "\00314%s\003: %s" % (reporter, text))
    if not reportlist:
        SendMessage(channel, "No reports on that save")

#prints the report list (save title, save author, save ID link, report count)
def PrintReportList(channel, reportlist):
    h = html.parser.HTMLParser()
    for report in reportlist:
        ID = report[1]
        count = int(report[0])
        title = h.unescape(report[2])
        author = report[3]
        SendMessage(channel, "\00302%s\003 by \00305%s\003:\00314 http://tpt.io/~%s#Reports, %s report%s" % (title, author, ID, count, "" if count == 1 else "s"))
        reportlist = SaveReports(ID)
        PrintReports(channel, reportlist[:count])

def GetConvoList():
    page = GetPage("http://powdertoy.co.uk/Conversations.html", GetTPTSessionInfo(0))
    if not page:
        return []
    match = re.search(".*conversationsUnread = (.+);</script>.*", page)
    if not match:
        return []
    parsed = json.loads(match.group(1))
    return parsed

def GetLinkedAccounts(account):
    if account.find(".") >= 0:
        page = GetPage("http://powdertoy.co.uk/IPTools/GetInfo.json?IP=%s" % account, GetTPTSessionInfo(0))
    else:
        page = GetPage("http://powdertoy.co.uk/IPTools/GetInfo.json?Username=%s" % account, GetTPTSessionInfo(0))
    if not page:
        return "There was an error fetching the page (probably a timeout)"

    data = json.loads(page)
    if data == False:
        return "Invalid data"

    output = []
    if "Username" in data:
        if "Banned" in data and data["Banned"] == "1":
            output.append("\x02\x0304%s\x02\x03:" % data["Username"])
        else:
            output.append("\x02%s\x02:" % data["Username"])
    elif "Address" in data:
        if "Network" in data and "NetworkTop" in data:
            output.append("\x02%s\x02 (%s - %s):" % (data["Address"], data["Network"], data["NetworkTop"]))
        else:
            output.append("\x02%s\x02:" % data["Address"])
    if "Country" in data:
        if "CountryCode" in data:
            output.append("%s (%s)," % (data["Country"], data["CountryCode"]))
        else:
            output.append("%s," % (data["Country"]))
    if "ISP" in data:
        output.append("%s," % data["ISP"])

    if "Users" in data and len(data["Users"]):
        output.append("Linked Accounts:")
        for userID in data["Users"]:
            if data["Users"][userID]["Banned"] == "1":
                output.append("\x02\x0304%s\x02\x03 (%s)" % (data["Users"][userID]["Username"], userID))
            else:
                output.append("\x02%s\x02 (%s)" % (data["Users"][userID]["Username"], userID,))
    elif "Addresses" in data and len(data["Addresses"]):
        output.append("Linked IPs:")
        output.append(", ".join("%s (%s)" % (ip[0], ip[1]) for ip in data["Addresses"]))
    return " ".join(output)

def DoComment(saveID, message, jacob1 = False):
    GetPage("http://powdertoy.co.uk/Browse/View.html?ID=%s" % (saveID), GetTPTSessionInfo(0) if jacob1 else GetTPTSessionInfo(3), {"Comment":message})

def DoUnpublish(saveID):
    GetPage("http://powdertoy.co.uk/Browse/View.html?ID=%s&Key=%s" % (saveID, GetTPTSessionInfo(1)), GetTPTSessionInfo(0), {"ActionUnpublish":"&nbsp;"})

def DoPublish(saveID):
    GetPage("http://powdertoy.co.uk/Browse/View.html?ID=%s&Key=%s" % (saveID, GetTPTSessionInfo(1)), GetTPTSessionInfo(0), {"ActionPublish":"&nbsp;"})

@command("ban", minArgs = 4, owner = True)
def Ban(username, hostmask, channel, text, account):
    """(ban <user ID> <ban time> <ban time units> <reason>). bans someone in TPT. Owner only. Add = to ban usernames that look like IDs"""
    if username != "jacob1":
        SendNotice(username, "Error, only jacob1 should be able to use this command")
    BanUser(text[0], text[1], text[2], " ".join(text[3:]))

@command("unban", minArgs = 1, owner = True)
def Unban(username, hostmask, channel, text, account):
    """(unban <user ID>). unbans someone in TPT. Owner only."""
    if username != "jacob1":
        SendNotice(username, "Error, only jacob1 should be able to use this command")
    UnbanUser(text[0])

@command("post", minArgs = 1, admin = True)
def Post(username, hostmask, channel, text, account):
    """(post <post ID>). Gets info on a TPT post. Admin only."""
    GetPostInfo(text[0])
    
@command("hide", minArgs = 1, owner = True)
def Hide(username, hostmask, channel, text, account):
    """(hide <post ID> [<reason>]). Hides a post in TPT. Owner only."""
    HidePost(text[0], False, " ".join(text[1:]))

@command("remove", minArgs = 1, admin = True)
def Remove(username, hostmask, channel, text, account):
    """(remove <post ID> [<reason>]). Removes a post in TPT. Owner only."""
    HidePost(text[0], True, " ".join(text[1:]))

@command("unhide", minArgs = 1, admin = True)
def Unhide(username, hostmask, channel, text, account):
    """(unhide <post ID>). Unhides a post in TPT. Admin only."""
    UnhidePost(text[0])

@command("lock", minArgs = 2, owner = True)
def Lock(username, hostmask, channel, text, account):
    """(lock <thread ID> <reason>). Locks a thread in TPT. Owner only."""
    LockThread(text[0], " ".join(text[1:]))

@command("unlock", minArgs = 1, owner = True)
def Unlock(username, hostmask, channel, text, account):
    """(unlock <thread ID>). Unlocks a thread in TPT. Owner only."""
    UnlockThread(text[0])

@command("promolevel", minArgs = 2, admin = True)
def Unlock(username, hostmask, channel, text, account):
    """(promolevel <save ID> <level>). Sets the promotion level on a save. Admin only."""
    if PromotionLevel(text[0], int(text[1])):
        SendMessage(channel, "Done.")
    else:
        SendMessage(channel, "Invalid promotion level.")

@command("ipmap", minArgs = 1, admin = True)
def IpMap(username, hostmask, channel, text, account):
    """(ipmap <username/ip>). Prints out linked accounts or IP addresses. Admin only."""
    SendMessage(channel, GetLinkedAccounts(text[0]))

@command("saveinfo", minArgs = 1, admin = True)
def SaveInfo(username, hostmask, channel, text, account):
    """(saveinfo <saveid>). Prints out lots of useful information about TPT saves. Admin only."""
    info = GetSaveInfo(text[0])
    formatted = FormatSaveInfo(info)
    for line in formatted.split("\n"):
        SendMessage(channel, line)

@command("getreports", minArgs=1, admin = True)
def GetReports(username, hostmask, channel, text, account):
    """(getreports <saveid> [numreports]). Prints out all (or numreports) reports from a save. Admin only."""
    count = None
    reportlist = SaveReports(text[0])
    if len(text) > 1:
        count = int(text[1])
    PrintReports(channel, reportlist[:count])

@command("markread", minArgs=1, admin = True)
def MarkRead(username, hostmask, channel, text, account):
    """(markread <saveid>). Marks a report on a save as read. Admin only."""
    GetPage("http://powdertoy.co.uk/Reports.html?Read=%s" % text[0], GetTPTSessionInfo(0))

@command("markallread", admin = True)
def MarkAllRead(username, hostmask, channel, text, account):
    """(markallread). Marks all reports that have been printed to channel previously as read. Admin only."""
    global seenReports
    reportlist = ReportsList()
    if reportlist == None:
        SendMessage(channel, "Error fetching reports")
        return
    markedread = []
    unread = []
    for report in reportlist:
        if report[1] in seenReports:
            GetPage("http://powdertoy.co.uk/Reports.html?Read=%s" % report[1], GetTPTSessionInfo(0))
            markedread.append(report[1])
        else:
            unread.append(report[1])
    if markedread:
        SendMessage(channel, "These saves were marked as read: %s" % (" ".join(markedread)))
    if unread:
        SendMessage(channel, "These saves still have unread reports: %s" % (" ".join(unread)))

@command("reports", admin = True)
def Reports(username, hostmask, channel, text, account):
    """(reports) No args. Prints out the reports list. Owner only."""
    global seenReports
    reportlist = ReportsList()
    if reportlist == None:
        SendMessage(channel, "Error fetching reports")
        return
    elif len(reportlist) == 0:
        SendMessage(channel, "No reports")
    else:
        PrintReportList(channel, reportlist)

    seenReports = {}
    for report in reportlist:
        seenReports[report[1]] = report[0]

@command("comment", minArgs=2, owner = True)
def Comment(username, hostmask, channel, text, account):
    """(comment <saveID> <comment>). Comments on a save as jacob1. Owner only."""
    DoComment(text[0], " ".join(text[1:]), True)
    SendMessage(channel, "Done.")

@command("unpublish", minArgs=1, admin = True)
def Unpublish(username, hostmask, channel, text, account):
    """(unpublish <saveID>). Unpublishes a save. Admin only."""
    DoUnpublish(text[0])
    SendMessage(channel, "Done.")

@command("publish", minArgs=1, admin = True)
def Publish(username, hostmask, channel, text, account):
    """(publish <saveID>). Publishes a save. Admin only."""
    DoPublish(text[0])
    SendMessage(channel, "Done.")

@command("readreport", minArgs=2, admin = True)
def Stolen(username, hostmask, channel, text, account):
    """(readreport <saveID> <comment>). Disables a save and comments with a message as jacobot. Admin only."""
    saveID = text[0]
    #DoUnpublish(saveID)
    PromotionLevel(saveID, -2)
    DoComment(saveID, " ".join(text[1:]))
    SendMessage(channel, "Done.")

@command("stolen", minArgs=2, admin = True)
def Stolen(username, hostmask, channel, text, account):
    """(stolen <stolenID> <originalID>). Disables a save and leaves a comment by jacobot with the original saveID, save name, and author. Admin only."""
    stolenID = text[0]
    saveID = text[1]
    #DoUnpublish(stolenID)
    PromotionLevel(stolenID, -2)
    info = GetSaveInfo(saveID)
    if info:
        DoComment(stolenID, "Save unpublished: stolen from id:%s (save \"%s\" by %s)." % (saveID, info["Name"], info["Username"]))
        SendMessage(channel, "Done.")
    else:
        SendMessage(channel, "Error getting original save info.")