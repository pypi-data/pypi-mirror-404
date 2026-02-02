from hrenpack.decorators import confirm
from hrenpack.filework import TextFile


class CompileError(Exception):
    pass


class ProgrammingLanguageSourceFile(TextFile):
    def __init__(self, path: str, compiler_url: str, options: str):
        super().__init__(path)
        self.compiler_url = compiler_url
        self.options = options

    def online_compile(self, output_filename):
        from requests import post

        data = {'src': self.read(), 'options': self.options}
        response = post(self.compiler_url, data)

        if response.status_code == 200:
            with open(output_filename, 'wb') as file:
                file.write(response.content)
        else:
            raise CompileError("Ошибка при компиляции")


class PythonFile(ProgrammingLanguageSourceFile):
    def __init__(self, path: str):
        super().__init__(path, '', '')
        del self.compiler_url, self.options, self.online_compile

    def run(self, confirm_enabled: bool = True):
        def cd():
            exec(self.read())

        @confirm
        def ce():
            exec(self.read())

        ce() if confirm_enabled else cd()
