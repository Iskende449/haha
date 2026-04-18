import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self) -> None:
        self._gemini_model = settings.GEMINI_MODEL

    async def _generate(self, prompt: str) -> str:
        if not settings.GEMINI_API_KEY:
            logger.warning('GEMINI_API_KEY is not configured, using local fallback text')
            return ''

        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(self._gemini_model)
            response = model.generate_content(prompt)
            text = (response.text or '').strip()
            return text
        except Exception as exc:  # noqa: BLE001
            logger.exception('Gemini generation failed: %s', exc)
            return ''

    async def generate_nomadic_blessing(self, kyrgyz_month: str, destination_name: str) -> str:
        prompt = (
            'You are a wise nomadic elder from Kyrgyz oral tradition. '
            f'Write exactly 2 sentences as a blessing for a traveler going to {destination_name}. '
            f'Include the spirit of the current month {kyrgyz_month}. Keep it poetic and warm.'
        )
        text = await self._generate(prompt)
        if text:
            return text
        return (
            f'In the month of {kyrgyz_month}, may your road to {destination_name} be protected by the winds of the steppe. '
            'May your heart stay humble, and may the wisdom of your ancestors guide each step.'
        )

    async def generate_legend_quest(self, destination_name: str, destination_description: str | None) -> str:
        prompt = (
            'Create one short riddle (2-3 lines) called a Legend Quest for a heritage traveler. '
            f'Location: {destination_name}. Context: {destination_description or "sacred place"}. '
            'The riddle should hint at the history and be solvable on-site.'
        )
        text = await self._generate(prompt)
        if text:
            return text
        return (
            f'Legend Quest: I keep silent stories carved by hands older than empires at {destination_name}. '
            'What listens without ears, yet speaks when sunlight touches stone?'
        )

    async def generate_legend_quest_with_answer(
        self,
        destination_name: str,
        destination_description: str | None,
    ) -> tuple[str, str]:
        prompt = (
            'Create a heritage mini-riddle and expected answer in this exact format: '
            'RIDDLE: <text>\\nANSWER: <short answer>. '
            f'Location: {destination_name}. Context: {destination_description or "sacred place"}.'
        )
        text = await self._generate(prompt)
        if text and 'ANSWER:' in text:
            parts = text.split('ANSWER:', maxsplit=1)
            riddle = parts[0].replace('RIDDLE:', '').strip()
            answer = parts[1].strip().splitlines()[0].strip().lower()
            if riddle and answer:
                return riddle, answer

        fallback_answer = destination_name.split()[0].strip('.,!?').lower()
        fallback_riddle = (
            f'Legend Quest: Name the first sacred word of this destination - "{destination_name}".'
        )
        return fallback_riddle, fallback_answer


ai_service = AIService()
