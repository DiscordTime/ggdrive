package main

import (
    "context"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "log"
    "net/http"
    "os"
    "ggdrive/utils" //Consider changing module name to github.com/discordtime/ggdrive

    "golang.org/x/oauth2"
    "golang.org/x/oauth2/google"
    "google.golang.org/api/drive/v3"
    "google.golang.org/api/option"
)

// Retrieve a token, saves the token, then returns the generated client.
func getClient(config *oauth2.Config) *http.Client {
    // The file token.json stores the user's access and refresh tokens, and is
    // created automatically when the authorization flow completes for the first
    // time.
    tokFile := "token.json"
    tok, err := tokenFromFile(tokFile)
    if err != nil {
        tok = getTokenFromWeb(config)
        saveToken(tokFile, tok)
    }
    return config.Client(context.Background(), tok)
}

// Request a token from the web, then returns the retrieved token.
func getTokenFromWeb(config *oauth2.Config) *oauth2.Token {
    authURL := config.AuthCodeURL("state-token", oauth2.AccessTypeOffline)
    fmt.Printf("Go to the following link in your browser then type the "+
    "authorization code: \n%v\n", authURL)

    var authCode string
    if _, err := fmt.Scan(&authCode); err != nil {
        log.Fatalf("Unable to read authorization code %v", err)
    }

    tok, err := config.Exchange(context.TODO(), authCode)
    if err != nil {
        log.Fatalf("Unable to retrieve token from web %v", err)
    }
    return tok
}

// Retrieves a token from a local file.
func tokenFromFile(file string) (*oauth2.Token, error) {
    f, err := os.Open(file)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    tok := &oauth2.Token{}
    err = json.NewDecoder(f).Decode(tok)
    return tok, err
}

// Saves a token to a file path.
func saveToken(path string, token *oauth2.Token) {
    fmt.Printf("Saving credential file to: %s\n", path)
    f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
    if err != nil {
        log.Fatalf("Unable to cache oauth token: %v", err)
    }
    defer f.Close()
    json.NewEncoder(f).Encode(token)
}

func ListFiles() error {
    fmt.Println("List files called")
    srv,err := Authenticate()
    if err != nil {
        return err
    }
    r, err := srv.Files.List().PageSize(10).
    Fields("nextPageToken, files(id, name)").Do()
    if err != nil {
        fmt.Println("Unable to retrieve files")
        return err
    }
    fmt.Println("Files:")
    if len(r.Files) == 0 {
        fmt.Println("No files found.")
    } else {
        for _, i := range r.Files {
            fmt.Printf("%s (%s)\n", i.Name, i.Id)
        }
    }
    return nil
}

func DownloadFile(fileId string) error {
    fmt.Println("DownloadFile called")
    srv,err := Authenticate()
    if err != nil {
        return err
    }
    filename,err := getFileName(srv, fileId)
    if err != nil {
        return err
    }

    fmt.Println("Downloading file:", filename)

    //fileSrv := drive.NewFilesService(srv)
    res, err := srv.Files.Get(fileId).Context(context.Background()).Download()
    fmt.Println(res)
    if err != nil {
        return err
    }
    err = utils.ToFile(res.Body, filename)
    if err != nil {
        return err
    }
    return nil
}

func UploadFile(filename string) error {
    fmt.Println("UploadFile called")
    srv,err := Authenticate()
    if err != nil {
        return err
    }
    contentType, err := utils.GetMimeType(filename)
    if err != nil {
        fmt.Println("Could not get mimetype of file")
        return err
    }
    fmt.Println("ContentType:", contentType)
    file,err := utils.GetFile(filename)
    if err != nil {
        return err
    }
    fileInfo,err := file.Stat()
    if err != nil {
        return err
    }
    defer file.Close()
 
    f := &drive.File{Name: filename, MimeType: contentType}
    progressFunction := func(now, size int64) {
        fmt.Printf("%d, %d\r", now, size)
    }
    res,err := srv.Files.Create(f).
        ProgressUpdater(progressFunction).
        ResumableMedia(context.Background(), file, fileInfo.Size(), contentType).
        Do()
    if err != nil {
        fmt.Println("Couldn't upload file")
        return err
    }
    fmt.Printf("Uploaded file: %s, id: %s\n", res.Name, res.Id)
    return nil
}

func getFileMetaData(srv *drive.Service, id string) (*drive.File, error) {
    fmt.Println("getFileMetaData called")
    //fields := "id, name, size"
    file,err := srv.Files.Get(id).Fields("id", "name", "size").Do()
    if err != nil {
        return nil, err
    }
    fmt.Println("filename:", file.Name)
    return file, nil
}

func getFileName(srv *drive.Service, id string) (string,error) {
    file,err := getFileMetaData(srv, id)
    if err != nil {
        fmt.Println("Could not get filename.", err)
        return "",err
    }
    return file.Name, nil
}

func Authenticate() (*drive.Service, error) { 
    ctx := context.Background()
    b, err := ioutil.ReadFile("credentials.json")
    if err != nil {
        fmt.Println("Unable to read client secret file: ", err)
        return nil, err
    }

    config, err := google.ConfigFromJSON(b, drive.DriveFileScope)
    if err != nil {
        fmt.Println("Unable to parse client secret file to config: ", err)
        return nil, err
    }
    client := getClient(config)
    srv,err := drive.NewService(ctx, option.WithHTTPClient(client)) 
    if err != nil {
        fmt.Println("Error while authenticating")
    }
    return srv,err
}
