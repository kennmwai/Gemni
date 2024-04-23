package com.bard.gemini.exception;

public class NoRecordFoundException extends RuntimeException {

    public NoRecordFoundException() {}

    public NoRecordFoundException(String message) {
        super(message);
    }

    public NoRecordFoundException(String message, Throwable cause) {
        super(message, cause);
    }
}
