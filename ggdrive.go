package main

import (
	"context"
	"fmt"
	"ggdrive/utils" //Consider changing module name to github.com/discordtime/ggdrive
	"os"
)

func main() {

    logger := utils.DefaultLogger{}



    for i := 0; i < len(os.Args); i++ {
	logger.LogD(os.Args[i])
    }


    ctx := context.Background()
    gSvc := NewGdriveService(ctx, logger)

    if (gSvc == nil) {
	fmt.Println("Exiting")
	return
    }
    driveRepo := NewDriveRepository(gSvc, logger)

    logger.LogD("Main", "Starting...")
    driveRepo.ListFiles(ctx)
    //driveRepo.UploadFile(ctx, "test.txt")
    //fmt.Println("Starting...")
    //err := DownloadFile(ctx, "1C71utWp3sOCx5yj-aLsXF3RR0dCaJ7ne")
    //if err != nil {
    //    log.Fatalf("Error while downloading file. %v", err)
    //}
}
