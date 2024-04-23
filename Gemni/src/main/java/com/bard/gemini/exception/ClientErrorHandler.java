package com.bard.gemini.exception;

import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

public class ClientErrorHandler {
    public static Mono<? extends Throwable> handleErrorResponse(ClientResponse clientResponse) {
        return clientResponse.bodyToMono(String.class)
                .flatMap(errorBody -> Mono.error(new WebClientResponseException(
                        clientResponse.statusCode().value(),
                        clientResponse.statusCode().toString(),
                        clientResponse.headers().asHttpHeaders(),
                        errorBody.getBytes(),
                        null
                )));
    }
}
