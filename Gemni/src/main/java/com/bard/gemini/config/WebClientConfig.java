package com.bard.gemini.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    private final static String GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyA7i-CgzUuKTZYKIh65wJ-6VwSByNZlutU";

    @Bean
    public WebClient getWebClientBuilder() {
        return WebClient.builder()
                .baseUrl(GEMINI_URL)
                .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
                .build();
    }
}
