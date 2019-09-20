#!/usr/bin/env python

import glob
import json
import os
import os.path
import re
import struct
import subprocess
import sys

dns = {
    'default':'https://mozilla.cloudflare-dns.com/dns-query',
    'cloudflare':'https://cloudflare-dns.com/dns-query',
    'google-rfc':'https://dns.google/dns-query',
    'google-json':'https://dns.google/resolve',
    'secure-dns':'https://doh.securedns.eu/dns-query',
    'quad9':'https://dns.quad9.net/dns-query'
    }

# Templates for configuration parameters
trr_mode = 'network.trr.mode'
trr_uri = 'network.trr.uri'
trr_custom_uri = 'network.trr.custom_uri'

def LOG(message):
    # Simple debug function to trace execution in Firefox developer console
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
            LOG("[!] Error getting Firefox default profile path")
            sys.exit()

    elif _platform == 'darwin':
        try:
            FF_PRF_DIR_DEFAULT = glob.glob(os.path.expanduser("~/Library/Application Support/Firefox/Profiles/*default*"))[0]
        except:
            LOG("[!] Error getting Firefox default profile path")
            sys.exit()

    elif _platform == 'linux' or _platform == 'linux2':
        try:
            FF_PRF_DIR_DEFAULT = glob.glob(os.path.expanduser("~/.mozilla/firefox/*default*"))[0]
        except:
            LOG("[!] Error getting Firefox default profile path")
            sys.exit()

    LOG("[i] Writing to file {}/user.js".format(FF_PRF_DIR_DEFAULT))
    return FF_PRF_DIR_DEFAULT

def get_firefox_user_file():
    user_file = "user.js"
    profile_dir = get_firefox_profile_dir()

    if not profile_dir:
        print("[!] Could not get Firefox profile directory. Aborting...")
        sys.exit()

    return profile_dir + "/" + user_file

def set_firefox_user_pref(key, value):
    return 'user_pref("{}", {});'.format(key, value)

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
    user = get_firefox_user_file()
    mode, uri, custom_uri = set_firefox_dns_pref(mode, dns[uri])

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

while True:
    received_message = get_message()
    data = json.loads(received_message)
    write_firefox_user_pref(data["mode"], data["uri"])
