import openai
import os

def create_openai_client(api_key: str):
    """
    Configure OpenAI using the provided API key and return a client object.
    Prefers the new openai.OpenAI client if available, otherwise sets openai.api_key
    and returns the openai module.
    """
    if not api_key:
        raise ValueError("API key must be provided")

    if hasattr(openai, "OpenAI"):
        return openai.OpenAI(api_key=api_key)
    openai.api_key = api_key
    return openai

def prompt_ai(prompt: str, client: openai.OpenAI, model: str) -> str:
    """
    Send a prompt to the OpenAI API and return the response text.

    Args:
        prompt: The prompt text to send to the AI.
        client: The OpenAI client to use for the request.

    Returns:
        The response text from the AI.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def generate_recommendations(available_items, user_profile) -> str:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = create_openai_client(openai_api_key)
    model = "gpt-4"
    prompt = f"""
            You are a fashion recommendation engine talking directly to the end user. Do not use the user's name or username, only use "you" instead. 
            
            Given the following user profile and available clothing items, generate a list of personalized clothing recommendations.
            User Bio: 
            {user_profile.bio}
            Style Preferences: 
            {user_profile.style_preferences}
            Favorite Colors: 
            {user_profile.favorite_colors}

            Available Items: 
            {available_items}

            Generate personalized clothing recommendations based on the user's profile and preferences.
        """
    try:
        recommendations = prompt_ai(prompt, client, model)
        return recommendations
    except Exception as e:
        print("Error generating recommendations:", e)
        return "Error generating recommendations."
