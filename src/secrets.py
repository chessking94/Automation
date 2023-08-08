from pykeepass import PyKeePass, pykeepass as pk


class secrets_constants():
    """A class for constants necessary for the secrets module"""
    PGP_PROPERTIES = [
        'DecryptPathDefault',
        'EncryptedExtension',
        'EncryptPathDefault',
        'SuppressDecryptDefault',
        'SuppressEncryptDefault'
    ]
    SFTP_PROPERTIES = [
        'HostKeyType',
        'HostKeyValue',
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


class keepass():
    """Class to interact with a Keepass file where secrets are saved

    Attributes
    ----------
    kp : pykeepass.PyKeePass
        Object representing a Keepass file
    group_title : str
        Name of the Keepass group in which the secret(s) are saved
    group : pykeepass.Group
        Object representing the data associated with the Keepass group
    entry : pykeepass.Entry
        Object representing the data associated with the Keepass entry

    TODO
    ----
    Implement keyfile opening of Keepass file

    """
    def __init__(self, filename: str, password: str, group_title: str, entry_title: str):
        """Inits keepass class

        Parameters
        ----------
        filename : str
            Full name of Keepass file to use
        password : str
            Password to open the Keepass file
        group_title : str
            Name of the group to find the entry in
        entry_title : str
            Name of the entry to extract information from

        Raises
        ------
        ValueError
            If group is not found or multiple groups are found
            If entry is not found or multiple entries are found
        TypeError
            If the unique group found is not the expected object type
            If the unique entry found is not the expected object type

        """
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
        """Obtains general data value

        Parameters
        ----------
        field : str
            The name of the field to retrieve information from

        Returns
        -------
        str : the value requested

        Raises
        ------
        NotImplementedError
            If 'field' is not an expected value

        """
        field = field.lower()
        field_list = ['username', 'password', 'url']
        if field not in field_list:
            raise NotImplementedError(f"field '{field}' is not a valid general field, expecting one of {field_list}")

        return getattr(self.entry, field)

    def getcustomproperties(self, string_field: str) -> str:
        """Obtains custom property value

        Parameters
        ----------
        string_field : str
            The name of the custom field to retrieve information from

        Returns
        -------
        str : the value requested

        Raises
        ------
        NotImplementedError
            If string_field is not an expected value for that Keepass group

        """
        property_list = []
        if self.group_title == 'test':
            property_list = ['Test']
        elif self.group_title == 'pgp':
            property_list = secrets_constants.PGP_PROPERTIES
        elif self.group_title == 'sftp':
            property_list = secrets_constants.SFTP_PROPERTIES

        if len(property_list) > 0:
            if string_field not in property_list:
                raise NotImplementedError(f"unexpected custom property '{string_field}'")

        props = self.entry.custom_properties
        return props.get(string_field)

    def readattachment(self, attachment_name: str) -> str:
        """Obtains text of an attachment

        Parameters
        ----------
        attachment_name : str
            The name of the attachment to read

        Returns
        -------
        str : the attachment text itself

        Raises
        ------
        IndexError
            If 'attachment_name' does not exist in the Keepass entry

        """
        attach = self.entry.attachments
        data = None
        for a in attach:
            if a.filename == attachment_name:
                data = a.data.decode('utf-8')
                break
        if data is None:
            raise IndexError(f'attachment {attachment_name} does not exist')

        return data

    def writecustomproperty(self, string_field: str, new_value: str, create_property: bool = False):
        """Writes custom property value

        Parameters
        ----------
        string_field : str
            The name of the custom field to write to
        new_value : str
            The value to write to the custom field
        create_property : bool, optional (default False)
            Indicator if the custom field should be created, if it does not exist

        Raises
        ------
        KeyError
            If custom property 'string_field' does not exist and 'create_property' is False

        """
        if string_field in self.entry.custom_properties or create_property:
            self.entry.set_custom_property(key=string_field, value=new_value)
        else:
            raise KeyError(f"keepass entry '{self.entry.title}' custom property '{string_field}' does not exist")
        self.kp.save()
