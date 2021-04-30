# gdrive-manager
A simple integration with Google Drive so we can upload and download files directly from the terminal.

## **How to use**

### **1. Pre-requisites**

### Important note: It's important to say that this needs credentials that would indentify your application. That's what gives the information to the user so they can authorize or not your application to upload and download. At this moment, we're not providing the credentials.json needed for this to work, so if you want to use this code, you need to go to [Google's Developer Console](https://console.developers.google.com/), create a project and create the OAuth credentials for it. You can download the credentials.json and use it here.

1. Python 3
2. Google Client Library

We created a `requirements.txt` where you can execute the following to install the needed libs:

```sh
pip install --upgrade -r requirements.txt
```
or
```sh
python3 -m pip install --upgrade -r requirements.txt
```

### **2. Configuring**

1. Clone this repo

 ```sh
 git clone git@github.com:DiscordTime/gdrive-manager.git
 ```
 or
 ```sh
 git clone https://github.com/DiscordTime/gdrive-manager.git
 ```

 2. If the script gdrive doesn't have execute permission, give it to it.

 ```sh
 chmod +x gdrive
 ```

 3. Go to your home folder and create a directory called `.gdrive` and put your `credentials.json` file in there.

 4. You can add this repo folder to you path so you can execute gdrive from anywhere on your terminal. Open your `.bashrc` or similars and add one of the following options:

 ```sh
 export PATH=$PATH:'<path-to-repo-folder>'
 ```
or
 ```sh
 alias gdrive='<path-to-repo-folder>/gdrive
 ```

### **3. Usage**

Available functions:

#### 1. Upload

```sh
gdrive upload --help
```

```sh
gdrive upload <file-to-upload>
```

#### 2. Download
```sh
gdrive download --help
```

You can download a file passing either the ***id*** or the ***name*** of your file
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

Important note: The ***extract*** function needs some extra programs to execute. By default, we pré-defined some of this programs and options. This is thefined in the ***extractor.py*** file and can be changed directly there, if you want it. We wish to improve and give users the possibility to choose which program they want to use to extract a file.

#### 3. List
```sh
gdrive list
```

```sh
gdrive list --help
```

The first time you're executing this, a Google page will open and ask for your account so it can integrate with your Google Drive account and then it will ask if you give permission to the app. Once you agree, you're all set.
