// ==========================================
// SRPCOM Download Manager (SDM) - Content Script
// 1. Direct Download Link Interception
// 2. IDM-Style Floating Video Grabber (YouTube & HTML5 Video)
// ==========================================

const DOWNLOAD_EXTENSIONS = [
  ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso",
  ".exe", ".msi", ".apk", ".bin",
  ".mp4", ".mkv", ".avi", ".mov", ".flv",
  ".mp3", ".wav", ".flac",
  ".pdf", ".docx", ".xlsx", ".pptx"
];

// 1. Intercept direct download links
document.addEventListener("click", (e) => {
  if (e.target.closest("#sdm-video-panel")) return;

  const link = e.target.closest("a");
  if (!link || !link.href) return;

  const urlStr = link.href.toLowerCase().split("?")[0].split("#")[0];
  const isDownload = DOWNLOAD_EXTENSIONS.some((ext) => urlStr.endsWith(ext));

  if (isDownload) {
    e.preventDefault();
    e.stopPropagation();
    chrome.runtime.sendMessage({
      action: "download",
      url: link.href,
      filename: link.download || "",
      cookies: document.cookie || "",
      referer: window.location.href
    });
    showToast("Mengirim unduhan ke SRPCOM Download Manager...");
  }
}, true);

// 2. IDM-Style Video Grabber Panel
function createVideoGrabber() {
  if (document.getElementById("sdm-video-panel")) return;

  // Find suitable container: on YouTube prefer #movie_player or .html5-video-player
  const isYouTube = window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be");
  let targetContainer = null;

  if (isYouTube) {
    // Only show on watch or shorts pages
    if (!window.location.pathname.includes("/watch") && !window.location.pathname.includes("/shorts")) {
      return;
    }
    targetContainer = document.getElementById("movie_player") || document.querySelector(".html5-video-player");
  } else {
    // Other video sites: find first active large video
    const videos = Array.from(document.querySelectorAll("video")).filter(v => {
      const rect = v.getBoundingClientRect();
      return rect.width > 240 && rect.height > 160;
    });
    if (videos.length > 0) {
      targetContainer = videos[0].parentElement || videos[0];
    }
  }

  if (!targetContainer) return;

  // Make sure container has relative positioning if not static
  const containerStyle = window.getComputedStyle(targetContainer);
  if (containerStyle.position === "static") {
    targetContainer.style.position = "relative";
  }

  const panel = document.createElement("div");
  panel.id = "sdm-video-panel";
  panel.style.cssText = `
    position: absolute;
    top: 14px;
    right: 14px;
    z-index: 2147483647;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    user-select: none;
    display: inline-block;
  `;

  panel.innerHTML = `
    <div id="sdm-btn-main" style="
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      color: #ffffff;
      border: 1px solid rgba(239, 68, 68, 0.6);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5);
      transition: all 0.2s ease;
    ">
      <span style="color: #ef4444; font-size: 14px;">⬇</span>
      <span>Unduh Video Ini (SDM)</span>
      <span style="font-size: 9px; opacity: 0.7; margin-left: 2px;">▼</span>
    </div>
    <div id="sdm-dropdown-menu" style="
      display: none;
      position: absolute;
      top: 100%;
      right: 0;
      margin-top: 4px;
      background: #181d28;
      border: 1px solid #374151;
      border-radius: 6px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
      min-width: 210px;
      overflow: hidden;
      z-index: 2147483647;
    ">
      <div class="sdm-menu-item" data-quality="best" style="padding: 8px 12px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #28303f;">
        <span>🎬</span> <b>Kualitas Terbaik</b> (1080p/HD MP4)
      </div>
      <div class="sdm-menu-item" data-quality="720" style="padding: 8px 12px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #28303f;">
        <span>🎥</span> <b>720p HD</b> (MP4)
      </div>
      <div class="sdm-menu-item" data-quality="480" style="padding: 8px 12px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #28303f;">
        <span>📱</span> <b>480p SD</b> (MP4)
      </div>
      <div class="sdm-menu-item" data-quality="360" style="padding: 8px 12px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #28303f;">
        <span>⚡</span> <b>360p Hemat</b> (MP4)
      </div>
      <div class="sdm-menu-item" data-quality="audio" style="padding: 8px 12px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px;">
        <span>🎵</span> <b>Audio Saja</b> (MP3 Musik)
      </div>
    </div>
  `;

  targetContainer.appendChild(panel);

  const mainBtn = panel.querySelector("#sdm-btn-main");
  const menu = panel.querySelector("#sdm-dropdown-menu");

  // Hover styling for main button
  mainBtn.addEventListener("mouseenter", () => {
    mainBtn.style.borderColor = "#ef4444";
    mainBtn.style.transform = "scale(1.02)";
  });
  mainBtn.addEventListener("mouseleave", () => {
    mainBtn.style.borderColor = "rgba(239, 68, 68, 0.6)";
    mainBtn.style.transform = "scale(1)";
  });

  // Toggle dropdown on click
  mainBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    menu.style.display = menu.style.display === "block" ? "none" : "block";
  });

  // Hover & Click on Menu Items
  panel.querySelectorAll(".sdm-menu-item").forEach((item) => {
    item.addEventListener("mouseenter", () => {
      item.style.background = "#2b3446";
      item.style.color = "#38bdf8";
    });
    item.addEventListener("mouseleave", () => {
      item.style.background = "transparent";
      item.style.color = "#f3f4f6";
    });
    item.addEventListener("click", (e) => {
      e.stopPropagation();
      const quality = item.getAttribute("data-quality") || "best";
      menu.style.display = "none";
      triggerVideoDownload(quality);
    });
  });

  // Close dropdown on click outside
  document.addEventListener("click", () => {
    menu.style.display = "none";
  });
}

function getPageVideoTitle() {
  const ytHeader = document.querySelector("h1.ytd-watch-metadata yt-formatted-string") ||
                   document.querySelector("h1.title yt-formatted-string") ||
                   document.querySelector("#title h1");
  if (ytHeader && ytHeader.textContent && ytHeader.textContent.trim()) {
    return ytHeader.textContent.trim();
  }

  if (document.title) {
    let t = document.title.replace(/\s*-\s*YouTube\s*$/i, "").trim();
    t = t.replace(/^\(\d+\)\s*/, "").replace(/^[🔴▶\s]+/, "").trim();
    if (t) return t;
  }
  return "";
}

function triggerVideoDownload(quality) {
  let videoUrl = window.location.href;
  const isYouTube = window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be");
  const activeVideo = document.querySelector("video");
  
  // If not YouTube and video element has direct http/https stream/mp4, prefer direct src if available
  if (!isYouTube && activeVideo && activeVideo.currentSrc && activeVideo.currentSrc.startsWith("http")) {
    videoUrl = activeVideo.currentSrc;
  }
  const videoTitle = getPageVideoTitle();

  chrome.runtime.sendMessage({
    action: "download_video",
    url: videoUrl,
    quality: quality,
    title: videoTitle,
    cookies: document.cookie || "",
    referer: window.location.href
  });

  showToast("🚀 Mengirim unduhan ke SRPCOM Download Manager...");
}

// 3. Floating In-Page Toast Notification
function showToast(message) {
  let toast = document.getElementById("sdm-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "sdm-toast";
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: rgba(15, 23, 42, 0.95);
      color: #ffffff;
      border: 1px solid #ef4444;
      border-radius: 8px;
      padding: 10px 18px;
      font-size: 13px;
      font-weight: 500;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
      z-index: 2147483647;
      opacity: 0;
      transition: opacity 0.3s ease, transform 0.3s ease;
      transform: translateY(10px);
      display: flex;
      align-items: center;
      gap: 8px;
    `;
    document.body.appendChild(toast);
  }

  toast.innerHTML = `<span style="color:#ef4444; font-size:16px;">⚡</span> <span>${message}</span>`;
  toast.style.opacity = "1";
  toast.style.transform = "translateY(0)";

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
  }, 3500);
}

// 4. Initialization & YouTube SPA Observer
function init() {
  createVideoGrabber();
}

// Run immediately & on interval to catch dynamic video players
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

setInterval(createVideoGrabber, 1800);

// Listen to YouTube SPA navigation events
window.addEventListener("yt-navigate-finish", () => {
  const existing = document.getElementById("sdm-video-panel");
  if (existing) existing.remove();
  setTimeout(createVideoGrabber, 500);
});

window.addEventListener("popstate", () => {
  const existing = document.getElementById("sdm-video-panel");
  if (existing) existing.remove();
  setTimeout(createVideoGrabber, 500);
});
