"""
Main entry point for the Advanced Multi-Model Chat Interface.
"""
import tkinter

from config import Config
from managers import ModelManager, ContextManager
from conversation import MessageHandler, ConversationStorage
from ui import MainWindow
from utils.logger import setup_logger


def main():
    """Initialize and run the application."""
    # Setup logging
    logger = setup_logger()
    logger.info("Root")
    
    # Initialize configuration
    config = Config()
    
    # Initialize core components
    model_manager = ModelManager(config)
    context_manager = ContextManager(model_manager)
    message_handler = MessageHandler()
    storage = ConversationStorage()
    
    # Create UI
    root = tkinter.Tk()
    app = MainWindow(
        root,
        config,
        model_manager,
        context_manager,
        message_handler,
        storage
    )
    
    # Run the application
    logger.info("Application initialized, starting main loop")
    app.run()


if __name__ == "__main__":
    main()
