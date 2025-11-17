import os
import github
import openai
import requests

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

def create_github_client(token: str):
    """
    Create and return a GitHub client using the provided token.
    """
    if not token:
        raise ValueError("GitHub token must be provided")
    return github.Github(token)

def get_pull_request_diff(token: str, repo_full_name: str, pr_number: int) -> str:
    """
    Return the unified diff (text) for the given pull request.

    Args:
        token: GitHub personal access token with repo access.
        repo_full_name: Repository full name like "owner/repo".
        pr_number: Pull request number.

    Raises:
        ValueError: if required args are missing.
        RuntimeError: for not found or other non-200 responses.
    """
    if not token:
        raise ValueError("GitHub token must be provided")
    if not repo_full_name:
        raise ValueError("Repository full name must be provided")
    if not pr_number:
        raise ValueError("Pull request number must be provided")


    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.diff",
        "Authorization": f"Bearer {token}",
        "User-Agent": "ai-review-script",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 404:
        raise RuntimeError(f"Pull request {pr_number} or repository {repo_full_name} not found")
    resp.raise_for_status()
    return resp.text

def post_pull_request_comment(token: str, repo_full_name: str, pr_number: int, comment: str) -> str:
    """
    Post a comment to the given pull request and return the comment URL.

    Args:
        token: GitHub personal access token with repo access.
        repo_full_name: Repository full name like "owner/repo".
        pr_number: Pull request number.
        comment: Text body of the comment.

    Returns:
        URL of the created comment.

    Raises:
        ValueError: if required args are missing.
        RuntimeError: on GitHub API errors.
    """
    if not token:
        raise ValueError("GitHub token must be provided")
    if not repo_full_name:
        raise ValueError("Repository full name must be provided")
    if not pr_number:
        raise ValueError("Pull request number must be provided")
    if comment is None or comment == "":
        raise ValueError("Comment text must be provided")

    gh = create_github_client(token)
    try:
        repo = gh.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        created = pr.create_issue_comment(comment)
        return getattr(created, "html_url", None) or getattr(created, "url", None)
    except github.GithubException as e:
        msg = None
        try:
            msg = e.data.get("message")
        except Exception:
            msg = str(e)
        raise RuntimeError(f"GitHub API error posting comment: {msg}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to post comment: {e}") from e

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

def generate_ai_review(openai_client, diff: str, model: str = "gpt-4") -> str:
    """
    Generate an AI review of the given pull request diff using the specified model.

    Args:
        openai_client: Configured OpenAI client.
        diff: Unified diff text of the pull request.
        model: OpenAI model to use for generating the review.

    Returns:
        Generated review text.

    Raises:
        RuntimeError: on OpenAI API errors.
    """
    if not diff:
        raise ValueError("Diff text must be provided")

    # Include the system instruction in the prompt since prompt_ai sends a single user message.
    prompt = (
        "You are an expert code reviewer. Please provide a thorough review of the following pull request diff. "
        "Provide your feedback in this format:\n"
        "- Summary of changes\n"
        "- Key issues found\n"
        "- Security considerations\n"
        "- Performance implications\n"
        "- Usability concerns\n"
        "- Compatibility issues\n"
        "Provide potential fixes or improvements where applicable. Potential fixes and improvements will include code snippets and examples.\n\n"
        f"Pull Request Diff:\n{diff}"
    )

    try:
        return prompt_ai(prompt, openai_client, model)
    except Exception as e:
        raise RuntimeError(f"OpenAI API error generating review: {e}") from e

def main():
    # Example usage
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    REPO_FULL_NAME = os.environ.get("REPO_FULL_NAME")
    PR_NUMBER = int(os.environ.get("PR_NUMBER"))
    MODEL = os.environ.get("MODEL")

    openai_client = create_openai_client(OPENAI_API_KEY)
    diff = get_pull_request_diff(GITHUB_TOKEN, REPO_FULL_NAME, PR_NUMBER)
    review = generate_ai_review(openai_client, diff, MODEL)
    comment_url = post_pull_request_comment(GITHUB_TOKEN, REPO_FULL_NAME, PR_NUMBER, review)
    print(f"Posted AI review comment: {comment_url}")

if __name__ == "__main__":
    main()