package com.bard.gemini.exception;

public class InvalidDataException extends RuntimeException {

    public InvalidDataException() {
    }

    public InvalidDataException(String message) {
        super(message);
    }

    public InvalidDataException(String message, Throwable cause) {
        super(message, cause);
    }
}
