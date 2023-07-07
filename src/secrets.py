"""secrets

Author: Ethan Hunt
Date: 2023-07-04
Version: 1.0

"""

from pykeepass import PyKeePass, pykeepass as pk

# TODO: Consider adding write functionality to Keepass DB, intentionally only implementing read at first


class keepass():
    def __init__(self, filename: str, password: str, group_title: str, entry_title: str):
        self.kp = PyKeePass(filename=filename, password=password)
        self.group_title = group_title

        groups = self.kp.find_groups(name=group_title, first=False)
        self.group = self._validategroup(groups)

        entries = self.kp.find_entries(group=self.group, title=entry_title, first=False)
        self.entry = self._validateentry(entries)

    def _validategroup(self, groups: list) -> pk.Group:
        group_count = len(groups)
        if group_count != 1:
            raise ValueError(f'expecting 1 group, found {group_count}')

        if not isinstance(groups[0], pk.Group):
            raise TypeError(f"expecting 'pykeepass.Group', got '{type(groups)}'")

        return groups[0]

    def _validateentry(self, entries: list):
        entry_count = len(entries)

        if entry_count != 1:
            raise ValueError(f'expecting 1 entry, found {entry_count}')

        if not isinstance(entries[0], pk.Entry):
            raise TypeError(f"expecting 'pykeepass.Entry', got '{type(entries)}'")

        return entries[0]

    def getgeneral(self, field: str) -> str:
        field = field.lower()
        field_list = ['title', 'username', 'password', 'url']  # TODO: Look into a more flexible way to do this validation
        if field not in field_list:
            raise NotImplementedError(f"field '{field}' is not a valid general field, expecting one of {field_list}")

        return getattr(self.entry, field)

    def getcustomproperties(self, string_field: str) -> str:
        # TODO: Look into a more elegant way to do this validation
        property_list = []
        if self.group_title == 'pgp':
            property_list = [
                'DecryptPathDefault',
                'EncryptedExtension',
                'EncryptPathDefault',
                'SuppressDecryptDefault',
                'SuppressEncryptDefault'
            ]
        elif self.group_title == 'sftp':
            property_list = [
                'LocalInDefault',
                'LocalOutDefault',
                'LoginType',
                'Passphrase',
                'Port',
                'RemoteInDefault',
                'RemoteOutDefault',
                'SuppressInDefault',
                'SuppressOutDefault'
            ]

        if len(property_list) > 0:
            if string_field not in property_list:
                raise NotImplementedError(f"unexpected custom property '{string_field}'")

        props = self.entry.custom_properties
        return props.get(string_field)

    def readattachment(self, attachment_name: str) -> str:
        attach = self.entry.attachments
        data = None
        for a in attach:
            if a.filename == attachment_name:
                data = a.data.decode('utf-8')
                break
        if data is None:
            raise IndexError(f'attachment {attachment_name} does not exist')

        return data
