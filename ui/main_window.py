"""
Main window UI and application orchestration.
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import threading
import re

from utils.logger import get_logger
from utils.file_importer import FileImporter
from .chat_display import ChatDisplay
from .parameter_controls import ParameterControls

def _clean_thought(text):
    """Remove model warm-up garbage from extracted thought content.

    The model frequently emits leading junk before its real analysis:
      - Concatenated no-space repetitions  e.g. "LumenLumenLumenLumen"
      - Space-separated repetitions        e.g. "Lumen Lumen Lumen"
      - Residual UI-label words            e.g. a lone "Thinking" or "Lumen"

    Each pass of the while-loop strips one batch of no-space repetitions so
    that consecutive batches (e.g. "LumenLumen...ThinkingThinking...") are all
    removed before returning the real analysis text.
    """
    if not text:
        return text

    # 1. Strip leading no-space word repetitions (e.g. "LumenLumenLumen").
    #    Loop because there may be consecutive batches of different words.
    while True:
        m = re.match(r'^([A-Za-z]{3,15})(?:\1){2,}', text, re.IGNORECASE)
        if m:
            text = text[m.end():]
        else:
            break

    # 2. Collapse space-separated repetitions anywhere (e.g. "Lumen Lumen" → "Lumen").
    text = re.sub(r'\b(\w+)(?:\s+\1\b){2,}', r'\1', text, flags=re.IGNORECASE)

    # 3. Strip any remaining leading role/UI-label words.
    text = re.sub(r'^(?:(?:Lumen|Thinking|Assistant|AI|Bot)\b\s*)+', '', text, flags=re.IGNORECASE)

    return text.strip()


class MainWindow:
    """Main application window and UI orchestrator."""
    
    def __init__(self, root, config, model_manager, context_manager, 
                 message_handler, storage):
        """
        Initialize the main window.
        
        Args:
            root: Tkinter root window
            config: Config instance
            model_manager: ModelManager instance
            context_manager: ContextManager instance
            message_handler: MessageHandler instance
            storage: ConversationStorage instance
        """
        self.root = root
        self.config = config
        self.model_manager = model_manager
        self.context_manager = context_manager
        self.message_handler = message_handler
        self.storage = storage
        self.file_importer = FileImporter()
        
        self.logger = get_logger("MainWindow")
        
        # UI state
        self.is_generating = False
        self.stop_flag = False
        
        # Configure window
        self.root.title("Root")
        self.root.geometry("1000x800")
        
        # Colors
        self.bg_color = "#1e1e2e"
        self.text_color = "#cdd6f4"
        self.input_bg = "#313244"
        self.accent_color = "#cba6f7"
        self.user_bg = "#45475a"
        self.assistant_bg = "#585b70"
        
        self.root.configure(bg=self.bg_color)
        
        # Status variable
        self.status_var = tk.StringVar(value="No model loaded")
        
        # Create UI
        self._create_widgets()
        self._setup_keyboard_shortcuts()
        
        # Add welcome message
        self._show_welcome_message()
    
    def _create_widgets(self):
        """Create all UI widgets."""
        # Top panel with model selector
        self._create_top_panel()
        
        # Second row of buttons
        self._create_button_row()
        
        # Parameter controls
        self.param_controls = ParameterControls(
            self.root, self.bg_color, self.text_color, self.input_bg
        )
        self.param_controls.pack(fill="x", padx=10, pady=5)
        
        # Status bar
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            bg=self.bg_color,
            fg=self.accent_color,
            font=("SF Mono", 10)
        )
        status_bar.pack(side="bottom", fill="x", padx=10, pady=5)
        
        # Chat display
        self.chat_display = ChatDisplay(
            self.root, self.bg_color, self.text_color, 
            self.user_bg, self.assistant_bg
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Input panel
        self._create_input_panel()
    
    def _create_top_panel(self):
        """Create the top panel with model selector and load button."""
        top_frame = tk.Frame(self.root, bg=self.bg_color)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        # Model label
        tk.Label(
            top_frame,
            text="Model:",
            bg=self.bg_color,
            fg=self.text_color,
            font=("SF Mono", 10, "bold")
        ).pack(side="left", padx=(0, 10))
        
        # Model selector
        self.model_selector = ttk.Combobox(
            top_frame,
            values=self.config.get_model_names(),
            state="readonly",
            width=20
        )
        self.model_selector.pack(side="left", padx=(0, 10))
        self.model_selector.bind("<<ComboboxSelected>>", self._on_model_selected)
        
        # Load button
        tk.Button(
            top_frame,
            text="Load Model",
            command=self._load_model,
            bg=self.accent_color,
            fg="#11111b",
            font=("SF Mono", 10, "bold"),
            padx=10
        ).pack(side="left", padx=(0, 10))
        
        # Stop button
        self.stop_button = tk.Button(
            top_frame,
            text="⏹ Stop",
            command=self._stop_generation,
            bg="#f38ba8",
            fg="#11111b",
            font=("SF Mono", 10, "bold"),
            padx=10,
            state="normal"
        )
        self.stop_button.pack(side="left", padx=(0, 10))
        
        # Clear button
        tk.Button(
            top_frame,
            text="Clear Chat",
            command=self._clear_conversation,
            bg="#fab387",
            fg="#11111b",
            font=("SF Mono", 10, "bold"),
            padx=10
        ).pack(side="left", padx=(0, 10))
    
    def _create_button_row(self):
        """Create the second row of buttons."""
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        buttons = [
            ("📊 Stats", self._show_stats, "#a6e3a1"),
            ("💾 Save", self._save_conversation, "#89b4fa"),
            ("📂 Load", self._load_conversation, "#94e2d5"),
            ("⚙️ System", self._edit_system_prompt, "#f9e2af"),
            ("📄 Import", self._import_file, "#f5c2e7"),
            ("📝 Export MD", self._export_markdown, "#b4befe"),
        ]
        
        for text, command, color in buttons:
            tk.Button(
                button_frame,
                text=text,
                command=command,
                bg=color,
                fg="#11111b",
                font=("SF Mono", 9),
                padx=8
            ).pack(side="left", padx=(0, 5))
    
    def _create_input_panel(self):
        """Create the input panel with entry and send button."""
        input_frame = tk.Frame(self.root, bg=self.bg_color)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.user_input = tk.Entry(
            input_frame,
            width=50,
            bg=self.input_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            font=("SF Mono", 12)
        )
        self.user_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", lambda e: self._send_message())
        self.user_input.bind("<Up>", lambda e: self._load_previous_input())
        self.user_input.bind("<Down>", lambda e: self._load_next_input())
        
        tk.Button(
            input_frame,
            text="Send",
            command=self._send_message,
            bg=self.accent_color,
            fg="#11111b",
            font=("SF Mono", 10, "bold"),
            padx=15
        ).pack(side="right")
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.root.bind("<Control-Shift-C>", lambda e: self._clear_conversation())
        self.root.bind("<Control-Shift-S>", lambda e: self._show_stats())
        self.root.bind("<Control-s>", lambda e: self._save_conversation())
        self.root.bind("<Control-o>", lambda e: self._load_conversation())
        self.root.bind("<Escape>", lambda e: self._stop_generation())
    
    def _show_welcome_message(self):
        """Show the welcome message."""
        welcome = """Root is booted! Start by loading a model above ^

Features:
• Streaming responses
• Save/Load conversations
• Adjustable parameters
• System prompt editing
• Keyboard shortcuts (Ctrl+S to save, Ctrl+O to load, Esc to stop)

Please select and load a model to begin."""
        self.chat_display.add_message("system", welcome)
    
    def _on_model_selected(self, event=None):
        """Handle model selection."""
        selected = self.model_selector.get()
        if selected:
            config = self.config.get_model_config(selected)
            ctx = config.get("n_ctx", 4096)
            self.status_var.set(f"Selected: {selected} (ctx: {ctx}) | Click 'Load Model'")
    
    def _load_model(self):
        """Load the selected model."""
        selected = self.model_selector.get()
        if not selected:
            self.status_var.set("Please select a model first")
            return
        
        def on_progress(message):
            self.root.after(0, lambda: self.status_var.set(message))
        
        def on_complete(success, message):
            self.root.after(0, lambda: self.status_var.set(message))
            if success:
                self.root.after(0, lambda: self.chat_display.add_message("system", message))
                # Update context manager with new max context
                ctx_size = self.model_manager.get_context_size()
                self.context_manager.update_max_context(ctx_size)
        
        # Load in background thread
        threading.Thread(
            target=lambda: self.model_manager.load_model(selected, on_progress, on_complete),
            daemon=True
        ).start()
    
    def _send_message(self):
        """Send a user message."""
        if self.is_generating:
            self.chat_display.add_message("system", "⚠️ Please wait or press Stop")
            return
        
        message = self.user_input.get().strip()
        if not message:
            return
        
        # Clear input and display message
        self.user_input.delete(0, "end")
        self.chat_display.add_message("user", message)
        
        # Add to history
        self.message_handler.add_user_message(message)
        
        # Show token count
        tokens = self.model_manager.estimate_tokens(message)
        self.status_var.set(f"📊 Sent {tokens} tokens")
        
        # Check if model is loaded
        if not self.model_manager.is_loaded():
            self.chat_display.add_message("system", "ERROR: Please load a model first!")
            return
        
        # Generate response in background thread
        threading.Thread(target=self._generate_response, daemon=True).start()

    def _parse_thinking(self, text):
        """
        Split reasoning/analysis from the response text.

        Handles both <think>...</think> blocks and <|channel|> token format.

        Returns:
            tuple: (thought_text, response_text)
              - During streaming an in-progress block is returned as thought
                with an empty response until the final response is available.
        """
        # Handle <|channel|> token format used by this model
        if '<|channel|>' in text or '<|start|>' in text:
            return self._parse_channel_response(text)

        # Handle one or more complete <think>...</think> blocks
        pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL)
        thoughts = pattern.findall(text)
        if thoughts:
            thought = '\n\n'.join(_clean_thought(t.strip()) for t in thoughts)
            response = pattern.sub('', text).strip()
            return thought, response

        # Handle an unclosed <think> block (mid-stream)
        open_idx = text.find('<think>')
        if open_idx != -1:
            thought = _clean_thought(text[open_idx + 7:])  # content after <think>
            response = text[:open_idx].strip()  # content before <think>
            return thought, response

        return '', text

    def _parse_channel_response(self, text):
        """
        Parse <|channel|>NAME<|message|>CONTENT format.

        The model emits an 'analysis' channel (internal reasoning) and a
        'final' channel (the actual reply).  Map analysis -> thought and
        final -> response so they render correctly in the UI.
        """
        # Complete analysis block present
        analysis_complete = re.search(
            r'<\|channel\|>analysis<\|message\|>(.*?)<\|end\|>',
            text, re.DOTALL
        )
        final_match = re.search(
            r'<\|channel\|>final<\|message\|>(.*?)(?:<\|end\|>|$)',
            text, re.DOTALL
        )

        if analysis_complete:
            thought = _clean_thought(analysis_complete.group(1).strip())
            response = final_match.group(1).strip() if final_match else ''
            return thought, response

        # Mid-stream: analysis block not yet closed – show as in-progress thought
        analysis_open = re.search(
            r'<\|channel\|>analysis<\|message\|>(.*)',
            text, re.DOTALL
        )
        if analysis_open:
            return _clean_thought(analysis_open.group(1).strip()), ''

        # Fallback: strip all <|token|> markers and return clean text
        cleaned = re.sub(r'<\|[^|]+\|>', '', text).strip()
        return '', cleaned

    def _generate_response(self):
        """Generate assistant response (runs in background thread)."""
        self.is_generating = True
        self.stop_flag = False
        
        # Update UI
        self.root.after(0, lambda: self.user_input.configure(state="normal"))
        self.root.after(0, lambda: self.stop_button.configure(state="normal"))
        model_name = self.model_manager.get_current_model()
        self.root.after(0, lambda: self.status_var.set(f"🤖 {model_name} is thinking..."))
        
        try:
            # Manage context
            managed_context = self.context_manager.manage_context(
                self.message_handler.get_history()
            )
            
            # Add empty assistant message placeholder.
            self.root.after(0, lambda: self.chat_display.add_message("assistant", ""))

            # Shared state written by the background thread, read by the main thread.
            # Using a dict so mutations are visible across the closure boundary.
            _latest = {"response": "", "thought": ""}
            _pending = [False]   # one-element list used as a mutable flag

            def _flush():
                """Main-thread callback: paint the latest streamed state once."""
                _pending[0] = False
                self.chat_display.update_last_message(
                    _latest["response"], thought=_latest["thought"]
                )

            # Generate with streaming — only ONE root.after update is ever
            # queued at a time, no matter how fast tokens arrive.
            response_text = ""
            for text in self.model_manager.generate(
                messages=managed_context,
                temperature=self.param_controls.get_temperature(),
                max_tokens=self.param_controls.get_max_tokens(),
                top_p=self.param_controls.get_top_p(),
                stream=True,
                on_stop_check=lambda: self.stop_flag
            ):
                response_text = text
                thought, response = self._parse_thinking(text)
                _latest["response"] = response
                _latest["thought"] = thought
                if not _pending[0]:
                    _pending[0] = True
                    self.root.after(0, _flush)

            # Guarantee the final complete state is always rendered.
            self.root.after(0, _flush)

            # Store clean response in history.
            _, clean_response = self._parse_thinking(response_text)
            self.message_handler.add_assistant_message(clean_response or response_text)

            # Check context management
            stats = self.context_manager.calculate_stats(self.message_handler.get_history())
            if stats["usage_percent"] > 150:
                msg = f"ℹ️ Context management active: {stats['total_messages']} messages, ~{stats['total_tokens']} tokens"
                self.root.after(0, lambda: self.chat_display.add_message("system", msg))
        
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self.chat_display.add_message("system", error_msg))
            self.logger.error(f"Generation error: {str(e)}", exc_info=True)
        
        # Restore UI
        self.is_generating = False
        self.root.after(0, lambda: self.user_input.configure(state="normal"))
        self.root.after(0, lambda: self.stop_button.configure(state="disabled"))
        self.root.after(0, lambda: self.status_var.set(f"✅ {model_name} ready"))
        self.root.after(0, lambda: self.user_input.focus())
    
    def _stop_generation(self):
        """Stop the current generation."""
        if self.is_generating:
            self.stop_flag = True
            self.status_var.set("Warning: Stopping generation...")
    
    def _clear_conversation(self):
        """Clear the conversation."""
        if messagebox.askyesno("Clear", "Clear conversation?"):
            self.message_handler.clear_history(keep_system=True)
            self.chat_display.clear()
            self.chat_display.add_message("system", "✨ Conversation cleared")
            self.status_var.set("Ready for input")
    
    def _show_stats(self):
        """Show context statistics."""
        stats = self.context_manager.calculate_stats(self.message_handler.get_history())
        
        msg = f"""📊 Context Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Total Messages: {stats['total_messages']}
• Total Tokens: ~{stats['total_tokens']:,} / {stats['max_context']:,} ({stats['usage_percent']:.1f}%)
• System: {stats['system_tokens']:,} tokens
• User: {stats['user_tokens']:,} tokens  
• Assistant: {stats['assistant_tokens']:,} tokens
• Model: {self.model_manager.get_current_model() or 'None'}
• Temperature: {self.param_controls.get_temperature()}
• Max Tokens: {self.param_controls.get_max_tokens()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        self.chat_display.add_message("system", msg)
    
    def _save_conversation(self):
        """Save conversation to JSON."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=self.storage.get_default_filename("json"),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            success, message = self.storage.save_to_json(
                filename,
                self.message_handler.get_history(),
                self.model_manager.get_current_model(),
                self.param_controls.get_parameters()
            )
            self.chat_display.add_message("system", message)
    
    def _load_conversation(self):
        """Load conversation from JSON."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            success, data, message = self.storage.load_from_json(filename)
            if success:
                # Load history
                self.message_handler.load_history(data.get("history", []))
                
                # Load parameters
                params = data.get("parameters", {})
                self.param_controls.set_parameters(params)
                
                # Redraw chat
                self.chat_display.clear()
                for msg in self.message_handler.get_history():
                    self.chat_display.add_message(msg["role"], msg["content"])
                
                model_info = data.get("model", "Unknown")
                self.chat_display.add_message("system", f"{message} (Model: {model_info})")
            else:
                self.chat_display.add_message("system", message)
    
    def _export_markdown(self):
        """Export conversation to Markdown."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            initialfile=self.storage.get_default_filename("md"),
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if filename:
            success, message = self.storage.export_to_markdown(
                filename,
                self.message_handler.get_history(),
                self.model_manager.get_current_model(),
                self.param_controls.get_parameters()
            )
            self.chat_display.add_message("system", message)
    
    def _edit_system_prompt(self):
        """Open system prompt editor dialog."""
        from tkinter.scrolledtext import ScrolledText
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit System Prompt")
        dialog.geometry("700x500")
        dialog.configure(bg=self.bg_color)
        
        tk.Label(
            dialog,
            text="System Prompt:",
            bg=self.bg_color,
            fg=self.text_color,
            font=("SF Mono", 12, "bold")
        ).pack(pady=10)
        
        text_widget = ScrolledText(
            dialog,
            wrap="word",
            font=("SF Mono", 11),
            bg=self.input_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            padx=10,
            pady=10
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", self.message_handler.get_system_prompt())
        
        button_frame = tk.Frame(dialog, bg=self.bg_color)
        button_frame.pack(pady=10)
        
        def save():
            prompt = text_widget.get("1.0", "end-1c").strip()
            if prompt:
                self.message_handler.set_system_prompt(prompt)
                dialog.destroy()
                self.chat_display.add_message("system", "✅ System prompt updated")
            else:
                messagebox.showwarning("Invalid", "System prompt cannot be empty!")
        
        def reset():
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", self.message_handler.DEFAULT_SYSTEM_PROMPT)
        
        tk.Button(button_frame, text="💾 Save", command=save, bg=self.accent_color,
                 fg="#11111b", font=("SF Mono", 10, "bold"), padx=15).pack(side="left", padx=5)
        tk.Button(button_frame, text="🔄 Reset", command=reset, bg="#fab387",
                 fg="#11111b", font=("SF Mono", 10, "bold"), padx=15).pack(side="left", padx=5)
        tk.Button(button_frame, text="✖ Cancel", command=dialog.destroy, bg="#f38ba8",
                 fg="#11111b", font=("SF Mono", 10, "bold"), padx=15).pack(side="left", padx=5)
    
    def _import_file(self):
        """Import a file into the conversation."""
        file_path = filedialog.askopenfilename(
            title="Select File to Import",
            filetypes=[
                ("All Supported", "*.xlsx *.xls *.txt *.md *.py *.json *.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("Text files", "*.txt *.md"),
                ("Code files", "*.py *.js *.java *.cpp *.c"),
                ("Data files", "*.json *.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            success, content, message = self.file_importer.import_file(file_path)
            if success:
                self.chat_display.add_message("system", message)
                self.message_handler.add_message("user", content)
            else:
                self.chat_display.add_message("system", message)
    
    def _load_previous_input(self):
        """Load previous input (up arrow)."""
        prev = self.message_handler.get_previous_input()
        if prev is not None:
            self.user_input.delete(0, "end")
            self.user_input.insert(0, prev)
    
    def _load_next_input(self):
        """Load next input (down arrow)."""
        next_input = self.message_handler.get_next_input()
        if next_input is not None:
            self.user_input.delete(0, "end")
            self.user_input.insert(0, next_input)
    
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()
