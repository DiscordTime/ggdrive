package main

import (
    "fmt"
    "io"
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

func getContentTypeFromOutput(output string) string {
    splited := strings.Split(output, ":")
    splited2 := strings.Split(splited[1], ";")
    return strings.Trim(splited2[0], " ")
}

func GetContentType(filename string) (string, error) {
    cmd := exec.Command("file", "-i", filename)
    out, err := cmd.Output()
    if err != nil {
        fmt.Println("Error executing command")
        return "", err
    }
    return getContentTypeFromOutput(string(out)), nil
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

