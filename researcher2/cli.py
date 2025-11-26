import argparse
import os
from dotenv import load_dotenv
from .core import ResearchAgent

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Researcher2 CLI")
    parser.add_argument("--prompt", type=str, help="Information about what to extract")
    parser.add_argument("--output", type=str, help="Output directory (overrides OUTPUTS env var)")
    
    args = parser.parse_args()

    if args.prompt:
        os.environ["RESEARCH_PROMPT"] = args.prompt
    
    if args.output:
        os.environ["OUTPUTS"] = args.output

    if not os.getenv("RESEARCH_PROMPT"):
        print("Error: RESEARCH_PROMPT environment variable or --prompt argument is required.")
        return

    agent = ResearchAgent()
    agent.run()

if __name__ == "__main__":
    main()
