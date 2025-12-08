"""AI recommendations by prompting chatGPT with items from db"""
import os
import openai


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

def generate_recommendations(available_items, user_profile, user_prompt: str = None) -> str:
    """
    Generate personalized clothing recommendations using AI based on user preferences and prompt.

    Args:
        available_items (list): Items with attributes `id`, `title`, `description`, `tag`.
        user_profile (object): User info with `bio`, `style_preferences`, `favorite_colors`.
        user_prompt (str, optional): Custom user request to guide recommendations.

    Returns:
        str: AI-generated recommendations including 3-6 item IDs in the format
             `RECOMMENDED_ITEMS: [id1, id2, ...]`. Returns an error message if generation fails.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = create_openai_client(openai_api_key)
    model = "gpt-4"

    # Format items with ID, title, description, and tag for the AI
    items_list = []
    for item in available_items:
        # THIS WAS FIXED FOR PYLINT I AM PRETTY SURE I DIDNT SCREW IT UP
        items_list.append(
            f"ID: {item.id} | Title: {item.title} | "
            f"Description: {item.description} | Category: {item.tag}"
        )
        # end pylint fix
    items_formatted = "\n".join(items_list)

    # Build the base prompt with user profile information
    base_prompt = f"""
            You are a fashion recommendation engine talking directly to the end user. Do not use the user's name or username, only use "you" instead. 
            
            User Bio: 
            {user_profile.bio}
            Style Preferences: 
            {user_profile.style_preferences}
            Favorite Colors: 
            {user_profile.favorite_colors}

            Available Items (with IDs): 
            {items_formatted}
        """

    # Add the user's custom prompt if provided
    if user_prompt:
        prompt = base_prompt + f"""
            
            User Request:
            {user_prompt}
            
            Generate personalized clothing recommendations based on the user's profile, preferences, and their specific request above.
            
            IMPORTANT: At the end of your response, list the IDs of recommended items in the following format:
            RECOMMENDED_ITEMS: [id1, id2, id3, ...]
            
            Include 3-6 item IDs that best match the user's request.
        """
    else:
        prompt = base_prompt + """
            
            Generate personalized clothing recommendations based on the user's profile and preferences.
            
            IMPORTANT: At the end of your response, list the IDs of recommended items in the following format:
            RECOMMENDED_ITEMS: [id1, id2, id3, ...]
            
            Include 3-6 item IDs that best match the user's profile.
        """

    try:
        recommendations = prompt_ai(prompt, client, model)
        return recommendations
    except (openai.OpenAIError, ValueError, KeyError) as exc:
        # Log the error for debugging while returning user-friendly message
        print(f"Recommendation generation error: {exc}")
        return "Error generating recommendations."
