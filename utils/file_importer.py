"""
File import functionality for various file types.
"""
import os
from .logger import get_logger

# Make pandas optional - only needed for Excel/CSV
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class FileImporter:
    """Handle importing various file types into the chat context."""
    
    def __init__(self):
        self.logger = get_logger("FileImporter")
        
        # Base supported extensions
        self.supported_extensions = {
            'text': ['.txt', '.md'],
            'code': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.hpp'],
            'data': ['.json']
        }
        
        # Add Excel/CSV only if pandas is available
        if PANDAS_AVAILABLE:
            self.supported_extensions['excel'] = ['.xlsx', '.xls']
            self.supported_extensions['csv'] = ['.csv']
        else:
            self.logger.warning("Pandas not available - Excel/CSV import disabled")
            self.logger.warning("To enable: pip install pandas")
    
    def import_file(self, file_path):
        """
        Import a file and return its content as a formatted string.
        
        Args:
            file_path: Path to the file to import
        
        Returns:
            tuple: (success: bool, content: str, message: str)
        """
        if not os.path.exists(file_path):
            return False, "", f"File not found: {file_path}"
        
        file_ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)
        
        try:
            if file_ext in self.supported_extensions.get('excel', []):
                if not PANDAS_AVAILABLE:
                    return False, "", "❌ Excel support requires pandas: pip install pandas"
                return self._import_excel(file_path, file_name)
            elif file_ext in self.supported_extensions.get('csv', []):
                if not PANDAS_AVAILABLE:
                    return False, "", "❌ CSV support requires pandas: pip install pandas"
                return self._import_csv(file_path, file_name)
            elif file_ext in self.supported_extensions['text'] or \
                 file_ext in self.supported_extensions['code'] or \
                 file_ext in self.supported_extensions['data']:
                return self._import_text_file(file_path, file_name, file_ext)
            else:
                return False, "", f"Unsupported file type: {file_ext}"
        
        except Exception as e:
            self.logger.error(f"Error importing file {file_path}: {str(e)}", exc_info=True)
            return False, "", f"Error importing file: {str(e)}"
    
    def _import_excel(self, file_path, file_name):
        """Import Excel file."""
        df = pd.read_excel(file_path)
        content = f"📊 Excel File: {file_name}\n\n{df.head(20).to_string()}"
        if len(df) > 20:
            content += f"\n\n... ({len(df)} total rows, showing first 20)"
        
        message = f"✅ Imported Excel file: {file_name} ({len(df)} rows, {len(df.columns)} columns)"
        self.logger.info(f"Imported Excel: {file_name}")
        return True, content, message
    
    def _import_csv(self, file_path, file_name):
        """Import CSV file."""
        df = pd.read_csv(file_path)
        content = f"📊 CSV File: {file_name}\n\n{df.head(20).to_string()}"
        if len(df) > 20:
            content += f"\n\n... ({len(df)} total rows, showing first 20)"
        
        message = f"✅ Imported CSV file: {file_name} ({len(df)} rows, {len(df.columns)} columns)"
        self.logger.info(f"Imported CSV: {file_name}")
        return True, content, message
    
    def _import_text_file(self, file_path, file_name, file_ext):
        """Import text-based files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Truncate if too long
        max_chars = 10000
        original_length = len(content)
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... (truncated, total {original_length} characters)"
        
        # Format based on file type
        if file_ext in self.supported_extensions['code'] or file_ext == '.json':
            formatted_content = f"[Imported file: {file_name}]\n\n```\n{content}\n```"
        else:
            formatted_content = f"[Imported file: {file_name}]\n\n{content}"
        
        message = f"✅ Imported file: {file_name} ({original_length} characters)"
        self.logger.info(f"Imported text file: {file_name}")
        return True, formatted_content, message
    
    def get_supported_filetypes(self):
        """Return a list of all supported file extensions."""
        all_extensions = []
        for extensions in self.supported_extensions.values():
            all_extensions.extend(extensions)
        return all_extensions
