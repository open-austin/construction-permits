#!/usr/bin/env python

import base64

import requests

REPO_URL = 'https://api.github.com/repos/open-austin/construction-permits/contents'


def create_file(path, branch, content, message, auth):
    url = '{}/{}'.format(REPO_URL, path.strip('/'))
    data = {
        'content': base64.b64encode(content),
        'branch': branch,
        'message': message
    }
    res = requests.put(url, json=data, auth=auth)
    res.raise_for_status()

    return res.json()
