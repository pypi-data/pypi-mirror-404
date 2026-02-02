import uuid
from datetime import datetime
from typing import Literal
from hrenpack.strwork import remove_extra_spaces
from hrenpack.filework import TextFile


class HostsFile(TextFile):
    comment_letter = '#'

    def __init__(self):
        super().__init__(r'C:/Windows/System32/drivers/etc/hosts')

    def read_hosts(self) -> dict:
        output = dict()
        for line in self.read_lines():
            if not line or line.startswith(self.comment_letter):
                continue
            ip, domain = remove_extra_spaces(line).split()
            output[ip] = domain
        return output

    def add_host(self, ip, domain, dont_backup: bool = False):
        entry = f'{ip} {domain}\n'
        self.add_data(entry)
        if not dont_backup:
            self.backup()

    def remove_host(self, domain, dont_backup: bool = False):
        hosts = self.read_hosts()
        with open(self.path, 'w', encoding='utf-8') as file:
            for ip, host in hosts.items():
                if domain == host:
                    file.write(f'{ip} {host}\n')
        if not dont_backup:
            self.backup()

    def backup(self):
        self.copy(f'hosts_backups/hosts-{datetime.now()}')
