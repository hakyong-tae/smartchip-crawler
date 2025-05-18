name: Daily SmartChip Race Crawler

on:
  schedule:
    - cron: '0 2 * * *'  # 매일 오전 11시 KST
  workflow_dispatch:

permissions:
  contents: read
  actions: read

jobs:
  crawl:
    runs-on: ubuntu-22.04

    steps:
    - name: 📦 Checkout repository
      uses: actions/checkout@v3

    - name: 📆 Set CURRENT_DATE (KST 기준)
      run: echo "CURRENT_DATE=$(TZ=Asia/Seoul date +'%Y-%m-%d')" >> $GITHUB_ENV

    - name: 🧹 Delete old output files
      run: rm -f output/events_*.json || true

    - name: 🐍 Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: 🧪 Install dependencies
      run: |
        pip install -r requirements.txt

    - name: 🚀 Run SmartChip crawler
      run: |
        python utils/races_crawler.py ${{ env.CURRENT_DATE }}

    - name: 💾 Upload today's result
      uses: actions/upload-artifact@v4
      with:
        name: smartchip-events-${{ env.CURRENT_DATE }}
        path: output/events_${{ env.CURRENT_DATE }}.json
