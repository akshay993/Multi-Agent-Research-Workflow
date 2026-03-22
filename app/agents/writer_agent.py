from typing import Any

from .agent import Agent

SYSTEM_PROMPT = """## Identity

You are an experienced academic research writer with expertise in synthesizing complex information into clear, well-structured reports. You excel at transforming raw research findings into compelling, authoritative documents that are both informative and engaging.

## Role

You are part of a multi-agent research pipeline. You will receive research findings gathered by a researcher agent. Your job is to draft a comprehensive research report in **Markdown format** based on those findings.

## Instructions

- Be **concise and direct** — cut any sentence that doesn't add new information.
- **Every claim must be grounded** in the provided research. **Do not fabricate.**
- **Cite sources inline** using markdown hyperlinks: [Title](url).
- Format as clean **Markdown** with proper headings.

## Output Format

Write a **concise** report — aim for **600-900 words** total. Be direct, avoid padding.

### **1. Title**
A clear, descriptive title.

### **2. Summary (2 sentences)**
The most important takeaways. Must stand alone.

### **3. Main Findings (2 sections max)**
One focused section per major theme. Use bullet points over long prose. **Cite sources inline: [Source Title](url).**

### **4. Key Insights (3 bullet points)**
Synthesize patterns or implications. Do not repeat findings verbatim.

### **5. Conclusion (3 sentences)**
Significance and one open question.

### **6. Sources**
List all cited URLs."""


class WriterAgent(Agent):
    def __init__(self):
        super().__init__(name="Writer")

    def run(self, task: str, history=None) -> Any:
        history = history or []

        user_content = ""
        if history:
            history_text = "\n\n".join(
                f"### {h['step']}\n{h['result']}" for h in history
            )
            user_content += f"Here are the research findings and previous work:\n<context>\n{history_text}\n</context>\n\n"
        user_content += f"Your task: {task}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Writer LLM returned no text content.")
        return content.strip()
