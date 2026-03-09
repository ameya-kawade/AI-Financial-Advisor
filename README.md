# AI Financial Advisor

Most of us know we should handle our money better, but it's hard to know where to start. I built this tool to give you a clear, honest look at your finances and use AI to help figure out the next steps. It’s designed to be simple, fast, and actually useful.

## What you can do with it

- **Check your financial health**: We look at 8 core areas—like your savings rate and debt-to-income ratio—and give you an overall score. No guesswork.
- **Plan for big goals**: Whether it's a house, education, or retirement, you can see if you're on track and how much more you need to save each month.
- **Get AI-powered advice**: The app uses Gemini (or a local Ollama model if you prefer privacy) to look at your specific numbers and suggest ways to optimize your spending or pay down debt.
- **Visualise your future**: Interactive charts show you where your money is going and where it could be in 10, 20, or 30 years.
- **Take it with you**: One click generates a clean PDF report with your full analysis and a 30-60-90 day action plan.

## Setup

### Prerequisites
- Python 3.9+
- A Google Gemini API key (optional) or Ollama (optional)

### Quick Start

1. **Clone and enter the project**
   ```bash
   git clone https://github.com/your-repo/ai-financial-advisor.git
   cd ai-financial-advisor
   ```

2. **Set up your environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure your keys**
   Copy `.env.example` to `.env` and add your `GOOGLE_API_KEY`. If you're using Ollama, make sure it's running locally.

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

## A bit about the tech
I used **Streamlit** for the interface because it's clean and responsive. The heavy lifting for numbers is done with **Pandas**, and the charts use **Plotly**. For the AI, I implemented a fallback system: it tries the best available cloud model first, but can drop down to a local model or even basic rules if you're offline or don't have an API key.

## Privacy & Responsibility
Your data stays local to your session. I also included a standard disclaimer because, while the AI is smart, it isn't a replacement for a human financial advisor. Use this for education and planning, but always double-check big decisions.
