# ROKO - Autonomous AI System

![ROKO Banner](https://img.shields.io/badge/ROKO-AI%20System-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=flat-square)
![License](https://img.shields.io/badge/License-Apache%202.0-yellow?style=flat-square)

## 🚀 Overview

**ROKO** is an advanced autonomous artificial intelligence system with natural language processing capabilities, persistent cognitive memory, and a modern web interface. The system is designed to offer intelligent and contextual interactions through a modular and scalable architecture.

## ✨ Key Features

- **Modern Web Interface**: Responsive and elegant interface built with Flask and Tailwind CSS
- **Cognitive Memory**: Long-term memory system with semantic search using FAISS
- **Secure Authentication**: Complete user authentication system
- **Parallel Processing**: Optimized pipeline for efficient request processing
- **Modular Architecture**: Well-separated and easy-to-maintain components
- **Multi-user Support**: Isolated workspaces for each user

## 📋 Requirements

- Python 3.8 or higher
- OpenAI API Key (for AI functionality)
- Dependencies listed in `requirements.txt`

## 🔧 Installation

1. **Clone the repository**
```bash
git clone https://github.com/RokoOfficial/ROKO.git
cd ROKO
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

4. **Run the system**
```bash
python app.py
```

The system will be available at `http://localhost:5000`

## 🎯 Operation Modes

### Web Mode (Default)
```bash
python app.py
```

### CLI Mode
```bash
python app.py cli
```

## 📁 Project Structure

```
ROKO/
├── Agents/              # AI agents
├── Memory/              # Cognitive memory system
├── Pipeline/            # Processing pipeline
├── Interface/           # Web and CLI interfaces
├── Utils/               # Utilities and helpers
├── templates/           # HTML templates
├── static/              # Static files (CSS, JS)
├── ARTEFATOS/          # Generated artifacts
├── CODERSPACE/         # User workspaces
└── app.py              # Main entry point
```

## 💰 Third-Party Service Costs

### ⚠️ IMPORTANT: Services that Require Payment

This project uses third-party services that **may generate costs**. Key points:

#### 🔴 OpenAI API (REQUIRED for full functionality)
- **Cost**: Pay-as-you-go
- **Required for**: Natural language processing, embeddings, intelligent responses
- **How to obtain**: https://platform.openai.com/api-keys
- **Pricing**: Varies by model (GPT-3.5, GPT-4, etc.)
- **Estimate**: ~$0.002 per 1K tokens (GPT-3.5-turbo)
- **Without API Key**: System will run in limited mode

#### 📊 Optional Services that May Generate Costs

1. **Production Hosting**
   - Services like AWS, Google Cloud, Azure, Heroku charge for resources
   - Recommended: Minimum 2GB RAM, 1 vCPU
   - Costs range from $5-50/month depending on provider

2. **Production Database**
   - SQLite (included) is free but limited for production
   - Paid alternatives: Managed PostgreSQL, MongoDB Atlas
   - Costs: $0-100/month depending on volume

### ✅ Free Components

- **Flask**: Free and open source web framework
- **FAISS**: Free vector search library (Meta/Facebook)
- **SQLite**: Free database included
- **Tailwind CSS**: Free CSS framework via CDN
- **Python**: Free and open source language

### 💡 Usage Recommendations

#### For Development/Testing (Minimum Cost)
```bash
# Use only OpenAI API (pay-as-you-go)
# Host locally or on own server
# Estimated costs: $5-20/month for API only
```

#### For Production (Moderate Cost)
```bash
# OpenAI API: $50-200/month (depending on usage)
# Hosting: $20-50/month
# Database: $0-30/month
# Estimated total: $70-280/month
```

### 📝 Legal Notice

**The ROKO source code is licensed under Apache 2.0 (free and open source), BUT:**

- You are responsible for third-party service costs you choose to use
- OpenAI API is required for full functionality and has associated costs
- Costs can vary significantly based on usage volume
- Always set spending limits and monitor usage
- The project is not responsible for costs incurred

**For complete cost details, see [COST_NOTICE.md](COST_NOTICE.md)**

## 🔐 Security

- Session-based authentication
- Secure password hashing
- SQL injection protection
- User input validation

## 🛠️ Technologies Used

- **Backend**: Python, Flask
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Database**: SQLite
- **AI**: OpenAI API, FAISS
- **Memory**: Vector embedding system

## 📊 Performance

- Support for multiple simultaneous requests
- Embedding cache for optimization
- FAISS index for fast semantic search
- Complete logging system

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## 📝 License

This project is licensed under the **Apache License 2.0**.

### What this means:

✅ **You CAN:**
- Use commercially
- Modify the code
- Distribute
- Sublicense
- Use contributor patents

⚠️ **You MUST:**
- Include a copy of the license
- State significant changes
- Include copyright notices
- Include patent notices (if applicable)

❌ **You CANNOT:**
- Hold authors liable
- Use trademarks without permission

### Important about Dependencies

This project uses third-party libraries that may have their own licenses:
- **OpenAI API**: Own terms of service
- **Flask**: BSD License
- **FAISS**: MIT License
- **Others**: See `requirements.txt` for details

See the [LICENSE](LICENSE) file for the complete Apache License 2.0 text.

## 📧 Contact

For questions or suggestions, open an issue on GitHub.

---

**ROKO** - Next Generation Autonomous Artificial Intelligence 🤖

*Developed with ❤️ by the ROKO team*
