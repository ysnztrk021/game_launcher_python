# 🎮 Game Launcher – Python Edition

Game Launcher est une application Windows écrite en **Python + CustomTkinter**,  
qui permet d’afficher **tous vos jeux** et **launchers** dans une interface moderne,  
avec **icônes automatiques**, **filtres**, **recherche**, et **lancement direct**.

L’application extrait les icônes Windows **directement depuis les fichiers `.lnk` ou `.exe`**,  
ce qui la rend compatible avec :

✔ Steam  
✔ Epic Games Launcher  
✔ Riot Games  
✔ Ubisoft Connect  
✔ Rockstar Launcher  
✔ EA App  
✔ Jeux installés localement  
✔ Tous raccourcis personnalisés  

---

## ✨ Fonctionnalités

- 🔍 **Scan automatique** des raccourcis dans deux dossiers dédiés :
  - `JEUX` → Jeux installés  
  - `LAUNCHERS` → Launchers (Steam, Epic, etc.)
- 🎨 **Affichage des icônes** extraites automatiquement depuis chaque raccourci
- 🚀 **Bouton Lancer** pour démarrer n’importe quel jeu/application
- 🧩 **Filtres intelligents** : Tous / Jeux / Launchers
- 🔎 **Recherche instantanée**
- 🔄 **Bouton Refresh** pour recharger la liste
- 🖼 Cache automatique des icônes pour accélérer les chargements
- 🪟 Interface moderne (mode sombre, design épuré)
- 🖥 Compatible Windows 10 / 11
- ⚙️ Possibilité de transformer l’app en **launcher.exe** via PyInstaller
- 🔧 Peut se lancer au démarrage de Windows

---

## 📂 Structure du projet
```bash
game-launcher/
│
├── launcher.py # Application principale
├── icon_cache/ # Cache automatique des icônes extraites
├── README.md # Documentation
└── app_icon.ico # Icône de l'application (facultatif)
```

Les dossiers contenant vos raccourcis doivent être sur votre bureau :

```YAML
C:\Users\$USER_NAME$\Desktop\JEUX
C:\Users\$USER_NAME$\Desktop\LAUNCHERS
```

---

# 🐍 Installation (avec environnement virtuel)

Il est **fortement recommandé** d’utiliser un environnement virtuel pour isoler l’application.

---

## 1️⃣ Installer Python 3.10+  
Téléchargement : https://www.python.org/downloads/

Assurez-vous de cocher :  
✔ **Add Python to PATH**

---

## 2️⃣ Créer un environnement virtuel

Dans le dossier `game-launcher/` :

```bash
python -m venv .venv
```

Cela crée un dossier :
```YAML
.venv/
```

---

## 3️⃣ Activer l'environnement virtuel
Sous Windows :
```bash
.venv\Scripts\activate
```

Vous devez voir (venv) apparaître dans le terminal.

---

### 2️⃣ Installer les dépendances

Ouvrez un terminal dans le dossier du projet :

```bash
pip install -r requirements.txt
```

▶️ Lancement de l’application (mode développement)
Dans le dossier où se trouve launcher.py :

```bash
python launcher.py
```
L'application s'ouvre immédiatement.

🧊 Générer un vrai .exe Windows
Vous pouvez transformer l'application en un fichier exécutable launcher.exe via PyInstaller.

1️⃣ Installer PyInstaller
```bash
pip install pyinstaller
```

2️⃣ Créer le .exe
Avec icône personnalisée :

```bash
pyinstaller launcher.py --onefile --noconsole --icon=app_icon.ico
```

Sans icône :

```bash
pyinstaller launcher.py --onefile --noconsole
```
Le .exe se trouve dans :
```bash
dist/launcher.exe
```
🪄 Lancement automatique au démarrage de Windows
Méthode recommandée
Créez un raccourci de launcher.exe

Ouvrez Win + R

Tapez : shell:startup

Glissez votre raccourci dans ce dossier

Votre launcher démarre maintenant automatiquement avec Windows.

🧠 Fonctionnement interne
🔹 Scan des jeux
L’appli lit le contenu des 2 dossiers :

JEUX = raccourcis .lnk → Jeux
LAUNCHERS = raccourcis .lnk → Launchers
Chaque fichier .lnk / .exe / .url devient un Item avec :

nom

chemin d'origine

type ("game" ou "launcher")

cible réelle (si c’est un .lnk)

🔹 Extraction des icônes Windows
L’appli utilise l’API Windows SHGetFileInfo() via ctypes

Les icônes sont converties en images via PIL

Elles sont ensuite stockées dans icon_cache/

Ce cache accélère le lancement de l’application

🔹 Interface graphique (CustomTkinter)
L’UI est entièrement dynamique :

Grille adaptative

Cartes (cards) avec icône, nom, type, chemin et bouton "Lancer"

Recherche live

Filtrage instantané

❓ FAQ
➤ Les icônes ne s'affichent pas ?
Vérifiez que vos fichiers sont bien dans JEUX et LAUNCHERS
et qu’ils sont au format .lnk ou .exe.

➤ Les jeux Steam ont des icônes ?
Oui ! On récupère l’icône directement depuis le raccourci .lnk,
car Steam ne stocke pas d’icône dans steam.exe.

➤ Est-ce que l’app fonctionne sans Internet ?
Oui, entièrement hors-ligne.

🏁 Conclusion
Ce Game Launcher est conçu pour être :

simple

rapide

personnalisable

local

sans dépendance Web

compatible avec tous les launchers PC

Il peut facilement devenir un projet plus avancé avec :

des temps de jeu

une détection automatique d’installation

un affichage de covers HD

un mode compact / mode grille

un thème clair

du multi-profil

🎮 Game Launcher – By Yasin
