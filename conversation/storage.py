"""
Conversation storage (save/load to JSON and export to Markdown).
"""
import json
import os
from datetime import datetime
from utils.logger import get_logger


class ConversationStorage:
    """Handle saving and loading conversations."""
    
    def __init__(self):
        self.logger = get_logger("ConversationStorage")
    
    def save_to_json(self, filepath, history, model_name=None, parameters=None):
        """
        Save conversation to JSON file.
        
        Args:
            filepath: Path to save the file
            history: Conversation history (list of messages)
            model_name: Name of the model used
            parameters: Dictionary of generation parameters
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            save_data = {
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "model": model_name,
                "history": history,
                "parameters": parameters or {}
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved conversation to {filepath}")
            return True, f"✅ Conversation saved to {os.path.basename(filepath)}"
        
        except Exception as e:
            self.logger.error(f"Error saving conversation: {str(e)}")
            return False, f"❌ Error saving: {str(e)}"
    
    def load_from_json(self, filepath):
        """
        Load conversation from JSON file.
        
        Args:
            filepath: Path to the JSON file
        
        Returns:
            tuple: (success: bool, data: dict, message: str)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            self.logger.info(f"Loaded conversation from {filepath}")
            return True, save_data, f"✅ Loaded conversation from {os.path.basename(filepath)}"
        
        except FileNotFoundError:
            error_msg = f"❌ File not found: {filepath}"
            self.logger.error(error_msg)
            return False, {}, error_msg
        
        except json.JSONDecodeError as e:
            error_msg = f"❌ Invalid JSON: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
        
        except Exception as e:
            error_msg = f"❌ Error loading: {str(e)}"
            self.logger.error(f"Error loading conversation: {str(e)}")
            return False, {}, error_msg
    
    def export_to_markdown(self, filepath, history, model_name=None, parameters=None):
        """
        Export conversation to Markdown file.
        
        Args:
            filepath: Path to save the markdown file
            history: Conversation history (list of messages)
            model_name: Name of the model used
            parameters: Dictionary of generation parameters
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"# Chat Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write metadata
                if model_name:
                    f.write(f"**Model:** {model_name}\n\n")
                
                if parameters:
                    param_str = ", ".join([f"{k}={v}" for k, v in parameters.items()])
                    f.write(f"**Parameters:** {param_str}\n\n")
                
                f.write("---\n\n")
                
                # Write messages
                for msg in history:
                    role = msg["role"].upper()
                    content = msg.get("content", "")
                    
                    if role == "SYSTEM":
                        f.write(f"**🖥️ SYSTEM:**\n{content}\n\n")
                    elif role == "USER":
                        f.write(f"**👤 USER:**\n{content}\n\n")
                    elif role == "ASSISTANT":
                        f.write(f"**🤖 ASSISTANT:**\n{content}\n\n")
                    
                    f.write("---\n\n")
            
            self.logger.info(f"Exported conversation to {filepath}")
            return True, f"✅ Exported to {os.path.basename(filepath)}"
        
        except Exception as e:
            self.logger.error(f"Error exporting conversation: {str(e)}")
            return False, f"❌ Error exporting: {str(e)}"
    
    def get_default_filename(self, extension="json"):
        """
        Generate a default filename with timestamp.
        
        Args:
            extension: File extension (without dot)
        
        Returns:
            str: Default filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"chat_{timestamp}.{extension}"
