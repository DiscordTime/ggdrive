<p align="center">
    <a href="https://github.com/DiscordTime/ggdrive/actions/workflows/main.yml">
        <img alt="CI" src="https://github.com/DiscordTime/ggdrive/actions/workflows/main.yml/badge.svg" /></a>
    <a href="https://www.python.org/">
        <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/ggdrive" /></a>
    <a href="#">
        <img alt="Code size" src="https://img.shields.io/github/languages/code-size/DiscordTime/ggdrive" /></a>
    <a href="https://github.com/DiscordTime/ggdrive/blob/master/LICENSE">
        <img alt="License" src="https://img.shields.io/pypi/l/ggdrive" /></a>
    <a href="https://pypi.org/project/ggdrive/">
        <img alt="Version" src="https://img.shields.io/pypi/v/ggdrive" /></a>
</p>

# ggdrive

A command-line script for Google Drive, for downloading and uploading files directly from the terminal.

- [Pre-requisites](#pre-requisites)
- [Installation](#installation)
- [Usage](#usage)

## Pre-requisites

### Important note: This project requires Google API credentials. That credential file enables the use of Google APIs by this application, and allows the user to login and allow (or deny) the application to access the user's Google Drive files. At this moment, we're not providing the credentials.json needed for this to work, so if you want to use this code, you need to go to [Google's Developer Console](https://console.developers.google.com/), create a project, and create the OAuth credentials for it, allowing for scopes "drive" and "drive.metadata". You can download the credentials.json and use it here.

After downloading your `credentials.json`, go to to your home folder, create a directory called `.gdrive`, and put your `credentials.json` file in there.

The first time you're executing this, a Google page will open and ask for your account, so it can integrate with your Google Drive account, and then it will ask if you give permission to the app. Once you agree, you're all set.

## Installation

### Install through pip (recommended)

```shell
python3 -m pip install ggdrive
```

That's it! You can advance to [Usage](#usage)

### ... Or install manually

This project requires:

1. Python 3.6 or greater.
2. Google Client Library

#### 1. Clone this repository

 ```sh
 git clone git@github.com:DiscordTime/ggdrive.git
 ```
 or
 ```sh
 git clone https://github.com/DiscordTime/ggdrive.git
 ```

#### 2. Install dependencies

We created a `requirements.txt` where you can execute the following to install the needed libs:

```sh
pip install --upgrade -r requirements.txt
```
or
```sh
python3 -m pip install --upgrade -r requirements.txt
```

#### 3. If the script gdrive doesn't have execution permission, give it to it.

 ```sh
 chmod +x gdrive
 ```

#### 4. Add to PATH environment variable (optional, recommended)

You can add this repo folder to you path, so you can execute gdrive from anywhere on your terminal. Open your `.bashrc` or similar and add one of the following options:

 ```sh
 export PATH=$PATH:'<path-to-repo-folder>'
 ```
or
 ```sh
 alias gdrive='<path-to-repo-folder>/gdrive
 ```

## Usage

Available functions:

### 1. Upload

```sh
gdrive upload --help
```

```sh
gdrive upload <file-to-upload>
```

### 2. Download
```sh
gdrive download --help
```

You can download a file passing either the ***id***, or the ***name*** of your file
```sh
gdrive download <(fileId/filename)-to-download>
```

To explicitly download via the ***id***, use one of the following:

```sh
gdrive download -i <id-of-file-to-download>
gdrive download --id <id-of-file-to-download>
```

To download a file via its name, use one of the following:
```sh
gdrive download -n <name-of-file-to-download>
gdrive download --name <name-of-file-to-download>
```

If you're sure that the file that you want to download is the last one that was modified, just use one of the following:
```sh
gdrive download -l
gdrive download --last
```

If the file is a compressed one, you can try extracting it as soon as it finished downloading by using the ***extract*** option (This option is to be used in combination with one of the above):

```sh
gdrive download -le
gdrive download -ei <id-of-file-to-download>
gdrive download -en <name-of-file-to-download>
gdrive download --last --extract
```

**NOTE**

The ***extract*** function needs some extra programs to execute. We implement a mechanism that tries to guess the extension of the file you're downloading and use the program you define to extract it. So, the first time you try to download a file of a certain type, when it's time to extract the file, our program will ask you which program you want to choose. After that, if you download a file with this same extension, it will extract it automatically (if you added the ***--extract*** option).

Those configurations are located with your other files that we need in the *.gdrive* in your *HOME* directory. The file is called ***data_config.json***

Sample
```json
{
  "configs": [
    {
      "ext": "application/x-tar",
      "encoding": "gzip",
      "prog": "tar",
      "attrs": "xzvf"
    },
    {
      "ext": null,
      "encoding": "gzip",
      "prog": "gunzip",
      "attrs": null
    },
    {
      "ext": "application/x-tar",
      "encoding": null,
      "prog": "tar",
      "attrs": "xvf"
    }
  ]
}
```

### 3. List
```sh
gdrive list
```

```sh
gdrive list --help
```
