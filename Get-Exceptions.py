#!/usr/bin/python

#Get-Exceptions.py "<SITE>" "<API token>"
#Get-Exceptions.py "https://somesite.sentinelone.net" "12345678901234567890123456789012345678901234567890123456789012345678901234567890"

import csv
import json
import asyncio
import aiohttp
import os
from xlsxwriter.workbook import Workbook
import requests
import sys
import contextlib
import io


# If you do not already have these modules, pip install them:
#pip install aiohttp
#pip install xlsxwriter
#pip install requests

if len(sys.argv) < 3 or len(sys.argv) > 4:
    print ('\r')
    print ('Invalid number of parameters. Call script with 2 or 3 parameters')
    print ('Param1 = hostname (Full URL of the management console i.e https://usea1-100.sentinelone.net)')
    print ('Param2 = APItoken (Your API Token. See the API Documentation for more information on how to generate it)')
    print ('Param3 (optional) = Proxy (Proxy details i.e http://username:password@proxy.com)' )
    print ()
    print ('For exmaple:')
    print ('    Get-Exceptions.py "<Host URL>" "<API Token>"')
    print ('    Get-Exceptions.py "https://somesite.sentinelone.net" "12345678901234567890123456789012345678901234567890123456789012345678901234567890"')
    print ()
    exit()
elif len(sys.argv) == 4:
    hostname = sys.argv[1]
    apitoken = sys.argv[2]
    proxy = sys.argv[3]
else:
    hostname = sys.argv[1]
    apitoken = sys.argv[2]
    proxy = ''

tokenscope = ''

firstrunpath = True
firstruncert = True
firstrunbrowser = True
firstrunfile = True
firstrunhash = True

countpath = 0
countcert = 0
countbrowser = 0
countfile = 0
counthash = 0

APIv = 'v2.1'

dictAccounts = {}
dictSites = {}
dictGroups = {}

def testLogin(hostname,apitoken,proxy):
    global APIv
    global tokenscope
    headers = {
        "Content-type": "application/json",
        "Authorization": "ApiToken " + apitoken }
    #r = requests.get(hostname + "/web/api/v2.1/system/info", headers=headers, proxies={'http' : proxy})
    r = requests.get(hostname + "/web/api/v2.1/user", headers=headers, proxies={'http' : proxy})
    if (r.status_code == 200):
        data = r.json()
        print("API 2.1 token validated")
        tokenscope = data['data']['scope']
        init()
    else:
        #r2 = requests.get(hostname + "/web/api/v2.0/system/info", headers=headers, proxies={'http' : proxy})
        r2 = requests.get(hostname + "/web/api/v2.0/user", headers=headers, proxies={'http' : proxy})
        if (r2.status_code == 200):
            data = r2.json()
            print("API 2.0 token validated")
            APIv = 'v2.0'
            tokenscope = data['data']['scope']
            init()
        else:
            print("Invalid API token or hostname. Exiting")
            exit()


def init():
    global APIv
    global tokenscope
    async def getAccounts(session, hostname, headers, proxy):
        params = '/web/api/' + APIv + '/accounts?limit=100' + '&countOnly=false&tenant=true'
        url = hostname + params
        while url:
            async with session.get(url, headers=headers, proxy=proxy) as response:
                if response.status != 200:
                    print('Status: ' + str(response.status) + ' Problem with the request. Exiting.')
                else:
                    data = await (response.json())
                    cursor = data['pagination']['nextCursor']
                    data = data['data']
                    if data:
                        for account in data:
                            #print('ACCOUNT: ' + account['id'] + ' | ' + account['name'])
                            dictAccounts[account['id']] = account['name']
                    if cursor:
                        paramsnext = '/web/api/' + APIv + '/accounts?limit=100' + '&cursor=' + cursor + '&countOnly=false&tenant=true'
                        url = hostname + paramsnext
                    else:
                        url = None   

    async def getSites(session, hostname, headers, proxy):
        params = '/web/api/' + APIv + '/sites?limit=100' + '&countOnly=false&tenant=true'
        url = hostname + params
        while url:
            async with session.get(url, headers=headers, proxy=proxy) as response:
                if response.status != 200:
                    print('Status: ' + str(response.status) + ' Problem with the request. Exiting.')
                else:
                    data = await (response.json())
                    cursor = data['pagination']['nextCursor']
                    data = data['data']
                    if data:
                        for site in data['sites']:
                            #print('SITE: ' + site['id'] + ' | ' + site['name'])
                            dictSites[site['id']] = site['name']
                    if cursor:
                        paramsnext = '/web/api/' + APIv + '/sites?limit=100' + '&cursor=' + cursor + '&countOnly=false&tenant=true'
                        url = hostname + paramsnext
                    else:
                        url = None

    async def getGroups(session, hostname, headers, proxy):
        params = '/web/api/' + APIv + '/groups?limit=100' + '&countOnly=false&tenant=true'
        url = hostname + params
        while url:
            async with session.get(url, headers=headers, proxy=proxy) as response:
                if response.status != 200:
                    print('Status: ' + str(response.status) + ' Problem with the request. Exiting.')
                else:
                    data = await (response.json())
                    cursor = data['pagination']['nextCursor']
                    data = data['data']
                    if data:
                        for group in data:
                            #print('GROUP: ' + group['id'] + ' | ' + group['name'] + ' | ' + group['siteId'])
                            dictGroups[group['id']] = group['name']
                    if cursor:
                        paramsnext = '/web/api/' + APIv + '/groups?limit=100' + '&cursor=' + cursor + '&countOnly=false&tenant=true'
                        url = hostname + paramsnext
                    else:
                        url = None

    async def exceptions_to_csv(querytype, session, hostname, headers, proxy, scope, exparam):
        params = '/web/api/' + APIv + '/exclusions?limit=1000&type=' + querytype + '&countOnly=false'
        url = hostname + params + exparam
        global firstrunpath
        global firstruncert
        global firstrunbrowser
        global firstrunfile
        global firstrunhash
        global countpath
        global countcert
        global countbrowser
        global countfile
        global counthash
        while url:
            async with session.get(url, headers=headers, proxy=proxy) as response:
                if response.status != 200:
                    print('Status: ' + str(response.status) + ' Problem with the request. Exiting.')
                    print('Details of above: ' + url)
                else:
                    data = await (response.json())
                    cursor = data['pagination']['nextCursor']
                    data = data['data']
                    if data:
                        for data in data:
                            if querytype == 'path':
                                f = csv.writer(open("exceptions_path.csv", "a+", newline='', encoding='utf-8'))
                                if firstrunpath:
                                    tmp = []
                                    tmp.append('Scope')
                                    for key, value in data.items():
                                        tmp.append(key)
                                    f.writerow(tmp)
                                    firstrunpath = False
                                tmp = []
                                tmp.append(scope)
                                for key, value in data.items():
                                    tmp.append(value)
                                f.writerow(tmp)
                                countpath += 1

                            elif querytype == 'certificate':
                                f = csv.writer(open("exceptions_certificate.csv", "a+", newline='', encoding='utf-8'))
                                if firstruncert:
                                    tmp = []
                                    tmp.append('Scope')
                                    for key, value in data.items():
                                        tmp.append(key)
                                    f.writerow(tmp)
                                    firstruncert = False
                                tmp = []
                                tmp.append(scope)
                                for key, value in data.items():
                                    tmp.append(value)
                                f.writerow(tmp)
                                countcert += 1

                            elif querytype == 'browser':
                                f = csv.writer(open("exceptions_browser.csv", "a+", newline='', encoding='utf-8'))
                                if firstrunbrowser:
                                    tmp = []
                                    tmp.append('Scope')
                                    for key, value in data.items():
                                        tmp.append(key)
                                    f.writerow(tmp)
                                    firstrunbrowser = False
                                tmp = []
                                tmp.append(scope)
                                for key, value in data.items():
                                    tmp.append(value)
                                f.writerow(tmp)
                                countbrowser += 1

                            elif querytype == 'file_type':
                                f = csv.writer(open("exceptions_file_type.csv", "a+", newline='', encoding='utf-8'))
                                if firstrunfile:
                                    tmp = []
                                    tmp.append('Scope')
                                    for key, value in data.items():
                                        tmp.append(key)
                                    f.writerow(tmp)
                                    firstrunfile = False
                                tmp = []
                                tmp.append(scope)
                                for key, value in data.items():
                                    tmp.append(value)
                                f.writerow(tmp)
                                countfile += 1

                            elif querytype == 'white_hash':
                                f = csv.writer(open("exceptions_white_hash.csv", "a+", newline='', encoding='utf-8'))
                                if firstrunhash:
                                    tmp = []
                                    tmp.append('Scope')
                                    for key, value in data.items():
                                        tmp.append(key)
                                    f.writerow(tmp)
                                    firstrunhash = False
                                tmp = []
                                tmp.append(scope)
                                for key, value in data.items():
                                    tmp.append(value)
                                f.writerow(tmp)
                                counthash += 1

                    if cursor:
                        paramsnext = '/web/api/' + APIv + '/exclusions?limit=1000&type=' + querytype + '&countOnly=false' + '&cursor=' + cursor
                        url = hostname + paramsnext + exparam
                    else:
                        url = None

    async def run(hostname, apitoken, proxy, scope):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-type": "application/json",
                "Authorization": "ApiToken " + apitoken}
            if scope == 'Account':
                exparam = '&accountIds='
                l = len(dictAccounts.items())
                printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                i = 0
                for key, value in dictAccounts.items():
                    printProgressBar(i + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                    typepath = asyncio.create_task(exceptions_to_csv('path', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typecert = asyncio.create_task(exceptions_to_csv('certificate', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typebrowser = asyncio.create_task(exceptions_to_csv('browser', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typefile_type = asyncio.create_task(exceptions_to_csv('file_type', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typewhite_hash = asyncio.create_task(exceptions_to_csv('white_hash', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    await typefile_type
                    await typebrowser
                    await typecert
                    await typepath
                    await typewhite_hash
                    i = i + 1
            elif scope == 'Site':
                exparam = '&siteIds='
                l = len(dictSites.items())
                printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                i = 0
                for key, value in dictSites.items():
                    printProgressBar(i + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                    typepath = asyncio.create_task(exceptions_to_csv('path', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typecert = asyncio.create_task(exceptions_to_csv('certificate', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typebrowser = asyncio.create_task(exceptions_to_csv('browser', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typefile_type = asyncio.create_task(exceptions_to_csv('file_type', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typewhite_hash = asyncio.create_task(exceptions_to_csv('white_hash', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    await typefile_type
                    await typebrowser
                    await typecert
                    await typepath
                    await typewhite_hash
                    i = i + 1
            elif scope == 'Group':
                exparam = '&groupIds='
                l = len(dictGroups.items())
                printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                i = 0
                for key, value in dictGroups.items():
                    printProgressBar(i + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
                    typepath = asyncio.create_task(exceptions_to_csv('path', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typecert = asyncio.create_task(exceptions_to_csv('certificate', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typebrowser = asyncio.create_task(exceptions_to_csv('browser', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typefile_type = asyncio.create_task(exceptions_to_csv('file_type', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    typewhite_hash = asyncio.create_task(exceptions_to_csv('white_hash', session, hostname, headers, proxy, scope + '|' + value + ' | ' + key, exparam + key))
                    await typefile_type
                    await typebrowser
                    await typecert
                    await typepath
                    await typewhite_hash
                    i = i + 1
            elif scope == 'Global':
                exparam = ''
                key = ''
                typepath = asyncio.create_task(exceptions_to_csv('path', session, hostname, headers, proxy, scope, exparam + key))
                typecert = asyncio.create_task(exceptions_to_csv('certificate', session, hostname, headers, proxy, scope, exparam + key))
                typebrowser = asyncio.create_task(exceptions_to_csv('browser', session, hostname, headers, proxy, scope, exparam + key))
                typefile_type = asyncio.create_task(exceptions_to_csv('file_type', session, hostname, headers, proxy, scope, exparam + key))
                typewhite_hash = asyncio.create_task(exceptions_to_csv('white_hash', session, hostname, headers, proxy, scope, exparam + key))
                await typefile_type
                await typebrowser
                await typecert
                await typepath
                await typewhite_hash

    async def runAccounts(hostname, apitoken, proxy):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-type": "application/json",
                "Authorization": "ApiToken " + apitoken}
            accounts = asyncio.create_task(getAccounts(session, hostname, headers, proxy))
            await accounts

    async def runSites(hostname, apitoken, proxy):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-type": "application/json",
                "Authorization": "ApiToken " + apitoken}
            sites = asyncio.create_task(getSites(session, hostname, headers, proxy))
            await sites

    async def runGroups(hostname, apitoken, proxy):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-type": "application/json",
                "Authorization": "ApiToken " + apitoken}
            groups = asyncio.create_task(getGroups(session, hostname, headers, proxy))
            await groups

    if tokenscope == 'account':
        print('Automatically limiting scope to match token scope: account!')
    if tokenscope == 'site':
        print('Automatically limiting scope to match token scope: site!')


    if tokenscope != 'site':
        print('Getting account/site/group structure for ' + hostname)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(runAccounts(hostname, apitoken, proxy))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(runSites(hostname, apitoken, proxy))


    loop = asyncio.get_event_loop()
    loop.run_until_complete(runGroups(hostname, apitoken, proxy))
    print('Finished getting account/site/group structure!')
    print('Accounts found: ' + str(len(dictAccounts)) + ' | ' + 'Sites found: ' + str(len(dictSites)) + ' | ' + 'Groups found: ' + str(len(dictGroups)))
    
    
    if tokenscope != 'account' and tokenscope != 'site':
        print('Getting GLOBAL scope exceptions...')
        scope = "Global"
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(hostname, apitoken, proxy, scope))
    
    if tokenscope != 'site':
        print('Getting ACCOUNT scope exceptions...')
        scope = "Account"
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(hostname, apitoken, proxy, scope))


    print('Getting SITE scope exceptions...')
    scope = "Site"
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(hostname, apitoken, proxy, scope))

    print('Getting GROUP scope exceptions...')
    scope = "Group"
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(hostname, apitoken, proxy, scope))

    # print results
    print('Total exceptions by type:')
    print('    PATH: ' + str(countpath))
    print('    CERT: ' + str(countcert))
    print('    BROWSER: ' + str(countbrowser))
    print('    FILE: ' + str(countfile))
    print('    HASH: ' + str(counthash))
    print('Creating XLSX...')

    filename = "Exceptions"
    workbook = Workbook(filename + '.xlsx')
    csvs = ["exceptions_path.csv", "exceptions_certificate.csv", "exceptions_browser.csv", "exceptions_file_type.csv", "exceptions_white_hash.csv"]
    for csvfile in csvs:
        worksheet = workbook.add_worksheet(csvfile.split(".")[0])
        if os.path.isfile(csvfile):
            with open(csvfile, 'r', encoding="utf8") as f:
                reader = csv.reader(f)
                for r, row in enumerate(reader):
                    for c, col in enumerate(row):
                        worksheet.write(r, c, col)
        if os.path.exists(csvfile):
            os.remove(csvfile)
    workbook.close()
    done = "Done! Created the file " + filename + ".xlsx"
    print(done)
    exit()

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

testLogin(hostname, apitoken, proxy)
