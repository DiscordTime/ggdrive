package main

import (
    "fmt"
    "log"
)

func prt(contentType string, err error) {
    if err != nil {
        fmt.Println("error", err)
        return
    }
    fmt.Println("contentType:", contentType)
}
func main() {

    fmt.Println("Starting...")
    err := Authenticate()
    if err != nil {
        log.Fatalf("Error while authenticating. %v", err)
    }

    err = UploadFile("test.txt") // Created a test file
    if err != nil {
        log.Fatalf("Error while uploading file. %v", err)
    }
    /*err = DownloadFile("1FgKPrFMi0AuE_dJmvEAS-K-LnsT-GYrV")
    if err != nil {
        log.Fatalf("Error while downloading file. %v", err)
    }*/


/*    ct, err := GetContentType("credentials.json")
    prt(ct,err)
    ct, err = GetContentType("README.md")
    prt(ct,err)
    ct, err = GetContentType("test.txt")
    prt(ct,err)
*/}
