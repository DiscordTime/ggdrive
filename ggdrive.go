package main

import (
    "ggdrive/utils" //Consider changing module name to github.com/discordtime/ggdrive
)

func main() {

    logger := utils.DefaultLogger{}
    driveRepo := NewDriveRepository(logger)

    logger.LogD("Main", "Starting...")
    driveRepo.UploadFile("test.txt")
    //fmt.Println("Starting...")
    //err := DownloadFile("1C71utWp3sOCx5yj-aLsXF3RR0dCaJ7ne")
    //if err != nil {
    //    log.Fatalf("Error while downloading file. %v", err)
    //}
}
