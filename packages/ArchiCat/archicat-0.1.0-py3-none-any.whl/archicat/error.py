
class ArchiCatError(Exception):
    def __init__(self,line: int,column: int,message: str):
        super().__init__(f'{message} ({line}:{column})')

class ArchiCatSyntaxError(ArchiCatError): pass

class ArchiCatNameError(ArchiCatError): pass

class ArchiCatInvalidBlockError(ArchiCatError): pass