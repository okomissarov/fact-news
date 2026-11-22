# Fact News evaluation benchmark

The 20 questions in `questions.json` are a **test plan**, not 20 completed answers.

## Evaluation rubric (score 0–2 each)
- **Correctness:** 0 unsupported/wrong; 1 partially grounded; 2 verified against retrieved data.
- **Provenance:** 0 missing; 1 dataset URL only; 2 exact underlying record + timestamp.
- **Coverage:** 0 cannot answer; 1 partial; 2 fully answers required scope.
- **Freshness:** 0 date missing/stale; 1 date available but lag unknown; 2 event/reporting dates and known lag identified.
- **Latency:** record observed wall-clock seconds (do not award a score without measurement).

Store observed results separately in `results/` as JSON and never mark a question complete based on documentation alone. For a cross-source question, confirm whether secondary reporting has actually been checked against official records. Separate API connectivity from end-to-end question-answer performance.

## Current implementation scope
The CLI implements bounded examples: recent Federal Register rows through DataDawn, the USAspending agency reference list, and GDELT's article discovery search. More complex benchmark questions are deliberately marked `not_implemented`. There is no LLM reasoning loop yet; these functions are the beginnings of its tool interface.
