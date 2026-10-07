let currentCategory = "all";
let currentQuickFilter = "all";
let currentSearch = "";
let currentOffset = 0;
const PAGE_LIMIT = 40;
let totalDeals = 0;
let searchTimer = null;

// Initial setup
document.addEventListener("DOMContentLoaded", () => {
    initCountdownTimer();
    loadStats();
    loadDeals(true);
    checkCrawlerStatus();

    setInterval(checkCrawlerStatus, 6000);
    setInterval(loadStats, 30000);
});

// Toast notification
function showToast(msg) {
    const box = document.getElementById("toast-container");
    const el = document.createElement("div");
    el.className = "toast";
    el.innerText = msg;
    box.appendChild(el);
    setTimeout(() => {
        el.style.opacity = "0";
        setTimeout(() => el.remove(), 250);
    }, 3200);
}

// Countdown timer to Lazada Flash Sale frames [0, 8, 12, 20]
function initCountdownTimer() {
    const frames = [0, 8, 12, 20];

    function update() {
        const now = new Date();
        const curH = now.getHours();
        let nextH = null;
        let isTomorrow = false;

        for (const h of frames) {
            if (curH < h) {
                nextH = h;
                break;
            }
        }
        if (nextH === null) {
            nextH = 0;
            isTomorrow = true;
        }

        const target = new Date(now);
        if (isTomorrow) {
            target.setDate(target.getDate() + 1);
        }
        target.setHours(nextH, 0, 0, 0);

        const diff = Math.max(0, Math.floor((target.getTime() - now.getTime()) / 1000));
        const hours = Math.floor(diff / 3600);
        const minutes = Math.floor((diff % 3600) / 60);
        const seconds = diff % 60;

        document.getElementById("deal-hours").innerText = String(hours).padStart(2, '0');
        document.getElementById("deal-minutes").innerText = String(minutes).padStart(2, '0');
        document.getElementById("deal-seconds").innerText = String(seconds).padStart(2, '0');
        document.getElementById("deal-next-slot").innerText = `Lên Deal Khung ${nextH}H${isTomorrow ? ' ngày mai' : ''}`;
    }

    update();
    setInterval(update, 1000);
}

// Load stats and last updated timestamp
async function loadStats() {
    try {
        const resp = await fetch("/api/stats");
        const res = await resp.json();
        if (res.status === "success") {
            const s = res.stats;
            document.getElementById("total-deals-count").innerText = Number(s.total_deals || 0).toLocaleString();
            if (s.last_updated) {
                const dt = new Date(s.last_updated);
                const dStr = dt.toLocaleDateString("vi-VN", { day: '2-digit', month: '2-digit', year: 'numeric' });
                const tStr = dt.toLocaleTimeString("vi-VN", { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                document.getElementById("last-update-time").innerText = `${dStr} ${tStr}`;
            }
        }
    } catch (e) {
        console.error("loadStats error:", e);
    }
}

// Major Category Selector
function selectCategory(cat, el) {
    document.querySelectorAll(".cat-btn").forEach(b => b.classList.remove("active"));
    el.classList.add("active");
    currentCategory = cat;
    loadDeals(true);
}

// Quick Price & Deal Filter Selector
function selectQuickFilter(filter, el) {
    document.querySelectorAll(".filter-pill-btn").forEach(b => b.classList.remove("active"));
    el.classList.add("active");
    currentQuickFilter = filter;
    loadDeals(true);
}

// Live Search
function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        currentSearch = document.getElementById("search-input").value.trim();
        loadDeals(true);
    }, 280);
}

// Load deals
async function loadDeals(reset = false) {
    if (reset) {
        currentOffset = 0;
    }

    let url = `/api/deals?limit=${PAGE_LIMIT}&offset=${currentOffset}&sort=discount_desc`;
    if (currentCategory && currentCategory !== "all") {
        url += `&category=${encodeURIComponent(currentCategory)}`;
    }
    
    // Quick filter params
    if (currentQuickFilter === "discount_50") {
        url += `&min_discount=50`;
    } else if (currentQuickFilter === "price_50k") {
        url += `&max_price=50000`;
    } else if (currentQuickFilter === "price_1k_9k") {
        url += `&min_price=1000&max_price=9999`;
    } else if (currentQuickFilter === "tmall") {
        url += `&is_tmall=true`;
    }

    if (currentSearch) {
        url += `&q=${encodeURIComponent(currentSearch)}`;
    }

    try {
        const resp = await fetch(url);
        const data = await resp.json();
        const deals = data.deals || [];
        totalDeals = data.total || 0;

        const grid = document.getElementById("product-grid");
        const emptyState = document.getElementById("empty-state");
        const loadMore = document.getElementById("load-more-container");

        if (reset) {
            grid.innerHTML = "";
        }

        if (deals.length === 0 && reset) {
            emptyState.style.display = "block";
            loadMore.style.display = "none";
            return;
        }

        emptyState.style.display = "none";

        const cardsHtml = deals.map(d => {
            const pSale = Math.round(d.display_price || d.flash_price || 0);
            const pOrig = Math.round(d.original_price || 0);
            const disc = d.discount_percent ? d.discount_percent.replace("%", "") : "";
            const title = escapeHtml(d.title || "Sản phẩm Lazada Flash Sale");
            const img = d.image_url || "https://filebroker-cdn.lazada.vn/kf/Se5e6b6f8d4a34475b57f25795dec4ef8p.jpg";
            const affLink = d.affiliate_url || d.product_url || "#";
            const checkUrl = d.product_url || affLink;

            let badgeHtml = "";
            if (disc && parseInt(disc) > 0) {
                badgeHtml = `<div class="deal-badge">-${disc}%</div>`;
            } else if (pSale <= 1000 && pSale > 0) {
                badgeHtml = `<div class="deal-badge">-99%</div>`;
            }

            return `
                <div class="deal-card">
                    ${badgeHtml}
                    <div class="card-img-wrapper">
                        <img class="card-img" loading="lazy" src="${img}" alt="${title}">
                    </div>
                    <div class="card-title" title="${title}">${title}</div>
                    <div class="card-prices">
                        <div style="display: flex; align-items: baseline; gap: 6px;">
                            <span class="price-sale">${pSale.toLocaleString()}đ</span>
                            ${pOrig > pSale ? `<span class="price-original">${pOrig.toLocaleString()}đ</span>` : ""}
                        </div>
                        <span style="font-size: 10px; font-weight: 700; color: #ff5722; background: rgba(255,87,34,0.1); padding: 2px 5px; border-radius: 4px; white-space: nowrap;">⚡ Flash Sale</span>
                    </div>
                    <div class="card-actions">
                        <button class="btn-card btn-get-link" onclick="copyAffiliateLink('${affLink}')">
                            Lấy Link
                        </button>
                        <a href="${checkUrl}" target="_blank" rel="noopener noreferrer" class="btn-card btn-check-price">
                            Check Giá
                        </a>
                    </div>
                </div>
            `;
        }).join("");

        grid.insertAdjacentHTML("beforeend", cardsHtml);

        currentOffset += deals.length;
        if (currentOffset < totalDeals) {
            loadMore.style.display = "block";
        } else {
            loadMore.style.display = "none";
        }

    } catch (e) {
        console.error("loadDeals error:", e);
    }
}

function loadMoreDeals() {
    loadDeals(false);
}

// Copy link action
function copyAffiliateLink(url) {
    if (!url || url === "#") {
        showToast("Không tìm thấy liên kết!");
        return;
    }
    navigator.clipboard.writeText(url).then(() => {
        showToast("✅ Đã sao chép link ưu đãi!");
    }).catch(() => {
        showToast("Không thể sao chép link");
    });
}

// Trigger background crawl
async function triggerCrawlNow() {
    const btn = document.getElementById("btn-crawl-now");
    const icon = document.getElementById("crawl-icon");
    const text = document.getElementById("crawl-text");

    btn.disabled = true;
    icon.innerText = "⏳";
    text.innerText = "Đang quét...";

    try {
        const resp = await fetch("/api/crawl/now", { method: "POST" });
        const res = await resp.json();
        showToast(res.message);
    } catch (e) {
        showToast("Lỗi kết nối máy chủ quét deal!");
    }
}

async function checkCrawlerStatus() {
    try {
        const resp = await fetch("/api/crawler/status");
        const res = await resp.json();
        const btn = document.getElementById("btn-crawl-now");
        const icon = document.getElementById("crawl-icon");
        const text = document.getElementById("crawl-text");

        if (res.is_crawling) {
            btn.disabled = true;
            icon.innerText = "⏳";
            text.innerText = "Đang quét...";
        } else {
            btn.disabled = false;
            icon.innerText = "⚡";
            text.innerText = "Quét Toàn Sàn";
        }
    } catch (e) {
        // ignore
    }
}

// Settings modal
async function openSettingsModal() {
    document.getElementById("settings-modal").classList.add("open");
    try {
        const resp = await fetch("/api/settings");
        const res = await resp.json();
        if (res.status === "success") {
            const s = res.settings;
            document.getElementById("cfg-aff-id").value = s.affiliate_id || "";
            document.getElementById("cfg-tele-token").value = s.telegram_bot_token || "";
            document.getElementById("cfg-tele-chat").value = s.telegram_chat_id || "";
            document.getElementById("cfg-interval").value = s.crawl_interval_minutes || "15";
        }
    } catch (e) {
        console.error(e);
    }
}

function closeSettingsModal() {
    document.getElementById("settings-modal").classList.remove("open");
}

async function saveSettings() {
    const payload = {
        affiliate_id: document.getElementById("cfg-aff-id").value.trim(),
        telegram_bot_token: document.getElementById("cfg-tele-token").value.trim(),
        telegram_chat_id: document.getElementById("cfg-tele-chat").value.trim(),
        crawl_interval_minutes: document.getElementById("cfg-interval").value.trim()
    };
    try {
        const resp = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const res = await resp.json();
        showToast(res.message);
        closeSettingsModal();
    } catch (e) {
        showToast("Lỗi lưu cấu hình!");
    }
}

async function testTelegramAlert() {
    try {
        const resp = await fetch("/api/notify/test", { method: "POST" });
        const res = await resp.json();
        showToast(res.message);
    } catch (e) {
        showToast("Lỗi gửi thử nghiệm!");
    }
}

function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}
