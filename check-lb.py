#!/usr/bin/env python

# Nagios plugin voor server-status pagina voor Apache 2.4.
# Dit checkt de status van hosts die gebruikt worden door mod_proxy_balancer.
#
# 2015-12-02     Cris van Pelt
#

import sys, re
from lxml import html, etree

# Het zoekt een tabel op met deze headers
HOST_HEADERS = [ "Sch", "Host", "Stat", "Route", "Redir", "F", "Set", "Acc", "Wr", "Rd" ]
NAGIOS_STATUS = { 'OK': 0, 'WARN': 1, 'CRIT': 2, 'UNKNOWN': 3 }

if len(sys.argv) < 2:
    print 'Gebruik: %s FRONT-PROXY' % sys.argv[0] 
    sys.exit(NAGIOS_STATUS['UNKNOWN'])

# wat nou sanity checking of error handling
doc = html.parse('http://%s/server-status' % sys.argv[1])
tables = doc.findall(".//table")

nagios_exitcode = 'UNKNOWN'
nagios_exitstrs = []

def new_status(old_status, new_status):
    if new_status == old_status:
        return old_status

    if old_status == 'UNKNOWN':
        return new_status

    if  NAGIOS_STATUS[new_status] > NAGIOS_STATUS[old_status]:
        return new_status

    return old_status

for t in tables:
    headers = []
    header_tags = t.findall(".//th")
    
    for h in header_tags:
        headers += [ h.text ]

    if headers == HOST_HEADERS:
        for row in t.findall(".//tr"):
            elems = row.findall(".//td")
            if elems:
                values = dict(zip(HOST_HEADERS, [ e.text for e in elems ]))

                # https://svn.apache.org/viewvc/httpd/httpd/trunk/modules/proxy/proxy_util.c?view=markup&pathrev=1715876
                if re.search('Ok', values['Stat']) == None:
                    nagios_exitcode = new_status(nagios_exitcode, 'WARN')
                if re.search('Ign', values['Stat']):
                    nagios_exitcode = new_status(nagios_exitcode, 'OK')
                if re.search('Drn', values['Stat']):
                    nagios_exitcode = new_status(nagios_exitcode, 'WARN')
                if re.search('Shut', values['Stat']):
                    nagios_exitcode = new_status(nagios_exitcode, 'WARN')
                if re.search('Dis', values['Stat']):
                    nagios_exitcode = new_status(nagios_exitcode, 'WARN')
                if re.search('Stop', values['Stat']):
                    nagios_exitcode = new_status(nagios_exitcode, 'CRIT')
                if re.search('Err', values['Stat']):
                    nagios_exitcode = new_status(nagios_exitcode, 'CRIT')
                if re.search('Init', values['Stat']):
                    nagios_exitcode = new_status(nagios_exitcode, 'OK')

                nagios_exitstrs += [ '(%s/%s: %s [F: %s, Acc: %s, Wr/Rd: %s/%s])' % \
                     (values['Host'], values['Sch'], values['Stat'], values['F'], values['Acc'], values['Wr'], values['Rd']) ]

print '%s - %s' % (nagios_exitcode, ' - '.join(nagios_exitstrs))
sys.exit(NAGIOS_STATUS[nagios_exitcode])
