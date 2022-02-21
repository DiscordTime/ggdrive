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
    err := DownloadFile("1C71utWp3sOCx5yj-aLsXF3RR0dCaJ7ne")
    if err != nil {
        log.Fatalf("Error while downloading file. %v", err)
    }
}
