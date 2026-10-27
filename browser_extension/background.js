const SERVER_BASE = "http://127.0.0.1:9876";

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
  if (info.menuItemId === "srpcom-download-video") {
    const videoUrl = info.srcUrl || (tab && tab.url) || "";
    const title = (tab && tab.title) || "";
    if (videoUrl) {
      await sendVideoToSRPCOM(videoUrl, "best", title, { referer });
    }
  } else {
    const targetUrl = info.linkUrl || info.srcUrl;
    if (targetUrl) {
      await sendToSRPCOM(targetUrl, "", { referer });
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
