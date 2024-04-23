package com.bard.gemini.exception;

public class FailedToProcessException extends RuntimeException {

    public FailedToProcessException() {}

    public FailedToProcessException(String message) {
        super(message);
    }

    public FailedToProcessException(String message, Throwable cause) {
        super(message, cause);
    }
}
