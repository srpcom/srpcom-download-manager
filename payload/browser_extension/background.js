const SERVER_BASE = "http://127.0.0.1:9876";

// 1. Right Click Context Menus
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

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "srpcom-download-video") {
    const videoUrl = info.srcUrl || (tab && tab.url) || "";
    const title = (tab && tab.title) || "";
    if (videoUrl) {
      sendVideoToSRPCOM(videoUrl, "best", title);
    }
  } else {
    const targetUrl = info.linkUrl || info.srcUrl;
    if (targetUrl) {
      sendToSRPCOM(targetUrl, "");
    }
  }
});

// 2. Intercept Messages from Content Script
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "download" && msg.url) {
    sendToSRPCOM(msg.url, msg.filename || "");
    sendResponse({ received: true });
  } else if (msg.action === "download_video" && msg.url) {
    sendVideoToSRPCOM(msg.url, msg.quality || "best", msg.title || "");
    sendResponse({ received: true });
  }
});

// 3. Intercept Native Browser Downloads (catches redirects, scripts, form downloads)
chrome.downloads.onCreated.addListener((downloadItem) => {
  const url = downloadItem.finalUrl || downloadItem.url;
  
  if (!url || url.startsWith("blob:") || url.startsWith("data:") || url.startsWith("chrome://")) {
    return;
  }

  // Cancel the native browser download
  chrome.downloads.cancel(downloadItem.id, () => {
    chrome.downloads.erase({ id: downloadItem.id });
  });

  // Forward to desktop SRPCOM Download Manager
  sendToSRPCOM(url, downloadItem.filename || "");
});

function sendToSRPCOM(url, filename) {
  const query = new URLSearchParams({
    url: url,
    filename: filename
  }).toString();

  fetch(`${SERVER_BASE}/add?${query}`, { method: "GET" })
    .then((res) => res.json())
    .catch((err) => {
      console.warn("Could not reach SRPCOM Download Manager. Pastikan aplikasi SRPCOM terbuka!", err);
    });
}

function sendVideoToSRPCOM(url, quality, title) {
  const query = new URLSearchParams({
    url: url,
    quality: quality,
    title: title
  }).toString();

  fetch(`${SERVER_BASE}/download_video?${query}`, { method: "GET" })
    .then((res) => res.json())
    .catch((err) => {
      console.warn("Could not reach SRPCOM Download Manager for video download. Pastikan aplikasi SRPCOM terbuka!", err);
    });
}
