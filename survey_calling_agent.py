import logging
import asyncio
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, RoomInputOptions
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import openai, silero, noise_cancellation
from livekit.api import DeleteRoomRequest

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

logger = logging.getLogger("calling-agent")
logger.setLevel(logging.INFO)

csv_file_path = Path(__file__).parent / "survey_data.csv"


class SurveyAgent(Agent):
    def __init__(
        self,
        question="이재명 후보와 홍준표 후보 중 누구를 더 지지하시나요?",
        context=None,
        job_context=None,
    ) -> None:
        self.survey_question = question
        self.context = context or {}
        self.job_context = job_context
        self.survey_answer = None
        self.phone_number = self.context.get("phone_number", "unknown")
        # Adjust for 0-based indexing since row_index from metadata is 1-based
        self.row_index = self.context.get(
            "row_index", 1
        )  # Default to 1 if not provided

        instructions = f"""
            You are conducting a brief phone survey in Korean. Your goal is to ask the following question:
            '{self.survey_question}'
            
            Be polite and professional. Introduce yourself as a survey caller named "Agent Kim", ask the question,
            and thank them for their time. Keep the call brief and focused on getting their answer.
            Don't ask any follow-up questions.
            
            Note: When you have an answer to the question, use the `record_survey_answer` function
            to persist what the user said. You should not use `record_survey_answer`
            unless you're sure that they've answered your question.
        """

        super().__init__(
            instructions=instructions,
            llm=openai.realtime.RealtimeModel(),
            vad=silero.VAD.load(),
        )

    @function_tool(
        name="record_survey_answer",
        description="""
        Save the survey answer to the CSV file and mark the survey status as completed.

        The answer should be short, direct, and without filler phrases.
        Avoid full sentences or politeness markers like "저는", "요", or "아마도".

        Examples:
        - "저는 바이든이요" → "바이든"
        - "기분이 좋아요" → "좋아요"
        - "아마 커피요" → "커피"
        
        Args:
            answer: The cleaned user answer from speech (e.g., a keyword or short phrase).
        """,
    )
    async def record_survey_answer(
        self, context: RunContext, answer: str
    ) -> tuple[None, str]:
        """Record the user's survey answer, update the CSV, and clean up the room."""

        logger.info(
            f"Recording survey answer: {answer} for phone number: {self.phone_number}"
        )

        # Load existing survey data
        df = pd.read_csv(csv_file_path, dtype=str)

        # Ensure row index is valid
        if not (0 <= self.row_index - 1 < len(df)):
            logger.error(f"Invalid row index: {self.row_index}")
            return None, "[Error] Could not update survey data."

        # Update the survey answer and status
        df.at[self.row_index - 1, "Answer"] = answer
        df.at[self.row_index - 1, "Status"] = "Completed"

        # Save changes back to CSV
        df.to_csv(csv_file_path, index=False)
        logger.info(f"Survey data updated successfully at row {self.row_index}")

        # Optionally, wait before closing the room to allow for polite call ending
        await asyncio.sleep(3)

        # Clean up: delete the LiveKit room
        try:
            await self.job_context.api.room.delete_room(
                DeleteRoomRequest(room=self.job_context.room.name)
            )
            logger.info(f"Room {self.job_context.room.name} deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete room: {e}")

        return None, "[Survey complete. Thank you!]"


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    metadata_json = ctx.job.metadata
    logger.info(f"Received metadata: {metadata_json}")

    metadata = json.loads(metadata_json)
    phone_number = metadata.get("phone_number", "unknown")
    row_index = metadata.get("row_index", 1)
    question = metadata.get(
        "question", "이재명 후보와 홍준표 후보 중 누구를 더 지지하시나요?"
    )

    logger.info(
        f"Parsed metadata - phone_number: {phone_number}, row_index: {row_index}, question: {question}"
    )

    context = {"phone_number": phone_number, "row_index": row_index}

    session = AgentSession()
    agent = SurveyAgent(question=question, context=context, job_context=ctx)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="survey-agent"))
