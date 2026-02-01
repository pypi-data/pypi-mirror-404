import psutil, subprocess


def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        try:
            # Проверяем имя процесса
            if proc.info['name'] == process_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def kill_process_if_is_running(process_name, *args, **kwargs):
    if is_process_running(process_name):
        subprocess.run(('taskkill', *args), **kwargs)
