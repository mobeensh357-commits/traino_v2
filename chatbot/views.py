import json
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from groq import Groq
from .models import FAQ, ChatHistory

logger = logging.getLogger(__name__)

# Static fallback responses (used only if everything fails)
FALLBACK_RESPONSE = "I'm not sure about that. Please visit our Help Center or contact support."

@csrf_exempt
@require_POST
def ask_chatbot(request):
    # 1. Parse message
    try:
        body = json.loads(request.body)
        user_message = body.get('message', '').strip()
    except:
        return JsonResponse({'answer': 'Invalid request.'}, status=400)

    if not user_message:
        return JsonResponse({'answer': 'Please type a message.'})

    # 2. Try FAQ matching first (rule‑based)
    best_faq = None
    best_score = 0
    active_faqs = FAQ.objects.filter(is_active=True).order_by('-priority')
    for faq in active_faqs:
        score = faq.match_score(user_message)
        if score > best_score:
            best_score = score
            best_faq = faq

    # If we have a good match (at least 1 keyword), use it immediately
    if best_faq and best_score >= 1:
        answer = best_faq.answer
        source = 'faq'
    else:
        # 3. No good FAQ match → call Groq AI
        source = 'groq'
        system_prompt = """You are Traino Assistant, a helpful AI for an online training platform.
Answer concisely and helpfully. Brand color is yellow (#F5C518).
If unsure, say so honestly."""

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=300,
            )
            answer = completion.choices[0].message.content.strip()
        except Exception as e:
            logger.exception("Groq API error")
            answer = FALLBACK_RESPONSE
            source = 'fallback'

    # 4. Save to chat history (if model exists)
    try:
        if request.user.is_authenticated:
            user_obj = request.user
            session_id = ''
        else:
            user_obj = None
            if not request.session.session_key:
                request.session.create()
            session_id = request.session.session_key

        ChatHistory.objects.create(
            user=user_obj,
            session_id=session_id,
            message=user_message,
            response=answer,
        )
    except Exception as e:
        logger.warning(f"Could not save chat history: {e}")

    # 5. Return answer
    return JsonResponse({'answer': answer, 'source': source})  # source is optional for debugging