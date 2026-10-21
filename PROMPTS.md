# AI tools and prompt record

## Tool and model

- Tool: OpenAI Codex coding agent
- Model: GPT-5.6

## Prompts, in chronological order

1. `Project: Boston Bioprocess — Take-Home Software Engineer Assessment` followed by the complete assessment implementation brief supplied in this Codex session. The request specified inspection before implementation; FastAPI/Pydantic, SQLite/SQLAlchemy, Angular/TypeScript/CSS, scikit-learn, and pytest; required scheduling and closed-loop-control behaviours; staged terminal commands; documentation; private-repository/hosting/recording requirements; and a request to inspect the data kit README and CSVs.
2. `attached assement pdf`
3. `done next?`
4. `ERROR: Operation cancelled by user`
5. `i will attach screenshot still some modifications needed because its look some ui defect the visuallly not appearing correctly the plots`
6. `what is the expecation for live dashboard from asessment pdf is live simulation and check accordingly because still dashboard looks incomplete and letters and the line collapsing`
7. `so what is this queue command 5? ... what are these when we do command post call?`
8. `no need of final ux so did we complete assesment most of the parts or still any thing there to proceed?`
9. `yeah please implement closed loop automationand  proceed to implement`

## Changes made after generated output

- Reviewed all generated code and ran backend tests and Angular production builds after implementation changes.
- Replaced placeholder pH and temperature simulation values with values replayed from the supplied run.
- Corrected dashboard chart scaling to use full replay history and filtered stale forecast overlays.
- Added readable axes, forecast styling, command markers, schedule violation presentation, and a simulator reset endpoint for repeatable demonstrations.
- Added README, ignore rules, and this record.

## Mistakes identified and corrected

- Early chart code combined a short reading window with an old forecast, compressing live traces; corrected by returning replay history and filtering stale predictions.
- Initial pH/temperature simulator values were fixed constants; corrected to replay supplied CSV values.
- The controller initially required a manual endpoint call; it now runs automatically every five simulated minutes after enough history exists.


