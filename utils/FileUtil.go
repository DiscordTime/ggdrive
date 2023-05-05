package utils

import (
	"errors"
	"fmt"
	"io"
	"mime"
	"os"
	"os/exec"
	"strings"
)

func GetFile(filename string) (*os.File, error) {
    fmt.Println("GetFile called")
    file,err := os.Open(filename)
    if err != nil {
        fmt.Println("Cannot open file: ", filename)
        return nil, err
    }
    return file, nil
}

func ReadFile(filename string, bufferSize int) ([]byte, error) {
    fmt.Println("ReadFile called")
    file,err := GetFile(filename)
    if err != nil {
        return nil, err
    }

    buffer := make([]byte, bufferSize)
    _,err = file.Read(buffer)
    if err != nil {
        fmt.Println("Cannot read file: ", filename)
        return nil, err
    }

    defer file.Close()
    return buffer, nil
}

func getMimeTypeFromExtension(filename string) (string, error) {
    mimetype := mime.TypeByExtension(filename)
    if mimetype == "" {
        return "", errors.New("Could not get MimeType from extension")
    }
    return mimetype, nil
}

func getMimeTypeFromOutput(output string) string {
    splited := strings.Split(output, ":")
    splited2 := strings.Split(splited[1], ";")
    return strings.Trim(splited2[0], " ")
}

func GetMimeType(filename string) (string, error) {
    file_cmd := "file"
    bin,err := exec.LookPath(file_cmd)
    if err != nil {
        fmt.Println("Could not find command:", file_cmd)
        return getMimeTypeFromExtension(filename)
    }

    cmd := exec.Command(bin, "-i", filename)
    out, err := cmd.Output()
    if err != nil {
        fmt.Println("Error executing command")
        return "", err
    }
    return getMimeTypeFromOutput(string(out)), nil
}

func ToFile(iocloser io.ReadCloser, filename string) error {
    outFile, err := os.Create(filename)
    if err != nil {
        return err
    }
    defer outFile.Close()
    _, err = io.Copy(outFile, iocloser)
    if err != nil {
        return err
    }

    return nil
}

