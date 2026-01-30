# 🍃 MongoChat

A SaaS-style AI assistant that allows users to securely connect and chat with their own MongoDB Atlas data using Google's Gemini AI.

Live Website: https://romannihal-mongo-chat-app-3iou6q.streamlit.app/

Built with **Streamlit**, **Google Gemini**, **PyMongo**, and **uv**.

## 🚀 Features

* **Bring Your Own Database:** Users securely connect their own MongoDB Atlas clusters via the UI.
* **AI-Powered Analysis:** Uses **Gemini 1.5 Flash** to reason across fetched JSON documents.
* **SaaS Constraints:** Includes built-in logic for a "Free Tier" (3 messages per session) and token limits.
* **Service-Oriented Architecture:** Modular codebase separating business logic, database services, and UI.
* **Modern Stack:** Powered by `uv` for lightning-fast dependency management.

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **AI Engine:** Google Gemini (Generative AI)
* **Database:** PyMongo (MongoDB Atlas)
* **Package Manager:** uv

## 🧪 Usage

> **⚠️ Important Prerequisite:** > Before connecting, ensure your MongoDB Atlas cluster allows connections from outside your local network. Go to **Network Access** in Atlas and select **"Allow Access from Anywhere"** (whitelist IP `0.0.0.0/0`). This is required for the Streamlit Cloud server to reach your database.

1.  Open the app in your browser.
2.  **Sidebar Config:**
    * **Connection String:** Paste your MongoDB Atlas URI (e.g., `mongodb+srv://...`).
    * **Database Name:** Enter the specific database name (e.g., `ecommerce_db`).
    * **Collection Name:** Enter the collection you want to chat with (e.g., `products`).
3.  **Link:** Click "Link Database" to securely fetch the documents and initialize the context.
4.  **Chat:** Ask questions to extract insights from your specific data (e.g., *"Which product has the highest rating?"*).