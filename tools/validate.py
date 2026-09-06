"""Validate approval records and immutable GitHub file bytes; never execute packages."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE = 524288


def require(condition, message):
    if not condition:
        raise ValueError(message)


def package_path(path):
    require(isinstance(path, str) and len(path) <= 240 and path.count('/') <= 7, 'Invalid path')
    for part in path.split('/'):
        require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', part) is not None
                and not part.endswith('.')
                and not re.match(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', part, re.I), 'Unsafe path')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirect rejected')


def validate():
    raw = (ROOT / 'catalog.json').read_bytes()
    require(len(raw) <= MAX_FILE, 'Catalog too large')
    data = json.loads(raw)
    require(data['schema'] == 1 and isinstance(data['extensions'], list)
            and len(data['extensions']) <= 200, 'Invalid schema')
    ids = set()
    opener = urllib.request.build_opener(NoRedirect)
    for release in data['extensions']:
        for key, limit in [('id', 48), ('name', 160), ('description', 320), ('version', 32),
                           ('repository', 160), ('commit', 40), ('php', 16), ('reviewed_at', 10)]:
            value = release[key]
            require(isinstance(value, str) and 0 < len(value.encode('utf-8')) <= limit
                    and not re.search(r'[\x00-\x1f\x7f]', value), 'Invalid field: ' + key)
        require(re.fullmatch(r'[a-z][a-z0-9_]{0,47}', release['id']) is not None
                and release['id'] not in ids, 'Duplicate or invalid id')
        package_path(release['id'])
        ids.add(release['id'])
        require(re.fullmatch(r'weewx-php/[a-z0-9][a-z0-9-]{0,79}', release['repository']) is not None, 'Invalid repository')
        require(re.fullmatch(r'[a-f0-9]{40}', release['commit']) is not None, 'Use a commit SHA')
        require(re.fullmatch(r'\d{1,4}\.\d{1,4}\.\d{1,4}', release['version']) is not None, 'Invalid version')
        require(re.fullmatch(r'\d{1,2}\.\d{1,2}(?:\.\d{1,2})?', release['php']) is not None, 'Invalid PHP version')
        require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', release['reviewed_at']) is not None, 'Invalid review date')
        require(type(release['api']) is int and release['api'] >= 1, 'Invalid API version')
        require(isinstance(release['requires'], list) and len(release['requires']) <= 16
                and all(isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,31}', value)
                        for value in release['requires']), 'Invalid requirements')
        files = release['files']
        require(isinstance(files, dict) and 1 <= len(files) <= 64, 'Invalid files')
        require(release['entry'] in files and release['entry'].endswith('.php') and release['review'] in files, 'Missing entry or review')
        settings = release.get('settings')
        if settings is not None:
            package_path(settings)
            require(release['api'] >= 2 and settings.endswith('.json') and settings in files, 'Invalid settings metadata')
        seen, total = set(), 0
        for path, checksum in files.items():
            package_path(path)
            key = path.lower()
            require(not any(key == prior or key.startswith(prior + '/') or prior.startswith(key + '/') for prior in seen), 'Conflicting paths')
            seen.add(key)
            require(isinstance(checksum, str) and re.fullmatch(r'[a-f0-9]{64}', checksum) is not None, 'Invalid checksum')
            url = f"https://raw.githubusercontent.com/{release['repository']}/{release['commit']}/{path}"
            with opener.open(url, timeout=15) as response:
                body = response.read(MAX_FILE + 1)
            require(len(body) <= MAX_FILE and hashlib.sha256(body).hexdigest() == checksum, 'Checksum mismatch: ' + path)
            if path == settings:
                schema = json.loads(body)
                require(len(body) <= 65536 and schema['schema'] == 1
                        and schema['scope'] in ('global', 'archive')
                        and isinstance(schema['fields'], list)
                        and 1 <= len(schema['fields']) <= 40, 'Invalid settings schema')
            total += len(body)
            require(total <= 4194304, 'Package too large')
        print(f"{release['id']} {release['version']}: {len(files)} files verified")


if __name__ == '__main__':
    validate()
