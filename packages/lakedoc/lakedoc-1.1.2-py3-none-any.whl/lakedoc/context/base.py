class LakeBaseContext(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __repr__(self):
        return f'<{self.__class__.__name__}: 0x{id(self):016X}>'
    
    def register(
        self,
        converter: str,
        converter_class,
        is_cover: bool = True,
    ):
        raise NotImplementedError
    
    def pick(self, converter: str):
        raise NotImplementedError
    
    def convert_content(self, html: str, converter: str = "markdown") -> str:
        raise NotImplementedError

    def convert_content_save(
        self,
        html: str,
        save_path=None,
        converter: str = "markdown",
        encoding: str = "utf-8",
    ):
        raise NotImplementedError
    
    def convert_file(
        self,
        read_path,
        converter: str = "markdown",
        encoding: str = "utf-8",
    ):
        raise NotImplementedError
    
    def convert_file_save(
        self,
        read_path,
        save_path=None,
        converter: str = "markdown",
        encoding: str = "utf-8",
    ):
        raise NotImplementedError