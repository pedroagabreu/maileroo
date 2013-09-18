#!/usr/bin/env python3

import sys
import smtplib
import time
import datetime
import re
import socket

from optparse import OptionParser

# hardcoded stuff
helo = 'maileroo'
gotosleep = 0

# function definition
def logthis(fp, msg):
	print(msg)
	fp.write(str(datetime.datetime.now()) + ' ')
	fp.write(msg + '\n')

# process options and set defaults
parser = OptionParser(usage="""Usage: %prog [option [arg]]""")
parser.add_option('-s', '--smtp-server',
    type='string', action='store', dest='server',
	default='localhost',
    help="""SMTP server""")
parser.add_option('-p', '--smtp-port',
    type='int', action='store', dest='port',
    help="""SMTP port""")
parser.add_option('-f', '--from-address',
    type='string', action='store', dest='sender',
    default='user@domain.tld',
    help="""envelope sender""")
parser.add_option('-r', '--rcpt-file',
    type='string', action='store', dest='rlist',
	default='recipients.txt',
    help="""file containing the envelope recipients""")
parser.add_option('-m', '--message-file',
    type='string', action='store', dest='eml',
	metavar='FILENAME',
	default='message.eml',
    help="""file containing the message to send""")
parser.add_option('-u', '--username',
    type='string', action='store', dest='user',
    help="""user name for SMTP AUTH""")
parser.add_option('-P', '--password',
    type='string', action='store', dest='password',
    help="""password for SMTP AUTH""")
parser.add_option('-t', '--starttls',
    action='store_true', dest='tls', default=False,
    help="""use STARTTLS""")
parser.add_option('-x', '--ssmtp',
    action='store_true', dest='ssmtp', default=False,
    help="""use SMTP over SSL""")
parser.add_option('-l', '--log-file',
    type='string', action='store', dest='logfile',
	default= 'mailer.log',
    help="""file to log to""")
opts, args = parser.parse_args()

# check if we want smtp auth
smtpauth = 0
if opts.user and opts.password:
	smtpauth = 1
elif opts.user and not opts.password:
	print('Error parsing options: Missing password for SMTP AUTH!')
	sys.exit(1)
elif not opts.user and opts.password:
	print('Error parsing options: Missing user name for SMTP AUTH!')
	sys.exit(1)

# are we using tls or ssmtp?
if opts.tls and opts.ssmtp:
	print('Error parsing options: STARTTLS or SSMTP, pick one!')
	sys.exit(1)

# handle default ports
if not opts.port:
	if opts.ssmtp:
		opts.port = 465
	else:
		opts.port = 25

# now start doing stuff!

# create our date header
d = datetime.datetime.utcnow()
dh = 'Date: ' + d.strftime("%a, %d %b %Y %H:%M:%S") + ' +0000 (UTC)\n'

# load message
msg = dh
f = open(opts.eml, 'r')
for line in f:
	if re.match("^Date: ", line):
		continue
	msg += line
f.close()

# load recipients
with open(opts.rlist, 'r') as r:
	rcptlist = r.readlines()

# go
log = open(opts.logfile, 'a')
logthis(log, 'Starting new cycle')

goodcount = 0
badcount = 0

for i in rcptlist:
	rcpt = i.strip()
	try:
		if opts.ssmtp:
			s = smtplib.SMTP_SSL(host=opts.server, port=opts.port)
		else:
			s = smtplib.SMTP(host=opts.server, port=opts.port)
		s.ehlo(name=helo)
		if opts.tls and not opts.ssmtp:
			s.starttls()
		if smtpauth == 1:
			s.login(opts.user, opts.password)
		s.sendmail(opts.sender, rcpt, msg)
		s.quit()
		goodcount = goodcount + 1
		logthis(log, 'Successfully sent to ' + rcpt)
	except (smtplib.SMTPException,
			socket.error) as e:
		badcount = badcount + 1
		logthis(log, 'Error sending to ' + rcpt + ': ' + str(e))
	if gotosleep != 0:
		time.sleep(gotosleep)

logthis(log, 'Finished cycle')
logthis(log, 'Total recipients: ' + str(len(rcptlist)))
logthis(log, 'Successful deliveries: ' + str(goodcount))
logthis(log, 'Unsuccessful deliveries: ' + str(badcount))
log.close()

sys.exit(0)

