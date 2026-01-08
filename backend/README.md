# 🚀 Deploy Docker Hub Images to IBM Code Engine (SSO Tutorial)

This guide explains **how Docker Hub connects to IBM Code Engine**, when you need a **PAT**, and how to **log in to Code Engine using Single Sign-On (SSO)** step by step.

---

## 1️⃣ Docker Hub → IBM Code Engine Authentication

### ❓ Do you need only Docker Hub username or also a PAT?

### ✅ Short Answer

| Docker Hub Image Type | Username Needed | PAT Needed | Registry Secret Needed |
|---------------------|----------------|------------|------------------------|
| **Public Image** | ❌ (only part of image name) | ❌ | ❌ |
| **Private Image** | ✅ | ✅ | ✅ |

---

## 🔓 Case A — Public Docker Hub Images (Recommended for Dev)

Example image:
```
docker.io/<username>/bisma:latest
```

### ✔ How it works
- IBM Code Engine pulls the image **anonymously**
- No authentication required
- **No PAT**
- **No registry secret**

### ✔ Example deploy command
```bash
ibmcloud ce application create \
  --name bisma \
  --image docker.io/<username>/bisma:latest \
  --port 8000
```

---

## 🔐 Case B — Private Docker Hub Images

### 🔧 Create a registry secret
```bash
ibmcloud ce registry create \
  --name dockerhub-secret \
  --server docker.io \
  --username <dockerhub-username> \
  --password <dockerhub-PAT>
```

---

## 2️⃣ Connecting to IBM Code Engine (SSO Tutorial)

### Step 1: Login with SSO
```bash
ibmcloud login
```

### Step 2: Target region
```bash
ibmcloud target -r us-south
```

### Step 3: Create or select project
Mostly you will fail to create this one so use the one that has been created.
```bash
ibmcloud ce project create --name mlops-forecasting
ibmcloud ce project select --name mlops-forecasting
```

---

## ✅ Checklist
```bash
ibmcloud login
ibmcloud target -r us-south
ibmcloud ce project select --name mlops-forecasting
ibmcloud ce application list
```

---

Happy deploying 🎉
