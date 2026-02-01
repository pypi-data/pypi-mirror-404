import os, tempfile, uuid, requests
from urllib.parse import urlencode
from tqdm import tqdm
from hrenpack import NullStr


class NetworkError(Exception):
    pass


def connection_check():
    error = NetworkError("Подключение к интернету отсутствует")
    try:
        response = requests.get("https://google.com", timeout=5)
        if response.status_code != 200:
            raise error
        return True
    except requests.ConnectionError:
        raise error


def is_connected() -> bool:
    try:
        connection_check()
    except NetworkError:
        return False
    else:
        return True


def connect_to_site(url: str, **kwargs) -> bool:
    if is_connected():
        response = requests.get(url, **kwargs)
        return response.status_code == 200
    else:
        return False


class TestResponse:
    def __init__(self, response: requests.Response):
        self.response = response

    def __call__(self, *args, **kwargs):
        if self.response.status_code == 200:
            self.success(*args, **kwargs)
        else:
            self.error(*args, **kwargs)

    def success(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


def download_file(url, name: str, to: str = '', params=None, use_progressbar: bool = False, **request_kwargs):
    path = os.path.join(to, name)
    response = requests.get(url, params, **request_kwargs)
    if use_progressbar:
        total_size = int(response.headers.get('content-length', 0))
        with open(path, 'wb') as file, tqdm(
                desc=name,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                bar.update(len(data))
                file.write(data)
    else:
        with open(path, 'wb') as file:
            file.write(response.content)
    return path


def download_file_to_temp(url, extension: str = '', name: str = '', params=None, use_progressbar: bool = False,
                          **request_kwargs):
    tempdir = tempfile.gettempdir()
    if not name:
        name = str(uuid.uuid4())
    if extension:
        extension = '.' + extension
    path = download_file(url, name + extension, tempdir, params, use_progressbar, **request_kwargs)
    return path


class ReCaptchaV3:
    def __init__(self, secret_key: str, site_key: NullStr, score_threshold: float = 0.5):
        self.secret_key = secret_key
        self.score_threshold = score_threshold
        self.site_key = site_key

    @property
    def js_api_url(self) -> str:
        return f'https://www.google.com/recaptcha/api.js?render={self.site_key}'

    def verify(self, token: str) -> bool:
        if not token:
            return False
        json = requests.post('https://www.google.com/recaptcha/api/siteverify',
                             {'secret': self.secret_key, 'response': token}).json()
        return json.get('success', False) and float(json.get('score', 0)) >= self.score_threshold


def GET_url(base_url: str, **params) -> str:
    return f'{base_url}?{urlencode(params)}'
