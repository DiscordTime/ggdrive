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
python -m pip install --upgrade -r requirements.txt
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

1. Upload
```sh
gdrive upload <file-to-upload>
```

2. Download
```sh
gdrive download <fileId-to-download>
```

3. List
```sh
gdrive list
```

The first time you're executing this, a Google page will open and ask for your account so it can integrate with your Google Drive account and then it will ask if you give permission to the app. Once you agree, you're all set.