#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import json
import os
import re
import struct
import subprocess
import sys

VERSION = "1.1.0"

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
    sys.stderr.write(message)

def get_firefox_profile_dir():
    FF_PRF_DIR_DEFAULT = None
    _platform = sys.platform
    
    if _platform == 'win32' or _platform == 'win64':
        try:
            # TODO: Check this case!
            # FF_PRF_DIR_DEFAULT = glob.glob("{}\\Mozilla\\Firefox\\Profiles\\*default-release*".format(os.getenv('APPDATA')))[0]
            FF_PRF_DIR_DEFAULT = glob.glob("{}\\Mozilla\\Firefox\\Profiles\\*default*".format(os.getenv('APPDATA')))[0]
        except:
            log("[!] Error getting Firefox default profile path")
            sys.exit()

    elif _platform == 'darwin':
        try:
            FF_PRF_DIR_DEFAULT = glob.glob(os.path.expanduser("~/Library/Application Support/Firefox/Profiles/*default*"))[0]
        except:
            log("[!] Error getting Firefox default profile path")
            sys.exit()

    elif _platform == 'linux' or _platform == 'linux2':
        try:
            FF_PRF_DIR_DEFAULT = glob.glob(os.path.expanduser("~/.mozilla/firefox/*default*"))[0]
        except:
            log("[!] Error getting Firefox default profile path")
            sys.exit()

    log("[i] Writing to file {}/user.js".format(FF_PRF_DIR_DEFAULT))
    return FF_PRF_DIR_DEFAULT

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
    get_mode = ''
    get_uri = ''

    if os.path.isfile(user_file):
        with open(user_file, 'r') as f:
            read = f.read()

            get_mode = re.search('user_pref\("{}", ?(.+?)\);'.format(trr_mode), read)
            if get_mode:
                get_mode = get_mode.group(1)

            get_uri = re.search('user_pref\("{}", "?(.+?)"?\);'.format(trr_uri), read)
            if get_uri:
                get_uri = get_uri.group(1)

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
