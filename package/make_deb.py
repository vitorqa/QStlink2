#! /usr/bin/python

import sys,os, re, argparse, iso8601, shutil
from subprocess import call, check_output, Popen
from xml.etree import ElementTree as ET

releases = ["oneiric", "precise", "quantal", "raring"]

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--release', help='The Ubuntu release')
parser.add_argument('-s', '--source', help='Build signed source package', action="store_true")
parser.add_argument('-b', '--bin', help='Build local binary package', action="store_true")
parser.add_argument('-p', '--ppa', help='Send source package to PPA', action="store_true")

def makeChangelog(release, dest, rev):
	
	print "Building changelog file from svn logs"
	tmp_svn = check_output(["svn log -r HEAD:"+str(rev-10)+" .. --limit 10 --xml"], shell=True)

	xml_obj = ET.fromstring(tmp_svn)

	result = ""
	for entry in xml_obj.iter('logentry'):
		
		revmsg = entry.find('msg').text
		revdate = iso8601.parse_date(entry.find('date').text)
		revauthor = entry.find('author').text
		row = "qstlink2 (0.%s~%s) %s; urgency=medium" % (entry.attrib["revision"], release, release)
		row += "\n\n  * " + revmsg.replace("\n", "\n    ") + "\n"
		#row += " -- Fabien Poussin <%s>  %s \r\n\r\n" %(revauthor, revdate.strftime("%a, %d %b %Y %H:%M:%S %z"))
		row += " -- Fabien Poussin <fabien.poussin@gmail.com>  %s \n\n" %(revdate.strftime("%a, %d %b %Y %H:%M:%S %z")) ## Need to force address to sign with certificate
		result +=row

	out = open(dest+"/debian/changelog", "w")
	out.write(result)
	out.close()
	
def copySrc(dest, rev):
	
	check_output(["rm -rf "+dest], shell=True)
	print check_output(["mkdir -v "+dest], shell=True)

	#~ print check_output(["shopt -s extglob; cp -r ../!(package) "+dest+"/"], shell=True)
	cmd = "find .. -maxdepth 1 \! \( -name package -o -name *.pro.user* -o -name .. \) -exec cp -r '{}' "+dest+"/ ';'"
	check_output([cmd], shell=True)
	
	print check_output(["cd "+dest+"; echo "" | dh_make -n --single -e fabien.poussin@gmail.com -c gpl3"], shell=True)

	print check_output(["cp -v debian/* "+dest+"/debian/"], shell=True)
	check_output(["rm -f "+dest+"/debian/*.ex "+dest+"/debian/*.EX "+dest+"/debian/ex.*"], shell=True)
	
	out = open(dest+"/version", "w")
	out.write(str(rev))
	out.close()
	
def makeSrc(dest):
	print "Building Source package"
	print check_output(["cd "+dest+"; debuild -j4 -S -sa"], shell=True)
	
def makeBin(dest):
	print "Building binary package"
	print check_output(["cd "+dest+"; debuild -j4 -b -uc -us"], shell=True)

def sendSrc(ver):
	print check_output(["dput ppa:mobyfab/qstlink2 "+ver+"_source.changes"], shell=True)

if __name__ == "__main__":

	args = parser.parse_args()
	
	if not args.release:
		parser.print_help()

	if args.release not in releases:
		print "Invalid Ubuntu release, please chose among:", releases
		sys.exit(1)
		
	ver = check_output(["grep \"VERSION =\" ../STlinkV2.pro | awk '{ print $3 }' "], shell=True).replace('\n','')
	if not ver:
		print "Could not fetch last version"
		sys.exit(1)

	print "Last version:" , ver
	
	folder_name = 'qstlink2-'+str(ver)+'~'+args.release
	print "Package version:" , folder_name
	
	copySrc(folder_name, ver)
	#makeChangelog(args.release, folder_name, svn_rev)
	
	if args.source:
		makeSrc(folder_name)
		if args.ppa:
			sendSrc('qstlink2_'+str(ver)+'~'+args.release)
	else:
		makeBin(folder_name)
		
	print check_output(["rm -rf "+folder_name], shell=True)
	
