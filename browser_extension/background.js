const SERVER_BASE = "http://127.0.0.1:9876";

const VIDEO_DOMAINS = [
  "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
  "tiktok.com", "facebook.com", "fb.watch", "instagram.com",
  "twitter.com", "x.com", "twitch.tv", "bilibili.com"
];

function isStreamingVideoUrl(url) {
  if (!url) return false;
  try {
    const host = new URL(url).hostname.toLowerCase();
    return VIDEO_DOMAINS.some((d) => host.includes(d));
  } catch (e) {
    return false;
  }
}

function cleanYouTubeUrl(url) {
  if (!url) return url;
  try {
    const u = new URL(url);
    if (u.hostname.includes("youtube.com") && u.pathname.includes("/watch")) {
      const vid = u.searchParams.get("v");
      if (vid) return `https://www.youtube.com/watch?v=${vid}`;
    } else if (u.hostname.includes("youtu.be")) {
      const vid = u.pathname.replace(/^\//, "");
      if (vid) return `https://www.youtube.com/watch?v=${vid}`;
    }
  } catch (e) {}
  return url;
}

// 1. Context Menus
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "srpcom-download-link",
    title: "Download with SRPCOM Download Manager",
    contexts: ["link", "image", "audio"]
  });

  chrome.contextMenus.create({
    id: "srpcom-download-video",
    title: "Download Video with SRPCOM (SDM)",
    contexts: ["video", "page"]
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const referer = (tab && tab.url) || "";
  let targetUrl = info.linkUrl || info.srcUrl || (tab && tab.url) || "";

  if (info.menuItemId === "srpcom-download-video") {
    let videoUrl = cleanYouTubeUrl(targetUrl);
    let title = (tab && tab.title) || "";
    if (title) {
      title = title.replace(/\s*-\s*YouTube\s*$/i, "").replace(/^\(\d+\)\s*/, "").replace(/^[🔴▶\s]+/, "").trim();
    }
    if (videoUrl) {
      await sendVideoToSRPCOM(videoUrl, "best", title, { referer });
    }
  } else {
    // Context menu: "srpcom-download-link"
    if (targetUrl) {
      if (isStreamingVideoUrl(targetUrl)) {
        // Automatically route YouTube and media stream links to video downloader!
        const cleanVideoUrl = cleanYouTubeUrl(targetUrl);
        await sendVideoToSRPCOM(cleanVideoUrl, "best", "", { referer });
      } else {
        await sendToSRPCOM(targetUrl, "", { referer });
      }
    }
  }
});

// 2. Intercept Messages from Content Script
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  const referer = (sender && sender.tab && sender.tab.url) || msg.referer || "";
  if (msg.action === "download" && msg.url) {
    sendToSRPCOM(msg.url, msg.filename || "", {
      referer: referer,
      cookies: msg.cookies || ""
    });
    sendResponse({ received: true });
  } else if (msg.action === "download_video" && msg.url) {
    sendVideoToSRPCOM(msg.url, msg.quality || "best", msg.title || "", {
      referer: referer,
      cookies: msg.cookies || ""
    });
    sendResponse({ received: true });
  }
  return true;
});

// 3. Intercept Native Browser Downloads (catches redirects, scripts, form downloads)
chrome.downloads.onCreated.addListener(async (downloadItem) => {
  const url = downloadItem.finalUrl || downloadItem.url;
  
  if (!url || url.startsWith("blob:") || url.startsWith("data:") || url.startsWith("chrome://")) {
    return;
  }

  // Cancel the native browser download
  chrome.downloads.cancel(downloadItem.id, () => {
    chrome.downloads.erase({ id: downloadItem.id });
  });

  const referer = downloadItem.referrer || "";
  await sendToSRPCOM(url, downloadItem.filename || "", { referer });
});

async function getCookiesForUrl(url) {
  try {
    if (chrome.cookies && url.startsWith("http")) {
      const cookies = await chrome.cookies.getAll({ url: url });
      if (cookies && cookies.length > 0) {
        return cookies.map((c) => `${c.name}=${c.value}`).join("; ");
      }
    }
  } catch (e) {
    console.debug("Could not get cookies for", url, e);
  }
  return "";
}

async function sendToSRPCOM(url, filename, options = {}) {
  const cookies = options.cookies || (await getCookiesForUrl(url));
  const payload = {
    url: url,
    filename: filename || "",
    cookies: cookies || "",
    referer: options.referer || "",
    user_agent: navigator.userAgent || ""
  };

  fetch(`${SERVER_BASE}/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then((res) => res.json())
    .catch((err) => {
      // Fallback to GET query params
      const query = new URLSearchParams({
        url: url,
        filename: filename || "",
        cookies: cookies || "",
        referer: options.referer || ""
      }).toString();
      fetch(`${SERVER_BASE}/add?${query}`).catch(() => {});
    });
}

async function sendVideoToSRPCOM(url, quality, title, options = {}) {
  const cookies = options.cookies || (await getCookiesForUrl(url));
  const payload = {
    url: url,
    quality: quality || "best",
    title: title || "",
    cookies: cookies || "",
    referer: options.referer || url,
    user_agent: navigator.userAgent || ""
  };

  fetch(`${SERVER_BASE}/download_video`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then((res) => res.json())
    .catch((err) => {
      // Fallback to GET query params
      const query = new URLSearchParams({
        url: url,
        quality: quality,
        title: title,
        cookies: cookies || "",
        referer: options.referer || url
      }).toString();
      fetch(`${SERVER_BASE}/download_video?${query}`).catch(() => {});
    });
}
