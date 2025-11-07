"""
Leave Management System - Main Entry Point

A professional AI-powered leave management chatbot system that helps employees:
- Check leave balances
- Apply for leave
- View leave history
- Cancel leave applications
- Query company leave policies

This system uses Google's Gemini AI with custom tools and maintains user session context
for natural conversation flows.
"""

from chatbot import simple_chatbot_interface, chatbot_api
def main():
    """Main function to run the chatbot interface"""
    print("🚀 Leave Management System")
    print("=" * 50)
    print("A professional AI-powered leave management chatbot")
    print("Features:")
    print("  ✓ Check leave balances")
    print("  ✓ Apply for leave")
    print("  ✓ View leave history") 
    print("  ✓ Cancel leave applications")
    print("  ✓ Query company policies")
    print("=" * 50)
    
    try:
        # Run the chatbot interface
        simple_chatbot_interface()
    except KeyboardInterrupt:
        print("\n\nGoodbye! Thanks for using the Leave Management System.")
    except Exception as e:
        print(f"\nError starting the system: {e}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()

