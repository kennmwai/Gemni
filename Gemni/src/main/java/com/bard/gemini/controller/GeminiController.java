package com.bard.gemini.controller;

import com.bard.gemini.model.questionGen.Content;
import com.bard.gemini.model.questionGen.Part;
import com.bard.gemini.model.questionGen.Question;
import com.bard.gemini.model.questionGen.RequestData;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.util.Arrays;

@RestController
public class GeminiController {
    @PostMapping("/chat")
    public ResponseEntity<String> chat(@RequestBody Question qn) {
        // Create RestTemplate
        RestTemplate restTemplate = new RestTemplate();
        RequestData req = new RequestData();
        // Define the request URL
        String url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyDnnF_HmF_duRhR4KVOY2mUoFE7dnqoLDM";

        // Define request headers
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        Part p = new Part(qn.getQuestion());
        Content ct = new Content(Arrays.asList(p), null);
        RequestData rr = new RequestData(Arrays.asList(ct));

        // Serialize RequestBody object to JSON string
        ObjectMapper mapper = new ObjectMapper();
        String json = null;
        try {
            json = mapper.writeValueAsString(rr);
        } catch (JsonProcessingException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
        System.out.println("softcoded: " + json);

        HttpEntity<String> requestEntity = new HttpEntity<>(json, headers);

        // Send POST request
        ResponseEntity<String> responseEntity = restTemplate.exchange(url, HttpMethod.POST, requestEntity,
                String.class);

        // Print response
        System.out.println("Response status code: " + responseEntity.getStatusCode());
        System.out.println("Response body: " + responseEntity.getBody());

        return responseEntity;
    }
}
