#!/usr/bin/env python

import boto3
import BaseHTTPServer
import ConfigParser
import os
import urllib2
import json
import hashlib
from pprint import pprint

from os import curdir,sep
import sys

client = boto3.client('sts', aws_access_key_id="",aws_secret_access_key="")

class AuthenticationError(Exception):
    pass

class AuthHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
    def do_GET(s):
        global auth_code
        global KEEP_RUNNING
        """Respond to a GET request."""
        if ('code' in s.path):
            KEEP_RUNNING = False
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()
            s.wfile.write("<html><head><title>Authorization successful</title></head>")
            s.wfile.write("<body><p>Successfully authorized</p>")
            auth_code = s.path
            s.wfile.write("</body></html>")
        else:
            f = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'index.html'))
            s.send_response(200)
            s.send_header('Content-type', 'text/html')
            s.end_headers()
            s.wfile.write(f.read())
            f.close()

server_class = BaseHTTPServer.HTTPServer
httpd = server_class(('', 8000), AuthHandler)
KEEP_RUNNING = True

config_file = 'google_aws.cfg'
config = ConfigParser.SafeConfigParser({
            'client_id':''
            })
config.read( [ config_file, os.path.expanduser('~/.google_aws.cfg') ])
if not config.has_section('google'):
    config.add_section('google')

client_id = config.get('google','client_id')



def get_credentials():

    state = hashlib.sha256(os.urandom(1024)).hexdigest()

    auth_url = "https://accounts.google.com/o/oauth2/auth?scope=email&state={1}&redirect_uri=http%3A%2F%2Flocalhost:8000%2F&response_type=id_token%20token&client_id={0}".format(client_id,state)

    sys.stderr.write(auth_url+"\n")


    def keep_running():
        global KEEP_RUNNING
        return KEEP_RUNNING
    try:
        while keep_running():
            httpd.handle_request()
    except KeyboardInterrupt:
        pass

    httpd.server_close()

    code = auth_code
    tokens = code.replace('/code?','').split('&')
    token = None
    access_token = None
    for a_token in tokens:
        token_bits = a_token.split('=')
        if token_bits[0] == 'access_token':
            access_token = token_bits[1]
        if token_bits[0] == 'id_token':
            token = token_bits[1]
        if token_bits[0] == 'state':
            if (token_bits[1] != state):
                raise AuthenticationError('State mismatch expecting {0}, is {1}'.format(state,token_bits[1]))

    req = urllib2.Request("https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={0}".format(access_token))
    response = urllib2.urlopen(req)
    user_info = json.load(response)
    if user_info['audience'] != client_id:
        raise AuthenticationError('Mismatching client ids')


    response = client.assume_role_with_web_identity(
        RoleArn=config.get('aws','role'),
        RoleSessionName=user_info['user_id'],
        WebIdentityToken=token,
        DurationSeconds=900
    )

    return(response['Credentials'])

if __name__ == '__main__':
    credentials = get_credentials()
    sys.stdout.write('AWS_ACCESS_KEY_ID={0} AWS_SECRET_ACCESS_KEY={1} AWS_SESSION_TOKEN={2} AWS_SECURITY_TOKEN={2}\n'.format(credentials['AccessKeyId'],credentials['SecretAccessKey'],credentials['SessionToken']))
