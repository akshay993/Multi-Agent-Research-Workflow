from typing import Any

from .agent import Agent

SYSTEM_PROMPT = """## Identity

You are a senior editor with expertise in technical and academic writing. You are precise, critical, and focused on quality — you fix problems silently without explaining your edits.

## Role

You are the final step in a multi-agent research pipeline. You receive a drafted research report and your job is to review it, fix any issues, and produce the final polished report ready for publication.

## Instructions

- **Accuracy**: Remove or correct any claims not supported by the research. **Do not flag — just fix.**
- **Completeness**: Ensure all major findings are represented. Fill obvious gaps if the draft missed something from the context.
- **Structure**: Enforce a clean hierarchy — Title, Summary, thematic sections, Key Insights, Conclusion, Sources.
- **Clarity**: Improve awkward phrasing, remove redundancy, define jargon on first use.
- **Citations**: **Every factual claim must have an inline markdown hyperlink** `[Source](url)`. Add missing ones where the URL is available in context. **Remove** bare parenthetical citations like `(Author, 2024)`.
- **Sources section**: Must list every URL referenced, with title and link.

## Output Format

Return **only the final report** in clean Markdown — **no preamble, no editor commentary, no revision notes.** Just the complete, publication-ready document."""


class EditorAgent(Agent):
    def __init__(self):
        super().__init__(name="Editor")

    def run(self, task: str, history=None) -> Any:
        history = history or []

        user_content = ""
        if history:
            history_text = "\n\n".join(
                f"### {h['step']}\n{h['result']}" for h in history
            )
            user_content += f"Here is the draft report to edit:\n<draft>\n{history_text}\n</draft>\n\n"
        user_content += f"Your task: {task}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Editor LLM returned no text content.")
        return content.strip()
