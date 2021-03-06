#!/usr/bin/env python

""" @author: Josep Flix / John Artieda """

import xml.dom.minidom, os, time
from xml import xpath
import re, datetime, string, sys, pprint
from optparse import OptionParser

usage = "usage: (example) %prog -p ~/www/SR2 -u http://cms-site-readiness.web.cern.ch/cms-site-readiness"
parser = OptionParser(usage=usage, version="%prog 1.0")
parser.add_option("-p", "--path_out", dest="path_out", help="Sets the PATH to store the produced data", metavar="PATH")
parser.add_option("-u", "--url", dest="url", help="Sets the base URL where produced data is accessible", metavar="URL")
parser.add_option("-c", "--css",     metavar="PATH",    default=".",   help="css file path")
(options, args) = parser.parse_args()

if len(sys.argv) != 5:
	parser.error("incorrect number of arguments. Check needed arguments with --help")

def getTierNumber(name):
	l=re.match("^T(\d+)",name);
	if not l:
		print "Error getting the Tier number from %s" % name
		return
	if name=="T0_CH_CERN": return 0
	else:	return l.group(1)

def Buff2CMS(unicode_buffer):
	buffer=str(unicode_buffer)
	name=buffer
	i=string.find(buffer,"_MSS")
	if i>0:
		name=buffer[0:i]
	i=string.find(buffer,"_Export")
	if i>0:
		name=buffer[0:i]
	return name

def Buff2CMS2(unicode_buffer):
	buffer=str(unicode_buffer)
	name=buffer
	i=string.find(buffer,"_Buffer")
	if i>0:
		name=buffer[0:i]
	i=string.find(buffer,"_Disk")
	if i>0:
		name=buffer[0:i]
	i=string.find(buffer,"_MSS")
	if i>0:
		name=buffer[0:i]
	i=string.find(buffer,"_ECHO")
	if i>0:
		name=buffer[0:i]
	i=string.find(buffer,"_Export")
	if i>0:
		name=buffer[0:i]
	return name

def TierExceptions(name):
	i=0
	if name=="": i=1
	if name=="T1_CH_CERN": i=1
	if name=="T1_CH_CERN_Buffer": i=1
	if name=="T2_CH_CAF": i=1
	if name=="T1_RAL_Stage": i=1
	if name=="T1_DE_FZK": i=1
	if name=="T2_RU_IHEP_Disk": i=1
	if name=="T2_KIPT": i=1
	if name=="T2_CUKUROVA": i=1
	if name[0:2]=="XT": i=1
	return i

today=datetime.datetime.utcnow()
timestamp=today.strftime("%Y-%m-%d %H:%M:%S")
todaystampfileSSB=today.strftime("%Y-%m-%d 00:00:01")
timestamphtml=today.strftime("%Y%m%d")

pathN=options.path_out + "/INPUTxmls"
fileN=pathN + "/enabledlinks.xml"
pathout= options.path_out + "/toSSB"
pathoutHTML= options.path_out + "/HTML"
pathoutPLOTS= options.path_out + "/PLOTS"
pathoutASCII= options.path_out + "/ASCii"
filehtml= pathoutHTML + '/CommissionedLinks_Sites_' + timestamphtml +'.html'
slinkhtml= './CommissionedLinks_Sites.html'

if options.url.find("pic.es") > 0:
	linkmetrics = options.url + "/CommLinksReports/CommissionedLinks_Sites_" + timestamphtml +'.html'
elif options.url.find("cern.ch") > 0:
	linkmetrics = options.url + "/CommLinksReports/HTML/CommissionedLinks_Sites_" + timestamphtml +'.html'

if not os.path.exists(options.path_out):
	os.makedirs(options.path_out)
if not os.path.exists(pathout):
	os.makedirs(pathout)
if not os.path.exists(pathoutHTML):
	os.makedirs(pathoutHTML)
if not os.path.exists(pathoutPLOTS):
	os.makedirs(pathoutPLOTS)
if not os.path.exists(pathN):
	os.makedirs(pathN)
if not os.path.exists(pathoutASCII):
	os.makedirs(pathoutASCII)

# Metric Thresholds

T1downlinkT0=1
T1uplinksT2s=20
T1downlinksuplinksT1s=4
T2uplinkT1s=2
T2downlinkT1s=4

# Output files :: feeds to SSB

# T1 :: commissioned downlink with the Tier-0 (T1downlinkT0)
metricPage1="%s/CommissionedLinks_SSBfeed_Tier1_1.txt" % pathout
# T1 :: >= (T1uplinksT2s) commissioned uplinks to Tier-2 sites
metricPage2="%s/CommissionedLinks_SSBfeed_Tier1_2.txt" % pathout
# T1 :: >= (T1downlinksuplinksT1s) downlinks/uplinks to other Tier-1 sites
metricPage3="%s/CommissionedLinks_SSBfeed_Tier1_3.txt" % pathout
# T2 :: >= (T2uplinkT1s) uplinks to Tier-1 sites
metricPage4="%s/CommissionedLinks_SSBfeed_Tier2_1.txt" % pathout
# T2 :: >= (T2downlinkT1s) downlinks from Tier-1 sites
metricPage5="%s/CommissionedLinks_SSBfeed_Tier2_2.txt" % pathout

url='https://cmsweb.cern.ch/phedex/datasvc/xml/prod/Links'
os.system("curl -ks -H 'Accept: text/xml'  '%s' > %s" % (url,fileN))
f=file(fileN,'r')
t= xml.dom.minidom.parse(f)
f.close()

sites={}
siteStatus1={}; siteStatus2={}; siteStatus3={}; siteStatus4={}; siteStatus5={}
siteColor1={}; siteColor2={}; siteColor3={}; siteColor4={}; siteColor5={}

for url in xpath.Evaluate('/phedex/link', t):

	source=url.getAttribute("from")
	if source.find("MSS")>0 : continue
	sourceName=Buff2CMS(source)
	sourceTier=getTierNumber(sourceName)

	target=url.getAttribute("to")
	if target.find("MSS")>0: continue
	targetName=Buff2CMS(target)
	targetTier=getTierNumber(targetName)

	# exceptions
	if TierExceptions(sourceName) or TierExceptions(targetName): continue
	if targetTier=="3" or sourceTier=="3" : continue

	if not sites.has_key(sourceName):
		sites[sourceName]={'upT0':[], 'downT0':[],'upT1':[], 'downT1':[], 'upT2':[], 'downT2':[]}

	value=url.getAttribute("status")
	if (value != "deactivated" ):
		if not sites.has_key(targetName):
			sites[targetName]={'upT0':[], 'downT0':[],'upT1':[], 'downT1':[], 'upT2':[], 'downT2':[]}

		uplink='upT%s' % targetTier
		downlink='downT%s' % sourceTier
		sites[sourceName][uplink].append(targetName)
		sites[targetName][downlink].append(sourceName)

	if sourceTier=="1" :
		sourceName2=Buff2CMS2(source) # if site has _Buffer or _Disk also creates site name T1_XX_YYY
		if not sites.has_key(sourceName2):
			sites[sourceName2]={'upT0':[], 'downT0':[],'upT1':[], 'downT1':[], 'upT2':[], 'downT2':[]}
		if (value != "deactivated" ):
			sites[sourceName2][uplink].append(targetName) # T1_XX_YYY adds _Buffer and _Disk links

	if targetTier=="1" :
		targetName2=Buff2CMS2(target) # if site has _Buffer or _Disk also creates site name T1_XX_YYY
		if (value != "deactivated" ):
			if not sites.has_key(targetName2):
				sites[targetName2]={'upT0':[], 'downT0':[],'upT1':[], 'downT1':[], 'upT2':[], 'downT2':[]}
			sites[targetName2][downlink].append(sourceName) # T1_XX_YYY adds _Buffer or _Disk links

# Build txt feed to SSB

keys=sites.keys()
keys.sort()

for i in range(0,len(keys)):
	site=keys[i]
	isT1=0
	isT2=0
	if site[1]=="1": isT1=1
	if site[1]=="2": isT2=1
	toT0=len(sites[site]["upT0"])
	fromT0=len(sites[site]["downT0"])
	toT1=len(sites[site]["upT1"])
	fromT1=len(sites[site]["downT1"])
	toT2=len(sites[site]["upT2"])
	fromT2=len(sites[site]["downT2"])

	if isT1:
		siteStatus1[site]=fromT0
		siteStatus2[site]=toT2
		ss3="%i(d)-%i(u)" % (fromT1,toT1)
		siteStatus3[site]=ss3
		siteStatus4[site]="n/a"
		siteStatus5[site]="n/a"

		site2=Buff2CMS2(site) # if name has _Buffer or _Disk --> create site name T1_XX_YYY

		siteColor1[site]="green"
		siteColor2[site]="green"
		siteColor3[site]="green"
		siteColor1[site2]="green"
		siteColor2[site2]="green"
		siteColor3[site2]="green"

		if fromT0<T1downlinkT0:
			siteColor1[site]="red"
			siteColor1[site2]="red" # if either Buffer or Disk are red, site should be red

		if toT2<T1uplinksT2s:
			siteColor2[site]="red"
			siteColor2[site2]="red" # if either Buffer or Disk are red, site should be red

		if toT1<T1downlinksuplinksT1s or fromT1<T1downlinksuplinksT1s:
			siteColor3[site]="red"
			siteColor3[site2]="red"	# if either Buffer or Disk are red, site should be red

	if isT2:

		siteStatus1[site]="n/a"
		siteStatus2[site]="n/a"
		siteStatus3[site]="n/a"

		siteStatus4[site]=toT1
		siteStatus5[site]=fromT1

		if toT1<T2uplinkT1s:
			siteColor4[site]="red"
		else:
			siteColor4[site]="green"

		if fromT1<T2downlinkT1s:
			siteColor5[site]="red"
		else:
			siteColor5[site]="green"

# Think how to manage CERN T0
    # T1:
    	# siteStatus1[site]=fromT0
     	# siteStatus2[site]=toT2
      	# ss3="%i(d)-%i(u)" % (fromT1,toT1)
       	# siteStatus3[site]=ss3
    # T2:
    	# siteStatus4[site]=toT1
     	# siteStatus5[site]=fromT1
	if site=="T0_CH_CERN":
		siteStatus1[site]="n/a"
		siteStatus2[site]="n/a"
		siteStatus3[site]="n/a"
		siteStatus4[site]="n/a"
		siteStatus5[site]="n/a"

# Build SSB txt input files

span = 86400
reptime="# - Report made on %s (UTC)\n" % timestamp

f=file(metricPage1,'w')
f.write('# Site Status derived from DDT Commissioned Links\n')
f.write('#\n')
mesT1_1="T1 needs DDT commissioned downlink from T0_CH_CERN"
mesT1_1_2="T1::downlinkT0"
mes="# - Status of %s (Requirement: %s)\n" % (mesT1_1_2,mesT1_1)
f.write(mes)
f.write('#\n')
f.write(reptime)
f.write('#\n')

siteList2Delete = []
for i in range(0,len(keys)):
	site=keys[i]
        try:
	    status=siteStatus1[site]
        except KeyError:
            print "No panic. I just couldn't find the site: %s." % site
            print "I will delete it from the site pool and continue."
            print "--Please try to find the reason. (Is this site new?"
            print "If so, ask transfer team whether they are currently working on this site or not.)"
            siteList2Delete.append(i)
            continue
	if status=="n/a": continue
	color=siteColor1[site]
	link = linkmetrics + "#" + mesT1_1_2
	f.write('%s\t%s\t%s\t%s\t%s\n' % (todaystampfileSSB, site, status, color, link))
f.close()

for i in siteList2Delete:
    del keys[i]

f=file(metricPage2,'w')
f.write('# Site Status derived from DDT Commissioned Links\n')
mesT1_2="T1 needs >= %s DDT commissioned uplinks to T2 sites" % T1uplinksT2s
mesT1_2_2="T1::uplinksT2s"
mesT2_2_2="T2::downlinkT1s"
mes="# - Status of %s (Requirement: %s)\n" % (mesT1_2_2,mesT1_2)
f.write('#\n')
f.write(mes)
f.write('#\n')
f.write(reptime)
f.write('#\n')
for i in range(0,len(keys)):
	site=keys[i]
	status=siteStatus2[site]
	if status=="n/a": continue
	color=siteColor2[site]
	link = linkmetrics + "#" + mesT1_2_2 + "_and_" + mesT2_2_2
	f.write('%s\t%s\t%s\t%s\t%s\n' % (todaystampfileSSB, site, status, color, link))

f.close()

f=file(metricPage3,'w')
f.write('# Site Status derived from DDT Commissioned Links\n')
mesT1_3="T1 needs >= %s DDT commissioned uplinks and downlinks, respectively, with other T1 sites" % T1downlinksuplinksT1s
mesT1_3_2="T1::downlinks/uplinksT1s"
mes="# - Status of %s (Requirement: %s)\n" % (mesT1_3_2,mesT1_3)
f.write('#\n')
f.write(mes)
f.write('#\n')
f.write(reptime)
f.write('#\n')
for i in range(0,len(keys)):
	site=keys[i]
	status=siteStatus3[site]
	if status=="n/a": continue
	color=siteColor3[site]
	link = linkmetrics + "#" + mesT1_3_2
	f.write('%s\t%s\t%s\t%s\t%s\n' % (todaystampfileSSB, site, status, color, link))

f.close()

f=file(metricPage4,'w')
f.write('# Site Status derived from DDT Commissioned Links\n')
mesT2_1="T2 needs >= %s commissioned uplinks to T1 sites" % T2uplinkT1s
mesT2_1_2="T2::uplinkT1s"
mes="# - Status of %s (Requirement: %s)\n" % (mesT2_1_2,mesT2_1)
f.write('#\n')
f.write(mes)
f.write('#\n')
f.write(reptime)
f.write('#\n')

for i in range(0,len(keys)):
	site=keys[i]
	status=siteStatus4[site]
	if status=="n/a": continue
	color=siteColor4[site]
	link = linkmetrics + "#" + mesT2_1_2
	f.write('%s\t%s\t%s\t%s\t%s\n' % (todaystampfileSSB, site, status, color, link))

f.close()

f=file(metricPage5,'w')
f.write('# Site Status derived from DDT Commissioned Links\n')
mesT2_2="T2 needs >= %s commissioned downlinks from T1 sites" % T2downlinkT1s
#mesT2_2_2="T2::downlinkT1s"
mes="# - Status of %s (Requirement: %s)\n" % (mesT2_2_2,mesT2_2)
f.write('#\n')
f.write(mes)
f.write('#\n')
f.write(reptime)
f.write('#\n')

for i in range(0,len(keys)):
	site=keys[i]
	status=siteStatus5[site]
	if status=="n/a": continue
	color=siteColor5[site]
	link = linkmetrics + "#" + mesT1_2_2 + "_and_" + mesT2_2_2
	f.write('%s\t%s\t%s\t%s\t%s\n' % (todaystampfileSSB, site, status, color, link))

f.close()


####################################################################
# Print Site html view
####################################################################

# --> Fill all available T1s and T2s:
availableT1 = {}
availableT2 = {}

for i in range(0,len(keys)):
	site=keys[i]
	if site[1]=="1":
		if "_Buffer" not in site and "_Disk" not in site: continue
		if not availableT1.has_key(site):
			availableT1[site]={}
	elif site[1]=="2":
		if not availableT2.has_key(site):
			availableT2[site]={}

keyst1=availableT1.keys()
keyst1.sort()

keyst2=availableT2.keys()
keyst2.sort()

fileHandle = open ( filehtml , 'w' )

fileHandle.write("<html><head><link type=\"text/css\" rel=\"stylesheet\" href=\""+options.css+"/style-css-links.css\"/></head>\n")
fileHandle.write("<body><center>\n")

lw1="15"
lw2="550"

# T1_1 view

dw="75"
dw2="125"

fileHandle.write("<a name=\""+ mesT1_1_2 + "\"></a>\n\n")

fileHandle.write("<p><div id=\"metrics\"> Status of " + mesT1_1_2 + "</div>\n")
fileHandle.write("<br><div id=\"site\">" + reptime + "</div>\n")

#legends

fileHandle.write("<br>\n")
fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=leg>\n")
fileHandle.write("<tr height=15>\n")
mes="Site status for %s (Requirement: %s).\n" % (mesT1_1_2,mesT1_1)
fileHandle.write("<td width=" + lw2 + " colspan=2><div id=\"legendexp\">" + mes + "</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=66FF44></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Site satisfies the requirement.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=FF6600></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Site failing the requirement.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("</table>\n")
fileHandle.write("<p>\n")

fileHandle.write("<p>\n")
fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=leg>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw2 + " colspan=2><div id=\"legendexp\">Status on Data Transfer Links.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=green></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Link is DDT-commissioned and enabled in Production PhEDEx instance.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=red></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Link is not DDT-commissioned and is disabled in Production PhEDEx instance.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("</table>\n")
fileHandle.write("<p>\n")

fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=stat>\n")
fileHandle.write("<p>\n")

for j in range(0,3):

	fileHandle.write("<tr height=15>\n")
	if j==0 or j==1:
		fileHandle.write("<td width=" + dw2 + "><div id=\"site\"></div></td>\n")
	if j==2:
		fileHandle.write("<td width=" + dw2 + "><div id=\"site\"> T0_CH_CERN to:</div></td>\n")
	for i in range(0,len(keyst1)):
		site=keyst1[i]
		if site[1]!="1": continue
		#if "T1_CH_CERN" in site: continue
		fromT0=len(sites[site]["downT0"])
		if j==1:
			if siteColor1[site]=="green":
				color="66FF44"
			if siteColor1[site]=="red":
				color="FF6600"
			if siteColor1[site]=="white":
				color="white"
			fileHandle.write("<td width=" + dw + " bgcolor=" + color + "><div id=\"site\">" + site + "</div></td>\n")
		if j==0:
			mes="%i link enabled" % siteStatus1[site]
			fileHandle.write("<td width=" + dw + "><div id=enabled>" + mes + "</div></td>\n")
		if j==2:
			fileHandle.write("<td width=" + dw + " bgcolor=" + siteColor1[site] + "></td>\n")
	fileHandle.write("</tr>\n")

fileHandle.write("</table>\n")
fileHandle.write("<p><br>\n")

# T1_3 view

dw="75"
dw2="150"
dw3="50"

fileHandle.write("<a name=\""+ mesT1_3_2 + "\"></a>\n\n")

fileHandle.write("<p><div id=\"metrics\"> Status of " + mesT1_3_2 + "</div>\n")
fileHandle.write("<br><div id=\"site\">" + reptime + "</div>\n")

#legends

lw2="800"

fileHandle.write("<br>\n")
fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=leg>\n")
fileHandle.write("<tr height=15>\n")
mes="Site status for %s (Requirement: %s).\n" % (mesT1_3_2,mesT1_3)
fileHandle.write("<td width=" + lw2 + " colspan=2><div id=\"legendexp\">" + mes + "</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=66FF44></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Site satisfies the requirement.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=FF6600></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Site failing the requirement.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("</table>\n")
fileHandle.write("<p>\n")

fileHandle.write("<p>\n")
fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=leg>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw2 + " colspan=2><div id=\"legendexp\">Status on Data Transfer Links.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=green></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Link is DDT-commissioned and enabled in Production PhEDEx instance.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=red></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Link is not DDT-commissioned and is disabled in Production PhEDEx instance.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("</table>\n")
fileHandle.write("<p>\n")

fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=stat>\n")
fileHandle.write("<p>\n")

fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + dw2 + "><div id=\"site\"></div></td>\n")

for k in range(0,len(availableT1)):
	t1site2=keyst1[k]
	mes="%s links enabled" % siteStatus3[t1site2]
	fileHandle.write("<td width=" + dw + " colspan=2><div id=enabled>" + mes + "</div></td>\n")
fileHandle.write("</tr>\n")

fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + dw2 + "><div id=\"site\"></div></td>\n")
for k in range(0,len(availableT1)):
	t1site2=keyst1[k]
	if siteColor3[t1site2]=="green":
		color="66FF44"
	if siteColor3[t1site2]=="red":
		color="FF6600"
	if siteColor3[t1site2]=="white":
		color="white"
	fileHandle.write("<td width=" + dw3 + " colspan=2 bgcolor=" + color + "><div id=\"site\">" + t1site2 + "</div></td>\n")
fileHandle.write("</tr>\n")

for j in range(0,len(availableT1)):

	t1site=keyst1[j]

	if siteColor3[t1site]=="green":
		color="66FF44"
	if siteColor3[t1site]=="red":
		color="FF6600"
	if siteColor3[t1site]=="white":
		color="white"

	fileHandle.write("<td width=" + dw + " bgcolor=" + color + "><div id=\"site\">" + t1site + "</div></td>\n")

	for k in range(0,len(availableT1)):
		t1site2=keyst1[k]

        	if sites[t1site]["upT1"].count(t1site2) != 0:
			color="green"
		else:
			color="red"
		if t1site==t1site2:
			color="black"
		if color=="black":
			fileHandle.write("<td width=" + dw3 + " bgcolor=" + color + "><div id=comment></div></td>\n")
		else:
			fileHandle.write("<td width=" + dw3 + " bgcolor=" + color + "><div id=comment>to:</div></td>\n")

        	if sites[t1site]["downT1"].count(t1site2) != 0:
			color="green"
		else:
			color="red"
		if t1site==t1site2:
			color="black"
		if color=="black":
			fileHandle.write("<td width=" + dw3 + " bgcolor=" + color + "><div id=comment></div></td>\n")
		else:
			fileHandle.write("<td width=" + dw3 + " bgcolor=" + color + "><div id=comment>from:</div></td>\n")

	fileHandle.write("</tr>\n")

fileHandle.write("</table>\n")
fileHandle.write("<p><br>\n")

# T2_1 view

dw="75"
dw2="125"

fileHandle.write("<a name=\""+ mesT2_1_2 + "\"></a>\n\n")

fileHandle.write("<p><div id=\"metrics\"> Status of " + mesT2_1_2 + "</div>\n")
fileHandle.write("<br><div id=\"site\">" + reptime + "</div>\n")

#legends

lw2="550"

fileHandle.write("<br>\n")
fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=leg>\n")
fileHandle.write("<tr height=15>\n")
mes="Site status for %s (Requirement: %s).\n" % (mesT2_1_2,mesT2_1)
fileHandle.write("<td width=" + lw2 + " colspan=2><div id=\"legendexp\">" + mes + "</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=66FF44></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Site satisfies the requirement.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=FF6600></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Site failing the requirement.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("</table>\n")
fileHandle.write("<p>\n")

fileHandle.write("<p>\n")
fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=leg>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw2 + " colspan=2><div id=\"legendexp\">Status on Data Transfer Links.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=green></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Link is DDT-commissioned and enabled in Production PhEDEx instance.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=red></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Link is not DDT-commissioned and is disabled in Production PhEDEx instance.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("</table>\n")
fileHandle.write("<p>\n")

fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=stat>\n")
fileHandle.write("<p>\n")

fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + dw2 + "><div id=\"site\"></div></td>\n")
fileHandle.write("<td width=" + dw2 + "><div id=\"site\"></div></td>\n")
for k in range(0,len(availableT1)):
	t1site=keyst1[k]
	fileHandle.write("<td width=" + dw + "><div id=\"site\">" + t1site + "</div></td>\n")
fileHandle.write("</tr>\n")

for j in range(0,len(availableT2)):

	t2site=keyst2[j]
	fileHandle.write("<tr height=15>\n")

	mes="%s links enabled" % siteStatus4[t2site]
	fileHandle.write("<td width=" + dw + "><div id=enabled>" + mes + "</div></td>\n")

	if siteColor4[t2site]=="green":
		color="66FF44"
	if siteColor4[t2site]=="red":
		color="FF6600"
	if siteColor4[t2site]=="white":
		color="white"

	fileHandle.write("<td width=" + dw2 + " bgcolor=" + color +"><div id=\"site\">" + t2site + " to:</div></td>\n")

	for k in range(0,len(availableT1)):
		t1site=keyst1[k]
        	if sites[t2site]["upT1"].count(t1site) != 0:
			color="green"
		else:
			color="red"
		fileHandle.write("<td width=" + dw + " bgcolor=" + color + "></td>\n")
	fileHandle.write("</tr>\n")

fileHandle.write("</table>\n")
fileHandle.write("<p><br>\n")

# T2_2 view

dw="75"
dw2="125"

fileHandle.write("<a name=\""+ mesT1_2_2 + "_and_" + mesT2_2_2 + "\"></a>\n\n")

fileHandle.write("<p><div id=\"metrics\"> Status of " + mesT2_2_2 + " & " + mesT1_2_2 + "</div>\n")
fileHandle.write("<br><div id=\"site\">" + reptime + "</div>\n")

#legends

fileHandle.write("<br>\n")
fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=leg>\n")
fileHandle.write("<tr height=15>\n")
mes="Site status for %s (Requirement: %s).\n" % (mesT2_2_2,mesT2_2)
fileHandle.write("<td width=" + lw2 + " colspan=2><div id=\"legendexp\">" + mes + "</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
mes="Site status for %s (Requirement: %s).\n" % (mesT1_2_2,mesT1_2)
fileHandle.write("<td width=" + lw2 + " colspan=2><div id=\"legendexp\">" + mes + "</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=66FF44></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Site satisfies the requirement.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=FF6600></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Site failing the requirement.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("</table>\n")
fileHandle.write("<p>\n")

fileHandle.write("<p>\n")
fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=leg>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw2 + " colspan=2><div id=\"legendexp\">Status on Data Transfer Links.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=green></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Link is DDT-commissioned and enabled in Production PhEDEx instance.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + lw1 + " bgcolor=red></td>\n")
fileHandle.write("<td width=" + lw2 + "><div id=\"legend\"> = Link is not DDT-commissioned and is disabled in Production PhEDEx instance.</div></td>\n")
fileHandle.write("</tr>\n")
fileHandle.write("</table>\n")
fileHandle.write("<p>\n")

fileHandle.write("<table border=\"0\" cellspacing=\"0\" class=stat>\n")
fileHandle.write("<p>\n")


fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + dw2 + "><div id=\"site\"></div></td>\n")
fileHandle.write("<td width=" + dw2 + "><div id=\"site2\">(T1::uplinksT2s)</div></td>\n")
for k in range(0,len(availableT1)):
	t1site=keyst1[k]
	mes="%i links enabled" % siteStatus2[t1site]
	fileHandle.write("<td width=" + dw + "><div id=enabled>" + mes + "</div></td>\n")
fileHandle.write("</tr>\n")

fileHandle.write("<tr height=15>\n")
fileHandle.write("<td width=" + dw2 + "><div id=\"site\">(T2::downlinkT1s)</div></td>\n")
fileHandle.write("<td width=" + dw2 + "><div id=\"site\"></div></td>\n")
for k in range(0,len(availableT1)):
	t1site=keyst1[k]
	if siteColor2[t1site]=="green":
		color="66FF44"
	if siteColor2[t1site]=="red":
		color="FF6600"
	if siteColor2[t1site]=="white":
		color="white"
	fileHandle.write("<td width=" + dw + " bgcolor=" + color + "><div id=\"site\">" + t1site + "</div></td>\n")
fileHandle.write("</tr>\n")

#fileHandle.write("<tr height=15>\n")
#fileHandle.write("<td width=" + dw2 + "><div id=\"site\"></div></td>\n")
#fileHandle.write("<td width=" + dw2 + "><div id=\"site\"></div></td>\n")
#for k in range(0,len(availableT1)):
#	t1site=keyst1[k]
#	fileHandle.write("<td width=" + dw + "><div id=\"site\">" + t1site + "</div></td>\n")
#fileHandle.write("</tr>\n")

for j in range(0,len(availableT2)):

	t2site=keyst2[j]
	fileHandle.write("<tr height=15>\n")

	mes="%s links enabled" % siteStatus5[t2site]
	fileHandle.write("<td width=" + dw + "><div id=enabled>" + mes + "</div></td>\n")

	if siteColor5[t2site]=="green":
		color="66FF44"
	if siteColor5[t2site]=="red":
		color="FF6600"
	if siteColor5[t2site]=="white":
		color="white"

	fileHandle.write("<td width=" + dw2 + " bgcolor=" + color +"><div id=\"site\">" + t2site + " from:</div></td>\n")

	for k in range(0,len(availableT1)):
		t1site=keyst1[k]
        	if sites[t2site]["downT1"].count(t1site) != 0:
			color="green"
		else:
			color="red"
		fileHandle.write("<td width=" + dw + " bgcolor=" + color + "></td>\n")
	fileHandle.write("</tr>\n")

fileHandle.write("</table>\n")
fileHandle.write("<p><br>\n")

fileHandle.write("</center></html></body>")
fileHandle.close()

os.chdir(pathoutHTML)
if os.path.isfile(slinkhtml): os.remove(slinkhtml)
os.symlink(os.path.split(filehtml)[1],slinkhtml)
