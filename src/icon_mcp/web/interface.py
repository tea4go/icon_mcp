"""Web interface - generates HTML and JS for icon selection UI."""

from __future__ import annotations

from ..lang import t, get_current_language


class WebInterface:
    """Generates the HTML/JS for the icon selection web UI."""

    def __init__(self, port: int = 31245):
        self.port = port

    def generate_html(self, search_id: str = "") -> str:
        """Generate the main HTML page."""
        lang = get_current_language()
        title = t("web.title")
        subtitle = t("web.subtitle")
        search_placeholder = t("web.searchPlaceholder")
        search_btn = t("web.searchButton")
        send_btn = t("web.sendSelected")
        no_selected = t("web.noIconsSelected")
        loading = t("web.loading")
        prev_text = t("web.previous")
        next_text = t("web.next")

        return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px 32px;
            text-align: center;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 6px; }}
        .header p {{ opacity: 0.85; font-size: 14px; }}
        .search-bar {{
            max-width: 600px;
            margin: 16px auto 0;
            display: flex;
            gap: 8px;
        }}
        .search-bar input {{
            flex: 1;
            padding: 10px 16px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            outline: none;
        }}
        .search-bar .search-btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.9);
            color: #5a4a8a;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: background 0.2s;
        }}
        .search-bar .search-btn:hover {{ background: #fff; }}
        .search-bar .search-btn:disabled {{ opacity: 0.6; cursor: not-allowed; }}
        .main {{
            width: 90%;
            margin: 0 auto;
            padding: 16px 0;
            display: flex;
            gap: 20px;
        }}
        .icon-area {{ flex: 1; }}
        .sidebar {{
            width: 280px;
            flex-shrink: 0;
        }}
        .icon-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 8px;
            overflow: visible;
        }}
        .icon-card {{
            background: white;
            border-radius: 8px;
            padding: 5px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
            aspect-ratio: 1;
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .icon-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        }}
        .icon-card.selected {{
            border: 2px solid #667eea;
            background: #f0f0ff;
        }}
        .icon-preview {{
            width: 56px;
            height: 56px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .icon-preview img, .icon-preview svg {{
            width: 100% !important;
            height: 100% !important;
        }}
        .icon-name {{
            font-size: 11px;
            color: #555;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .icon-card .btn {{
            margin-top: 0;
            padding: 3px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
            background: #667eea;
            color: white;
            transition: background 0.2s;
            width: 20px;
            height: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }}
        .icon-card .btn:hover {{ background: #5a6fd6; }}
        .icon-card .btn.select-btn {{
            position: absolute;
            top: 4px;
            left: 4px;
            background: transparent;
            color: transparent;
            border: none;
            box-shadow: none;
        }}
        .icon-card .btn.selected-btn {{
            background: #4caf50;
            color: white;
        }}
        .card-actions {{
            position: absolute;
            bottom: 4px;
            right: 4px;
            display: flex;
            gap: 2px;
        }}
        .card-actions .btn {{
            margin-top: 0;
            padding: 3px;
            font-size: 14px;
            width: 20px;
            height: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }}
        .card-actions .save-dropdown {{ position: relative; display: inline-flex; width: 20px; height: 20px; overflow: visible; }}
        .card-actions .save-dropdown .btn.save-btn {{ padding: 0; font-size: 14px; line-height: 1; width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center; overflow: visible; }}
        .icon-card .btn.copy-btn {{
            background: #f0f0f5;
            color: #555;
        }}
        .icon-card .btn.copy-btn:hover {{ background: #e2e2ee; }}
        .icon-card .btn.copy-btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}
        .save-dropdown {{ position: relative; display: inline-block; }}
        .icon-card .btn.save-btn {{
            background: #f0f0f5;
            color: #555;
        }}
        .icon-card .btn.save-btn:hover {{ background: #e2e2ee; }}
        .icon-card .btn.save-btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}
        .save-menu {{
            display: none;
            position: fixed;
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            overflow: hidden;
            min-width: 110px;
        }}
        .save-menu.open {{ display: block; }}
        .save-menu button {{
            display: block;
            width: 100%;
            padding: 6px 14px;
            border: none;
            background: white;
            color: #555;
            font-size: 13px;
            text-align: left;
            cursor: pointer;
        }}
        .save-menu button:hover {{ background: #f0f0f5; }}
        .sidebar-box {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            position: sticky;
            top: 24px;
        }}
        .sidebar-box h3 {{
            font-size: 16px;
            margin-bottom: 12px;
            color: #333;
        }}
        .selected-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        .selected-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            border-bottom: 1px solid #eee;
            font-size: 13px;
        }}
        .selected-item .remove-btn {{
            margin-left: auto;
            background: none;
            border: none;
            color: #e74c3c;
            cursor: pointer;
            font-size: 16px;
        }}
        .send-btn {{
            width: 100%;
            padding: 12px;
            margin-top: 16px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .send-btn:hover {{ opacity: 0.9; }}
        .send-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            margin-top: 24px;
            flex-wrap: wrap;
        }}
        .pagination button {{
            padding: 8px 14px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: white;
            cursor: pointer;
            font-size: 14px;
        }}
        .pagination button:hover {{ background: #f0f0f0; }}
        .pagination button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
        .pagination button.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        .pagination .page-info {{
            font-size: 14px;
            color: #666;
        }}
        .loading {{
            text-align: center;
            padding: 60px;
            font-size: 16px;
            color: #999;
        }}
        .spinner {{
            display: inline-block;
            width: 36px;
            height: 36px;
            border: 3px solid #eee;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-bottom: 12px;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .message {{
            padding: 12px 20px;
            border-radius: 8px;
            margin: 16px 0;
            font-size: 14px;
            display: none;
        }}
        .message.success {{ background: #d4edda; color: #155724; display: block; }}
        .message.error {{ background: #f8d7da; color: #721c24; display: block; }}
        @media (max-width: 768px) {{
            .main {{ flex-direction: column; padding: 16px; }}
            .sidebar {{ width: 100%; }}
            .icon-grid {{ grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p><a href="https://www.iconfont.cn" target="_blank" style="color:inherit;opacity:0.85">{subtitle}</a></p>
        <div class="search-bar">
            <input type="text" id="filterInput" placeholder="{search_placeholder}"
                   oninput="filterIcons(this.value)"
                   onkeydown="if(event.key==='Enter'){{remoteSearch();}}">
            <button id="searchBtn" class="search-btn" onclick="remoteSearch()">{search_btn}</button>
        </div>
    </div>
    <div class="main">
        <div class="icon-area">
            <div id="message" class="message"></div>
            <div id="loading" class="loading" style="display:none;">
                <div class="spinner"></div>
                <div>{loading}</div>
            </div>
            <div id="iconGrid" class="icon-grid"></div>
            <div id="pagination" class="pagination" style="display:none;">
                <button id="prevBtn" onclick="goToPage(currentPage-1)">{prev_text}</button>
                <span id="pageNumbers"></span>
                <button id="nextBtn" onclick="goToPage(currentPage+1)">{next_text}</button>
            </div>
        </div>
        <div class="sidebar">
            <div class="sidebar-box">
                <h3 id="selectedTitle">{no_selected}</h3>
                <div id="selectedList" class="selected-list"></div>
                <button class="send-btn" id="sendBtn" onclick="sendSelectedIcons()" disabled>
                    {send_btn}
                </button>
            </div>
        </div>
    </div>
    <script>
        const SEARCH_ID = '{search_id}';
        const WS_PORT = {self.port};
    </script>
    <script src="/site.js"></script>
    <!-- 全局保存菜单，避免被卡片遮挡 -->
    <div id="globalSaveMenu" class="save-menu">
        <button data-fmt="png">PNG</button>
        <button data-fmt="bmp">BMP</button>
        <button data-fmt="ico">ICO</button>
    </div>
</body>
</html>"""

    def generate_js(self) -> str:
        """Generate client-side JavaScript."""
        selected_text = t("web.selectedCount")
        no_selected = t("web.noIconsSelected")
        select_btn = t("web.selectButton")
        selected_btn = t("web.selectedButton")
        copy_btn = t("web.copyButton")
        copied_text = t("web.copied")
        copy_failed = t("web.copyFailed")
        save_btn = t("web.saveButton")
        save_failed = t("web.saveFailed")
        error_text = t("web.error")
        send_text = t("web.sendSelected")

        return f"""
// === MCP Icon Server - Client JS ===
let selectedIcons = new Map();
let currentIcons = [];
let allIcons = [];
let websocket = null;
let currentPage = 1;
let totalPages = 1;
let pageSize = 15;

// 根据视口高度动态计算每页图标数，让内容撑满一屏
function calcPageSize() {{
    const gridTop = document.querySelector('.icon-area').getBoundingClientRect().top;
    const availableH = window.innerHeight - gridTop - 60; // 预留分页栏空间
    const cardH = 110; // 每个 icon-card 大致高度
    const cols = Math.max(1, Math.floor(document.getElementById('iconGrid').clientWidth / 108)); // 每行列数
    const rows = Math.max(1, Math.floor(availableH / cardH));
    return Math.max(cols * rows, 20);
}}

// Initialize
document.addEventListener('DOMContentLoaded', function() {{
    if (SEARCH_ID) {{
        pageSize = calcPageSize();
        connectWebSocket();
        loadCachedResults(1);
    }}
}});

function connectWebSocket() {{
    try {{
        websocket = new WebSocket('ws://localhost:' + WS_PORT + '/ws?searchId=' + SEARCH_ID);
        websocket.onopen = function() {{
            console.log('WebSocket connected');
            setInterval(function() {{
                if (websocket && websocket.readyState === WebSocket.OPEN) {{
                    websocket.send(JSON.stringify({{type: 'ping'}}));
                }}
            }}, 30000);
        }};
        websocket.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            console.log('WS message:', data);
        }};
        websocket.onclose = function() {{
            console.log('WebSocket disconnected');
            setTimeout(connectWebSocket, 3000);
        }};
    }} catch(e) {{
        console.error('WebSocket error:', e);
    }}
}}

async function loadCachedResults(page) {{
    const loading = document.getElementById('loading');
    const grid = document.getElementById('iconGrid');
    loading.style.display = 'block';
    grid.innerHTML = '';

    try {{
        const resp = await fetch('/api/cache?searchId=' + SEARCH_ID + '&page=' + page + '&pageSize=' + pageSize);
        const data = await resp.json();
        if (data.error) {{
            showMessage(data.error, 'error');
            return;
        }}
        currentIcons = data.icons || [];
        allIcons = currentIcons;
        totalPages = data.totalPages || 1;
        currentPage = data.page || 1;
        displayIcons(currentIcons);
        updatePagination();
    }} catch(e) {{
        showMessage('{error_text}: ' + e.message, 'error');
    }} finally {{
        loading.style.display = 'none';
    }}
}}

function displayIcons(icons) {{
    const grid = document.getElementById('iconGrid');
    grid.innerHTML = '';
    icons.forEach(function(icon, index) {{
        const card = document.createElement('div');
        card.className = 'icon-card' + (selectedIcons.has(icon.id) ? ' selected' : '');
        card.onclick = function() {{ toggleSelection(icon); }};

        let preview = '';
        if (icon.show_svg) {{
            preview = icon.show_svg;
        }} else if (icon.icon) {{
            preview = '<img src="' + icon.icon + '" alt="' + (icon.name||'') + '">';
        }} else {{
            preview = '<span style="font-size:32px;color:#ccc;">&#128196;</span>';
        }}

        const isSelected = selectedIcons.has(icon.id);
        const hasSvg = !!icon.show_svg;
        card.innerHTML =
            '<div class="icon-preview">' + preview + '</div>' +
            '<div class="icon-name">' + (icon.name || 'icon-' + icon.id) + '</div>' +
            '<button class="btn select-btn ' + (isSelected ? 'selected-btn' : '') + '"' +
            ' title="{select_btn}">' +
            (isSelected ? '\u2714' : '') + '</button>' +
            '<div class="card-actions">' +
            '<button class="btn copy-btn" data-id="' + icon.id + '"' +
            (hasSvg ? '' : ' disabled') + ' title="{copy_btn}">' +
            '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button>' +
            '<div class="save-dropdown">' +
            '<button class="btn save-btn"' + (hasSvg ? '' : ' disabled') +
            ' title="{save_btn}">' +
            '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg></button>' +
            '</div>' +
            '</div>';
        // 复制按钮：阻止冒泡（避免触发卡片选择），复制 AddPng 可用的 PNG Base64
        const copyEl = card.querySelector('.copy-btn');
        if (copyEl) {{
            copyEl.onclick = function(e) {{
                e.stopPropagation();
                copyAddPng(icon, copyEl);
            }};
        }}
        // 保存下拉：点击主按钮切换菜单，点击子项下载对应格式图片
        const dropdown = card.querySelector('.save-dropdown');
        if (dropdown && hasSvg) {{
            const saveBtn = dropdown.querySelector('.save-btn');
            saveBtn.onclick = function(e) {{
                e.stopPropagation();
                const globalMenu = document.getElementById('globalSaveMenu');
                const isOpen = globalMenu.classList.contains('open') && globalMenu._triggerBtn === saveBtn;
                closeAllSaveMenus();
                if (!isOpen) {{
                    // 计算按钮位置，菜单向上弹出
                    const btnRect = saveBtn.getBoundingClientRect();
                    globalMenu.style.visibility = 'hidden';
                    globalMenu.style.display = 'block';
                    const menuW = globalMenu.offsetWidth || 90;
                    const menuH = globalMenu.offsetHeight || 100;
                    globalMenu.style.display = '';
                    globalMenu.style.visibility = '';
                    globalMenu.style.left = (btnRect.right - menuW) + 'px';
                    globalMenu.style.top = (btnRect.top - menuH - 4) + 'px';
                    globalMenu._currentIcon = icon;
                    globalMenu._triggerBtn = saveBtn;
                    globalMenu.classList.add('open');
                }}
            }};
        }}
        grid.appendChild(card);
    }});
}}

async function copyAddPng(icon, btnEl) {{
    const svg = icon.show_svg;
    if (!svg) return;
    const original = btnEl.textContent;
    btnEl.disabled = true;
    try {{
        const resp = await fetch('/api/png', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ svg: svg, size: 32 }})
        }});
        const data = await resp.json();
        if (!resp.ok || !data.base64) {{
            throw new Error(data.error || 'no base64');
        }}
        await copyToClipboard(formatAddPng(data.base64));
        showMessage('{copied_text}', 'success');
        btnEl.textContent = '\\u2713';
        setTimeout(function() {{ btnEl.textContent = original; btnEl.disabled = false; }}, 1200);
    }} catch(e) {{
        showMessage('{copy_failed}: ' + e.message, 'error');
        btnEl.disabled = false;
    }}
}}

// 把单行 Base64 格式化为 Delphi 字符串拼接片段：每行 64 字符、8 空格缩进、单引号包裹、行尾带 +
function formatAddPng(b64) {{
    const lines = [];
    for (let i = 0; i < b64.length; i += 64) {{
        lines.push("        '" + b64.slice(i, i + 64) + "'+");
    }}
    return lines.join('\\n');
}}

// 关闭除 except 外的所有已打开保存菜单，并重置卡片层级
function closeAllSaveMenus() {{
    const globalMenu = document.getElementById('globalSaveMenu');
    if (globalMenu) globalMenu.classList.remove('open');
}}

// 初始化全局菜单按钮事件
function initGlobalSaveMenu() {{
    const globalMenu = document.getElementById('globalSaveMenu');
    if (!globalMenu) return;
    globalMenu.querySelectorAll('button[data-fmt]').forEach(function(item) {{
        item.onclick = function(e) {{
            e.stopPropagation();
            const icon = globalMenu._currentIcon;
            globalMenu.classList.remove('open');
            if (icon) {{
                const fmt = item.getAttribute('data-fmt');
                // 同时保存多个尺寸；ICO 最大支持到 256，跳过 512
                [16, 24, 32, 48, 256, 512].forEach(function(size) {{
                    if (fmt === 'ico' && size > 256) return;
                    saveIcon(icon, fmt, size);
                }});
            }}
        }};
    }});
}}
document.addEventListener('DOMContentLoaded', initGlobalSaveMenu);

// 点击页面任意其他位置关闭已打开的保存菜单
document.addEventListener('click', function() {{ closeAllSaveMenus(); }});

// 请求后端把 SVG 栅格化为指定格式并触发浏览器下载
async function saveIcon(icon, fmt, size) {{
    size = size || 32;
    const svg = icon.show_svg;
    if (!svg) return;
    try {{
        const resp = await fetch('/api/raster', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ svg: svg, format: fmt, size: size }})
        }});
        if (!resp.ok) {{
            let msg = 'rasterize failed';
            try {{ msg = (await resp.json()).error || msg; }} catch(_) {{}}
            throw new Error(msg);
        }}
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = (icon.name || 'icon-' + icon.id) + '.' + size + '.' + fmt;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function() {{ URL.revokeObjectURL(url); }}, 1000);
    }} catch(e) {{
        showMessage('{save_failed}: ' + e.message, 'error');
    }}
}}

async function copyToClipboard(text) {{
    // 优先用现代剪贴板 API（localhost 下可用），否则回退 execCommand
    if (navigator.clipboard && window.isSecureContext) {{
        await navigator.clipboard.writeText(text);
        return;
    }}
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try {{ document.execCommand('copy'); }} finally {{ document.body.removeChild(ta); }}
}}

function toggleSelection(icon) {{
    if (selectedIcons.has(icon.id)) {{
        selectedIcons.delete(icon.id);
    }} else {{
        selectedIcons.set(icon.id, icon);
    }}
    displayIcons(currentIcons);
    updateSelectedList();
}}

function updateSelectedList() {{
    const list = document.getElementById('selectedList');
    const title = document.getElementById('selectedTitle');
    const btn = document.getElementById('sendBtn');
    const count = selectedIcons.size;

    title.textContent = count > 0 ? '{selected_text}'.replace('{{count}}', count) : '{no_selected}';
    btn.disabled = count === 0;

    list.innerHTML = '';
    selectedIcons.forEach(function(icon, id) {{
        const item = document.createElement('div');
        item.className = 'selected-item';
        item.innerHTML =
            '<span>' + (icon.name || 'icon-' + id) + '</span>' +
            '<button class="remove-btn" onclick="event.stopPropagation(); removeSelected(' + id + ')">x</button>';
        list.appendChild(item);
    }});
}}

function removeSelected(id) {{
    selectedIcons.delete(id);
    displayIcons(currentIcons);
    updateSelectedList();
}}

function filterIcons(query) {{
    if (!query) {{
        currentIcons = allIcons;
    }} else {{
        const q = query.toLowerCase();
        currentIcons = allIcons.filter(function(icon) {{
            return (icon.name || '').toLowerCase().includes(q);
        }});
    }}
    displayIcons(currentIcons);
}}

// 从 iconfont.cn 重新搜索：把新结果覆盖到同一 searchId，再重载第一页。
// 复用原 searchId，使 MCP 端的 check_selection_status 轮询和 WebSocket 不受影响。
async function remoteSearch() {{
    const input = document.getElementById('filterInput');
    const q = (input.value || '').trim();
    if (!q) return;
    if (!SEARCH_ID) {{
        showMessage('{error_text}: searchId', 'error');
        return;
    }}
    const btn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const grid = document.getElementById('iconGrid');
    btn.disabled = true;
    loading.style.display = 'block';
    grid.innerHTML = '';
    try {{
        const resp = await fetch('/api/search', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ q: q, searchId: SEARCH_ID }})
        }});
        const data = await resp.json();
        if (!resp.ok || !data.success) {{
            throw new Error(data.error || 'search failed');
        }}
        pageSize = calcPageSize();
        await loadCachedResults(1);  // loadCachedResults 负责关闭 loading
    }} catch(e) {{
        showMessage('{error_text}: ' + e.message, 'error');
        loading.style.display = 'none';
    }} finally {{
        btn.disabled = false;
    }}
}}

function updatePagination() {{
    const pag = document.getElementById('pagination');
    const nums = document.getElementById('pageNumbers');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    if (totalPages <= 1) {{
        pag.style.display = 'none';
        return;
    }}
    pag.style.display = 'flex';
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;

    nums.innerHTML = '';
    const maxVisible = 7;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    if (endPage - startPage < maxVisible - 1) {{
        startPage = Math.max(1, endPage - maxVisible + 1);
    }}

    for (let i = startPage; i <= endPage; i++) {{
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = i === currentPage ? 'active' : '';
        btn.onclick = function() {{ goToPage(i); }};
        nums.appendChild(btn);
    }}
}}

function goToPage(page) {{
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadCachedResults(page);
}}

// 窗口大小变化时重新计算并刷新
window.addEventListener('resize', function() {{
    const newSize = calcPageSize();
    if (newSize !== pageSize) {{
        pageSize = newSize;
        loadCachedResults(1);
    }}
}});

async function sendSelectedIcons() {{
    if (selectedIcons.size === 0) return;

    const icons = Array.from(selectedIcons.values());
    try {{
        const resp = await fetch('/api/save', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ icons: icons, searchId: SEARCH_ID }})
        }});
        const data = await resp.json();
        if (data.success) {{
            showMessage('Sent ' + icons.length + ' icons to MCP client!', 'success');
            setTimeout(function() {{ window.close(); }}, 2000);
        }} else {{
            showMessage(data.error || 'Send failed', 'error');
        }}
    }} catch(e) {{
        showMessage('Error: ' + e.message, 'error');
    }}
}}

function showMessage(text, type) {{
    const msg = document.getElementById('message');
    msg.textContent = text;
    msg.className = 'message ' + type;
    if (type === 'success') {{
        setTimeout(function() {{ msg.style.display = 'none'; }}, 5000);
    }}
}}
"""
