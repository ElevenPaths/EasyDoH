#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import json
import os
import re
import struct
import subprocess
import sys
import ConfigParser

VERSION = "1.1.3"

# Templates for configuration parameters
trr_mode = 'network.trr.mode'
trr_uri = 'network.trr.uri'
trr_custom_uri = 'network.trr.custom_uri'

# Read a message from stdin and decode it.
def get_message():
    if sys.version_info.major == 3:
        raw_length = sys.stdin.buffer.read(4)
        if len(raw_length) == 0:
            sys.exit(0)
        message_length = struct.unpack('@I', raw_length)[0]
        message = sys.stdin.buffer.read(message_length).decode('utf-8')

    else:
        raw_length = sys.stdin.read(4)
        if len(raw_length) == 0:
            sys.exit(0)
        message_length = struct.unpack('@I', raw_length)[0]        
        message = sys.stdin.read(message_length)

    return json.loads(message)

# Encode a message for transmission, given its content.
def encode_message(messageContent):
    encodedContent = json.dumps(messageContent)
    if sys.version_info.major == 3:
        encodedContent = encodedContent.encode('utf-8')
    encodedLength = struct.pack('@I', len(encodedContent))
    return {'length': encodedLength, 'content': encodedContent}

# Send an encoded message to stdout.
def send_message(encoded_message):
    if sys.version_info.major == 3:
        sys.stdout.buffer.write(encoded_message['length'])
        sys.stdout.buffer.write(encoded_message['content'])
        sys.stdout.buffer.flush()
    else:
        sys.stdout.write(encoded_message['length'])
        sys.stdout.write(encoded_message['content'])
        sys.stdout.flush()

 # Simple debug function to trace execution in Firefox developer console
def log(message):
    if sys.version_info.major == 3:
        sys.stdout.buffer.write(message)
    else:
        sys.stderr.write(message)

def get_firefox_profile_dir():
    default_profile_path = None
    _platform = sys.platform
    mozilla_profile = None
    
    if _platform == 'win32' or _platform == 'win64':
        mozilla_profile = os.path.join(os.getenv('APPDATA'), 'Mozilla\\Firefox')
    elif _platform == 'darwin':
        mozilla_profile = os.path.expanduser('~/Library/Application Support/Firefox')
    elif _platform == 'linux' or _platform == 'linux2':
        mozilla_profile = os.path.expanduser('~/.mozilla/firefox')
    
    if mozilla_profile:
        mozilla_profile_ini = os.path.join(mozilla_profile, 'profiles.ini')
        profile = ConfigParser.ConfigParser()
        profile.read(mozilla_profile_ini)
        try:          
            default_profile_path = os.path.normpath(os.path.join(mozilla_profile, profile.get('Profile0', 'Path')))
        except Exception as e:
            log(e)
            log("[!] Error getting Firefox default profile path")
            sys.exit(1)

    return default_profile_path

def get_firefox_user_file():
    user_file = "user.js"
    profile_dir = get_firefox_profile_dir()

    if not profile_dir:
        log("[!] Could not get Firefox profile directory. Aborting...")
        sys.exit()

    return os.path.join(profile_dir, user_file)

def set_firefox_user_pref(key, value):
    return 'user_pref("{}", {});'.format(key, value)

def get_firefox_dns_pref():
    user_file = get_firefox_user_file()
    get_mode = '1'
    get_uri = 'https://mozilla.cloudflare-dns.com/dns-query'

    if os.path.isfile(user_file):
        with open(user_file, 'r') as f:
            read = f.read()

            get_mode_search = re.search('user_pref\("{}", ?(.+?)\);'.format(trr_mode), read)
            if get_mode_search:
                get_mode = get_mode_search.group(1)

            get_uri_search = re.search('user_pref\("{}", "?(.+?)"?\);'.format(trr_uri), read)
            if get_uri_search:
                get_uri = get_uri_search.group(1)

    return get_mode, get_uri

def set_firefox_dns_pref(mode, uri):
    set_mode = set_firefox_user_pref(trr_mode, mode)
    set_uri = set_firefox_user_pref(trr_uri, '"{}"'.format(uri))
    set_custom_uri = set_firefox_user_pref(trr_custom_uri, '"{}"'.format(uri))
    return set_mode, set_uri, set_custom_uri

def add_data_file(file, pref, value):
    if pref in file:
        file = re.sub('user_pref\("{}",.*\);'.format(pref), value, file)
    else:
        file += '\n' + value

    return file

def format_file(file):
    if os.path.isfile(file):
        format_file = ""

        with open(file, 'r+') as f:
            for line in f:
                if line != "\n":
                    format_file += line

            f.seek(0)
            f.truncate(0)
            f.write(format_file)
            
        if format_file == "":
            os.remove(file)

def write_firefox_user_pref(mode, uri):
    if uri.find("manual;") == 0:
        uri = uri.split(";")[1]

    user = get_firefox_user_file()
    mode, uri, custom_uri = set_firefox_dns_pref(mode, uri)

    if not os.path.isfile(user):
        open(user, 'w').close()

    with open(user, 'r+') as f:
        read = f.read()

        read = add_data_file(read, trr_mode, mode)
        read = add_data_file(read, trr_uri, uri)
        read = add_data_file(read, trr_custom_uri, custom_uri)

        f.seek(0)
        f.truncate(0)
        f.write(read)

    format_file(user)

def uninstall():
    user = get_firefox_user_file()

    if os.path.isfile(user):
        with open(user, 'r+') as f:
            uninstall_file = ""

            for line in f:
                if trr_mode not in line and trr_uri not in line and trr_custom_uri not in line:
                    uninstall_file += line

            f.seek(0)
            f.truncate(0)
            f.write(uninstall_file)

    format_file(user)

try:
    if sys.argv[1] == 'uninstall':
        uninstall()
        print('\n')
        print('Uninstalled!')
        sys.exit(0)
except Exception as e:
    pass

while True:
    received_message = get_message()
    data = json.loads(received_message)
    if data["mode"] == "version":
        values = {"mode": "version", "uri": VERSION}
        send_message(encode_message(values))
    elif data["mode"] == "init":
        mode, uri = get_firefox_dns_pref()
        values = {"mode": mode, "uri": uri}
        send_message(encode_message(values))
    else:
        write_firefox_user_pref(data["mode"], data["uri"])
