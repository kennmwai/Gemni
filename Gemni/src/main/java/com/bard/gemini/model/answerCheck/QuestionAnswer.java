package com.bard.gemini.model.answerCheck;

import com.bard.gemini.model.questionGen.Question;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@ToString
@Builder
public class QuestionAnswer {
    private String question;
    private String answer;
    private String suggestedAnswer;
    private int rating;
    private final int maxRating = 10;
    
}
