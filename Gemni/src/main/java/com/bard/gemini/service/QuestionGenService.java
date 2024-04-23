package com.bard.gemini.service;

import com.bard.gemini.exception.ClientErrorHandler;
import com.bard.gemini.exception.InvalidDataException;
import com.bard.gemini.model.questionGen.Content;
import com.bard.gemini.model.questionGen.Part;
import com.bard.gemini.model.questionGen.Question;
import com.bard.gemini.model.questionGen.RequestData;
import com.bard.gemini.model.questionGen.ResponseData;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Service;
import org.springframework.util.ObjectUtils;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.List;

@Service
@Slf4j
public class QuestionGenService {

    @Autowired
    private WebClient webClient;

    public ResponseData generateQuestions(Question inputQuestion) {

        if (ObjectUtils.isEmpty(inputQuestion) || inputQuestion.getQuestion().isEmpty()) {
            log.error("Empty/Invalid question provided");
            throw new InvalidDataException("Empty/Invalid question provided");
        }

        final RequestData requestData = RequestData.builder()
                .contents(List.of(new Content(List.of(new Part(inputQuestion.getQuestion())), null)))
                .build();


        ResponseData responseData = webClient
                .post()
                .body(Mono.just(requestData), RequestData.class)
                .retrieve()
                .onStatus(HttpStatusCode::isError, ClientErrorHandler::handleErrorResponse)
                .bodyToMono(ResponseData.class)
                .block();

        log.info("RESPONSE : {}", responseData);

        return responseData;
    }
}
