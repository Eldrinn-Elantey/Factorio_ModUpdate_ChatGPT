#!/usr/bin/python3

import os
import requests
import json
import glob
import zipfile

# Конфигурация
MODS_DIR = 'mods'  # Папка с модами относительно текущей директории
SETTINGS_DIR = 'settings'  # Папка с настройками относительно текущей директории
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'server-settings.json')

# Функция для получения настроек из файла server-settings.json
def load_settings():
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
    return settings

# Функция для получения списка установленных модов и их версий из файлов info.json
def get_installed_mods():
    installed_mods = {}
    zip_files = glob.glob(os.path.join(MODS_DIR, '*.zip'))
    
    for zip_file in zip_files:
        mod_name = os.path.basename(zip_file).replace('.zip', '')
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            info_files = [f.filename for f in zip_ref.filelist if f.filename.endswith('info.json')]
            if not info_files:
                print(f"Info file not found for mod '{mod_name}' in archive '{zip_file}'. Skipping...")
                continue
            info_file = info_files[0]  # Берем первый найденный info.json
            with zip_ref.open(info_file) as f:
                info_data = json.load(f)
                mod_name = info_data.get('name')  # Получаем имя мода из info.json
                if not mod_name:
                    print(f"Name not found in info file for mod '{mod_name}' in archive '{zip_file}'. Skipping...")
                    continue
                installed_mods[mod_name] = info_data.get('version', 'Unknown')
    
    return installed_mods

# Функция для удаления старых версий модов
def remove_old_versions(mod_name):
    old_versions = glob.glob(os.path.join(MODS_DIR, f'{mod_name}_*.zip'))
    for old_version in old_versions:
        os.remove(old_version)
        print(f'Removed old version: {old_version}')

# Функция для обновления модов
def update_mods(mods, username, token):
    headers = {'Authorization': f'Bearer {token}'}
    updated_mods = []
    for mod, current_version in mods.items():
        response = requests.get(f'https://mods.factorio.com/api/mods/{mod}/full', headers=headers)
        if response.status_code == 200:
            mod_data = response.json()
            if 'releases' in mod_data and mod_data['releases']:
                latest_release = mod_data['releases'][-1]
                latest_version = latest_release['version']
                if current_version == latest_version:
                    print(f'{mod} is already up to date (version {current_version}).')
                    continue
                
                updated_mods.append((mod, current_version, latest_version))
            else:
                print(f'No releases found for mod {mod}')
        else:
            print(f'Failed to fetch data for mod {mod}: {response.status_code}')
    
    # Вывод списка модов для обновления и запрос подтверждения
    if updated_mods:
        print("\nMods to update:")
        for mod, old_version, new_version in updated_mods:
            print(f'{mod}: {old_version} --> {new_version}')
        
        # Запрос подтверждения
        confirmation = input("Do you want to update these mods? (yes/no): ").strip().lower()
        if confirmation in ('yes', 'y'):
            for mod, current_version, latest_version in updated_mods:
                download_url = f'https://mods.factorio.com{latest_release["download_url"]}'
                download_response = requests.get(download_url, headers=headers, stream=True)
                file_path = os.path.join(MODS_DIR, latest_release['file_name'])
                
                # Удаление старых версий
                remove_old_versions(mod)

                # Загрузка новой версии
                with open(file_path, 'wb') as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f'Updated {mod} to version {latest_version}')
        else:
            print("Update cancelled.")
    else:
        print("\nNo mods to update.")

# Основной скрипт
def main():
    settings = load_settings()
    username = settings.get('username')
    token = settings.get('token')
    if not (username and token):
        print("Error: Username or token not found in server settings.")
        return
    mods = get_installed_mods()
    update_mods(mods, username, token)

if __name__ == '__main__':
    main()
