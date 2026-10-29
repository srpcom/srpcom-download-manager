// ==========================================
// SRPCOM Download Manager (SDM) - Content Script
// 1. Direct Download Link Interception
// 2. IDM-Style Floating Video Grabber (YouTube & HTML5 Video)
// 3. YouTube Action Bar Button (Below Video Title)
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
  if (e.target.closest("#sdm-video-panel") || e.target.closest("#sdm-yt-action-bar")) return;

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

// 2. Helper: Find active video and player container
function getActiveVideoContainer() {
  const isYouTube = window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be");

  if (isYouTube) {
    const isWatchOrShorts = window.location.pathname.includes("/watch") ||
                            window.location.pathname.includes("/shorts") ||
                            window.location.pathname.includes("/live");
    if (!isWatchOrShorts) return null;

    // 1. Look for active video element first
    const activeVideo = Array.from(document.querySelectorAll("video")).find(v => {
      return (v.offsetWidth > 150 && v.offsetHeight > 100) || (!v.paused && v.currentTime > 0);
    }) || document.querySelector("video");

    if (activeVideo) {
      const parentPlayer = activeVideo.closest(".html5-video-player") ||
                           activeVideo.closest("#movie_player") ||
                           activeVideo.closest("ytd-player") ||
                           activeVideo.parentElement;
      if (parentPlayer) return parentPlayer;
    }

    // 2. Fallbacks for YouTube
    return document.getElementById("movie_player") ||
           document.querySelector(".html5-video-player") ||
           document.querySelector("ytd-player #container") ||
           document.querySelector("#player-container");
  } else {
    // Non-YouTube video sites (Facebook, TikTok, Vimeo, Bilibili, etc.)
    const videos = Array.from(document.querySelectorAll("video")).filter(v => {
      const rect = v.getBoundingClientRect();
      return (rect.width > 200 && rect.height > 120) || (v.offsetWidth > 200 && v.offsetHeight > 120);
    });
    if (videos.length > 0) {
      const playing = videos.find(v => !v.paused && v.currentTime > 0);
      const chosen = playing || videos[0];
      return chosen.parentElement || chosen;
    }
  }

  return null;
}

// 3. IDM-Style Floating Video Grabber Panel
function createVideoGrabber() {
  const isYouTube = window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be");
  const targetContainer = getActiveVideoContainer();
  if (!targetContainer) return;

  const existingPanel = document.getElementById("sdm-video-panel");
  if (existingPanel) {
    // If properly attached inside target container and visible, keep it
    if (targetContainer.contains(existingPanel) && existingPanel.isConnected) {
      return;
    }
    existingPanel.remove();
  }

  // Ensure target container is positioned relative
  const containerStyle = window.getComputedStyle(targetContainer);
  if (containerStyle.position === "static") {
    targetContainer.style.position = "relative";
  }

  const panel = document.createElement("div");
  panel.id = "sdm-video-panel";

  // Position: On YouTube, place just below the top control bar (top: 55px; right: 16px)
  // On other sites, place at top: 14px; right: 14px;
  const topOffset = isYouTube ? "55px" : "14px";
  const rightOffset = "16px";

  panel.style.cssText = `
    position: absolute !important;
    top: ${topOffset} !important;
    right: ${rightOffset} !important;
    z-index: 2147483647 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    user-select: none !important;
    display: inline-block !important;
    opacity: 0.95;
    visibility: visible !important;
    pointer-events: auto;
    margin: 0 !important;
    padding: 0 !important;
    line-height: normal !important;
    transform: translateY(0);
    transition: opacity 0.35s ease, transform 0.35s ease !important;
  `;

  panel.innerHTML = `
    <div id="sdm-btn-main" style="
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
      color: #ffffff !important;
      border: 1.5px solid rgba(239, 68, 68, 0.8) !important;
      border-radius: 6px !important;
      padding: 6px 12px !important;
      font-size: 12px !important;
      font-weight: 600 !important;
      cursor: pointer !important;
      display: flex !important;
      align-items: center !important;
      gap: 6px !important;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6) !important;
      transition: all 0.2s ease !important;
      pointer-events: auto !important;
    ">
      <span style="color: #ef4444; font-size: 14px; font-weight: bold;">⬇</span>
      <span style="color: #ffffff; font-size: 12px;">Unduh Video Ini (SDM)</span>
      <span style="font-size: 9px; opacity: 0.8; margin-left: 2px;">▼</span>
    </div>
    <div id="sdm-dropdown-menu" style="
      display: none;
      position: absolute !important;
      top: 100% !important;
      right: 0 !important;
      margin-top: 4px !important;
      background: #181d28 !important;
      border: 1px solid #374151 !important;
      border-radius: 6px !important;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7) !important;
      min-width: 220px !important;
      overflow: hidden !important;
      z-index: 2147483647 !important;
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

  // Auto-hide controller:
  // Automatically hides the button during video watching so it doesn't disturb viewing.
  // Smoothly fades back in when user moves the mouse over the video player.
  let hideTimer = null;
  let isPanelHovered = false;

  function showPanel() {
    panel.style.setProperty("opacity", "0.95", "important");
    panel.style.setProperty("pointer-events", "auto", "important");
    panel.style.setProperty("transform", "translateY(0)", "important");
  }

  function hidePanel() {
    if (isPanelHovered || menu.style.display === "block") return;
    panel.style.setProperty("opacity", "0", "important");
    panel.style.setProperty("pointer-events", "none", "important");
    panel.style.setProperty("transform", "translateY(-4px)", "important");
  }

  function scheduleHide(delayMs = 2800) {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      hidePanel();
    }, delayMs);
  }

  function onPlayerActivity() {
    showPanel();
    scheduleHide(2800);
  }

  function onPlayerLeave() {
    scheduleHide(800);
  }

  // Bind mouse activity listeners on video player container
  if (targetContainer._sdm_onActivity) {
    targetContainer.removeEventListener("mousemove", targetContainer._sdm_onActivity);
    targetContainer.removeEventListener("mouseenter", targetContainer._sdm_onActivity);
    targetContainer.removeEventListener("mouseleave", targetContainer._sdm_onLeave);
  }
  targetContainer._sdm_onActivity = onPlayerActivity;
  targetContainer._sdm_onLeave = onPlayerLeave;
  targetContainer.addEventListener("mousemove", onPlayerActivity);
  targetContainer.addEventListener("mouseenter", onPlayerActivity);
  targetContainer.addEventListener("mouseleave", onPlayerLeave);

  // Bind play/pause on video element
  const vidElem = targetContainer.querySelector("video") || document.querySelector("video");
  if (vidElem && !vidElem._sdm_playBound) {
    vidElem._sdm_playBound = true;
    vidElem.addEventListener("play", onPlayerActivity);
    vidElem.addEventListener("pause", onPlayerActivity);
  }

  // Hover styling and keeping panel visible when cursor is over the button
  panel.addEventListener("mouseenter", () => {
    isPanelHovered = true;
    clearTimeout(hideTimer);
    panel.style.setProperty("opacity", "1", "important");
    mainBtn.style.borderColor = "#ef4444";
    mainBtn.style.transform = "scale(1.02)";
  });
  panel.addEventListener("mouseleave", () => {
    isPanelHovered = false;
    mainBtn.style.borderColor = "rgba(239, 68, 68, 0.8)";
    mainBtn.style.transform = "scale(1)";
    scheduleHide(2000);
  });

  // Toggle dropdown on click
  mainBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const willOpen = menu.style.display !== "block";
    menu.style.display = willOpen ? "block" : "none";
    if (willOpen) {
      clearTimeout(hideTimer);
      showPanel();
    } else {
      scheduleHide(2000);
    }
  });

  // Quality menu clicks
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
      scheduleHide(1000);
      triggerVideoDownload(quality);
    });
  });

  // Close dropdown on click outside
  document.addEventListener("click", () => {
    if (menu.style.display === "block") {
      menu.style.display = "none";
      scheduleHide(1500);
    }
  });

  // Initial appearance: show for 3.5 seconds on load, then auto-hide
  showPanel();
  scheduleHide(3500);
}

// 4. Native Action Bar Button (Below Video Title on YouTube)
function createYouTubeActionBarButton() {
  const isYouTube = window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be");
  if (!isYouTube || !window.location.pathname.includes("/watch")) return;

  const existingBarBtn = document.getElementById("sdm-yt-action-bar");
  if (existingBarBtn && existingBarBtn.isConnected) return;
  if (existingBarBtn) existingBarBtn.remove();

  // Find YouTube's action buttons container (Like, Share, Download, etc.)
  const actionsContainer = document.querySelector("#top-level-buttons-computed") ||
                           document.querySelector("ytd-watch-metadata #actions #top-level-buttons-computed") ||
                           document.querySelector("ytd-menu-renderer #top-level-buttons-computed");
  if (!actionsContainer) return;

  const wrapper = document.createElement("div");
  wrapper.id = "sdm-yt-action-bar";
  wrapper.style.cssText = `
    display: inline-flex !important;
    align-items: center !important;
    position: relative !important;
    margin-left: 8px !important;
    user-select: none !important;
    z-index: 100 !important;
  `;

  wrapper.innerHTML = `
    <button id="sdm-yt-action-btn" type="button" style="
      background: rgba(239, 68, 68, 0.15) !important;
      color: #ffffff !important;
      border: 1px solid #ef4444 !important;
      border-radius: 18px !important;
      height: 36px !important;
      padding: 0 14px !important;
      font-size: 13px !important;
      font-weight: 600 !important;
      font-family: Roboto, Arial, sans-serif !important;
      cursor: pointer !important;
      display: inline-flex !important;
      align-items: center !important;
      gap: 6px !important;
      transition: all 0.2s ease !important;
    ">
      <span style="color: #ef4444; font-size: 14px;">⚡</span>
      <span>Unduh SDM</span>
      <span style="font-size: 10px; opacity: 0.8;">▼</span>
    </button>
    <div id="sdm-yt-action-menu" style="
      display: none;
      position: absolute !important;
      top: 100% !important;
      left: 0 !important;
      margin-top: 6px !important;
      background: #181d28 !important;
      border: 1px solid #374151 !important;
      border-radius: 8px !important;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.8) !important;
      min-width: 220px !important;
      overflow: hidden !important;
      z-index: 2147483647 !important;
    ">
      <div class="sdm-action-item" data-quality="best" style="padding: 9px 14px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #28303f;">
        <span>🎬</span> <b>Kualitas Terbaik</b> (1080p MP4)
      </div>
      <div class="sdm-action-item" data-quality="720" style="padding: 9px 14px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #28303f;">
        <span>🎥</span> <b>720p HD</b> (MP4)
      </div>
      <div class="sdm-action-item" data-quality="480" style="padding: 9px 14px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #28303f;">
        <span>📱</span> <b>480p SD</b> (MP4)
      </div>
      <div class="sdm-action-item" data-quality="360" style="padding: 9px 14px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #28303f;">
        <span>⚡</span> <b>360p Hemat</b> (MP4)
      </div>
      <div class="sdm-action-item" data-quality="audio" style="padding: 9px 14px; color: #f3f4f6; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 8px;">
        <span>🎵</span> <b>Audio Saja</b> (MP3 Musik)
      </div>
    </div>
  `;

  actionsContainer.appendChild(wrapper);

  const btn = wrapper.querySelector("#sdm-yt-action-btn");
  const actMenu = wrapper.querySelector("#sdm-yt-action-menu");

  btn.addEventListener("mouseenter", () => {
    btn.style.background = "rgba(239, 68, 68, 0.3) !important";
    btn.style.transform = "scale(1.02)";
  });
  btn.addEventListener("mouseleave", () => {
    btn.style.background = "rgba(239, 68, 68, 0.15) !important";
    btn.style.transform = "scale(1)";
  });

  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    actMenu.style.display = actMenu.style.display === "block" ? "none" : "block";
  });

  wrapper.querySelectorAll(".sdm-action-item").forEach((item) => {
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
      actMenu.style.display = "none";
      triggerVideoDownload(quality);
    });
  });

  document.addEventListener("click", () => {
    actMenu.style.display = "none";
  });
}

function getPageVideoTitle() {
  const isYouTube = window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be");

  // 1. YouTube specific title detection
  if (isYouTube) {
    const ytPrimary = document.querySelector("ytd-watch-metadata #title h1 yt-formatted-string") ||
                      document.querySelector("#above-the-fold #title h1 yt-formatted-string") ||
                      document.querySelector("#below #title h1 yt-formatted-string") ||
                      document.querySelector("h1.ytd-watch-metadata yt-formatted-string");
    if (ytPrimary && ytPrimary.textContent && ytPrimary.textContent.trim()) {
      return ytPrimary.textContent.trim();
    }

    if (document.title) {
      let t = document.title.replace(/\s*-\s*YouTube\s*$/i, "").trim();
      t = t.replace(/^\(\d+\)\s*/, "").replace(/^[🔴▶\s]+/, "").trim();
      if (t && t.toLowerCase() !== "youtube") {
        return t;
      }
    }
  }

  // 2. Generic document.title
  if (document.title) {
    let t = document.title.replace(/\s*-\s*(YouTube|Vimeo|Dailymotion|Facebook)\s*$/i, "").trim();
    t = t.replace(/^\(\d+\)\s*/, "").replace(/^[🔴▶\s]+/, "").trim();
    if (t) return t;
  }

  // 3. Fallback generic headers
  const genericH1 = document.querySelector("h1");
  if (genericH1 && genericH1.textContent && genericH1.textContent.trim()) {
    return genericH1.textContent.trim();
  }

  return "";
}

function triggerVideoDownload(quality) {
  let videoUrl = window.location.href;
  const isYouTube = window.location.hostname.includes("youtube.com") || window.location.hostname.includes("youtu.be");
  const activeVideo = document.querySelector("video");
  
  // Clean YouTube watch or shorts URL to standard clean watch format
  if (isYouTube) {
    try {
      const u = new URL(videoUrl);
      if (u.pathname.includes("/watch")) {
        const vid = u.searchParams.get("v");
        if (vid) {
          videoUrl = `https://www.youtube.com/watch?v=${vid}`;
        }
      } else if (u.pathname.includes("/shorts/")) {
        const parts = u.pathname.split("/shorts/");
        if (parts[1]) {
          const shortId = parts[1].split("/")[0].split("?")[0];
          videoUrl = `https://www.youtube.com/watch?v=${shortId}`;
        }
      }
    } catch (e) {}
  } else if (!isYouTube && activeVideo && activeVideo.currentSrc && activeVideo.currentSrc.startsWith("http")) {
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

// 5. Floating In-Page Toast Notification
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

// 6. Unified Update Manager
function updateAllGrabbers() {
  createVideoGrabber();
  createYouTubeActionBarButton();
}

function reinitGrabbers() {
  const oldPanel = document.getElementById("sdm-video-panel");
  if (oldPanel) oldPanel.remove();
  const oldAction = document.getElementById("sdm-yt-action-bar");
  if (oldAction) oldAction.remove();

  updateAllGrabbers();
  setTimeout(updateAllGrabbers, 600);
  setTimeout(updateAllGrabbers, 1500);
}

// Run immediately and on DOM events
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", updateAllGrabbers);
} else {
  updateAllGrabbers();
}

// Fast periodic check
setInterval(updateAllGrabbers, 1200);

// Listen to YouTube and SPA navigation events on BOTH document & window
document.addEventListener("yt-navigate-finish", reinitGrabbers);
document.addEventListener("yt-page-data-updated", reinitGrabbers);
window.addEventListener("yt-navigate-finish", reinitGrabbers);
window.addEventListener("popstate", reinitGrabbers);

// MutationObserver to catch dynamic video players as soon as they appear in the DOM
const domObserver = new MutationObserver(() => {
  const isWatch = window.location.pathname.includes("/watch") || window.location.pathname.includes("/shorts");
  const needsPanel = !document.getElementById("sdm-video-panel") && !!document.querySelector("video");
  const needsActionBar = isWatch && !document.getElementById("sdm-yt-action-bar") && !!document.querySelector("#top-level-buttons-computed");
  if (needsPanel || needsActionBar) {
    updateAllGrabbers();
  }
});

function startObserver() {
  const root = document.documentElement || document.body;
  if (root) {
    try {
      domObserver.observe(root, {
        childList: true,
        subtree: true
      });
    } catch (e) {}
  } else {
    document.addEventListener("DOMContentLoaded", startObserver);
  }
}
startObserver();
