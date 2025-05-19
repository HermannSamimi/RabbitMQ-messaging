# RabbitMQ Messaging with GitHub Actions

A simple example of producing and consuming JSON messages via RabbitMQ, storing data in MongoDB, and automating the workflow using GitHub Actions (including a daily cron trigger at 08:00 EET). Two parallel producers (`producer.py` and `producer_2s.py`) generate fake user data and send it to a queue, while `consumer.py` reads and inserts it into a MongoDB collection for up to 1 minute per run.

---

## 📂 Repository Structure

```txt
├── producer.py         # First producer script
├── producer_2s.py      # Second producer (same logic, separate source)
├── consumer.py         # Consumer script that reads from RabbitMQ and writes to MongoDB
├── requirements.txt    # Python dependencies
└── .github/
    └── workflows/
        └── schedule.yml  # GitHub Actions workflow definition
``` 

## 🛠️ Prerequisites

- **Python 3.11** (or compatible)
- **RabbitMQ** instance (e.g., CloudAMQP)
- **MongoDB Atlas** cluster (or any TLS-enabled MongoDB)
- **GitHub repository** with Secrets configured

## ⚙️ Configuration

1. **Clone this repo**
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Install dependencies**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. **Environment variables**
   Create a `.env` file (for local runs) or set GitHub Secrets:
   ```ini
   RABBITMQCREDENTIAL=amqps://user:pass@host/vhost
   MONGO_URI=mongodb+srv://user:pass@cluster0…/mydb?retryWrites=true&w=majority
   ```

### 🔒 GitHub Secrets

Add the following in your repository's **Settings → Secrets**:
- `RABBITMQCREDENTIAL` → Your RabbitMQ URI
- `MONGO_URI` → Your MongoDB connection string

No extra quotes (`"` or `'`) should surround the secret values.

## 🚀 Running Locally

- **Producer 1**:
  ```bash
  python producer.py
  ```

- **Producer 2**:
  ```bash
  python producer_2s.py
  ```

- **Consumer**:
  ```bash
  python consumer.py
  ```

Each script runs indefinitely; they generate or consume messages until you stop them (or for 5 minutes in the consumer by default).

## 🤖 GitHub Actions Workflow

The workflow (`.github/workflows/schedule.yml`) runs three jobs in parallel:

1. **Producer** (`producer.py`) — runs for 60 s  
2. **Producer 2** (`producer_2s.py`) — runs for 60 s  
3. **Consumer** (`consumer.py`) — runs for 60 s  

It is triggered on:
- **`push`** events
- **Manual** (`workflow_dispatch`)
- **Scheduled**: daily at **08:00 Europe/Tallinn** (06:00 UTC)

Timeouts are wrapped with `timeout 60s … || true` so that the jobs always exit successfully after 1 minute.

### Modifying the Schedule

To change the cron time, edit the `schedule` block in `schedule.yml` (remember, GitHub cron is in UTC):
```yaml
on:
  schedule:
    - cron: 'MIN HOUR * * *'  # MIN and HOUR in UTC
```

## 🤝 Contributing

Feel free to open issues or pull requests for enhancements, bug fixes, or improvements!

---

*Happy messaging!*