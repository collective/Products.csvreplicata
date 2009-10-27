class csvreplicataException(Exception):
    pass

class csvreplicataBrokenReferenceException(Exception):
    pass

class csvreplicataConflictException(Exception):
    pass

class csvreplicataPermissionException(Exception):
    pass

class csvreplicataNonExistentContainer(Exception):
    pass

class csvreplicataMissingFileInArchive(Exception):
    pass