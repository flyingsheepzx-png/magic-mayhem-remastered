"""Review exactly the tracked or staged public files without printing secrets.

Usage: python tools/check_publication.py [--staged]
The check reports paths/line numbers only. It never authenticates or uploads.
"""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_EMAILS = {'sergiogdb@gmail.com', 'opencode@microsoft.com', 'listserv@lists.research.microsoft.com'}
SECRET_PATTERNS = {
    'private-key': r'-----BEGIN (?:[A-Z0-9 ]*PRIVATE KEY)-----',
    'github-token': r'\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b',
    'api-token': r'\b(?:sk-[A-Za-z0-9_\-]{20,}|AKIA[A-Z0-9]{16}|AIza[0-9A-Za-z_\-]{30,})\b',
    'credential-in-url': r'https?://[^\s/@:]+:[^\s/@]+@',
    'literal-credential': r'(?i)(?:api[_-]?key|password|passwd|access[_-]?token|client[_-]?secret|authorization|cookie)\s*[:=]\s*["\x27]([^"\x27\r\n]{5,})',
}
BANNED_SUFFIXES = {'.exe', '.dll', '.bin', '.obj', '.res', '.pdb', '.log', '.dmp', '.sav',
                   '.ogg', '.wav', '.mp3', '.mp4', '.avi', '.zip', '.7z', '.safetensors', '.gguf'}
BANNED_PARTS = {'out', '.venv', '__pycache__', 'save', 'saves', 'preserved-player-data', 'logs',
                'backups', 'playtests', '.ssh', '.git'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true')
    args = parser.parse_args()
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    staged = {}
    if args.staged:
        entries = subprocess.check_output(['git', 'ls-files', '-s', '-z'], cwd=ROOT).decode('utf-8').split('\0')
        identities = []
        for entry in filter(None, entries):
            metadata, filename = entry.split('\t', 1)
            mode, oid, stage = metadata.split()
            if stage != '0' or mode != '100644':
                raise SystemExit('Unmerged, executable or symlink entry requires manual review: '+filename)
            identities.append((filename, oid))
        batch = subprocess.check_output(['git', 'cat-file', '--batch'], cwd=ROOT,
            input=''.join(oid+'\n' for _, oid in identities).encode('ascii'))
        position = 0
        for filename, oid in identities:
            end = batch.index(b'\n', position)
            returned_oid, kind, size = batch[position:end].decode('ascii').split()
            if returned_oid != oid or kind != 'blob':
                raise SystemExit('Unexpected staged object: '+filename)
            start = end+1
            staged[filename] = batch[start:start+int(size)]
            position = start+int(size)+1
    findings = []
    total = 0
    for name in filter(None, names):
        p = Path(name)
        parts = {part.lower() for part in p.parts}
        if p.suffix.lower() in BANNED_SUFFIXES or parts & BANNED_PARTS or p.name.lower().startswith('.env'):
            findings.append({'file': name, 'rule': 'excluded-file-type-or-directory'})
        if re.search(r'(?i)(?:credential|secret|password|token)(?:s)?\.(?:json|ini|txt|yaml|yml)$', p.name):
            findings.append({'file': name, 'rule': 'private-configuration-filename'})
        data = staged[name] if args.staged else (ROOT/name).read_bytes()
        total += len(data)
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError:
            if name == 'modernization/build/remastered-1.1-options-render-v1/wrapper/src/config.c':
                # Upstream legacy source contains single-byte localized strings.
                text = data.decode('cp1252')
            else:
                allowed = name == 'modernization/build/remastered-1.1-options-render-v1/wrapper/config/cnc-ddraw.ico'
                if not allowed:
                    findings.append({'file': name, 'rule': 'unreviewed-non-text-file'})
                continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for rule, pattern in SECRET_PATTERNS.items():
                if re.search(pattern, line):
                    findings.append({'file': name, 'line': line_number, 'rule': rule})
            for match in re.finditer(r'(?i)[A-Z]:[/\\]+Users[/\\]+([^\s"\x27`/\\]+)', line):
                if match.group(1).upper() not in {'DEVELOPER', 'PUBLIC', 'USERNAME', '<USER>'}:
                    findings.append({'file': name, 'line': line_number, 'rule': 'personal-home-directory'})
            for match in re.finditer(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])', line):
                try:
                    ip = ipaddress.ip_address(match.group())
                    if ip.is_private and not ip.is_loopback and not ip.is_unspecified:
                        findings.append({'file': name, 'line': line_number, 'rule': 'private-network-address'})
                except ValueError:
                    pass
            emails = re.findall(r'(?i)[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}', line)
            for email in emails:
                upstream = '/wrapper/' in name and email.lower() in UPSTREAM_EMAILS
                # The allow-list itself documents the reviewed public upstream notices.
                allowlist_source = name == 'tools/check_publication.py' and email.lower() in UPSTREAM_EMAILS
                if not upstream and not allowlist_source:
                    findings.append({'file': name, 'line': line_number, 'rule': 'unreviewed-email-address'})
    result = {'files': len(list(filter(None, names))), 'bytes': total,
              'mode': 'staged' if args.staged else 'tracked', 'findings': findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if findings:
        sys.exit(1)

if __name__ == '__main__':
    main()
