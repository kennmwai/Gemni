package com.bard.gemini.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
public class APIExceptionHandler {

    @ExceptionHandler(value = {InvalidDataException.class})
    public ResponseEntity<?> handleInvalidDataException(InvalidDataException ex) {
        return new ResponseEntity<>(new ErrorData(ex.getMessage(), ex, HttpStatus.BAD_REQUEST), HttpStatus.BAD_REQUEST);
    }
}
