"""
Chat display widget for showing conversation messages.
"""
import re
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from utils.logger import get_logger

# Strip model-emitted role prefixes like "Assistant:", "**Lumen:**", "AI: ", "Lumen\n", or bare "Lumen"
_ROLE_PREFIX_RE = re.compile(
    r'^(?:\*{1,2})?(?:assistant|lumen|ai|model|bot|response)(?:\*{1,2})?(?:[:\-]\s*|\s*\n|\s*$)',
    re.IGNORECASE,
)


class ChatDisplay:
    """Custom widget for displaying chat messages."""

    def __init__(self, parent, bg_color, text_color, user_bg, assistant_bg):
        self.logger = get_logger("ChatDisplay")
        self.bg_color = bg_color
        self.text_color = text_color
        self.user_bg = user_bg
        self.assistant_bg = assistant_bg

        self.widget = ScrolledText(
            parent,
            wrap="word",
            state="normal",
            bg=bg_color,
            fg=text_color,
            insertbackground=text_color,
            font=("SF Mono", 11),
            padx=15,
            pady=15,
        )

        self._configure_tags()

        # Mark name used to anchor the current assistant block for in-place
        # replacement during streaming.  Marks track position reliably even as
        # the widget content grows, unlike the old integer line-number approach.
        self._MARK = "assistant_block_start"

    # ── Tag configuration ──────────────────────────────────────────────────

    def _configure_tags(self):
        w = self.widget

        # Role labels
        w.tag_config(
            "user_header",
            foreground="#89dceb",
            font=("SF Mono", 9, "bold"),
            lmargin1=10,
            spacing1=14,
            spacing3=4,
        )
        w.tag_config(
            "assistant_header",
            foreground="#cba6f7",
            font=("SF Mono", 9, "bold"),
            lmargin1=10,
            spacing1=14,
            spacing3=4,
        )

        # Message bodies
        w.tag_config(
            "user_body",
            foreground=self.text_color,
            lmargin1=10,
            lmargin2=10,
            spacing3=2,
        )
        w.tag_config(
            "assistant_body",
            foreground=self.text_color,
            lmargin1=10,
            lmargin2=10,
            spacing3=2,
        )

        # Subtle divider between messages
        w.tag_config(
            "msg_sep",
            foreground="#313244",
            lmargin1=10,
            spacing1=6,
            spacing3=6,
        )

        # Thought / reasoning section
        w.tag_config(
            "thought_header",
            foreground="#89b4fa",
            font=("SF Mono", 9, "bold"),
            lmargin1=10,
            spacing1=6,
            spacing3=2,
        )
        w.tag_config(
            "thought",
            foreground="#6c7086",
            font=("SF Mono", 10, "italic"),
            lmargin1=20,
            lmargin2=20,
            spacing1=1,
            spacing3=1,
        )
        w.tag_config(
            "thought_sep",
            foreground="#313244",
            lmargin1=10,
            spacing1=4,
            spacing3=8,
        )

        # System notices
        w.tag_config(
            "system",
            foreground="#a6e3a1",
            lmargin1=10,
            spacing1=6,
            spacing3=6,
        )

        # Markdown block-level headers
        w.tag_config(
            "h1",
            foreground="#cba6f7",
            font=("SF Mono", 14, "bold"),
            lmargin1=10,
            lmargin2=10,
            spacing1=10,
            spacing3=4,
        )
        w.tag_config(
            "h2",
            foreground="#89b4fa",
            font=("SF Mono", 12, "bold"),
            lmargin1=10,
            lmargin2=10,
            spacing1=8,
            spacing3=3,
        )
        w.tag_config(
            "h3",
            foreground="#a6adc8",
            font=("SF Mono", 11, "bold"),
            lmargin1=10,
            lmargin2=10,
            spacing1=6,
            spacing3=2,
        )

        # Inline emphasis
        w.tag_config("bold", foreground=self.text_color, font=("SF Mono", 11, "bold"))
        w.tag_config("italic", foreground=self.text_color, font=("SF Mono", 11, "italic"))

        # Code
        w.tag_config(
            "code_block",
            foreground="#a6e3a1",
            background="#181825",
            font=("SF Mono", 10),
            lmargin1=20,
            lmargin2=20,
            spacing1=8,
            spacing3=8,
        )
        w.tag_config(
            "inline_code",
            foreground="#f9e2af",
            background="#313244",
            font=("SF Mono", 10),
        )

        # Lists
        w.tag_config(
            "bullet_marker",
            foreground="#cba6f7",
            font=("SF Mono", 11),
            lmargin1=20,
        )
        w.tag_config(
            "bullet_body",
            foreground=self.text_color,
            lmargin1=34,
            lmargin2=34,
        )

        # Horizontal rule
        w.tag_config(
            "hr",
            foreground="#45475a",
            lmargin1=10,
            spacing1=4,
            spacing3=4,
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def pack(self, **kwargs):
        self.widget.pack(**kwargs)

    def add_message(self, role, content, thought=""):
        """Add a message to the display."""
        self.widget.configure(state="normal")

        if role == "user":
            self.widget.insert("end", "You\n", "user_header")
            self._render_markdown(content.strip(), "user_body")
            self.widget.insert("end", "\n", "user_body")
            self._insert_separator()
        elif role == "assistant":
            # Plant the mark BEFORE inserting so delete("mark", "end") captures
            # the entire block.  Left gravity keeps it pinned to the insertion
            # point even as new characters are added after it.
            self.widget.mark_set(self._MARK, "end")
            self.widget.mark_gravity(self._MARK, "left")
            self._insert_assistant_block(content, thought)
        else:  # system
            self.widget.insert("end", content + "\n\n", "system")

        self.widget.see("end")
        self.widget.configure(state="normal")

    def update_last_message(self, text, thought=""):
        """Replace the last assistant message in-place (used during streaming)."""
        if self._MARK not in self.widget.mark_names():
            return
        self.widget.configure(state="normal")
        # Resolve the mark to an explicit "line.col" string first.
        # Using the mark name directly in delete() can silently no-op on some
        # platforms; an explicit index is always reliable.
        start = self.widget.index(self._MARK)
        if self.widget.compare(start, "<", "end"):
            self.widget.delete(start, "end")
        # Re-anchor mark at the clean tail position.
        self.widget.mark_set(self._MARK, "end")
        self.widget.mark_gravity(self._MARK, "left")
        self._insert_assistant_block(text, thought)
        self.widget.see("end")
        self.widget.configure(state="normal")

    def clear(self):
        """Clear all messages from the display."""
        self.widget.configure(state="normal")
        self.widget.delete("1.0", "end")
        if self._MARK in self.widget.mark_names():
            self.widget.mark_unset(self._MARK)
        self.widget.configure(state="disabled")

    def get_widget(self):
        return self.widget

    # ── Internal rendering ─────────────────────────────────────────────────

    def _insert_assistant_block(self, content, thought=""):
        """Insert optional thought section then the assistant response."""
        if thought:
            self.widget.insert("end", "Thinking\n", "thought_header")
            self.widget.insert("end", thought.strip() + "\n", "thought")
            self.widget.insert("end", "─" * 48 + "\n", "thought_sep")

        self.widget.insert("end", "Lumen\n", "assistant_header")

        # Remove any role prefix the model may have echoed at the start
        clean = _ROLE_PREFIX_RE.sub("", content).strip()
        self._render_markdown(clean, "assistant_body")
        self.widget.insert("end", "\n", "assistant_body")
        self._insert_separator()

    def _insert_separator(self):
        self.widget.insert("end", "─" * 64 + "\n", "msg_sep")

    def _render_markdown(self, content, base_tag):
        """Parse markdown blocks and render each with the appropriate tag."""
        if not content:
            return

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]

            # Fenced code block
            if re.match(r"^\s*```", line):
                code_lines = []
                i += 1
                while i < len(lines) and not re.match(r"^\s*```", lines[i]):
                    code_lines.append(lines[i])
                    i += 1
                if code_lines:
                    self.widget.insert("end", "\n".join(code_lines) + "\n", "code_block")
                i += 1  # skip closing fence
                continue

            # Horizontal rule
            if re.match(r"^[-*_]{3,}\s*$", line) and line.strip():
                self.widget.insert("end", "─" * 48 + "\n", "hr")
                i += 1
                continue

            # ATX headers — render text without the # markers
            h_match = re.match(r"^(#{1,3})\s+(.*)", line)
            if h_match:
                level = len(h_match.group(1))
                self._insert_inline(h_match.group(2).rstrip() + "\n", f"h{level}")
                i += 1
                continue

            # Unordered list item
            b_match = re.match(r"^\s*[*\-+]\s+(.*)", line)
            if b_match:
                self.widget.insert("end", "  •  ", "bullet_marker")
                self._insert_inline(b_match.group(1) + "\n", "bullet_body")
                i += 1
                continue

            # Ordered list item
            n_match = re.match(r"^\s*(\d+)\.\s+(.*)", line)
            if n_match:
                self.widget.insert("end", f"  {n_match.group(1)}.  ", "bullet_marker")
                self._insert_inline(n_match.group(2) + "\n", "bullet_body")
                i += 1
                continue

            # Empty line
            if not line.strip():
                self.widget.insert("end", "\n", base_tag)
                i += 1
                continue

            # Normal line with possible inline formatting
            self._insert_inline(line + "\n", base_tag)
            i += 1

    def _insert_inline(self, text, base_tag):
        """Split on **bold**, *italic*, `code` markers and insert each span."""
        pattern = re.compile(r"(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`)")
        for part in pattern.split(text):
            if part.startswith("**") and part.endswith("**") and len(part) > 4:
                self.widget.insert("end", part[2:-2], "bold")
            elif part.startswith("*") and part.endswith("*") and len(part) > 2:
                self.widget.insert("end", part[1:-1], "italic")
            elif part.startswith("`") and part.endswith("`") and len(part) > 2:
                self.widget.insert("end", part[1:-1], "inline_code")
            else:
                self.widget.insert("end", part, base_tag)
