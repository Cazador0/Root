"""
Parameter controls widget for adjusting model parameters.
"""
import tkinter as tk
from utils.logger import get_logger


class ParameterControls:
    """Widget for controlling model generation parameters."""
    
    def __init__(self, parent, bg_color, text_color, input_bg):
        """
        Initialize parameter controls.
        
        Args:
            parent: Parent tkinter widget
            bg_color: Background color
            text_color: Text color
            input_bg: Input field background color
        """
        self.logger = get_logger("ParameterControls")
        self.bg_color = bg_color
        self.text_color = text_color
        self.input_bg = input_bg
        
        # Create control variables
        self.temp_var = tk.DoubleVar(value=0.7)
        self.max_tokens_var = tk.IntVar(value=32768)
        self.top_p_var = tk.DoubleVar(value=0.95)
        
        # Create the frame
        self.frame = tk.Frame(parent, bg=bg_color)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the parameter control widgets."""
        # Temperature slider
        tk.Label(
            self.frame,
            text="Temp:",
            bg=self.bg_color,
            fg=self.text_color,
            font=("SF Mono", 9)
        ).pack(side="left", padx=5)
        
        self.temp_slider = tk.Scale(
            self.frame,
            from_=0.0,
            to=2.0,
            resolution=0.1,
            orient="horizontal",
            variable=self.temp_var,
            bg=self.bg_color,
            fg=self.text_color,
            highlightthickness=0,
            length=120,
            width=15
        )
        self.temp_slider.pack(side="left", padx=5)
        
        # Top P slider
        tk.Label(
            self.frame,
            text="Top-P:",
            bg=self.bg_color,
            fg=self.text_color,
            font=("SF Mono", 9)
        ).pack(side="left", padx=5)
        
        self.top_p_slider = tk.Scale(
            self.frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.top_p_var,
            bg=self.bg_color,
            fg=self.text_color,
            highlightthickness=0,
            length=120,
            width=15
        )
        self.top_p_slider.pack(side="left", padx=5)
        
        # Max tokens entry
        tk.Label(
            self.frame,
            text="Max Tokens:",
            bg=self.bg_color,
            fg=self.text_color,
            font=("SF Mono", 9)
        ).pack(side="left", padx=5)
        
        self.max_tokens_entry = tk.Entry(
            self.frame,
            textvariable=self.max_tokens_var,
            width=8,
            bg=self.input_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            font=("SF Mono", 9)
        )
        self.max_tokens_entry.pack(side="left", padx=5)
    
    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)
    
    def get_temperature(self):
        """Get current temperature value."""
        return self.temp_var.get()
    
    def get_max_tokens(self):
        """Get current max tokens value."""
        return self.max_tokens_var.get()
    
    def get_top_p(self):
        """Get current top-p value."""
        return self.top_p_var.get()
    
    def set_temperature(self, value):
        """Set temperature value."""
        self.temp_var.set(value)
    
    def set_max_tokens(self, value):
        """Set max tokens value."""
        self.max_tokens_var.set(value)
    
    def set_top_p(self, value):
        """Set top-p value."""
        self.top_p_var.set(value)
    
    def get_parameters(self):
        """Get all parameters as a dictionary."""
        return {
            "temperature": self.get_temperature(),
            "max_tokens": self.get_max_tokens(),
            "top_p": self.get_top_p()
        }
    
    def set_parameters(self, params):
        """
        Set all parameters from a dictionary.
        
        Args:
            params: Dictionary containing parameter values
        """
        if "temperature" in params:
            self.set_temperature(params["temperature"])
        if "max_tokens" in params:
            self.set_max_tokens(params["max_tokens"])
        if "top_p" in params:
            self.set_top_p(params["top_p"])
