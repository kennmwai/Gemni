package com.bard.gemini.controller;

import com.bard.gemini.model.questionGen.Question;
import com.bard.gemini.model.answerCheck.QuestionAnswerSet;
import com.bard.gemini.service.AnswerEvaluateService;
import com.bard.gemini.service.QuestionGenService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.lang.NonNull;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class QuestionGenController {

    @Autowired
    private QuestionGenService questionGenService;

    @Autowired
    private AnswerEvaluateService answerEvaluateService;

    @PostMapping("/generateQuestion")
    public ResponseEntity<?> generateQuestion(@RequestBody @NonNull Question inputQuestion) {
        return ResponseEntity.ok(questionGenService.generateQuestions(inputQuestion));
    }

    @PostMapping("/checkCorrectness")
    public ResponseEntity<?> checkTheCorrectness(@RequestBody @NonNull QuestionAnswerSet questionAnswerSet) {
        return ResponseEntity.ok(answerEvaluateService.evaluateAnswer(questionAnswerSet));
    }

}
