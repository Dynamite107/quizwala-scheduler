import config
import scheduler
import sys
import logging

def main():
    print("========================================")
    print("🚀 QuizWala Scheduler v1.0 Initiated 🚀")
    print("========================================")
    
    try:
        # Step 1: Validate Environment, Paths, and Tokens
        print("⏳ Validating environment and media files...")
        config.validate_environment()
        
        # Step 2: Start Scheduler Engine
        print("\n⏳ Starting main scheduling engine...")
        scheduler.run_scheduler()
        
        print("\n========================================")
        print("✅ Process Completed Successfully!")
        print("========================================")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        logging.error(f"Fatal Error in run.py: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
