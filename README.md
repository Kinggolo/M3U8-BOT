# 🟢 **VERY FAST M3U8 BOT – V1 STABLE**

**Fast | Queue System | Auto-Retry | Custom Filenames | Colab Ready**

This bot downloads **M3U8/HLS videos** with:
✔ Queue System
✔ Auto Retry (3x)
✔ Chunk Merge
✔ Custom Filename Support
✔ Progress + Success Messages
✔ Multi-Video Batch Download Support
✔ Fully working in **Google Colab** with just **one line**

---

# 🚀 **Run in Google Colab (ONE LINE ONLY)**

After you upload your `bot.py` to GitHub → copy the **raw URL** and paste below:

> Replace
> `<RAW_URL>` = Your GitHub Raw link
> `<YOUR_BOT_TOKEN>` = Your Telegram Bot Token
> `<YOUR_CHAT_ID>` = Your personal chat ID

```bash
!wget -q -O bot.py "<RAW_URL>" && BOT_TOKEN="<YOUR_BOT_TOKEN>" CHAT_ID="<YOUR_CHAT_ID>" python3 bot.py
```

✨ That’s it. Bot starts instantly.

---

# 📌 **How to Get RAW URL (Important)**

1. Open your GitHub repo → `bot.py`
2. Click **Raw**
3. Copy URL (will look like):

```
https://raw.githubusercontent.com/USERNAME/REPO/main/bot.py
```

Paste in the Colab command.

---

# 📝 **Features (V1 Stable)**

### ✅ **1. Queue System**

Send multiple M3U8 links → all go into queue.
Bot downloads **one by one** in order.

### ✅ **2. Auto-Retry**

If a download fails:

* Retry 3 times
* If still not working → moved to failed list

### ✅ **3. Custom Filenames**

Send link like:

```
Lec-1 : DC Machine | https://example.com/video.m3u8
```

Bot will save:

```
Lec-1 - DC Machine.mp4
```

### ✅ **4. Progress Status**

Bot sends:

* added to queue
* starting download
* total chunks
* merging
* completed

### ✅ **5. Batch Download Ready**

You can send **multiple links continuously** without waiting.

### ✅ **6. Clean Code + No Auto-Spam**

Bot starts only after first link.

---

# 🧪 **Supported Inputs**

✔ Direct M3U8 link
✔ Custom name + M3U8 link
✔ Multiple messages (queued automatically)

❌ DRM-protected M3U8 not supported

---

# 📦 **Environment Variables**

Bot requires:

```
BOT_TOKEN=
CHAT_ID=
```

Automatically injected in one-line Colab command.

---

# 📂 **Folder Output**

All videos saved automatically as:

```
/content/downloads/
```

Filename = custom name OR auto-timestamp.

---

# 🛠 **Run Locally (Optional)**

```bash
pip install requests tqdm
BOT_TOKEN="YOUR_TOKEN" CHAT_ID="YOUR_CHAT_ID" python3 bot.py
```

---

# 🎉 **V1 Stable – Summary / Release Notes**

* Added full **Queue System**
* Auto-Retry engine added
* Custom filename support
* Clean status messages
* Optimized chunk merging
* Improved performance + stability
* One-line Colab launch added
* All known bugs fixed
