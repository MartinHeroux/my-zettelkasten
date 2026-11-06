# Installation and first launch

## Supported environment

My Zettelkasten is currently an **experimental Linux pilot**, tested on **Linux Mint 22.3 / Python 3.12.3**.

The application requires Python 3.10+, Tkinter, and Python virtual-environment support. Other operating systems have not yet been verified.

Before using the application for important work, test it with a disposable collection and maintain independent backups of your notes.

## 1. Recommended installation — Linux Mint

My Zettelkasten includes an installation script that automatically configures the application for desktop use.

The script has been tested on Linux Mint. It installs the required system packages, creates a dedicated Python virtual environment, and registers My Zettelkasten in the application menu.

### Download the repository

Open a terminal and run:

```bash
sudo apt update
sudo apt install git

git clone https://github.com/MartinHeroux/my-zettelkasten.git
cd personal-zettelkasten
```

### Run the installer

```bash
bash scripts/install-linux.sh
```

The installer:

1. Installs Python, Tkinter, Git, and virtual-environment support.
2. Downloads or updates the application source in `~/.local/share/my-zettelkasten/source/`.
3. Creates a dedicated Python virtual environment in `~/.local/share/my-zettelkasten/.venv/`.
4. Installs the application and its Python dependencies.
5. Creates the `~/.local/bin/my-zettelkasten` terminal launcher.
6. Registers My Zettelkasten in the Linux Mint application menu using its application icon.

### Launch the application

Open the Linux Mint menu and search for **My Zettelkasten**.

Alternatively, run:

```bash
~/.local/bin/my-zettelkasten
```

You do not need to activate the virtual environment manually.

On first launch, choose **New Collection** or **Open Collection**. The application remembers your last-used collection.

### Verify the installation

```bash
~/.local/bin/my-zettelkasten --version
```

The installed version is also available through **Help → About My Zettelkasten**.

### Update the application

The installation script can be run again to update My Zettelkasten:

```bash
bash scripts/install-linux.sh
```

The installer retrieves the latest changes from the GitHub repository and reinstalls the Python package.

Your collections remain separate from the application installation.

## 2. Manual installation — Development and advanced users

If you prefer to run My Zettelkasten directly from its source code, you can install it manually.

Install the required system packages:

```bash
sudo apt update
sudo apt install python3 python3-tk python3-venv git
```

Clone the repository and enter the project directory:

```bash
git clone https://github.com/MartinHeroux/my-zettelkasten.git
cd personal-zettelkasten
```

Create a virtual environment and install the package:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Launch the application:

```bash
python -m zettelkasten
```

Check the installed version:

```bash
python -m zettelkasten --version
```

This installation runs from your development directory and does not automatically create a Linux Mint application-menu entry.

## 3. Choosing an installation method

| | Automatic installation | Manual installation |
|---|---|---|
| Intended use | Everyday desktop use | Development and testing |
| Virtual environment | Created automatically | Created manually |
| Linux Mint menu launcher | Yes | No |
| Terminal command | `my-zettelkasten` | `python -m zettelkasten` |
| Updating | Rerun installation script | `git pull` and `pip install -e .` |

Both methods use the same application source code and can open the same collections.

If you have both installations, remember that they use separate Python virtual environments. Updating one does not automatically update the other.

## 4. Launch My Zettelkasten

Run:

```bash
python -m zettelkasten
```

On first launch, the application displays a welcome screen offering:

- **New Collection:** Create a collection in a folder of your choice.
- **Open Collection:** Open an existing collection, including one stored on Dropbox or another synchronised directory.
- **Recent Collections:** Quickly reopen a previously used collection, once you have opened one.

You do not need to specify a collection path on the command line.

### Creating a new collection

Select **New Collection**, choose the parent directory where you want the collection stored, and enter a name.

For example, you might create:

```text
~/Dropbox/My-Zettelkasten
```

The application creates the collection directory and its initial structure, including a `notes/` folder.

New, empty collections receive a pinned **Start here** note and a linked introductory tutorial.

### Opening an existing collection

Select **Open Collection** and navigate to the collection directory.

A valid collection contains a `notes/` subdirectory.

Collections can be located anywhere you have appropriate file access, including Dropbox, external drives, or other synchronised folders.

The application does not require collections to be stored in your home directory.

## 5. Opening collections on subsequent launches

My Zettelkasten remembers the last collection you opened.

When you quit while a collection is open, the application automatically reopens that collection on the next launch.

You can also use:

- **File → New Collection** to create another collection.
- **File → Open Collection** to open an existing collection.
- **File → Recent Collections** to access up to 10 previously opened collections.
- **File → Close Collection** to close the current collection and return to the welcome screen.

Closing a collection does not delete its files. If you close a collection before quitting, the welcome screen appears on the next launch rather than automatically reopening that collection.

If a previously opened collection is unavailable—for example, because Dropbox is not accessible—the application displays a warning rather than recreating the missing directory.

### Opening a specific collection from the terminal

For users who prefer command-line launching, the original option remains available:

```bash
python -m zettelkasten --collection ~/Dropbox/My-Zettelkasten
```

You can also display the welcome screen explicitly:

```bash
python -m zettelkasten --welcome
```

## 6. Check the installed version

To display the installed version without opening the graphical interface:

```bash
python -m zettelkasten --version
```

For example:

```text
My Zettelkasten 0.5.4
```

The same version information is available within the application under **Help → About My Zettelkasten**.

The version is retrieved from the installed Python package metadata.

## 7. Installing a Linux Mint application-menu launcher

My Zettelkasten can also be installed with a dedicated virtual environment and a desktop launcher, allowing it to start directly from the Linux Mint application menu.

With this arrangement, you can:

- Search for **My Zettelkasten** in the Linux Mint menu.
- Launch the application without opening a terminal.
- Use the application's branded icon.
- Open your last-used collection automatically.

The application can also be started with a terminal command such as:

```bash
my-zettelkasten
```

This requires a launcher to be configured separately; cloning the repository and running `pip install -e .` does not automatically create a Linux Mint menu entry.

A dedicated installation script can automate this process by cloning the repository, creating a private virtual environment, and registering a `.desktop` launcher.

## 8. Updating My Zettelkasten

If you installed the application by cloning the GitHub repository, navigate to the project directory and run:

```bash
git pull --ff-only
source .venv/bin/activate
python -m pip install -e .
```

Then verify the version:

```bash
python -m zettelkasten --version
```

Your collections are stored separately from the application code and should not need to be moved or recreated when updating.

If you installed My Zettelkasten through a separate Linux Mint bootstrap script, update that installation using the script's own update procedure. Updating a development checkout does not automatically update a separate desktop installation.

## 9. Understanding collections

A **collection** is a directory containing notes, attachments, and collection-specific settings. It is not simply a subject folder.

A typical collection includes:

```text
My-Zettelkasten/
├── notes/
├── inbox/
├── attachments/
├── recovery/
├── trash/
└── settings.json
```

Some directories and files may be created as they become necessary.

The selected bibliography path is stored in the collection's `settings.json`.

Application-level preferences, including the last-used collection and Recent Collections history, are stored separately under:

```text
~/.config/personal-zettelkasten/preferences.json
```

Your collection files remain ordinary Markdown and associated files, readable independently of My Zettelkasten.

## 10. Running the tests

From the project directory, with the virtual environment activated:

```bash
python -m unittest discover -s tests -v
```

Tkinter GUI smoke tests can also be run on a graphical Linux desktop or using Xvfb:

```bash
xvfb-run -a python tests/gui_smoke.py
```

Install `xvfb` if necessary.

Automated tests do not replace manual testing, particularly when using important collections or synchronised folders.

## Common problems

**`No module named tkinter`**

Install Tkinter:

```bash
sudo apt install python3-tk
```

**`No module named zettelkasten`**

Activate your virtual environment and reinstall the application from the project directory:

```bash
source .venv/bin/activate
python -m pip install -e .
```

**`python: command not found`**

Use `python3` to create the virtual environment, then activate it. The virtual environment provides the `python` command.

**No graphical display / `$DISPLAY` missing**

Launch the application from a graphical desktop session. Automated GUI tests can use Xvfb.

**The application reports an older version**

Refresh the installed package metadata:

```bash
python -m pip install -e .
python -m zettelkasten --version
```

If using a Linux Mint menu launcher, remember that it may use a separate virtual environment from your development installation.

**A Dropbox collection cannot be opened**

Confirm that Dropbox is running, the collection directory is accessible, and the folder contains `notes/`.

The application will not automatically recreate a missing collection.

**Empty bibliography or missing Zotero references**

Follow the [Zotero setup guide](ZOTERO_SETUP.md). The bundled sample contains only fictional references.

## Backups and data safety

**Do not store your only copy of valuable notes in the application source directory or a disposable test collection.**

Keep independent backups of the entire collection, including notes, attachments, settings, and recovery files.

Dropbox or another synchronisation service is not a substitute for an independent backup.

See [Backup and recovery](BACKUP_AND_RECOVERY.md) for further guidance.