package utils

import (
    "fmt"
)

const _isDebug = true

type Logger interface {
    LogD(string, ...interface{})
}

type DefaultLogger struct {}

func (logger DefaultLogger) LogD(tag string, msg ...interface{}) {
    if _isDebug {
        fmt.Printf("[%s] %s\n", tag, msg)
    }
}
