from setuptools import setup, find_packages

setup(
    name="researcher2",
    version="0.1.0",
    packages=find_packages(),
        "requests",
        "python-dotenv",
        "wolframalpha",
        "arxiv",
        "biopython",
        "google-genai",
        "googlesearch-python",
    ],
    entry_points={
        "console_scripts": [
            "researcher2=researcher2.cli:main",
        ],
    },
    author="Antigravity",
    description="A Python research agent that executes research workflows using various tools.",
)
