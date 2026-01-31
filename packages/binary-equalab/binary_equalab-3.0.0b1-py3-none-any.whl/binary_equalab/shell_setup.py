import platform
import os
import subprocess
import shutil
import sys

def detect_shell():
    """Detect current shell based on OS and Env"""
    system = platform.system()
    
    if system == "Windows":
        return "powershell"
    
    # Check for Termux
    if "com.termux" in os.environ.get("PREFIX", ""):
        return "termux"
        
    shell_env = os.environ.get("SHELL", "")
    if "zsh" in shell_env:
        return "zsh"
    elif "bash" in shell_env:
        return "bash"
        
    return "unknown"

def install_nerd_font():
    """Install Cascadia Code Nerd Font"""
    print("📦 [Binary Setup] Instalando Nerd Font...")
    system = platform.system()
    
    if system == "Windows":
        try:
            # Try via oh-my-posh if installed, or winget
            subprocess.run(["oh-my-posh", "font", "install", "CascadiaCode"], check=False)
        except FileNotFoundError:
            print("⚠️ Oh My Posh no encontrado, omitiendo fuente automática.")

    elif system == "Linux":
        if "com.termux" in os.environ.get("PREFIX", ""):
            print("ℹ️ En Termux, configura la fuente manualmente en Termux Settings.")
        else:
            # Generic Linux font install (simple version)
            font_dir = os.path.expanduser("~/.local/share/fonts")
            os.makedirs(font_dir, exist_ok=True)
            # Todo: Download zip logic if needed
            print("ℹ️ Descarga CascadiaCode.zip de NerdFonts y ponlo en ~/.local/share/fonts")

def install_oh_my_posh_windows():
    print("📦 [Binary Setup] Instalando Oh My Posh en Windows...")
    
    # Check if winget exists
    if shutil.which("winget"):
        subprocess.run(["winget", "install", "JanDeDobbeleer.OhMyPosh"])
    else:
        # Fallback to store or manual
        print("⚠️ Winget no encontrado. Instala Oh My Posh desde Microsoft Store.")
        return

    # Theme config
    # We can inject our theme later
    print("✅ Oh My Posh instalado. Configura tu $PROFILE.")

def install_oh_my_zsh_termux():
    print("📦 [Binary Setup] Configurando Termux (Zsh + Oh My Zsh)...")
    
    # Install dependencies
    subprocess.run(["pkg", "install", "zsh", "git", "curl", "-y"])
    
    # Install Oh My Zsh (Unattended)
    subprocess.run([
        "sh", "-c",
        'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
    ])
    
    # Plugins (Autosuggestions!)
    custom_dir = os.path.expanduser("~/.oh-my-zsh/custom")
    subprocess.run([
        "git", "clone", 
        "https://github.com/zsh-users/zsh-autosuggestions.git",
        f"{custom_dir}/plugins/zsh-autosuggestions"
    ])
    
    subprocess.run([
        "git", "clone", 
        "https://github.com/zsh-users/zsh-syntax-highlighting.git",
        f"{custom_dir}/plugins/zsh-syntax-highlighting"
    ])
    
    # Update .zshrc
    zshrc_path = os.path.expanduser("~/.zshrc")
    with open(zshrc_path, "r") as f:
        content = f.read()
    
    content = content.replace('plugins=(git)', 'plugins=(git zsh-autosuggestions zsh-syntax-highlighting)')
    # Set Theme (agnoster is good default, or powerlevel10k)
    content = content.replace('ZSH_THEME="robbyrussell"', 'ZSH_THEME="agnoster"')
    
    with open(zshrc_path, "w") as f:
        f.write(content)
        
    # Change shell
    subprocess.run(["chsh", "-s", "zsh"])
    
    print("✅ Termux configurado. Reinicia la app.")

def run_setup():
    print("╔═══════════════════════════════════════╗")
    print("║   🎨 Binary EquaLab Shell Setup       ║")
    print("╚═══════════════════════════════════════╝")
    
    shell = detect_shell()
    print(f"🔍 Entorno detectado: {shell.upper()}")
    
    if shell == "powershell":
        install_oh_my_posh_windows()
        install_nerd_font()
    
    elif shell == "termux":
        install_oh_my_zsh_termux()
        
    elif shell == "zsh" or shell == "bash":
        print(f"ℹ️ Para Linux/Mac ({shell}), recomendamos Starship o Oh My Zsh manualmente por ahora.")
    
    else:
        print("⚠️ Shell no soportado totalmente. Intenta instalar 'starship' manualmente.")

if __name__ == "__main__":
    run_setup()
