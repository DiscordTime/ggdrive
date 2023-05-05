package main

import (
    "context"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "log"
    "net/http"
    "os"
    "ggdrive/utils"

    "golang.org/x/oauth2"
    "golang.org/x/oauth2/google"
    "google.golang.org/api/drive/v3"
    "google.golang.org/api/option"
)

type GSvc interface {
    GetFileName(string) (string, error)
    ListFiles(int) (*drive.FileList, error)
    DownloadFile(context.Context, string) (*drive.File, error)
    UploadFile(context.Context, string) error
}

type GdriveService struct {
    logger utils.Logger
    srv *drive.Service
}

func NewGdriveService(ctx context.Context, logger utils.Logger) *GdriveService {
    // Not ideal, but it's fine for now
    srv, err := authenticate(ctx)
    if (err != nil) {
        return nil
    }
    
    return &GdriveService {
        logger: logger,
        srv: srv,
    }
}

func getFileMetaData(srv *drive.Service, id string) (*drive.File, error) {
    fmt.Println("getFileMetaData called")

    file,err := srv.Files.Get(id).Fields("id", "name", "size").Do()
    if err != nil {
        fmt.Printf("Could not get file metadata for id %s\n", id)
        return nil, err
    }
    fmt.Println("filename:", file.Name)
    return file, nil
}

func (g GdriveService) DownloadFile(ctx context.Context, fileId string) error {
    filename,err := g.GetFileName(fileId)
    if err != nil {
        return err
    }

    fmt.Println("Downloading file:", filename)

    res, err := g.srv.Files.Get(fileId).Context(ctx).Download()
    fmt.Println(res)
    if err != nil {
        return err
    }
    err = utils.ToFile(res.Body, filename)
    return err
}

func (g GdriveService) ListFiles(pageSize int) (*drive.FileList, error) {
    return g.srv.Files.List().PageSize(int64(pageSize)).Fields("nextPageToken, files(id, name)").Do()
}

func (g GdriveService) GetFileName(id string) (string, error) {
    file,err := getFileMetaData(g.srv, id)
    if err != nil {
        fmt.Println("Could not get filename.", err)
        return "",err
    }
    return file.Name, nil
}

func (g GdriveService) UploadFile(ctx context.Context, filename string) error {
    contentType, err := utils.GetMimeType(filename)
    if err != nil {
        g.logger.LogD("GDriveRepository", "Could not get mimetype of file: ", filename)
        return err
    }
    g.logger.LogD("GDriveRepository", "ContentType:", contentType)

    file, err := utils.GetFile(filename)
    if err != nil {
        return err
    }

    fileInfo, err := file.Stat()
    if err != nil {
        return err
    }
    defer file.Close()
 
    f := &drive.File{Name: filename, MimeType: contentType}
    progressFunction := func(now, size int64) {
        fmt.Printf("%d, %d\r", now, size)
    }

    res, err := g.srv.Files.Create(f).
        ProgressUpdater(progressFunction).
        ResumableMedia(ctx, file, fileInfo.Size(), contentType).
        Do()

    if err != nil {
        fmt.Println("Couldn't upload file")
        return err
    }
    fmt.Printf("Uploaded file: %s, id: %s\n", res.Name, res.Id)
    return nil
}

func authenticate(ctx context.Context) (*drive.Service, error) {
    b, err := ioutil.ReadFile("credentials.json")
    if err != nil {
        return nil, err
    }

    config, err := google.ConfigFromJSON(b, drive.DriveFileScope)
    if err != nil {
        //fmt.Println("Unable to parse client secret file to config: ", err)
        return nil, err
    }
    client := getClient(ctx, config)
    srv,err := drive.NewService(ctx, option.WithHTTPClient(client)) 
    if err != nil {
        return nil, err
        //fmt.Println("Error while authenticating")
    }

    return srv, nil
}

// Retrieve a token, saves the token, then returns the generated client.
func getClient(ctx context.Context, config *oauth2.Config) *http.Client {
    // The file token.json stores the user's access and refresh tokens, and is
    // created automatically when the authorization flow completes for the first
    // time.
    tokFile := "token.json"
    tok, err := tokenFromFile(tokFile)
    if err != nil {
        tok = getTokenFromWeb(config)
        saveToken(tokFile, tok)
    }
    return config.Client(ctx, tok)
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

