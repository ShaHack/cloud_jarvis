import requests
import schedule
import time
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ===== SETTINGS =====
TOKEN = "YOUR_TELEGRAM_TOKEN"
HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN"
NEWS_API = "YOUR_NEWS_API_KEY"
CHAT_ID = "YOUR_CHAT_ID"

# ===== MEMORY =====
memory = []

# ===== AI CHAT =====
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.text
    memory.append({"user": user})

    prompt = ""
    for m in memory[-10:]:
        if "user" in m:
            prompt += "User: " + m["user"] + "\n"
        if "assistant" in m:
            prompt += "Assistant: " + m["assistant"] + "\n"

    prompt += "User: " + user + "\nAssistant:"

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    response = requests.post(
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large",
        headers=headers,
        json={"inputs": prompt},
    )

    try:
        answer = response.json()[0]["generated_text"]
    except:
        answer = "AI busy. Try again."

    memory.append({"assistant": answer})

    await update.message.reply_text(answer)


# ===== CYBER NEWS =====
def cyber_news():
    url = f"https://newsapi.org/v2/everything?q=cybersecurity&language=en&apiKey={NEWS_API}"
    data = requests.get(url).json()

    news = "🚨 Cyber Security News:\n\n"

    for article in data["articles"][:5]:
        news += article["title"] + "\n" + article["url"] + "\n\n"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": news}
    )


# ===== CVE ALERT =====
def cve_alerts():
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=5"
    data = requests.get(url).json()

    alert = "⚠️ Latest CVE Alerts:\n\n"

    for item in data["vulnerabilities"]:
        cve = item["cve"]["id"]
        desc = item["cve"]["descriptions"][0]["value"]
        alert += f"{cve}\n{desc[:120]}...\n\n"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": alert}
    )


# ===== SCHEDULER =====
def run_tasks():
    schedule.every().day.at("09:00").do(cyber_news)
    schedule.every().day.at("10:00").do(cve_alerts)

    while True:
        schedule.run_pending()
        time.sleep(60)


# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    threading.Thread(target=run_tasks).start()

    print("Cloud Jarvis running...")
    app.run_polling()


if __name__ == "__main__":
    main()