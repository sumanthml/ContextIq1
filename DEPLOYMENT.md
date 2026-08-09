# 🌐 ContextIQ: 100% Free Production Deployment Guide

This guide details how to deploy **ContextIQ** online for **100% free forever** with custom HTTPS domains, automatic SSL certificates, and zero hosting costs.

---

## 🛠️ Deployment Architecture

* **Frontend**: Hosted free on **Vercel** (`https://contextiq.vercel.app`)
* **Backend**: Hosted free on **Render** / **Hugging Face Spaces** / **Cloud Run** (`https://contextiq-backend.onrender.com`)
* **Database & Vectors**: Persistent local disk storage + Cohere & Groq free tier APIs.

---

## STEP 1: Deploy Backend (100% Free Web Service)

### Option A: Render.com (Recommended - 1-Click Free Blueprint)
1. Push your repository to **GitHub**.
2. Go to [Render.com](https://render.com) (sign up for free).
3. Click **New +** $\rightarrow$ **Blueprint**.
4. Connect your GitHub repo and select the `/backend` folder.
5. Render will automatically detect `render.yaml` and provision your free Python FastAPI web service!
6. Copy your deployed backend URL: `https://your-backend-name.onrender.com`.

### Option B: Hugging Face Spaces (Alternative 100% Free Docker Hosting)
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Name it `contextiq-backend` and select **Docker** SDK.
3. Push the `backend/` directory to Hugging Face $\rightarrow$ your backend will be live at `https://yourname-contextiq-backend.hf.space`!

---

## STEP 2: Deploy Frontend (100% Free on Vercel)

1. Go to [Vercel.com](https://vercel.com) and log in with GitHub.
2. Click **Add New** $\rightarrow$ **Project**.
3. Import your `CONTEXTIQ` repository.
4. Set the **Root Directory** to `frontend`.
5. Under **Environment Variables**, add:
   * **Key**: `NEXT_PUBLIC_API_URL`
   * **Value**: `https://your-backend-name.onrender.com/api/v1` (replace with your backend URL from Step 1).
6. Click **Deploy**!

Vercel will build your project in ~30 seconds and give you your live production URL: `https://contextiq.vercel.app`.

---

## STEP 3: Verify Live Production App

1. Open `https://contextiq.vercel.app` in your browser or on your phone!
2. Click **Register Account** or **Sign In**.
3. Upload a document, chat, and test real-time streaming!
4. **Log out and log back in** $\rightarrow$ verify your documents and chats remain saved forever.

---

## 🏆 Resume Showcase Links

Once deployed, add these impressive live links to your resume:
* **Live App**: `https://contextiq.vercel.app`
* **API Documentation**: `https://your-backend-name.onrender.com/docs`
* **GitHub Repository**: `https://github.com/yourusername/contextiq`
