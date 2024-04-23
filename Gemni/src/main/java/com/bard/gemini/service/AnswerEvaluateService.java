package com.bard.gemini.service;

import com.bard.gemini.exception.ClientErrorHandler;
import com.bard.gemini.model.answerCheck.QuestionAnswerSet;
import com.bard.gemini.model.questionGen.Content;
import com.bard.gemini.model.questionGen.Part;
import com.bard.gemini.model.questionGen.RequestData;
import com.bard.gemini.model.questionGen.ResponseData;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.List;

@Service
@Slf4j
public class AnswerEvaluateService {

    @Autowired
    private WebClient webClient;

    private final static String PROMPT_STRING = "For each QuestionAnswer evaluate the provided 'answer' with the 'question' and update the 'rating' as per the correctness ranging from 0 to 'maxRating' also if the 'answer' is false or not good update the 'suggestedAnswer' with right answer and return updated String as response : ";

    public ResponseData evaluateAnswer(QuestionAnswerSet questionAnswerSet) {

        final String query = PROMPT_STRING + questionAnswerSet.getQuestionAnswersSet().toString();

        final RequestData requestData = RequestData.builder()
                .contents(List.of(new Content(List.of(new Part(query)), null)))
                .build();

        ResponseData responseData = webClient
                .post()
                .body(Mono.just(requestData), RequestData.class)
                .retrieve()
                .onStatus(HttpStatusCode::isError, ClientErrorHandler::handleErrorResponse)
                .bodyToMono(ResponseData.class)
                .block();

        return responseData;

    }
}
