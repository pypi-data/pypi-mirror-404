# Style Guide for python code
# https://peps.python.org/pep-0008/
# https://google.github.io/styleguide/pyguide.html

############ IMPORT THIS FILE USING BELOW COMMAND #############

### update github submodule (libraries) before pushing the latest update to github
# git submodule add https://github.com/optimus/libraries
# git submodule update --remote

# git submodule update

# git submodule update --init
# git add {submodule}

# update submodules/libraries to latest version for each submodule
# git submodule update --remote --init --recursive

### add any filename.py to .gitignore and remove it from cache using below command
# git rm -r --cached .
# git add .
# git commit -m "untrack files contained in the .gitignore file"

#########################################################
# Local testing on 
# C:\Users\Admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\optimuslib
# /home/pi/.local/lib/python3.11/site-packages/optimuslib/optimuslib.py
# ~/.local/lib/python3.11/site-packages/optimuslib/optimuslib.py

### import code
# import optimuslib
# from optimuslib.optimuslib import log
# optimuslib = optimuslib.optimuslib

### import libraries to file using import sys 
# import sys
# import os
# try:
    # sys.path.append(r'C:/Users/username/Desktop/Python Projects/python-automation-scripts/libraries')
    # print('Fetching libraries from default libraries folder')
    # import optimuslib
    # from optimuslib import log
    # import githuboptimuslib
# except ModuleNotFoundError:
    # print('Libraries not found in default folder. Fetching in the subfolder..')
    # # subfolder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'libraries'))
    # # sys.path.append(subfolder_path)
    # from libraries import optimuslib
    # from libraries import githuboptimuslib
    # from libraries.optimuslib import log
#########################################################

# import optimuslib
# from optimuslib import log

### delete logs file before start of any script
# optimuslib.writeOutput('logs.txt','')

### calculate script execution duration
# scriptStartTime = optimuslib.getTime()
# log.info('Script Duration: %s', str(optimuslib.getTime()-scriptStartTime))

#########################################################
### kill python processes
# taskkill /IM "py.exe" /F & taskkill /IM "python.exe" /F

#########################################################

### import file from parent directory in python
# import sys
# sys.path.insert(0, '..')
# import filename
    ## import file from parent-parent directory
        # sys.path.insert(0, '../..')

#########################################################

### publish package in python
# https://python-poetry.org/docs/#installing-with-the-official-installer
# open cmd as an admin mode
# for first petry authentication, get the library token from https://pypi.org/manage/account/token/ & enter 
    # > poetry config pypi-token.pypi {token}
# poetry version patch && poetry build && poetry publish

# install latest package in system
# python -m pip install --upgrade optimuslib

# https://python-poetry.org/docs/managing-dependencies/
# manually update the dependency in the pyproject.toml file

### install the latest library version
# python -m pip install --no-cache-dir --upgrade optimuslib
# OR
# python -m pip install --no-cache-dir  --upgrade -r requirements.txt



############## LOG INFO IN TERMINAL AND log.txt FILE ###################
import logging

# Creating logger
# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG, filename='logs.txt', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# logging.basicConfig(level=logging.DEBUG, filename='logs.txt', format='%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s', datefmt='%d-%b-%y %H:%M:%S')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
# log.setLevel(logging.INFO)

# # Handler - 1
file = logging.FileHandler('optimuslibLogs.log', 'a', 'utf-8')
# fileformat = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(filename)s - %(module)s:%(funcName)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fileformat = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file.setLevel(logging.DEBUG)
# file.setLevel(logging.INFO)
file.setFormatter(fileformat)

# # Handler - 2
stream = logging.StreamHandler()
# streamformat = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
streamformat = fileformat
stream.setLevel(logging.DEBUG)
# stream.setLevel(logging.INFO)
stream.setFormatter(streamformat)

# # Adding all handlers to the logs
log.addHandler(file)
log.addHandler(stream)

def loglib(data):
    log.info(data)
    log.info('%d %s','1', 'a')
    log.info('%d %s' % ('1', 'a'))
    log.info('%d %s' % '1' % 'a')

###### CHECK OS AND PERFORM COMMAND ACCORDINGLY
# get OS version
import platform
def checkOS():
    osType = platform.system()
    osVersion = platform.platform()
    oshostname = platform.node()
    # log.info('osType: %s, osVersion: %s, oshostname: %s', osType, osVersion, oshostname)
    log.info(f'osType: {osType}, osVersion: {osVersion}, oshostname: {oshostname}')
    return osType, osVersion, oshostname


osType, osVersion, oshostname = checkOS()
if osType == 'Windows':
    proxyhost = 'http://127.0.0.1:8080'
    proxyhost = None
    log.setLevel(logging.INFO)    
    file.setLevel(logging.INFO)
    stream.setLevel(logging.INFO)
    # log.setLevel(logging.DEBUG)
    # file.setLevel(logging.DEBUG)
    # stream.setLevel(logging.DEBUG)
else:
    proxyhost = None
    # log.setLevel(logging.INFO)    
    # file.setLevel(logging.INFO)
    # stream.setLevel(logging.INFO)
    log.setLevel(logging.DEBUG)
    file.setLevel(logging.DEBUG)
    stream.setLevel(logging.DEBUG)


############## RUN AN OS COMMAND AND RETURN OUTPUT AND ERRORS ###################
import subprocess, sys
def runCommand(command, outputFile=r'tempREQD.txt'):
    # to run all commands properly
    # to run all tools from Tools folder path
    log.info('[+] Command: %s',command)
    commandUpdated=[]
    # currentDirUpdated=[]
    currentDir = os.getcwd()
    for line in command:
        if ' ' in line:
            line = '"'+line+'"'
        commandUpdated.append(line)
    # if ' ' in currentDir:
        # currentDir = '"'+currentDir+'"'
    # currentDirUpdated.append(currentDir)
    # log.info('[+] CLI Command: %s\\%s',' '.join(currentDirUpdated),' '.join(commandUpdated))
    log.info('[+] CLI Command: "%s\\%s',currentDir,' '.join(commandUpdated))
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p.communicate()
    # if out is not None:
        # out = out.decode()
    # if err is not None:
        # err = err.decode()
    log.debug('out: %s', str(out))
    log.debug('err: %s', str(err))
    f = open(outputFile, 'wb')
    f.write(out)
    f.close  
    return out,err
    
############## TRAVERSE A DIRECTORY AND RETURN FILENAMES AND FULL PATH OF FILES ###################
import os

def filetype(filepath):
    # need to add file.exe to path if it is not there to run filetype command
    # currentDir = os.getcwd()
    # command = 'set PATH=%PATH%;file.exe'
    # runCommand(command, tempoutputfile)

    command = ['file', filepath]
    # command = [r'Tools\file\file.exe', filepath]
    # tempoutputfile = r'tempREQD.txt'
    # tempoutputfile = r'C:\Users\NanwaniS\AppData\Local\Temp\tempREQD.txt'
    out,err=runCommand(command)
    filetypelist = ['executable', 'installer']
    # if any(value in filetypelist for word in str(out)):
    if 'executable' in str(out):
        return 'binary file'
    elif 'document' in str(out):
        return 'program database file'
    elif 'program database' in str(out):
        return 'program database file'
    elif 'Windows setup INFormation' in str(out):
        return 'Windows setup INFormation file'
    elif 'data' in str(out):
        return 'data file'
    else:
        return 'unknown file type'

def traverse(path):
    
    filenames = []
    filetypevalues = []
    fileextensions = []
    filepaths = []
    i=0
    for path, subdirs, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(path, filename)
            # filetypevalue = filetype(filepath)
            filetypevalue = ''
            fileextension = os.path.splitext(filename)[1]
            i+=1
            log.info('\n\t[%d/%d]FilePath: %s', i, len(files), filepath)
            log.info('\n\t\tFileName: %s\n\t\tFileType: %s\n\t\tFileExtn: %s', filename, filetypevalue, fileextension)
            # log.info('\t\tFileName: %s\n\t\tFileType: %s\n\t\tFileExtn: %s\n\t\tFilePath: %s', filename, filetypevalue, fileextension, filepath)
            filenames.append(filename)
            filepaths.append(filepath)
            filetypevalues.append(filetypevalue)
            fileextensions.append(fileextension)

    return filenames,filetypevalues,fileextensions,filepaths
 
# '''
############## REQUESTS LIBRARY ###################
'''
import time, sys, requests
# import sys
import requests
requests.packages.urllib3.disable_warnings()

# For Futures - Parallel Processing of Requests
from requests_futures.sessions import FuturesSession
# futuresworkercount = 1
# futuresworkercount = 30 ### good to have
# futuresworkercount = 50
futuresworkercount = 100
# futuresworkercount = 300
s=FuturesSession(max_workers=futuresworkercount)

# s = requests.Session()
# proxyhost = 'http://127.0.0.1:8088'
# proxyhost = 'http://127.0.0.1:8888'
# s.proxies = { 'http': proxyhost, 'https': proxyhost}

# would retry if requests failed with given status code


# class LogRetry(Retry):
# """
# Adding extra logs before making a retry request
# """
# def __init__(self, *args, **kwargs):
# logger.info(f'<add your logs here>')
   # super().__init__(*args, **kwargs)

   # retries = LogRetry(<your args>)

from requests.adapters import HTTPAdapter, Retry
from http.client import HTTPConnection
from http.client import HTTPSConnection
from socket import gethostbyname, gaierror

responseCodeForceList = [429,500,502,503,504]
# responseCodeForceList = [403,429,500,502,503,504]

retryCount = 0
def Retry(total=10,backoff_factor=1,status_forcelist=responseCodeForceList,raise_on_status=False):
    global retryCount
    # logging.basicConfig(level=logging.DEBUG)
    log.info('Retrying...')
    retryCount += 1
    if retryCount>total:
        return False
    return Retry(total=total,backoff_factor=backoff_factor,status_forcelist=status_forcelist,raise_on_status=raise_on_status)
    
# retries = Retry(total,backoff_factor,status_forcelist,raise_on_status)
# retries = doRetry
retries = 10

adapterHTTPS = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1, pool_block=True, max_retries=retries)
adapterHTTPS.pool_class = HTTPSConnection

s.mount('https://', adapterHTTPS)


# s.mount('http://', requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1, pool_block=True, max_retries=retries, poolclass=HTTPConnection))

s.mount('http://', HTTPAdapter(max_retries=retries))
# would retry if requests failed with given status code

# def header_size(headers):
    # return sum(len(key) + len(value) + 4 for key, value in headers.items()) + 2


totalRequestsSent=0
# from retrying import retry
# @retry(stop_max_attempt_number=10)
# def sendRequest(method,requestUrl,cookies=None,headers=None,data=None,json=None,timeout=None,allow_redirects=True):
# import pythonproxy
def sendRequest(method, requestUrl, cookies=None, headers=None, data=None, json=None, params=None, files=None, timeout=None, proxyhost=None, validResponseCodes=False, allow_redirects=True, verify=False):
    global totalRequestsSent
    
    
    # proxyhost = 'http://127.0.0.1:8888'
    if proxyhost:
        log.debug('Using proxy: %s', proxyhost)
        s.proxies = { 'http': proxyhost, 'https': proxyhost}
        # pythonproxy.parseProxyHostAndRun(proxyhost)

'''
    # if not validResponseCodes:
    #     # validResponseCodes = [200,201,302,307,401,400,403,404,405,406]
    #     validResponseCodes = [200,201,302,307,401,400,404,405,406]
'''
    totalRequestsSent += 1
    
    # log.info('[%d/%d] Sending Request: %s',totalRequestsSent,len(requestUrl),requestUrl)
    log.debug(f'\t[{totalRequestsSent}] Sending Request: {requestUrl}')
    # log.info('\t[%d] Sending Request: %s',totalRequestsSent,requestUrl)

    # log.debug('Sending request - \n\t Request URL: %s %s\n\tRequest Headers: %s\n\t Request Data: %s\n\tRequest Json Data: %s', method, requestUrl, headers, data, json)
    try:
        if method=='get' or method=='GET':
            response=s.get(requestUrl, cookies=cookies, headers=headers, data=data, json=json, params=params, files=files, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
        if method=='post' or method=='POST':
            response=s.post(requestUrl, cookies=cookies, headers=headers, data=data, json=json, params=params, files=files, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
        if method=='patch' or method=='PATCH':
            response=s.patch(requestUrl, cookies=cookies, headers=headers, data=data, json=json, params=params, files=files, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
        if method=='delete' or method=='DELETE':
            response=s.delete(requestUrl, cookies=cookies, headers=headers, data=data, json=json, params=params, files=files, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
        if method=='put' or method=='PUT':
            response=s.put(requestUrl, cookies=cookies, headers=headers, data=data, json=json, params=params, files=files, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
        # # log.debug('Recieved Response - Response Status Code: %d\n\tResponse Headers: %s\n\tResponse Data: %s', response.result().status_code, str(response.result().headers), str(response.result().text))
        log.debug(f'Recieved Response - Response Status Code: {response.result().status_code}\n\tResponse Data: {str(response.result().text)}')
        return response
    # except requests.exceptions.ConnectionError as e:
    # except (MalformedRequest, InternalError, StatusUnknown, ConnectionError, ConnectionResetError, http.client.RemoteDisconnected, RemoteDisconnected, ProtocolError, HTTPException, socket.gaierror) as e:
    except requests.exceptions.ConnectionError as e:
        log.error(f'ConnectionError occured - {e}')
        log.error('Sleeping for 15 secods before next request')
        time.sleep(15)
        sendRequest(method, requestUrl, cookies, headers, data, json, params, files, timeout, proxyhost, validResponseCodes, allow_redirects, verify)
        # sys.exit()
    except requests.exceptions.ConnectionResetError as e:
        log.error(f'Exception occured - {e}')
        log.error('Is your internet connection Stable?')
        sys.exit()
    except requests.exceptions.RequestException as e:
        log.error(f"Request failed: {e}")
    except ConnectionRefusedError as e:
        log.error(f'Exception occured - {e}')
        log.error('Is proxy set and server not running?')
        sys.exit()

    # responseFutures = response.result()
    # responseStatusCode = responseFutures.status_code
    # responseHeaders = str(responseFutures.headers)
    # responseData = str(responseFutures.text)
    # log.debug('Recieved Response - Response Status Code: %d\n\tResponse Headers: %s\n\tResponse Data: %s', responseStatusCode, responseHeaders, responseData)
    # log.debug('Recieved Response - Response Status Code: %d\n\tResponse Headers: %s\n\tResponse Data: %s', responseFutures.result().status_code, str(responseFutures.result().headers), str(responseFutures.result().text))
    # log.debug('Recieved Response - %s', responseFutures.result())
    # totalRequestsSent+=1
    # log.info('Request '+str(totalRequestsSent)+' sent.')
    
    # calculating request and response size
    # request_line_size = len(s.request.method) + len(s.request.path_url) + 12
    # request_size = request_line_size + header_size(s.request.headers) + int(s.request.headers.get('content-length', 0))
    # response_line_size = len(s.responseFutures.reason) + 15
    # response_size = response_line_size + header_size(s.headers) + int(s.headers.get('content-length', 0))
    # total_size = request_size + response_size
     # log.info('\t\tResponse Code - %s', responseStatusCode)
    return response

    # if responseStatusCode in validResponseCodes:
        # return response
    # else:
        # return False

def sendBulkRequests(method, requestUrlList, cookies=None, headers=None, data=None, json=None, timeout=None, allow_redirects=True, proxyhost=None):
    global totalRequestUrl, totalBulkRequestsSent
    totalBulkRequestsSent=0
    totalRequestUrl = len(requestUrlList)
    futureResponseList = []
    for requestUrl in requestUrlList:
        totalBulkRequestsSent+=1
        # log.info('Sending Bulk Request...[%d/%d]', totalBulkRequestsSent, totalRequestUrl)
        log.debug(f'Sending Bulk Request...[{totalBulkRequestsSent}/{totalRequestUrl}]')
        futureResponse = sendRequest(method, requestUrl, cookies=cookies, headers=headers, data=data, json=json, timeout=timeout, allow_redirects=allow_redirects, proxyhost=proxyhost)
        futureResponseList.append(futureResponse)
    return futureResponseList

################# REQUESTS MODULE DEBUGGING
'''
########## CORRECTED BY CHATGPT
import time, sys, requests, logging
from requests.adapters import HTTPAdapter, Retry
from requests_futures.sessions import FuturesSession
requests.packages.urllib3.disable_warnings()

# Setup logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Response codes to force retry on
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

# Max retry attempts
MAX_RETRIES = 5

# Futures Session for parallel async requests
futuresworkercount = 100
s = FuturesSession(max_workers=futuresworkercount)

# Configure retry strategy
retry_strategy = Retry(
    total=MAX_RETRIES,
    backoff_factor=1,  # Exponential backoff: 1,2,4,8...
    status_forcelist=RETRY_STATUS_CODES,
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    raise_on_status=False
)

adapter = HTTPAdapter(max_retries=retry_strategy)
s.mount("https://", adapter)
s.mount("http://", adapter)

totalRequestsSent = 0


def _handle_429(response, attempt):
    """Handles 429 Too Many Requests with delay/retry."""
    if response.status_code != 429:
        return False

    retry_after = response.headers.get("Retry-After")
    if retry_after:
        delay = int(retry_after)
    else:
        delay = min(2 ** attempt, 60)  # exponential backoff, max 60s

    log.warning(f"429 Too Many Requests - sleeping {delay}s before retry...")
    time.sleep(delay)
    return True


def sendRequest(method, requestUrl, cookies=None, headers=None, data=None, json=None, params=None, files=None, timeout=None, proxyhost=None, allow_redirects=True, verify=False):
    """Send HTTP request with retry + 429 handling."""
    global totalRequestsSent
    totalRequestsSent += 1

    if proxyhost:
        log.debug('Using proxy: %s', proxyhost)
        s.proxies = {'http': proxyhost, 'https': proxyhost}

    log.debug(f'[{totalRequestsSent}] Sending Request: {requestUrl}')

    method = method.lower()
    attempts = 0

    while attempts < MAX_RETRIES:
        try:
            if method == "get":
                response = s.get(requestUrl, cookies=cookies, headers=headers, params=params, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
            elif method == "post":
                response = s.post(requestUrl, cookies=cookies, headers=headers, data=data, json=json, files=files, params=params, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
            elif method == "patch":
                response = s.patch(requestUrl, cookies=cookies, headers=headers, data=data, json=json, files=files, params=params, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
            elif method == "delete":
                response = s.delete(requestUrl, cookies=cookies, headers=headers, data=data, json=json, files=files, params=params, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
            elif method == "put":
                response = s.put(requestUrl, cookies=cookies, headers=headers, data=data, json=json, files=files, params=params, timeout=timeout, allow_redirects=allow_redirects, verify=verify)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            result = response.result()

            # Handle 429 manually
            if result.status_code == 429:
                if _handle_429(result, attempts):
                    attempts += 1
                    continue

            log.debug(f"Response [{result.status_code}] - {result.text}...")
            # log.debug(f"Response [{result.status_code}] - {result.text[:200]}...")
            return response

        except requests.exceptions.ConnectionError as e:
            log.error(f'ConnectionError: {e} - retrying in 5s...')
            time.sleep(5)
        except requests.exceptions.RequestException as e:
            log.error(f"Request failed: {e}")
            break

        attempts += 1

    log.error(f"Request failed after {MAX_RETRIES} attempts: {requestUrl}")
    return None


def sendBulkRequests(method, requestUrlList, **kwargs):
    """Send multiple requests in bulk."""
    futureResponseList = []
    for idx, requestUrl in enumerate(requestUrlList, 1):
        log.debug(f'Sending Bulk Request...[{idx}/{len(requestUrlList)}]')
        futureResponse = sendRequest(method, requestUrl, **kwargs)
        futureResponseList.append(futureResponse)
    return futureResponseList
########### CORRECTED BY CHATGPT
'''
# GET ALL COOKIES IN SESSION
print(s.cookies.get_dict())

headers = {'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36'}

enctoken = s.cookies.get('enctoken')
headers.update({'Authorization': 'enctoken '+enctoken})
headers.update({'X-Csrftoken': s.cookies.get('public_token')})


# print password as ****
import urllib.parse
password = urllib.parse.quote(password)

'''

############# Cookie & Session Saving and fetching
# sessionFile = r'session'
import pickle

# SAVE SESSION
def saveRequestsSession(sessionFile):
    with open(sessionFile, 'wb') as f:
        pickle.dump(s.cookies, f)

# RESTORE SESSION
def restoreRequestsSession(sessionFile):
    with open(sessionFile, 'rb') as f:
        s.cookies.update(pickle.load(f))
    return(s.cookies)

def getCookies():
    # return session.cookies.get_dict()
    return s.cookies.get_dict()

def clearCookies():
    s.cookies.clear()

# cookies = optimuslib.restoreRequestsSession(sessionFile)
# headers.update({'Authorization': 'enctoken '+cookies.get('enctoken')})
# headers.update({'X-Csrftoken': cookies.get('public_token')})


########## FILES OPERATION
# APPEND ANYTHING TO FILE
def appendOutput(filename,output):
    f = open(filename, 'a')
    f.write(output+'\n')
    f.close()

# Creates a new file
def createFile(filename):
    with open(filename, 'w') as fp:
        pass

# WRITE ANYTHING TO FILE
def writeOutput(filename,output,end='\n'):
    # log.info('Writing file: `%s`', filename)
    f = open(filename, 'w')
    # f.write(output+'\n')
    f.write(str(output)+end)
    f.close()

# DELETE EVERYTHING FROM FILE
def deleteFileData(filename,output):
    # log.info('Writing file: `%s`', filename)
    f = open(filename, 'w')
    # f.write(output+'\n')
    f.write(str(output))
    f.close()

# READ TO FILE
def readFile(filename):
    # log.info('Reading file: `%s`', filename)
    try:
        f = open(filename, 'r')
        output=f.read()
        f.close()
    except FileNotFoundError:
        output = ''
    return output

# READ TO FILE
def readSingleDataFromFile(filename):
    # log.info('Reading file: `%s`', filename)
    output = readFile(filename)
    output=output.replace('\n','')
    return output

# READ linebyline in FILE
def readLinesFromFile(filename):
    lines = []
    # log.info('Reading file: `%s`', filename)
    with open(filename, 'r') as file:
        # Read each line in the file
        for line in file:
            # Print each line
            lines.append(line.strip())
    return lines

# download file from web
def downloadFile(downloadUrl, directoryPath, filename, extension):
    # file=requests.get(downloadUrl)
    file=requests.get(downloadUrl)
    if file.status_code==200:
        with open(directoryPath+"/"+filename+"."+extension, 'wb') as f:
            f.write(file.content)
        return True
    else:
        return False
'''
def downloadFile(downloadUrl, directoryPath, filename, extension, cookies=None, headers=None, data=None, json=None, timeout=None, proxyhost=None, validResponseCodes=False, allow_redirects=True, verify=False):
    # file=requests.get(downloadUrl)
    file=sendRequest('get', downloadUrl, cookies=cookies, headers=headers, data=data, json=json, timeout=timeout, proxyhost=proxyhost, validResponseCodes=validResponseCodes, allow_redirects=allow_redirects, verify=verify)
    if file.result().status_code==200:
        with open(directoryPath+"/"+filename+"."+extension, 'wb') as f:
            f.write(file.result().content)
        return True
    else:
        return False
'''
# move file from one dir to another
import shutil
def moveFile(file_path, destination):
    # file to move
    # file_path = r"C:\example\test.txt"

    # destination folder
    # destination = r"C:\example\backup"

    # move file
    shutil.move(file_path, destination)

def renameFile(current_file_name, new_file_name):
    os.rename(current_file_name, new_file_name)



########### TELEGRAM BOT NOTIFICATION - BOT DETAILS ##############
def getTelegramBotInfo(botToken):
    log.info('Fetching BOT Information')
    url = 'https://api.telegram.org/bot'+botToken+'/getMe'
    response = sendRequest('get', url, proxyhost=proxyhost)
    responseJson = response.result().json()
    if responseJson['ok']==True:
        if responseJson['result']:
            id = responseJson['result']['id']
            is_bot = responseJson['result']['is_bot']
            first_name = responseJson['result']['first_name']
            username = responseJson['result']['username']
            can_join_groups = responseJson['result']['can_join_groups']
            can_read_all_group_messages = responseJson['result']['can_read_all_group_messages']
            supports_inline_queries = responseJson['result']['supports_inline_queries']
            getVarInfo('id',id)
            getVarInfo('is_bot',is_bot)
            getVarInfo('first_name',first_name)
            getVarInfo('username',username)
            getVarInfo('can_join_groups',can_join_groups)
            getVarInfo('can_read_all_group_messages',can_read_all_group_messages)
            getVarInfo('supports_inline_queries',supports_inline_queries)
            return True
        else:
            return False
    else:
        getVarInfo('responseJson',responseJson)
        return False

########### TELEGRAM BOT NOTIFICATION - FETCH RECEIVED MESSAGES ##############
def getTelegramBotUpdates(botToken, update_id, type='user'):
    log.info('Checking new messages...')
    url = 'https://api.telegram.org/bot'+botToken+'/getUpdates?offset='+str(update_id+1)
    response = sendRequest('get', url, proxyhost=proxyhost)
    try:
        responseJson = response.result().json()
        if responseJson['ok']==True:
            if responseJson['result']:
                for result in responseJson['result']:
                    update_id = result['update_id']
                    if type=='user':
                        log.info('Reading Telegram Messages to Bot, Type: User')
                        try:
                            messageData = result['message']
                        except:
                             messageData = result['edited_message']
                        message_id = messageData['message_id']
                        fromId = messageData['from']['id']
                        fromFirstName = messageData['from']['first_name']
                        try:
                            fromUsername = messageData['from']['username']
                        except:
                            fromUsername = ''
                        chatId = messageData['chat']['id']
                        date = messageData['date']
                        text = messageData['text']
                        getVarInfo('update_id',update_id)
                        getVarInfo('message_id',message_id)
                        getVarInfo('fromId',fromId)
                        getVarInfo('fromFirstName',fromFirstName)
                        getVarInfo('fromUsername',fromUsername)
                        getVarInfo('chatId',chatId)
                        getVarInfo('date',date)
                        getVarInfo('text',text)
                        # return update_id, message_id, fromId, fromFirstName, fromUsername, chatId, date, text
                        # log.info('update_id, text, chatId, fromFirstName, fromUsername', update_id, text, chatId, fromFirstName, fromUsername)
                        return update_id, text, chatId, fromFirstName, fromUsername
                    if type=='group':
                        log.info('Reading Telegram Messages to Bot, Type: Group')
                        # message_id = result['message']['message_id']
                        date = result['channel_post']['date']
                        text = result['channel_post']['text']
                        getVarInfo('update_id',update_id)
                        getVarInfo('date',date)
                        getVarInfo('text',text)
                        # log.info('%s, %s', update_id, text)
                        return update_id, text

            else:
                log.info('\tNo Data in Result')
                return 0, False, False, False, False
        else:
            getVarInfo('responseJson',responseJson)
            return 0, False, False, False, False
    except (KeyError, TypeError, ValueError) as e:
        log.info('Exception Occured 202502042248: %s', e)
        getVarInfo('responseJson',responseJson)
        return 0, False, False, False, False
    

def clearTelegramBotUpdates(botToken, update_id=0):
    log.info('Checking new messages...')
    url = 'https://api.telegram.org/bot'+botToken+'/getUpdates?offset='+str(update_id+1)
    response = sendRequest('get', url, proxyhost=proxyhost)
    try:
        responseJson = response.result().json()
        if responseJson['ok']==True:
            if responseJson['result']:
                update_id = responseJson['result'][0]['update_id']
                clearTelegramBotUpdates(botToken, update_id)
                return True
        else:
            getVarInfo('responseJson',responseJson)
            return False
    except (KeyError, TypeError, ValueError) as e:
        log.info('Exception Occured: %s', e)
        getVarInfo('responseJson',responseJson)
        return False

def fetchOTPTelegram(botToken, otpFetchWaitTime):
    # 2FA - autofetch via telegram
    log.info('Fetching 2FA request with TOTP')
    twofa_value = 0
    retryCount = 0
    while retryCount<60:
        log.info('Sleeping for %d seconds', otpFetchWaitTime)
        time.sleep(otpFetchWaitTime)
        try:
            update_id, text = getTelegramBotUpdates(botToken, -1, 'group')
            log.info('update_id: %s, text: %s', update_id, text)
            twofa_value = text[-6:]
            break
        except ValueError as e:
            retryCount += 1
            log.exception('Retrying %d since ValueError: %s',retryCount, e)
        # print(update_id, text)
    return twofa_value
########### TELEGRAM BOT NOTIFICATION - SEND ##############

# function to validate if length is > 4096
def sendTelegramBotNotification(botToken,chatId,message, parse_mode=''):
    msgs = [message[i:i + 4096] for i in range(0, len(message), 4096)]
    for text in msgs:
         sendTelegramBotNotificationMain(botToken,chatId,text, parse_mode)
            
def sendTelegramBotNotificationMain(botToken,chatId,message, parse_mode=''):
    log.info('Sending Message via BOT')
    
    
    '''
    url = 'https://api.telegram.org/bot'+botToken+'/sendMessage?chat_id='+chatId+'&text='+message
    data = ''
    '''
    
    url = 'https://api.telegram.org/bot'+botToken+'/sendMessage'
    # data = {'chat_id': chatId, 'text': message, 'parse_mode': parse_mode}
    data = {'chat_id': chatId, 'text': message, 'parse_mode': parse_mode, 'link_preview_options': {'is_disabled': True}}
    # data = {'chat_id': chatId, 'text': message, 'parse_mode': parse_mode, 'disable_web_page_preview': True}
    
    # proxyhost = locals()
    # proxyhost= 'http://127.0.0.1:8080'
    response = sendRequest('post', url, json=data, proxyhost=proxyhost)
    responseJson = response.result().json()
    if responseJson['ok']==True:
        return True
    else:
        log.info('Telegram Bot Message Send Failure Error Description: %s', responseJson['description'])
        getVarInfo('responseJson',responseJson)
        return False
        
# send telegram Photo
def sendTelegramBotPhoto(botToken,chatId,filePath):
    photoFile = open(filePath, 'rb')
    url = 'https://api.telegram.org/bot'+botToken+'/sendPhoto'
    params = {'chat_id': chatId}
    files = {'photo': photoFile}
    response = sendRequest('post', url, params=params, files=files, proxyhost=proxyhost)
    responseJson = response.result().json()
    if responseJson['ok']==True:
        return True
    else:
        log.info('Telegram Bot Message Send Failure Error Description: %s', responseJson['description'])
        getVarInfo('responseJson',responseJson)
        return False

# send telegram document
def sendTelegramBotDocument(botToken,chatId,filePath):
    documentFile = open(filePath, 'rb')
    url = 'https://api.telegram.org/bot'+botToken+'/sendDocument'
    params = {'chat_id': chatId}
    files = {'document': documentFile}
    response = sendRequest('post', url, params=params, files=files, proxyhost=proxyhost)
    responseJson = response.result().json()
    if responseJson['ok']==True:
        return True
    else:
        log.info('Telegram Bot Message Send Failure Error Description: %s', responseJson['description'])
        getVarInfo('responseJson',responseJson)
        return False
   
# if(optimuslib.sendTelegramNotification(botToken, chatId,output)):
    # print('Telegram Notification Sent.')

########## TWILIO SMS ALERT ###############
'''
from twilio.rest import Client
def sendTwilioSMS(account_sid,auth_token,messagingServiceSid,toNumber,message):
    client = Client(account_sid, auth_token)
    msg = client.messages.create(toNumber, messaging_service_sid=messagingServiceSid, body=message)
    print(msg.sid)
'''
############## CREATING DICT ##############
# import sys 
# sys.path.append(r'C:\Users\username\Desktop\Python Projects\python-automation-scripts\libraries')
# import optimuslib

# path = r'C:\Users\username\Desktop\package-files-from-github-search'
# filenames,filepaths = optimuslib.traverse(path)

# finalDict={}
# singleEntry = {}
# allEntry = []
# for filename,filepath in zip(filenames,filepaths):
    # singleEntry['filename']=filename
    # singleEntry['filepath']=filepath
    # OR
    # singleEntry = {
        # 'filename': filename,
        # 'filepath': filepath
        # }
    # allEntry.append(singleEntry.copy())
# finalDict['data']=allEntry
# import json
# finalDict = json.dumps(finalDict)
# print(finalDict)

########### SAVE JSON DATA TO A FILE ###############
import json

def jsonDumpToFile(filename,dictionary):
    json_object = json.dumps(dictionary, indent=4)
    try:
        with open(filename, "w") as outfile:
            outfile.write(json_object)
    except FileNotFoundError:
        createFile(filename)
        with open(filename, "w") as outfile:
            outfile.write(json_object)
        
    # log.info('Json dict dumped to file `%s`',filename)

######### READ JSON DATA FROM A FILE ###########
import json
def jsonLoadsFromFile(filename):
    dictionary = json.load(open(filename))
    # log.info('Json dict loaded from file `%s`',filename)
    return dictionary

###################################################
def copyToClipboard(string):
    import pyperclip
    if pyperclip.copy(string):
        log.info('String copied to clipboard!')
        return True
    else:
        return False
    
##########################################

def getVarInfo(string, variable):
    # try:
        # log.info('len(%s): %d', string, len(variable))
    # except TypeError as e:
        # log.info('Typeerror: %s', e)
    log.debug('Name: %s, Value: %s, Type: %s', str(string), str(variable), type(variable))
    
def getListInfo(string, variable):
    try:
        log.info('len(%s): %d', string, len(variable))
    except TypeError as e:
        log.info('Typeerror: %s', e)
    log.info('%s Data: %s', string, variable)

def removeValueFromList(string, list):
    ### if string is substring of values in list
    listNew = []
    for data in list:
        if string.lower() in data.lower():
            pass
        else:
            listNew.append(data)
    # OR
    ### if string is whole value in list
    list.remove(string)
    return listNew

#######################################

def getTime():
    from datetime import datetime
    return datetime.now()

def getEpochTime():
    import time
    epoch_time=round(time.time()*1000)
    return epoch_time
    
def getDate():
    from datetime import datetime
    date = datetime.today().strftime('%Y-%m-%d')
    return date

def epochToTime(epochString):
    from time import strftime, localtime
    return strftime('%Y-%m-%d %H:%M:%S', localtime(epochString))


def incrementDateByDays(date, days, format='%Y%m%d'):
    from datetime import datetime, timedelta
    # date = '20230630'
    # updatedDate = (datetime.strptime(date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
    updatedDate = (datetime.strptime(date, format) + timedelta(days)).strftime(format)
    # log.info('Date %s incremented by %d : %s', date, days, updatedDate)
    return updatedDate

def decrementDateByDays(date, days, format='%Y%m%d'):
    from datetime import datetime, timedelta
    # date = '20230630'
    # updatedDate = (datetime.strptime(date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
    updatedDate = (datetime.strptime(date, format) - timedelta(days)).strftime(format)
    # log.info('Date %s incremented by %d : %s', date, days, updatedDate)
    return updatedDate

# updatedDate = decrementDateByDays('2023-12-30', 1, '%Y-%m-%d')
# print('updatedDate: '+updatedDate)
#####################################


# SELENIUM
# https://github.com/0p71mu5/PersonalLaptop-PentestingScripts/blob/478c29c83bd4ff6d1dcc49b6ebbc33e8206ce490/Python_Scripts/kahoot.it.py

def click_function(to_do,x_arg):
    log.info('Clicking '+to_do)
    # driver.find_element_by_xpath(xpathValue).click()
    page = wait.until(EC.presence_of_element_located((By.XPATH, x_arg)))
    driver.execute_script("window.stop();")
    try:
        page.click()
    except ElementNotVisibleException as e:
        log.info("ElementNotVisibleException occured. "+str(e))
        raise ElementNotVisibleException
    except TimeoutException as e:
        log.info("TimeoutException occured. "+str(e))
        raise TimeoutException
    log.info(' '+to_do+' Clicked')

def send_keys_function(to_do,x_arg,data):
    log.info('Entering '+to_do)
    page = wait.until(EC.presence_of_element_located((By.XPATH, x_arg)))
    page.send_keys(data + Keys.ENTER)
    log.info(' '+to_do+' Entered')

def check_text_function(text,x_arg):
    log.info('Checking text '+text)
    page = wait.until(EC.presence_of_element_located((By.XPATH, x_arg+'//*[contains(text(),'+text+')]')))
    page.send_keys(data + Keys.ENTER)
    log.info(' '+text+' text Checked')

def select_file_from_computer(image_path):
    # Opens File Explore window
    log.info("Opening file explorer")
    sleep(wait_time)
    autoit.win_active("Open")
    autoit.control_set_text("Open", "Edit1", image_path)
    autoit.control_send("Open", "Edit1", "{ENTER}")
    log.info(f"Sleeping for {wait_time} seconds...", )
    sleep(wait_time)
    
# click_function('Sign In',"//a[@data-nav-ref='nav_ya_signin']",)
# send_keys_function('Email', '//input[@type="email"]', config.u)
# send_keys_function('password', '//input[@type="password"]', config.p)

############################
import os
def createFolder(foldername):
    # try:
    #     if os.mkdir(foldername):
    #         log.info(f"Folder Created: {foldername}")
    # except FileExistsError:
    #     log.info(f"{foldername} folder already exists")
    if not os.path.exists(foldername):
        os.makedirs(foldername)

############################
import re
def removeKeyword(string, keyword):
    string = re.sub(keyword, '', string)
    return string


###########################
import csv
import json

def json_to_csv(json_file, csv_file):
    with open(json_file, 'r') as f:
        json_obj = json.load(f)
    """Convert a JSON object to a CSV file"""
    # Open the CSV file for writing
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # Write the header row
        header = []
        for item in json_obj:
            header.extend(get_keys(item, parent_key=None))
        writer.writerow(header)
        getVarInfo('header', header)
        
        # Write the data rows
        for item in json_obj:
            row = []
            get_values(item, row, parent_key=None)
            writer.writerow(row)
            getVarInfo('row', row)

def get_keys(item, parent_key=None):
    """Return a list of keys from a nested dictionary or list of dictionaries"""
    getVarInfo('item', item)
    keys = []
    if isinstance(item, dict):
        for key in item.keys():
            value = item[key]
            new_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, (dict, list)):
                keys.extend(get_keys(value, new_key))
            else:
                keys.append(new_key)
    elif isinstance(item, list):
        for i, value in enumerate(item):
            new_key = f"{parent_key}[{i}]" if parent_key else str(i)
            if isinstance(value, (dict, list)):
                keys.extend(get_keys(value, new_key))
            else:
                keys.append(new_key)
                
    getVarInfo('keys', keys)
    return keys

def get_values(item, row, parent_key=None):
    """Append values from a nested dictionary or list of dictionaries to a list"""
    if isinstance(item, dict):
        for key in item.keys():
            value = item[key]
            new_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, (dict, list)):
                get_values(value, row, new_key)
            else:
                row.append(value)
    elif isinstance(item, list):
        for i, value in enumerate(item):
            new_key = f"{parent_key}[{i}]" if parent_key else str(i)
            if isinstance(value, (dict, list)):
                get_values(value, row, new_key)
            else:
                row.append(value)

# Example usage
# json_to_csv(json_file, "data.csv")


def dataToCSV(indexString, arrayData, outputFile):
    import pandas as pd
    # df = pd.DataFrame(vulnerability_list, columns=['srcPath','packageName','packageVersion','packageEcosystem','summary','details','id','severity','references'])
    # indexString = ['srcPath','packageName','packageVersion','packageEcosystem','summary','details','id','severity','references']
    if indexString:
        df = pd.DataFrame(arrayData, columns=indexString)
    else:
        df = pd.DataFrame(arrayData)
    # Save the DataFrame to a CSV file
    df.to_csv(outputFile, index=False)
    return True

import pandas as pd
import os

def append_array_to_csv(file_path, data, headers=None):
    df = pd.DataFrame([data])
    if headers is not None:
        df.columns = headers
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        df.to_csv(file_path, mode='w', index=False, header=headers is not None)
    else:
        df.to_csv(file_path, mode='a', index=False, header=False)

# def write_array_to_csv(file_path, data, headers=None):
#     df = pd.DataFrame([data])
#     if headers is not None:
#         df.columns = headers
#     if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
#         df.to_csv(file_path, mode='w', index=False, header=headers is not None)
#     else:
#         df.to_csv(file_path, mode='w', index=False, header=False)
def write_array_to_csv(file_path, data, headers=None):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def read_csv_to_arrays(file_path):
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        return []
    df = pd.read_csv(file_path, header=None)
    return df.values.tolist()

def delete_array_from_csv(file_path, array_to_delete):
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        return
    df = pd.read_csv(file_path, header=None)
    df = df[~df.apply(tuple, axis=1).isin([tuple(array_to_delete)])]
    df.to_csv(file_path, index=False, header=False)

def clear_csv(file_path, headers=None):
    df = pd.DataFrame()
    if headers is not None:
        df = pd.DataFrame(columns=headers)
    df.to_csv(file_path, index=False, header=headers is not None)


# find md5hash of a file
import hashlib
def md5(file_path):
    """Return the MD5 hash of a file."""
    with open(file_path, "rb") as f:
        md5_hash = hashlib.md5()
        while chunk := f.read(8192):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

    # print(md5(file_path))


# def folderDifference(folder1, folder2, outputfile):
    # filenames,filetypevalues,fileextensions,filepaths = traverse(path)
    


# Refs: https://note.nkmk.me/en/python-str-remove-strip/
from base64 import b64encode
def basicAuth(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'
    
# set env variable (need to run as admin)
def setEnvVar(envVariableName, envVariableValue):
    # setx OCAuthToken "BearerToken" /M
    command = ['setx', envVariableName, envVariableValue, '/M']
    runCommand(command)


# convert tabulate table data to image_path
# ref https://stackoverflow.com/questions/29760402/converting-a-txt-file-to-an-image-in-python
from math import ceil

from PIL import (
    Image,
    ImageFont,
    ImageDraw,
)

PIL_GRAYSCALE = 'L'
PIL_WIDTH_INDEX = 0
PIL_HEIGHT_INDEX = 1
COMMON_MONO_FONT_FILENAMES = [
    # 'DejaVuSansMono.ttf',  # Linux
    # 'Consolas Mono.ttf',   # MacOS, I think
    # 'Consola.ttf',         # Windows, I think
]

def textfile_to_image(text_file_path, image_output_path):
    """Convert text file to a grayscale image.

    arguments:
    text_file_path - the content of this file will be converted to an image
    font_path - path to a font file (for example impact.ttf)
    """
    # parse the file into lines stripped of whitespace on the right side
    with open(text_file_path) as f:
        lines = tuple(line.rstrip() for line in f.readlines())

    # choose a font (you can see more detail in the linked library on github)
    font = None
    large_font = 20  # get better resolution with larger size
    for font_filename in COMMON_MONO_FONT_FILENAMES:
        try:
            font = ImageFont.truetype(font_filename, size=large_font)
            log.error(f'Using font "{font_filename}".')
            break
        except IOError:
            log.error(f'Could not load font "{font_filename}".')
    if font is None:
        font = ImageFont.load_default()
        log.error('Using default font.')

    # make a sufficiently sized background image based on the combination of font and lines
    font_points_to_pixels = lambda pt: round(pt * 96.0 / 72)
    margin_pixels = 20

    # height of the background image
    tallest_line = max(lines, key=lambda line: font.getsize(line)[PIL_HEIGHT_INDEX])
    max_line_height = font_points_to_pixels(font.getsize(tallest_line)[PIL_HEIGHT_INDEX])
    realistic_line_height = max_line_height * 0.8  # apparently it measures a lot of space above visible content
    image_height = int(ceil(realistic_line_height * len(lines) + 2 * margin_pixels))

    # width of the background image
    widest_line = max(lines, key=lambda s: font.getsize(s)[PIL_WIDTH_INDEX])
    max_line_width = font_points_to_pixels(font.getsize(widest_line)[PIL_WIDTH_INDEX])
    image_width = int(ceil(max_line_width + (2 * margin_pixels)))

    # draw the background
    background_color = 255  # white
    image = Image.new(PIL_GRAYSCALE, (image_width, image_height), color=background_color)
    draw = ImageDraw.Draw(image)

    # draw each line of text
    font_color = 0  # black
    horizontal_position = margin_pixels
    for i, line in enumerate(lines):
        vertical_position = int(round(margin_pixels + (i * realistic_line_height)))
        draw.text((horizontal_position, vertical_position), line, fill=font_color, font=font)

    # image.show()
    image.save(image_output_path)
    return True


############ CHECK STRING FORMAT
### check only number:
def stringIsNumeric(text):
    return text.isnumeric()

def stringIsAlpha(text):
    return text.isalpha()

def stringIsAlphaNumeric(text):
    return text.isalnum()

def stringIsAscii(text):
    return text.isascii()

########## log message in console and send telegram notification
def printAndSend(botToken,chatId,output):
    print(output)
    log.info(output)
    sendTelegramBotNotification(botToken,chatId,output)

def logAndSend(botToken,chatId,output):
    log.info(output)
    # sendTelegramBotNotification(botToken,chatId,output)
    sendDiscordBotNotification(botToken,chatId,output)

########## format a number as per indian currency 
def formatCurrencyIndian(number):
    """
    Format a number as per Indian currency format with commas.
    Example: 12345678.90 -> '1,23,45,678.90'
    """
    number_str = "{:.2f}".format(number)
    integer_part, decimal_part = number_str.split(".")
    # Handle negative numbers
    sign = ""
    if integer_part.startswith('-'):
        sign = "-"
        integer_part = integer_part[1:]

    # First group (last 3 digits)
    if len(integer_part) > 3:
        last3 = integer_part[-3:]
        rest = integer_part[:-3]
        # Group rest in pairs
        pairs = []
        while len(rest) > 2:
            pairs.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            pairs.insert(0, rest)
        formatted = sign + ",".join(pairs + [last3]) + "." + decimal_part
    else:
        formatted = sign + integer_part + "." + decimal_part
    return formatted

########### DISCORD BOT NOTIFICATION - BOT DETAILS ##############
# def getDiscordBotInfo(botToken):
#     log.info('Fetching BOT Information')
#     url = 'https://api.telegram.org/bot'+botToken+'/getMe'
#     response = sendRequest('get', url, proxyhost=proxyhost)
#     responseJson = response.result().json()
#     if responseJson['ok']==True:
#         if responseJson['result']:
#             id = responseJson['result']['id']
#             is_bot = responseJson['result']['is_bot']
#             first_name = responseJson['result']['first_name']
#             username = responseJson['result']['username']
#             can_join_groups = responseJson['result']['can_join_groups']
#             can_read_all_group_messages = responseJson['result']['can_read_all_group_messages']
#             supports_inline_queries = responseJson['result']['supports_inline_queries']
#             getVarInfo('id',id)
#             getVarInfo('is_bot',is_bot)
#             getVarInfo('first_name',first_name)
#             getVarInfo('username',username)
#             getVarInfo('can_join_groups',can_join_groups)
#             getVarInfo('can_read_all_group_messages',can_read_all_group_messages)
#             getVarInfo('supports_inline_queries',supports_inline_queries)
#             return True
#         else:
#             return False
#     else:
#         getVarInfo('responseJson',responseJson)
#         return False

########### DISCORD BOT NOTIFICATION - FETCH RECEIVED MESSAGES ##############
def getDiscordBotUpdates(botToken, channelId, messageCount=1):
    log.info('Checking new messages...')
    url = 'https://discord.com/api/v10/channels/'+channelId+'/messages?limit='+str(messageCount)
    headers = {'Authorization': 'Bot ' + botToken}
    response = sendRequest('get', url, headers=headers, proxyhost=proxyhost)
    # response = sendRequest('get', url, proxyhost=proxyhost)
    # try:
    if response.result().status_code == 200:
        responseJson = response.result().json()
        for msg in responseJson:
            author = msg['author']
            content = msg['content']
            timestamp = msg['timestamp']
            id = msg['id']
            username = author['username']
            # print(f"[{author['username']}] {content}")

            getVarInfo('id',id)
            getVarInfo('timestamp',timestamp)
            getVarInfo('username',username)
            getVarInfo('content',content)

            return id, timestamp, username, content
    #         else:
    #             log.info('\tNo Data in Result')
    #             return 0, False, False, False, False
    #     else:
    #         getVarInfo('responseJson',responseJson)
    #         return 0, False, False, False, False
    # except (KeyError, TypeError, ValueError) as e:
    #     log.info('Exception Occured 202502042248: %s', e)
    #     getVarInfo('responseJson',responseJson)
    #     return 0, False, False, False, False
    

# def clearDiscordBotUpdates(botToken, update_id=0):
#     log.info('Checking new messages...')
#     url = 'https://api.telegram.org/bot'+botToken+'/getUpdates?offset='+str(update_id+1)
#     response = sendRequest('get', url, proxyhost=proxyhost)
#     try:
#         responseJson = response.result().json()
#         if responseJson['ok']==True:
#             if responseJson['result']:
#                 update_id = responseJson['result'][0]['update_id']
#                 clearTelegramBotUpdates(botToken, update_id)
#                 return True
#         else:
#             getVarInfo('responseJson',responseJson)
#             return False
#     except (KeyError, TypeError, ValueError) as e:
#         log.info('Exception Occured: %s', e)
#         getVarInfo('responseJson',responseJson)
#         return False

def fetchOTPDiscord(botToken, otpFetchWaitTime, otpChannelId):
    # 2FA - autofetch via telegram
    log.info('Fetching 2FA request with TOTP')
    twofa_value = 0
    retryCount = 0
    while retryCount<60:
        log.info('Sleeping for %d seconds', otpFetchWaitTime)
        time.sleep(otpFetchWaitTime)
        try:
            id, timestamp, username, content = getDiscordBotUpdates(botToken, otpChannelId, messageCount=1)
            log.info('update_id: %s, text: %s', id, content)
            twofa_value = content[-6:]
            twofa_value = twofa_value.replace("-","")
            twofa_value = twofa_value.replace("S","")
            twofa_value = twofa_value.replace("T","")
            getVarInfo('twofa_value',twofa_value)
            break
        except ValueError as e:
            retryCount += 1
            log.exception('Retrying %d since ValueError: %s',retryCount, e)
        # print(update_id, text)
    return twofa_value

########### DISCORD BOT NOTIFICATION - SEND ##############

# function to validate if length is > 4096
def sendDiscordBotNotification(botToken,channelId,message, parse_mode=''):
    msgs = [message[i:i + 2000] for i in range(0, len(message), 4096)]
    for text in msgs:
         sendDiscordBotNotificationMain(botToken,channelId,text, parse_mode)
            
def sendDiscordBotNotificationMain(botToken,channelId,message, parse_mode=''):
    log.info('Sending Message via BOT')
    
    url = f'https://discord.com/api/v10/channels/{channelId}/messages'
    data = {'content': message}
    headers = {'Authorization': 'Bot ' + botToken}
    # proxyhost= 'http://127.0.0.1:8080'
    response = sendRequest('post', url, headers=headers, json=data, proxyhost=proxyhost)
    if response.result().status_code == 200:
        return True
    else:
        responseJson = response.result().json()
        try:
            errorCode = responseJson['errors']['content']['_errors'][0]['code']
            errorMessage = responseJson['errors']['content']['_errors'][0]['message']
            log.info(f'Discord Bot Message Send Failure Error Description: {errorCode} - {errorMessage}')
        except:
            errorMessage = responseJson['message']
            log.info(f'Discord Bot Message Send Failure Error Description: {errorMessage}')
        getVarInfo('responseJson',responseJson)
        return False
        
# send telegram document
def sendDiscordBotFile(botToken,channelId,filePath):
    documentFile = open(filePath, 'rb')
    url = f'https://discord.com/api/v10/channels/{channelId}/messages'
    files = {'file': documentFile}
    headers = {'Authorization': 'Bot ' + botToken}
    response = sendRequest('post', url, headers=headers, files=files, proxyhost=proxyhost)
    # response = sendRequest('post', url, params=params, files=files, proxyhost=proxyhost)
    responseJson = response.result().json()
    if response.result().status_code == 200:
        if responseJson['type']==0:
            return True
    else:
        log.info('Discord Bot Message Send Failure Error Description: %s', responseJson['description'])
        getVarInfo('responseJson',responseJson)
        return False


# format table for discord message
def buildUnicodeTable(headers, rows):
    col_widths = [len(h) for h in headers]

    for row in rows:
        for idx, cell in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(cell)))

    top_border = '┌' + '┬'.join('─' * (w + 2) for w in col_widths) + '┐'
    header_row = '│ ' + ' │ '.join(headers[i].ljust(col_widths[i]) for i in range(len(headers))) + ' │'
    mid_border = '├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤'

    data_rows = []
    for row in rows:
        data_row = '│ ' + ' │ '.join(str(row[i]).ljust(col_widths[i]) for i in range(len(row))) + ' │'
        data_rows.append(data_row)

    bottom_border = '└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘'

    table = [top_border, header_row, mid_border] + data_rows + [bottom_border]
    return '\n'.join(table)
# if(optimuslib.sendTelegramNotification(botToken, chatId,output)):
    # print('Telegram Notification Sent.')


# getDiscordBotUpdates(botToken, channelId, messageCount)
# fetchOTPDiscord(botToken, otpFetchWaitTime, otpChannelId)
# sendDiscordBotNotification(botToken,channelId,message)
# sendDiscordBotFile(botToken,channelId,filePath)


########################## FETCH OTP FROM GMAIL VIA APP PASSWORD ##########################
import imaplib
import email
import time
import re
import quopri
import threading
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone


def extract_clean_text(msg):
    """Extract readable text from HTML email"""
    text = ""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            raw = part.get_payload(decode=True)
            decoded = quopri.decodestring(raw).decode(errors="ignore")
            soup = BeautifulSoup(decoded, "html.parser")
            text += soup.get_text(" ")
    return text


def is_recent(msg):
    """Check if email was received within MAX_AGE_SECONDS"""
    date_hdr = msg.get("Date")
    if not date_hdr:
        return False

    try:
        msg_time = parsedate_to_datetime(date_hdr)
        if msg_time.tzinfo is None:
            msg_time = msg_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age = (now - msg_time).total_seconds()
        return 0 <= age <= MAX_AGE_SECONDS
    except Exception:
        return False


def input_with_timeout(prompt, timeout):
    """Get user input with timeout"""
    result = {"value": None}

    def ask():
        try:
            result["value"] = input(prompt)
        except EOFError:
            pass

    t = threading.Thread(target=ask, daemon=True)
    t.start()
    t.join(timeout)

    return result["value"]


# ============== IMAP OTP ==================

def poll_for_otp(EMAIL, APP_PASSWORD, SENDER, SUBJECT, POLL_INTERVAL, POLL_TIMEOUT, MAX_AGE_SECONDS):
    """Poll Gmail IMAP for OTP email"""
    IMAP_SERVER = "imap.gmail.com"
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, APP_PASSWORD)

    start = time.time()

    while time.time() - start < POLL_TIMEOUT:
        # 🔑 Gmail IMAP requires re-select to refresh UNSEEN
        mail.select("inbox", readonly=False)

        status, messages = mail.search(
            None,
            f'(UNSEEN FROM "{SENDER}" SUBJECT "{SUBJECT}")'
        )

        ids = messages[0].split()

        for eid in ids:
            _, data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            if not is_recent(msg):
                continue

            body = extract_clean_text(msg)
            match = re.search(r"OTP[^0-9]*(\d{6})", body, re.IGNORECASE)

            if match:
                # mark email as read
                mail.store(eid, "+FLAGS", "\\Seen")
                mail.logout()
                return match.group(1)

        log.info("Waiting for OTP...")
        time.sleep(POLL_INTERVAL)

    mail.logout()
    raise TimeoutError("Auto OTP fetch timed out")


def get_gmail_otp(EMAIL, APP_PASSWORD, SENDER, SUBJECT,POLL_INTERVAL,POLL_TIMEOUT,MAX_AGE_SECONDS,MANUAL_INPUT_TIMEOUT):
    """Get OTP automatically or fall back to manual input"""
    try:
        otp = poll_for_otp(EMAIL, APP_PASSWORD, SENDER, SUBJECT, POLL_INTERVAL, POLL_TIMEOUT, MAX_AGE_SECONDS)
        log.info("OTP received automatically:", otp)
        return otp

    except TimeoutError:
        log.info("⚠️ Auto OTP fetch timed out.")
        log.info(f"Please enter OTP manually (waiting {MANUAL_INPUT_TIMEOUT} seconds)...")

        manual_otp = input_with_timeout("Enter OTP: ", MANUAL_INPUT_TIMEOUT)

        if manual_otp and manual_otp.strip().isdigit():
            return manual_otp.strip()

        raise TimeoutError("No OTP entered within manual input window")

# ================== RUN ===================


################################################
log.info('[+] Optimuslib Import Sucessfull.')

