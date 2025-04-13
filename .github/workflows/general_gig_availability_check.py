name: general_gig_availability_check

on:
  repository_dispatch:
    types: [craigslist_alert]

jobs:
  autoresponder:
    runs-on: ubuntu-latest

    steps:
      # Step 1: Checkout your repository
      - name: Checkout repository
        uses: actions/checkout@v3

      # Step 2: Debug directory structure (optional for troubleshooting)
      - name: Debug directory structure
        run: ls -R

      # Step 3: Set up Python environment
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      # Step 4: Upgrade pip
      - name: Upgrade pip
        run: python -m pip install --upgrade pip

      # Step 5: Install dependencies
      - name: Install dependencies
        run: |
          pip install flake8 pytest  # Include testing/linting tools if needed
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      # Step 6: (Optional) Lint code with flake8
      - name: Lint with flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      # Step 7: (Optional) Test with pytest
      - name: Run tests with pytest
        run: pytest

      # Step 8: Run the auto-responder Python script
      - name: Run auto-responder
        run: python general_gig_availability_check.py
