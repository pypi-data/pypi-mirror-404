import platform

if platform.system() == 'Windows':
    import winreg


    class RegistryError(Exception):
        pass


    def remove_registry_keys(hive: str, *keys):
        for key in keys:
            try:
                hive = eval(f'winreg.{hive}')
                subkey = key
                winreg.DeleteKey(hive, subkey)
                print(f"Удален ключ реестра: {key}")
            except OSError as e:
                raise RegistryError(f"Не удалось удалить ключ реестра {key}: {e}")


    def remove_registry_values(hive, subkey, *value_names):
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                for value_name in value_names:
                    try:
                        winreg.DeleteValue(reg_key, value_name)
                    except FileNotFoundError:
                        raise FileNotFoundError(f"Значение {value_name} не найдено в {subkey}")
                    except Exception as e:
                        raise RegistryError(f"Ошибка при удалении {value_name}: {e}")
        except PermissionError:
            raise OSError("Ошибка: Не хватает прав для удаления значений.")
        except Exception as e:
            raise RegistryError(f"Ошибка: {e}")


    def remove_values_in_keys(hive, **value_names):
        """Указывайте значения через **kwargs: ключ=(значение1, значение2) или
        введите _d_i_c_t_={ключ: (значение1, значение2)}"""
        if '_d_i_c_t_' in value_names:
            value_names = value_names['_d_i_c_t_']
        for key in value_names:
            values = value_names[key]
            remove_registry_values(hive, key, *values)
else:
    raise ImportError('windows_registry is only supported on Windows')
