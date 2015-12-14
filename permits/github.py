#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64

import requests
from secrets import GITHUB_AUTH

REPO_URL = 'https://api.github.com/repos/open-austin/construction-permits/contents'


def url_for_path(path):
    return '{}/{}'.format(REPO_URL, path.strip('/'))


def get_file(path, branch, auth=GITHUB_AUTH):
    url = url_for_path(path)
    params = {
        'ref': branch,
    }
    res = requests.get(url, params=params, auth=auth)
    print(res.text)
    res.raise_for_status()

    return res.json()


def create_or_update_file(path, branch, content, message, auth=GITHUB_AUTH):
    url = url_for_path(path)
    encoded_content = base64.b64encode(content)
    data = {
        'content': encoded_content,
        'branch': branch,
        'message': message,
    }

    try:
        existing_file = get_file(path, branch)
        if encoded_content == existing_file['content']:
            print('Not updating {}, content is identical'.format(path))
            return existing_file
        data['sha'] = existing_file['sha']
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 404:
            raise e

    res = requests.put(url, json=data, auth=auth)
    print(res.text)
    res.raise_for_status()

    return res.json()
