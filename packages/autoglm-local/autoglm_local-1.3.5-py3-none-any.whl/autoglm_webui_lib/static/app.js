/**
 * AI-APPUI自动化测试平台 v2.0
 * 前端交互逻辑
 */

// ============ 状态管理 ============
const state = {
    selectedDevice: null,
    selectedPlatform: 'android',  // 'android' | 'ios'
    testCases: [],
    apiConfigs: [],
    scenarios: [],
    currentTaskId: null,
    isRunning: false,
    ws: null,
    runTimer: null,
    runStartTime: null,
    currentHistoryId: null,
    editingCaseId: null,
    editingApiId: null,
    systemInfo: null,
    currentScenarioName: '',  // 当前场景名称
    selectedHistoryIds: [],   // 选中的历史记录 ID（用于生成报告）
    // 多用户隔离相关
    currentLocal: null,       // 当前选中的本地端名称
    localClients: [],         // 所有在线的本地端列表
};

// ============ 初始化 ============
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadSystemInfo();
    loadApiConfigs();
    loadScenarios();
    loadHistory();
    // 先加载本地端列表，再刷新设备
    loadLocalClients();

    // 定时刷新本地端列表和设备（5秒间隔）
    setInterval(loadLocalClients, 5000);
});

// ============ 本地端管理（多用户隔离） ============

async function loadLocalClients() {
    try {
        const res = await fetch('/local/list');
        const locals = await res.json();
        state.localClients = locals.filter(l => l.online);
        
        // 从 localStorage 恢复上次选择的本地端
        const savedLocal = localStorage.getItem('selectedLocal');
        const currentValid = state.currentLocal && state.localClients.find(l => l.name === state.currentLocal);
        
        if (!currentValid) {
            // 当前选中的本地端无效，需要重新选择
            if (savedLocal && state.localClients.find(l => l.name === savedLocal)) {
                state.currentLocal = savedLocal;
            } else if (state.localClients.length > 0) {
                state.currentLocal = state.localClients[0].name;
                localStorage.setItem('selectedLocal', state.currentLocal);
            } else {
                state.currentLocal = null;
            }
            // 切换本地端时加载对应的测试用例
            loadTestCasesFromLocal();
        }
        
        renderLocalSelector();
        refreshDevices();
    } catch (e) {
        console.error('加载本地端列表失败:', e);
        // 如果加载失败，仍尝试刷新设备
        refreshDevices();
    }
}

function renderLocalSelector() {
    const select = document.getElementById('localSelect');
    const status = document.getElementById('localStatus');
    if (!select) return;
    
    if (state.localClients.length === 0) {
        select.innerHTML = '<option value="">-- 无在线本地端 --</option>';
        select.disabled = true;
        if (status) status.innerHTML = '<span class="status-badge offline">离线</span>';
        return;
    }
    
    select.disabled = false;
    select.innerHTML = state.localClients.map(l => `
        <option value="${l.name}" ${l.name === state.currentLocal ? 'selected' : ''}>
            ${l.name} (${l.devices?.length || 0}台设备)
        </option>
    `).join('');
    
    if (status) {
        status.innerHTML = `<span class="status-badge online">${state.localClients.length}个在线</span>`;
    }
}

function switchLocal(localName) {
    if (localName === state.currentLocal) return;
    
    // 保存当前本地端的测试用例
    saveTestCasesToLocal();
    
    // 切换到新本地端
    state.currentLocal = localName;
    localStorage.setItem('selectedLocal', localName);
    
    // 清空当前设备选择
    state.selectedDevice = null;
    state.selectedPlatform = 'android';
    
    // 加载新本地端的测试用例
    loadTestCasesFromLocal();
    
    // 刷新设备列表和截图
    refreshDevices();
    clearScreenshot();
    
    showToast(`已切换到本地端: ${localName}`, 'success');
}

function saveTestCasesToLocal() {
    if (state.currentLocal) {
        localStorage.setItem(`testCases_${state.currentLocal}`, JSON.stringify(state.testCases));
    }
}

function loadTestCasesFromLocal() {
    if (state.currentLocal) {
        const saved = localStorage.getItem(`testCases_${state.currentLocal}`);
        state.testCases = saved ? JSON.parse(saved) : [];
    } else {
        state.testCases = [];
    }
    renderTestCases();
}

function clearScreenshot() {
    const img = document.getElementById('deviceScreen');
    if (img) {
        img.src = '';
        img.style.display = 'none';
    }
    const placeholder = document.querySelector('.screen-placeholder');
    if (placeholder) {
        placeholder.style.display = 'flex';
    }
}

async function loadSystemInfo() {
    try {
        const res = await fetch('/system/info');
        state.systemInfo = await res.json();

        // 更新 UI 显示系统支持状态
        updateSystemStatus();
    } catch (e) {
        console.error('加载系统信息失败:', e);
    }
}

function updateSystemStatus() {
    const info = state.systemInfo;
    if (!info) return;

    // 更新 header 中的支持状态
    const headerInfo = document.querySelector('.header-right .system-status');
    if (headerInfo) {
        headerInfo.innerHTML = `
            <span class="support-badge ${info.ios_support ? 'enabled' : 'disabled'}">
                <span class="material-icons-round">phone_iphone</span>iOS
            </span>
            <span class="support-badge ${info.scrcpy_support ? 'enabled' : 'disabled'}">
                <span class="material-icons-round">cast</span>scrcpy
            </span>
        `;
    }
}

function initEventListeners() {
    // 设备
    document.getElementById('refreshDevices').addEventListener('click', refreshDevices);
    document.getElementById('refreshScreen').addEventListener('click', refreshScreen);

    // API 配置
    document.getElementById('addApiConfig').addEventListener('click', () => showApiConfigModal());
    document.getElementById('saveApiModal').addEventListener('click', saveApiConfig);
    document.getElementById('cancelApiModal').addEventListener('click', closeApiConfigModal);
    document.getElementById('closeApiModal').addEventListener('click', closeApiConfigModal);

    // 输入法
    document.getElementById('switchIme').addEventListener('click', switchIme);
    document.getElementById('installAdbKeyboard').addEventListener('click', installAdbKeyboard);

    // 场景
    document.getElementById('saveScenario').addEventListener('click', () => showScenarioModal());
    document.getElementById('confirmSaveScenario').addEventListener('click', saveScenario);
    document.getElementById('cancelScenarioModal').addEventListener('click', closeScenarioModal);
    document.getElementById('closeScenarioModal').addEventListener('click', closeScenarioModal);

    // 测试用例
    document.getElementById('addTestCase').addEventListener('click', () => showTestCaseModal());
    document.getElementById('saveCaseModal').addEventListener('click', saveTestCase);
    document.getElementById('cancelCaseModal').addEventListener('click', closeTestCaseModal);
    document.getElementById('closeCaseModal').addEventListener('click', closeTestCaseModal);
    document.getElementById('selectAllCases').addEventListener('change', toggleSelectAll);
    document.getElementById('clearCases').addEventListener('click', clearTestCases);

    // CSV 导入导出
    document.getElementById('importCsv').addEventListener('click', () => document.getElementById('csvFileInput').click());
    document.getElementById('csvFileInput').addEventListener('change', handleCsvUpload);
    document.getElementById('exportCsv').addEventListener('click', exportTestCases);
    document.getElementById('downloadTemplate').addEventListener('click', downloadTemplate);

    // 执行
    document.getElementById('runSelected').addEventListener('click', runSelectedCases);
    document.getElementById('stopTask').addEventListener('click', stopTask);
    document.getElementById('clearLogs').addEventListener('click', clearLogs);

    // Tab 切换
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // 历史
    document.getElementById('closeHistoryModal').addEventListener('click', closeHistoryModal);
    document.getElementById('closeHistoryModalBtn').addEventListener('click', closeHistoryModal);
    document.getElementById('exportExcel').addEventListener('click', exportExcel);

    // 输入法错误弹窗
    document.getElementById('closeImeErrorModal').addEventListener('click', () => {
        document.getElementById('imeErrorModal').classList.remove('show');
    });
}

// ============ 设备管理 ============
async function refreshDevices() {
    const btn = document.getElementById('refreshDevices');
    if (btn) btn.classList.add('spinning');

    try {
        // 根据选中的本地端过滤设备
        let url = '/devices';
        if (state.currentLocal) {
            url += `?local_name=${encodeURIComponent(state.currentLocal)}`;
        }
        const res = await fetch(url);
        const devices = await res.json();
        renderDeviceList(devices);
    } catch (e) {
        showToast('获取设备列表失败', 'error');
    } finally {
        if (btn) btn.classList.remove('spinning');
    }
}

function renderDeviceList(devices) {
    const container = document.getElementById('deviceList');

    if (!devices.length) {
        container.innerHTML = '<div class="empty-state">未发现设备<br><small>请通过 USB 或 WiFi 连接设备</small></div>';
        return;
    }

    container.innerHTML = devices.map(d => {
        const isIOS = d.platform === 'ios';
        const icon = isIOS ? 'phone_iphone' : 'phone_android';
        const iconColor = isIOS ? '#1565C0' : '#3DDC84';
        const platformBadge = isIOS
            ? '<span class="platform-badge ios">iOS</span>'
            : '<span class="platform-badge android">Android</span>';
        const modelName = d.model || (isIOS ? 'iPhone' : 'Android');
        const shortSerial = d.serial.length > 16 ? d.serial.substring(0, 16) + '...' : d.serial;

        return `
        <div class="device-item ${state.selectedDevice === d.serial ? 'selected' : ''}" 
             data-serial="${d.serial}"
             data-platform="${d.platform}"
             onclick="selectDevice('${d.serial}', '${d.platform}')">
            <div class="device-icon" style="color: ${iconColor}">
                <span class="material-icons-round">${icon}</span>
            </div>
            <div class="device-info">
                <div class="device-name">
                    <span class="device-model-name">${modelName}</span>
                    ${platformBadge}
                </div>
                <div class="device-serial" title="${d.serial}">${shortSerial}</div>
            </div>
            <div class="device-status">
                ${(d.screen_on && d.unlocked) ? 
                  '<span class="status-badge ready">就绪</span>' : 
                  '<span class="status-badge locked">屏幕锁定/关闭</span>'}
            </div>
        </div>
    `}).join('');
}

async function selectDevice(serial, platform = 'android') {
    state.selectedDevice = serial;
    state.selectedPlatform = platform;

    document.querySelectorAll('.device-item').forEach(el => {
        el.classList.toggle('selected', el.dataset.serial === serial);
    });

    // 更新连接状态
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    statusDot.classList.add('connected');
    statusText.textContent = `${serial.length > 15 ? serial.substring(0, 15) + '...' : serial} (${platform === 'ios' ? 'iOS' : 'Android'})`;

    // iOS 设备检查 WDA 配置
    if (platform === 'ios') {
        try {
            const wdaRes = await fetch(`/ios/wda/config/${serial}`);
            const wdaData = await wdaRes.json();
            if (!wdaData.wda_url) {
                showToast('iOS 设备需要配置 WDA URL，请点击"远程控制"按钮进行配置', 'info');
            }
        } catch (e) {
            console.error('检查 WDA 配置失败:', e);
        }
    }

    // 刷新截图
    refreshScreen();

    // 根据平台启用/禁用功能
    const isAndroid = platform === 'android';

    // 输入法管理（仅 Android）
    const imeSection = document.querySelector('.ime-section');
    if (imeSection) {
        imeSection.style.display = isAndroid ? 'block' : 'none';
    }

    if (isAndroid) {
        loadInputMethods();
        document.getElementById('switchIme').disabled = false;
        document.getElementById('installAdbKeyboard').disabled = false;
    }

    // 显示/隐藏 scrcpy 按钮（仅 Android）
    const scrcpyBtn = document.getElementById('toggleScrcpy');
    if (scrcpyBtn) {
        scrcpyBtn.style.display = isAndroid ? 'flex' : 'none';
    }
}

// ============ Scrcpy 投屏控制 ============
let scrcpyRunning = false;

async function toggleScrcpy() {
    if (!state.selectedDevice) {
        showToast('请先选择设备', 'warning');
        return;
    }

    if (state.selectedPlatform === 'ios') {
        showToast('scrcpy 仅支持 Android 设备', 'warning');
        return;
    }

    const btn = document.getElementById('toggleScrcpy');

    if (scrcpyRunning) {
        // 停止 scrcpy
        try {
            await fetch(`/scrcpy/stop/${state.selectedDevice}`, { method: 'POST' });
            scrcpyRunning = false;
            btn.innerHTML = '<span class="material-icons-round">cast</span>投屏';
            btn.classList.remove('active');
            showToast('投屏已停止', 'info');
        } catch (e) {
            showToast('停止投屏失败', 'error');
        }
    } else {
        // 启动 scrcpy
        try {
            const res = await fetch(`/scrcpy/start/${state.selectedDevice}`, { method: 'POST' });
            const data = await res.json();

            if (data.status === 'started' || data.status === 'already_running') {
                scrcpyRunning = true;
                btn.innerHTML = '<span class="material-icons-round">cast_connected</span>停止投屏';
                btn.classList.add('active');
                showToast('投屏已启动，请查看弹出的窗口', 'success');
            } else {
                showToast(data.message || '启动投屏失败', 'error');
            }
        } catch (e) {
            showToast('启动投屏失败: ' + e.message, 'error');
        }
    }
}

async function checkScrcpyStatus() {
    if (!state.selectedDevice) return;

    try {
        const res = await fetch(`/scrcpy/status/${state.selectedDevice}`);
        const data = await res.json();

        const btn = document.getElementById('toggleScrcpy');
        if (btn) {
            scrcpyRunning = data.running;
            if (data.running) {
                btn.innerHTML = '<span class="material-icons-round">cast_connected</span>停止投屏';
                btn.classList.add('active');
            } else {
                btn.innerHTML = '<span class="material-icons-round">cast</span>投屏';
                btn.classList.remove('active');
            }
        }
    } catch (e) {
        console.error('检查投屏状态失败:', e);
    }
}

async function refreshScreen() {
    if (!state.selectedDevice) {
        showToast('请先选择设备', 'warning');
        return;
    }

    try {
        // 根据平台选择截图接口
        const isIOS = state.selectedPlatform === 'ios';
        const endpoint = isIOS
            ? `/ios/screenshot/${state.selectedDevice}`
            : `/screenshot/${state.selectedDevice}`;

        const res = await fetch(endpoint);
        const data = await res.json();

        if (data.status === 'success') {
            const img = document.getElementById('deviceScreen');
            const placeholder = document.getElementById('screenPlaceholder');

            img.src = `data:image/png;base64,${data.image}`;
            img.style.display = 'block';
            placeholder.style.display = 'none';

            const platformLabel = isIOS ? 'iOS' : 'Android';
            document.getElementById('screenInfo').textContent =
                `${data.width || '?'} × ${data.height || '?'} (${platformLabel})`;
        }
    } catch (e) {
        showToast('获取截图失败', 'error');
    }
}

// ============ 输入法管理 ============
function shortenImeName(ime) {
    // 提取输入法的简短名称
    const parts = ime.split('/');
    const lastPart = parts[parts.length - 1];
    // 如果是完整类名，取最后的类名
    const className = lastPart.split('.').pop();

    // 特殊处理常见输入法
    if (ime.toLowerCase().includes('adbkeyboard')) return 'ADB Keyboard ✅';
    if (ime.toLowerCase().includes('google')) return 'Google 输入法';
    if (ime.toLowerCase().includes('sogou')) return '搜狗输入法';
    if (ime.toLowerCase().includes('baidu')) return '百度输入法';
    if (ime.toLowerCase().includes('samsung')) return '三星输入法';
    if (ime.toLowerCase().includes('swiftkey')) return 'SwiftKey';
    if (ime.toLowerCase().includes('gboard')) return 'Gboard';

    // 如果类名太长，截取
    return className.length > 20 ? className.substring(0, 18) + '...' : className;
}

async function loadInputMethods() {
    if (!state.selectedDevice) return;

    try {
        const res = await fetch(`/input_methods/${state.selectedDevice}`);
        const data = await res.json();

        const select = document.getElementById('imeSelect');
        select.innerHTML = data.imes.map(ime => {
            const shortName = shortenImeName(ime);
            const isSelected = ime === data.current;
            return `<option value="${ime}" ${isSelected ? 'selected' : ''} title="${ime}">${shortName}</option>`;
        }).join('');
        select.disabled = false;
        document.getElementById('switchIme').disabled = false;

        // 提示当前是否是 ADB Keyboard
        const isAdb = data.current && data.current.toLowerCase().includes('adbkeyboard');
        const hint = document.getElementById('imeHint');
        if (hint) {
            hint.textContent = isAdb ? '✅ 当前已使用 ADB Keyboard' : '💡 建议切换到 ADB Keyboard';
            hint.style.background = isAdb ? 'var(--success-light)' : 'var(--warning-light)';
            hint.style.color = isAdb ? 'var(--success)' : 'var(--warning)';
        }
    } catch (e) {
        console.error('加载输入法失败:', e);
    }
}

async function switchIme() {
    if (!state.selectedDevice) return;

    const ime = document.getElementById('imeSelect').value;
    if (!ime) {
        showToast('请选择要切换的输入法', 'warning');
        return;
    }

    const btn = document.getElementById('switchIme');
    btn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('ime', ime);

        const res = await fetch(`/switch_ime/${state.selectedDevice}`, {
            method: 'POST',
            body: formData
        });

        if (res.ok) {
            showToast('输入法切换成功', 'success');
            // 重新加载输入法列表以显示当前选中状态
            await loadInputMethods();
        } else {
            const err = await res.json();
            showToast(err.detail || '切换失败', 'error');
        }
    } catch (e) {
        showToast('切换输入法失败: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
    }
}

async function installAdbKeyboard() {
    if (!state.selectedDevice) return;

    const btn = document.getElementById('installAdbKeyboard');
    btn.disabled = true;
    btn.innerHTML = '<span class="material-icons-round">hourglass_empty</span>安装中...';

    try {
        const res = await fetch(`/install_adbkeyboard/${state.selectedDevice}`, {
            method: 'POST'
        });
        const data = await res.json();

        if (res.ok) {
            showToast(data.message, 'success');
            loadInputMethods();
        } else {
            showToast(data.detail || '安装失败', 'error');
        }
    } catch (e) {
        showToast('安装失败', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-icons-round">download</span>安装 ADB Keyboard';
    }
}

// ============ API 配置管理 ============
async function loadApiConfigs() {
    try {
        const res = await fetch('/api_configs');
        state.apiConfigs = await res.json();
        renderApiConfigs();
    } catch (e) {
        console.error('加载API配置失败:', e);
    }
}

function renderApiConfigs() {
    const list = document.getElementById('apiConfigList');
    const select = document.getElementById('activeApiConfig');
    const currentSelected = select.value; // 保存当前选中值

    if (!state.apiConfigs.length) {
        list.innerHTML = '<div class="empty-state">暂无配置<br><small style="color:var(--danger);">⚠️ 必须添加API配置才能执行测试</small></div>';
        select.innerHTML = '<option value="">⚠️ 请先添加API配置（必选）</option>';
        select.classList.add('config-required');
        return;
    }

    list.innerHTML = state.apiConfigs.map(c => {
        const isSelected = currentSelected === c.id;
        return `
        <div class="api-config-item ${isSelected ? 'selected' : ''}" data-id="${c.id}">
            <div>
                <div class="config-name">${c.name} ${isSelected ? '<span class="selected-badge">✓ 当前使用</span>' : ''}</div>
                <div class="config-model">${c.model}</div>
            </div>
            <div style="display:flex;gap:4px;">
                <button class="icon-btn" onclick="editApiConfig('${c.id}')" title="编辑">
                    <span class="material-icons-round">edit</span>
                </button>
                <button class="icon-btn" onclick="deleteApiConfig('${c.id}')" title="删除">
                    <span class="material-icons-round">delete</span>
                </button>
            </div>
        </div>
    `}).join('');

    select.innerHTML = '<option value="">-- 请选择API配置（必选）--</option>' +
        state.apiConfigs.map(c => `<option value="${c.id}" ${c.id === currentSelected ? 'selected' : ''}>${c.name}</option>`).join('');
    
    // 根据是否选中更新样式
    if (currentSelected) {
        select.classList.remove('config-required');
        select.classList.add('config-selected');
    } else {
        select.classList.add('config-required');
        select.classList.remove('config-selected');
    }
    
    // 监听选择变化
    select.onchange = function() {
        renderApiConfigs(); // 重新渲染以更新选中状态
    };
}

function showApiConfigModal(config = null) {
    state.editingApiId = config?.id || null;
    document.getElementById('apiModalTitle').textContent = config ? '编辑 API 配置' : '添加 API 配置';
    document.getElementById('apiConfigName').value = config?.name || '';
    document.getElementById('apiBaseUrl').value = config?.base_url || 'https://open.bigmodel.cn/api/paas/v4';
    document.getElementById('apiModel').value = config?.model || 'autoglm-phone';
    document.getElementById('apiKey').value = config?.api_key || '';
    document.getElementById('apiConfigModal').classList.add('show');
}

function closeApiConfigModal() {
    document.getElementById('apiConfigModal').classList.remove('show');
    state.editingApiId = null;
}

async function saveApiConfig() {
    const config = {
        id: state.editingApiId || '',
        name: document.getElementById('apiConfigName').value,
        base_url: document.getElementById('apiBaseUrl').value,
        model: document.getElementById('apiModel').value,
        api_key: document.getElementById('apiKey').value,
    };

    if (!config.name || !config.base_url || !config.api_key) {
        showToast('请填写完整信息', 'warning');
        return;
    }

    try {
        const url = state.editingApiId ? `/api_configs/${state.editingApiId}` : '/api_configs';
        const method = state.editingApiId ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (res.ok) {
            showToast('保存成功', 'success');
            closeApiConfigModal();
            loadApiConfigs();
        } else {
            showToast('保存失败', 'error');
        }
    } catch (e) {
        showToast('保存失败', 'error');
    }
}

function editApiConfig(id) {
    const config = state.apiConfigs.find(c => c.id === id);
    if (config) showApiConfigModal(config);
}

async function deleteApiConfig(id) {
    if (!confirm('确定删除此配置？')) return;

    try {
        await fetch(`/api_configs/${id}`, { method: 'DELETE' });
        showToast('已删除', 'success');
        loadApiConfigs();
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

// ============ 测试用例管理 ============
function showTestCaseModal(testCase = null) {
    state.editingCaseId = testCase?.id || null;
    document.getElementById('caseModalTitle').textContent = testCase ? '编辑测试用例' : '添加测试用例';
    document.getElementById('caseName').value = testCase?.name || '';
    document.getElementById('caseDescription').value = testCase?.description || '';
    document.getElementById('caseExpected').value = testCase?.expected || '';
    document.getElementById('testCaseModal').classList.add('show');
}

function closeTestCaseModal() {
    document.getElementById('testCaseModal').classList.remove('show');
    state.editingCaseId = null;
}

function saveTestCase() {
    const name = document.getElementById('caseName').value.trim();
    const description = document.getElementById('caseDescription').value.trim();
    const expected = document.getElementById('caseExpected').value.trim();

    if (!name || !description) {
        showToast('请填写用例名称和测试步骤', 'warning');
        return;
    }

    if (state.editingCaseId) {
        const idx = state.testCases.findIndex(c => c.id === state.editingCaseId);
        if (idx !== -1) {
            state.testCases[idx] = { ...state.testCases[idx], name, description, expected };
        }
    } else {
        state.testCases.push({
            id: generateId(),
            name,
            description,
            expected,
            selected: false
        });
    }

    renderTestCases();
    saveTestCasesToLocal();  // 保存到 localStorage
    closeTestCaseModal();
    showToast('保存成功', 'success');
}

function renderTestCases() {
    const container = document.getElementById('testCaseList');
    const total = state.testCases.length;
    const selected = state.testCases.filter(c => c.selected).length;

    document.getElementById('totalCases').textContent = total;
    document.getElementById('selectedCases').textContent = selected;

    if (!total) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="material-icons-round">playlist_add</span>
                <p>添加或导入测试用例</p>
            </div>
        `;
        return;
    }

    container.innerHTML = state.testCases.map((c, i) => `
        <div class="test-case-item ${c.selected ? 'selected' : ''}" data-id="${c.id}">
            <input type="checkbox" class="case-checkbox" 
                   ${c.selected ? 'checked' : ''} 
                   onchange="toggleCaseSelection('${c.id}')">
            <div class="case-content" onclick="showTestCaseModal(state.testCases.find(tc=>tc.id==='${c.id}'))">
                <div class="case-name">${i + 1}. ${c.name}</div>
                <div class="case-desc">${c.description.substring(0, 50)}${c.description.length > 50 ? '...' : ''}</div>
            </div>
            <div class="case-actions-mini">
                <button class="icon-btn" onclick="event.stopPropagation();showTestCaseModal(state.testCases.find(tc=>tc.id==='${c.id}'))" title="编辑">
                    <span class="material-icons-round">edit</span>
                </button>
                <button class="icon-btn" onclick="event.stopPropagation();deleteTestCase('${c.id}')" title="删除">
                    <span class="material-icons-round">delete</span>
                </button>
            </div>
        </div>
    `).join('');
}

function toggleCaseSelection(id) {
    const tc = state.testCases.find(c => c.id === id);
    if (tc) tc.selected = !tc.selected;
    renderTestCases();
}

function toggleSelectAll() {
    const checked = document.getElementById('selectAllCases').checked;
    state.testCases.forEach(c => c.selected = checked);
    renderTestCases();
}

function deleteTestCase(id) {
    state.testCases = state.testCases.filter(c => c.id !== id);
    renderTestCases();
    saveTestCasesToLocal();  // 保存到 localStorage
}

function clearTestCases() {
    if (!state.testCases.length) return;
    if (!confirm('确定清空所有测试用例？')) return;
    state.testCases = [];
    renderTestCases();
    saveTestCasesToLocal();  // 保存到 localStorage
}

// ============ CSV 导入导出 ============
async function handleCsvUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/upload_csv', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (res.ok) {
            state.testCases = [...state.testCases, ...data.test_cases];
            renderTestCases();
            saveTestCasesToLocal();  // 保存到 localStorage
            showToast(`导入 ${data.count} 条用例`, 'success');
        } else {
            showToast(data.detail || '导入失败', 'error');
        }
    } catch (e) {
        showToast('导入失败', 'error');
    }

    e.target.value = '';
}

function exportTestCases() {
    if (!state.testCases.length) {
        showToast('没有可导出的用例', 'warning');
        return;
    }

    const csv = 'name,description,expected\n' +
        state.testCases.map(c =>
            `"${c.name}","${c.description.replace(/"/g, '""')}","${(c.expected || '').replace(/"/g, '""')}"`
        ).join('\n');

    downloadFile(csv, 'test_cases.csv', 'text/csv');
}

function downloadTemplate() {
    window.location.href = '/template_csv';
}

// ============ 场景管理 ============
async function loadScenarios() {
    try {
        const res = await fetch('/scenarios');
        state.scenarios = await res.json();
        renderScenarios();
    } catch (e) {
        console.error('加载场景失败:', e);
    }
}

function renderScenarios() {
    const container = document.getElementById('scenarioList');

    if (!state.scenarios.length) {
        container.innerHTML = '<div class="empty-state">暂无保存的场景</div>';
        return;
    }

    container.innerHTML = state.scenarios.map(s => `
        <div class="scenario-item" onclick="loadScenario('${s.id}')">
            <span class="scenario-name">${s.name}</span>
            <span class="scenario-count">${s.test_cases.length}条</span>
            <button class="icon-btn" onclick="event.stopPropagation();deleteScenario('${s.id}')" title="删除">
                <span class="material-icons-round">delete</span>
            </button>
        </div>
    `).join('');
}

function showScenarioModal() {
    if (!state.testCases.length) {
        showToast('请先添加测试用例', 'warning');
        return;
    }
    document.getElementById('scenarioName').value = '';
    document.getElementById('scenarioModal').classList.add('show');
}

function closeScenarioModal() {
    document.getElementById('scenarioModal').classList.remove('show');
}

async function saveScenario() {
    const name = document.getElementById('scenarioName').value.trim();
    if (!name) {
        showToast('请输入场景名称', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('name', name);
    formData.append('test_cases', JSON.stringify(state.testCases));

    try {
        const res = await fetch('/scenarios', {
            method: 'POST',
            body: formData
        });

        if (res.ok) {
            showToast('保存成功', 'success');
            closeScenarioModal();
            loadScenarios();
        } else {
            showToast('保存失败', 'error');
        }
    } catch (e) {
        showToast('保存失败', 'error');
    }
}

function loadScenario(id) {
    const scenario = state.scenarios.find(s => s.id === id);
    if (!scenario) return;

    if (state.testCases.length && !confirm('加载场景将替换当前用例，确定吗？')) {
        return;
    }

    state.currentScenarioName = scenario.name;  // 保存场景名称
    state.testCases = scenario.test_cases.map(c => ({
        ...c,
        id: generateId(),
        selected: false
    }));
    renderTestCases();
    saveTestCasesToLocal();  // 保存到 localStorage
    showToast(`已加载场景: ${scenario.name}`, 'success');
}

async function deleteScenario(id) {
    if (!confirm('确定删除此场景？')) return;

    try {
        await fetch(`/scenarios/${id}`, { method: 'DELETE' });
        showToast('已删除', 'success');
        loadScenarios();
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

// ============ 任务执行 ============
async function runSelectedCases() {
    if (!state.selectedDevice) {
        showToast('请先选择设备', 'warning');
        return;
    }

    const selectedCases = state.testCases.filter(c => c.selected);
    if (!selectedCases.length) {
        showToast('请选择要执行的用例', 'warning');
        return;
    }

    const apiConfigId = document.getElementById('activeApiConfig').value;

    // 检查 API 配置
    if (!apiConfigId) {
        showToast('请先选择 API 配置！', 'warning');
        return;
    }

    const platform = state.selectedPlatform || 'android';

    // iOS 设备需要 WDA URL
    let wdaUrl = '';
    if (platform === 'ios') {
        try {
            const wdaRes = await fetch(`/ios/wda/config/${state.selectedDevice}`);
            const wdaData = await wdaRes.json();
            wdaUrl = wdaData.wda_url || '';

            if (!wdaUrl) {
                showToast('iOS 设备需要先配置 WDA URL！请点击"远程控制"进行配置', 'warning');
                return;
            }
        } catch (e) {
            showToast('获取 WDA 配置失败', 'error');
            return;
        }
    }

    setRunningState(true);
    clearLogsContent();
    resetMetrics();
    updateTaskStatus('running');

    try {
        // 获取当前场景名称（如果有）
        const scenarioName = state.currentScenarioName || '';
        
        const requestBody = {
            device_id: state.selectedDevice,
            test_cases: selectedCases,
            platform: platform,
            wda_url: wdaUrl,
            api_config_id: apiConfigId,
            max_steps: 0, // 不限制步数
            lang: 'cn',
            scenario_name: scenarioName,
            local_name: state.currentLocal || ''  // 本地端名称（多用户隔离）
        };

        const res = await fetch('/run_batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!res.ok) {
            const err = await res.json();
            if (err.detail && err.detail.includes('ADB Keyboard')) {
                showImeErrorModal(err.detail);
            } else if (err.detail && err.detail.includes('WDA')) {
                showToast(err.detail, 'warning');
            } else {
                showToast(err.detail || '启动任务失败', 'error');
            }
            setRunningState(false);
            updateTaskStatus('failed');
            return;
        }

        const data = await res.json();
        state.currentTaskId = data.batch_id;

        startRunTimer();
        connectWebSocket(data.batch_id);

    } catch (e) {
        showToast('启动任务失败: ' + e.message, 'error');
        setRunningState(false);
        updateTaskStatus('failed');
    }
}

async function stopTask() {
    if (!state.currentTaskId) return;

    try {
        await fetch(`/stop_task/${state.currentTaskId}`, { method: 'POST' });
        showToast('任务已停止', 'warning');
        
        // 立即停止执行状态
        setRunningState(false);
        stopRunTimer();
        updateTaskStatus('stopped');
        
        // 关闭 WebSocket
        if (state.ws) {
            state.ws.close();
            state.ws = null;
        }
        
        // 刷新历史
        loadHistory();
    } catch (e) {
        showToast('停止失败', 'error');
    }
}

function connectWebSocket(taskId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/${taskId}`);

    ws.onopen = () => {
        addLog({ type: 'info', content: '已连接，等待日志...', timestamp: getTime() });
    };

    ws.onmessage = (event) => {
        const log = JSON.parse(event.data);
        handleLogMessage(log);
    };

    ws.onclose = () => {
        state.ws = null;
        // WebSocket 关闭 = 任务结束，立即停止执行状态
        if (state.isRunning) {
            console.log('WebSocket closed, stopping running state');
            setRunningState(false);
            stopRunTimer();
            // 尝试获取最终状态
            if (state.currentTaskId) {
                fetch(`/task/${state.currentTaskId}`).then(res => res.json()).then(data => {
                    if (data && data.status) {
                        updateTaskStatus(data.status);
                    }
                }).catch(() => {});
            }
            loadHistory();
        }
    };

    ws.onerror = () => {
        addLog({ type: 'error', content: 'WebSocket 连接错误', timestamp: getTime() });
    };

    state.ws = ws;
}

function handleLogMessage(log) {
    // 更新截图
    if (log.type === 'screenshot' && log.image) {
        const img = document.getElementById('deviceScreen');
        const placeholder = document.getElementById('screenPlaceholder');
        // 判断是否为文件路径（新格式）或 base64（旧格式）
        img.src = log.image.startsWith('screenshots/') 
            ? `/data/${log.image}` 
            : `data:image/png;base64,${log.image}`;
        img.style.display = 'block';
        placeholder.style.display = 'none';
        if (log.width && log.height) {
            document.getElementById('screenInfo').textContent = `${log.width} × ${log.height}`;
        }
    }

    // 更新性能指标
    if (log.type === 'metrics') {
        updateMetrics(log);
    }

    // 任务完成
    if (log.type === 'complete' || log.type === 'batch_complete') {
        setRunningState(false);
        stopRunTimer();
        updateTaskStatus(log.status);
        // 延迟刷新历史，确保服务端已收到同步数据
        setTimeout(() => loadHistory(), 1500);
        // 再次刷新确保数据同步
        setTimeout(() => loadHistory(), 3000);
    }
    
    // 单个用例完成时也刷新历史
    if (log.type === 'case_complete') {
        setTimeout(() => loadHistory(), 500);
    }

    // 错误
    if (log.type === 'error') {
        if (!log.content?.includes('batch_complete')) {
            addLog(log);
        }
    }

    // 添加日志
    if (['info', 'step', 'thinking', 'action', 'success', 'error', 'case_start', 'case_complete'].includes(log.type)) {
        addLog(log);
    }
}

function addLog(log) {
    const container = document.getElementById('logContainer');
    const placeholder = container.querySelector('.log-placeholder');
    if (placeholder) placeholder.remove();

    let content = log.content || '';
    if (log.type === 'action' && log.action) {
        content = JSON.stringify(log.action, null, 2);
    }

    const logEl = document.createElement('div');
    logEl.className = `log-entry ${log.type}`;
    logEl.innerHTML = `<span class="timestamp">${log.timestamp}</span>${escapeHtml(content)}`;

    container.appendChild(logEl);
    container.scrollTop = container.scrollHeight;
}

function clearLogs() {
    clearLogsContent();
}

function clearLogsContent() {
    document.getElementById('logContainer').innerHTML = `
        <div class="log-placeholder">
            <span class="material-icons-round">article</span>
            <p>等待执行任务...</p>
        </div>
    `;
}

// ============ 状态更新 ============
function setRunningState(running) {
    state.isRunning = running;
    document.getElementById('runSelected').disabled = running;
    document.getElementById('stopTask').disabled = !running;

    if (running) {
        document.getElementById('runSelected').innerHTML =
            '<span class="material-icons-round">hourglass_empty</span>执行中...';
    } else {
        document.getElementById('runSelected').innerHTML =
            '<span class="material-icons-round">play_arrow</span>执行选中用例';
    }
}

function updateTaskStatus(status) {
    const el = document.getElementById('taskStatus');
    const statusMap = {
        'running': '执行中',
        'success': '已完成',
        'completed': '已完成',
        'failed': '失败',
        'stopped': '已中断'
    };
    el.textContent = statusMap[status] || status;
    el.className = 'card-value status-value ' + status;
}

function updateMetrics(metrics) {
    if (metrics.ttft) {
        document.getElementById('ttft').textContent = metrics.ttft.toFixed(2) + 's';
    }
    if (metrics.thinking_time) {
        document.getElementById('thinkingTime').textContent = metrics.thinking_time.toFixed(2) + 's';
    }
    if (metrics.total_time) {
        document.getElementById('totalTime').textContent = metrics.total_time.toFixed(2) + 's';
    }
}

function resetMetrics() {
    document.getElementById('ttft').textContent = '-';
    document.getElementById('thinkingTime').textContent = '-';
    document.getElementById('totalTime').textContent = '-';
    document.getElementById('runTime').textContent = '00:00';
}

function startRunTimer() {
    state.runStartTime = Date.now();
    state.runTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - state.runStartTime) / 1000);
        const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const secs = String(elapsed % 60).padStart(2, '0');
        document.getElementById('runTime').textContent = `${mins}:${secs}`;
    }, 1000);
}

function stopRunTimer() {
    if (state.runTimer) {
        clearInterval(state.runTimer);
        state.runTimer = null;
    }
}

// ============ 历史记录 ============
async function loadHistory() {
    try {
        const res = await fetch('/history');
        const history = await res.json();
        renderHistory(history);
    } catch (e) {
        console.error('加载历史失败:', e);
    }
}

function renderHistory(history) {
    const container = document.getElementById('historyList');
    state.selectedHistoryIds = [];  // 重置选中状态

    if (!history.length) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="material-icons-round">history</span>
                <p>暂无历史记录</p>
            </div>
        `;
        return;
    }

    // 生成报告按钮
    let headerHtml = `
        <div class="history-header" style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-bottom:1px solid var(--border);">
            <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--text-muted);cursor:pointer;">
                <input type="checkbox" id="selectAllHistory" onchange="toggleSelectAllHistory(this.checked)">
                全选
            </label>
            <button class="btn btn-small btn-outline" onclick="generateReport()" id="genReportBtn" disabled>
                <span class="material-icons-round" style="font-size:14px;">description</span>
                生成报告
            </button>
        </div>
    `;

    let itemsHtml = history.map(h => {
        const statusIcon = h.status === 'completed' || h.status === 'success' ? 'check_circle' :
            h.status === 'stopped' ? 'pause_circle' : 'error';
        const statusClass = h.status === 'completed' || h.status === 'success' ? 'success' :
            h.status === 'stopped' ? 'stopped' : 'failed';
        
        // 显示名称：优先场景名，否则显示时间
        const displayName = h.name || h.scenario_name || formatTime(h.start_time);
        const subInfo = h.scenario_name ? `场景: ${h.scenario_name}` : formatTime(h.start_time);

        return `
            <div class="history-item">
                <input type="checkbox" class="history-checkbox" data-id="${h.id}" onclick="event.stopPropagation();toggleHistorySelect('${h.id}')" style="margin-right:8px;">
                <div class="history-status-icon ${statusClass}" onclick="showHistoryDetail('${h.id}')">
                    <span class="material-icons-round">${statusIcon}</span>
                </div>
                <div class="history-info" onclick="showHistoryDetail('${h.id}')" style="cursor:pointer;">
                    <div class="history-time" title="${displayName}">${displayName.length > 20 ? displayName.substring(0, 20) + '...' : displayName}</div>
                    <div class="history-stats">
                        ${h.completed_cases || 0}/${h.total_cases || 0} 用例 · ${statusClass === 'success' ? '成功' : statusClass === 'stopped' ? '中断' : '失败'}
                    </div>
                </div>
                <div class="history-actions" style="display:flex;flex-direction:row;gap:6px;">
                    <button class="emoji-btn" onclick="event.stopPropagation();exportHistoryExcel('${h.id}')" title="导出Excel">📥</button>
                    <button class="emoji-btn" onclick="event.stopPropagation();confirmDeleteHistory('${h.id}')" title="删除">🗑️</button>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = headerHtml + itemsHtml;
}

// 历史记录选择相关函数
function toggleHistorySelect(id) {
    const idx = state.selectedHistoryIds.indexOf(id);
    if (idx > -1) {
        state.selectedHistoryIds.splice(idx, 1);
    } else {
        state.selectedHistoryIds.push(id);
    }
    updateReportButton();
}

function toggleSelectAllHistory(checked) {
    const checkboxes = document.querySelectorAll('.history-checkbox');
    state.selectedHistoryIds = [];
    checkboxes.forEach(cb => {
        cb.checked = checked;
        if (checked) {
            state.selectedHistoryIds.push(cb.dataset.id);
        }
    });
    updateReportButton();
}

function updateReportButton() {
    const btn = document.getElementById('genReportBtn');
    if (btn) {
        btn.disabled = state.selectedHistoryIds.length === 0;
        btn.innerHTML = `<span class="material-icons-round" style="font-size:14px;">description</span>生成报告${state.selectedHistoryIds.length > 0 ? ` (${state.selectedHistoryIds.length})` : ''}`;
    }
}

async function generateReport() {
    if (state.selectedHistoryIds.length === 0) {
        showToast('请先选择历史记录', 'warning');
        return;
    }

    const reportName = prompt('请输入报告名称（可选）:', `AI-UI测试报告_${new Date().toISOString().slice(0,10)}`);
    if (reportName === null) return;  // 取消

    try {
        const res = await fetch('/report/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                record_ids: state.selectedHistoryIds,
                report_name: reportName || ''
            })
        });

        if (res.ok) {
            const data = await res.json();
            showToast('报告已生成，切换到报告页面查看', 'success');
            // 清空选择
            state.selectedHistoryIds = [];
            loadHistory();
            // 切换到报告 Tab
            switchTab('reports');
        } else {
            const err = await res.json();
            showToast(err.detail || '生成失败', 'error');
        }
    } catch (e) {
        showToast('生成报告失败: ' + e.message, 'error');
    }
}

function showHistoryDetail(id) {
    state.currentHistoryId = id;

    // 使用新的详情 API
    fetch(`/history/${id}`).then(res => res.json()).then(record => {
        if (!record) return;

        const content = document.getElementById('historyDetailContent');
        content.innerHTML = (record.case_results || []).map((c, i) => {
            const statusClass = c.status === 'success' ? 'success' : c.status === 'stopped' ? 'stopped' : 'failed';
            const statusText = c.status === 'success' ? '通过' : c.status === 'stopped' ? '中断' : '失败';

            const screenshots = c.screenshots || [];
            const screenshotHtml = screenshots.slice(-3).map(s => {
                // 判断是否为文件路径（新格式）或 base64（旧格式）
                const imgSrc = s.image && s.image.startsWith('screenshots/') 
                    ? `/data/${s.image}` 
                    : `data:image/png;base64,${s.image}`;
                return `<img src="${imgSrc}" onclick="window.open(this.src)">`;
            }).join('');

            return `
                <div class="history-detail-case">
                    <div class="history-detail-header">
                        <span>${i + 1}. ${c.case_name}</span>
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </div>
                    <div class="history-detail-body">
                        <p><strong>结果：</strong>${c.result || '-'}</p>
                        <p><strong>完成时间：</strong>${formatFullTime(c.end_time)}</p>
                        ${screenshotHtml ? `<div class="history-screenshot-preview">${screenshotHtml}</div>` : ''}
                    </div>
                </div>
            `;
        }).join('');

        document.getElementById('historyDetailModal').classList.add('show');
    });
}

function closeHistoryModal() {
    document.getElementById('historyDetailModal').classList.remove('show');
    state.currentHistoryId = null;
}

function exportExcel() {
    if (!state.currentHistoryId) return;
    window.location.href = `/export_excel/${state.currentHistoryId}`;
}

function exportHistoryExcel(id) {
    if (confirm('确定要导出此记录为Excel文件？')) {
        window.location.href = `/export_excel/${id}`;
    }
}

function confirmDeleteHistory(id) {
    if (confirm('⚠️ 确定要删除此历史记录吗？\n\n删除后将无法恢复！')) {
        deleteHistory(id);
    }
}

async function deleteHistory(id) {
    try {
        await fetch(`/history/${id}`, { method: 'DELETE' });
        showToast('已删除', 'success');
        loadHistory();
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

// ============ Tab 切换 ============
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.toggle('active', el.id === tabName + 'Tab');
    });
    
    // 切换到报告 Tab 时加载报告列表
    if (tabName === 'reports') {
        loadReports();
    }
}

// ============ 报告管理 ============
async function loadReports() {
    try {
        const res = await fetch('/reports');
        const reports = await res.json();
        renderReports(reports);
    } catch (e) {
        console.error('加载报告失败:', e);
    }
}

function renderReports(reports) {
    const container = document.getElementById('reportsList');

    if (!reports.length) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="material-icons-round">description</span>
                <p>暂无测试报告</p>
                <small style="color:var(--text-muted);">在历史记录中选择记录后点击"生成报告"</small>
            </div>
        `;
        return;
    }

    container.innerHTML = reports.map(r => {
        const createTime = formatTime(r.created_at);
        return `
            <div class="report-item">
                <div class="report-icon">
                    <span class="material-icons-round">description</span>
                </div>
                <div class="report-info" onclick="openReport('${r.id}')" title="${r.name}">
                    <div class="report-name">${r.name || '测试报告'}</div>
                    <div class="report-meta">${createTime} · ${r.total_records || 0} 条记录</div>
                </div>
                <div class="report-actions">
                    <button class="emoji-btn" onclick="event.stopPropagation();openReport('${r.id}')" title="查看报告">📄</button>
                    <button class="emoji-btn" onclick="event.stopPropagation();confirmDeleteReport('${r.id}')" title="删除">🗑️</button>
                </div>
            </div>
        `;
    }).join('');
}

function openReport(id) {
    window.open(`/report/${id}`, '_blank');
}

async function confirmDeleteReport(id) {
    if (!confirm('确定删除此报告？')) return;
    
    try {
        await fetch(`/report/${id}`, { method: 'DELETE' });
        showToast('已删除', 'success');
        loadReports();
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

// ============ 弹窗 ============
function showImeErrorModal(message) {
    document.getElementById('imeErrorMessage').textContent = message;
    document.getElementById('imeErrorModal').classList.add('show');
}

// ============ Toast ============
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="material-icons-round">${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : type === 'warning' ? 'warning' : 'info'}</span>
        <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============ 工具函数 ============
function generateId() {
    return Math.random().toString(36).substr(2, 8);
}

function getTime() {
    return new Date().toLocaleTimeString('zh-CN', { hour12: false });
}

function formatTime(isoString) {
    if (!isoString) return '-';
    const d = new Date(isoString);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hour = String(d.getHours()).padStart(2, '0');
    const minute = String(d.getMinutes()).padStart(2, '0');
    const second = String(d.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

function formatFullTime(isoString) {
    if (!isoString) return '-';
    const d = new Date(isoString);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hour = String(d.getHours()).padStart(2, '0');
    const minute = String(d.getMinutes()).padStart(2, '0');
    const second = String(d.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

// ============ 远程控制 ============
const remoteControl = {
    ws: null,
    canvas: null,
    ctx: null,
    deviceId: null,
    platform: 'android',
    wdaUrl: null,
    screenWidth: 0,
    screenHeight: 0,
    canvasWidth: 0,
    canvasHeight: 0,
    isConnected: false,
    frameCount: 0,
    lastFpsUpdate: 0,
    isDragging: false,
    dragStart: null,
    refreshInterval: null,

    async start() {
        if (!state.selectedDevice) {
            showToast('请先选择设备', 'warning');
            return;
        }

        this.deviceId = state.selectedDevice;
        this.platform = state.selectedPlatform || 'android';

        // iOS 设备需要先配置 WDA
        if (this.platform === 'ios') {
            const wdaConfig = await this.checkIOSWdaConfig();
            if (!wdaConfig) {
                this.showWdaConfigModal();
                return;
            }
            this.wdaUrl = wdaConfig;
        }

        document.getElementById('remoteDeviceId').textContent = this.deviceId;
        document.getElementById('remoteControlModal').classList.add('show');
        document.getElementById('remotePlaceholder').classList.remove('hidden');
        document.getElementById('remoteStatus').textContent = '连接中...';

        // 显示平台信息
        const platformLabel = this.platform === 'ios' ? 'iOS (WDA)' : 'Android (ADB)';
        document.getElementById('remoteResolution').textContent = platformLabel;

        this.initCanvas();
        this.connect();
    },

    async checkIOSWdaConfig() {
        try {
            const res = await fetch(`/ios/wda/config/${this.deviceId}`);
            const data = await res.json();
            return data.wda_url;
        } catch (e) {
            return null;
        }
    },

    showWdaConfigModal() {
        const url = prompt(
            'iOS 设备需要配置 WebDriverAgent URL\n' +
            '请输入 WDA URL (例如: http://192.168.1.100:8100):\n\n' +
            '提示:\n' +
            '1. 需要在 iOS 设备上运行 WebDriverAgent\n' +
            '2. 通过 USB 连接时使用: http://localhost:8100\n' +
            '3. 通过 WiFi 连接时使用设备 IP',
            'http://localhost:8100'
        );

        if (url) {
            this.setIOSWdaConfig(url);
        }
    },

    async setIOSWdaConfig(url) {
        try {
            const res = await fetch(`/ios/wda/config/${this.deviceId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ wda_url: url })
            });

            if (res.ok) {
                this.wdaUrl = url;
                showToast('WDA 配置已保存', 'success');
                // 重新启动远程控制
                this.start();
            } else {
                showToast('配置保存失败', 'error');
            }
        } catch (e) {
            showToast('配置保存失败: ' + e.message, 'error');
        }
    },

    stop() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        this.isConnected = false;
        document.getElementById('remoteControlModal').classList.remove('show');
        document.getElementById('remoteStatus').textContent = '未连接';
    },

    initCanvas() {
        this.canvas = document.getElementById('remoteCanvas');
        this.ctx = this.canvas.getContext('2d');

        // 绑定事件
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('mouseleave', (e) => this.onMouseUp(e));

        // 触摸事件（移动端）
        this.canvas.addEventListener('touchstart', (e) => this.onTouchStart(e));
        this.canvas.addEventListener('touchmove', (e) => this.onTouchMove(e));
        this.canvas.addEventListener('touchend', (e) => this.onTouchEnd(e));

        // 文本输入回车
        document.getElementById('remoteTextInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendText();
        });
    },

    async connect() {
        try {
            // 根据平台选择不同的 API
            const screenEndpoint = this.platform === 'ios'
                ? `/ios/remote/screen/${this.deviceId}`
                : `/remote/screen/${this.deviceId}`;

            // 先获取一帧屏幕以获取尺寸
            const res = await fetch(screenEndpoint);
            const data = await res.json();

            if (data.status === 'success') {
                this.screenWidth = data.width;
                this.screenHeight = data.height;
                const platformLabel = this.platform === 'ios' ? 'iOS' : 'Android';
                document.getElementById('remoteResolution').textContent = `${data.width} × ${data.height} (${platformLabel})`;

                // 加载图片
                const img = new Image();
                img.onload = () => {
                    this.resizeCanvas(img.width, img.height);
                    this.ctx.drawImage(img, 0, 0, this.canvasWidth, this.canvasHeight);
                    document.getElementById('remotePlaceholder').classList.add('hidden');
                };
                img.src = `data:image/png;base64,${data.image}`;

                // 启动 WebSocket 连接
                this.connectWebSocket();
            } else {
                throw new Error(data.detail || '获取屏幕失败');
            }
        } catch (e) {
            console.error('连接失败:', e);
            document.getElementById('remoteStatus').textContent = '连接失败';

            if (this.platform === 'ios') {
                showToast('iOS 连接失败，请检查 WDA 是否运行', 'error');
            } else {
                showToast('远程控制连接失败: ' + e.message, 'error');
            }

            // 回退到轮询模式
            this.startPollingMode();
        }
    },

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // 根据平台选择不同的 WebSocket 端点
        const wsPath = this.platform === 'ios'
            ? `/ws/ios/remote/${this.deviceId}`
            : `/ws/remote/${this.deviceId}`;
        const wsUrl = `${protocol}//${window.location.host}${wsPath}`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                this.isConnected = true;
                document.getElementById('remoteStatus').textContent = '已连接 (WebSocket)';
                showToast('远程控制已连接', 'success');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'screen') {
                    this.updateScreen(data.image);
                    this.updateFps();
                }
            };

            this.ws.onclose = () => {
                this.isConnected = false;
                document.getElementById('remoteStatus').textContent = '连接断开';
                // 回退到轮询模式
                if (document.getElementById('remoteControlModal').classList.contains('show')) {
                    this.startPollingMode();
                }
            };

            this.ws.onerror = (e) => {
                console.error('WebSocket 错误:', e);
                // 回退到轮询模式
                this.startPollingMode();
            };
        } catch (e) {
            console.error('WebSocket 创建失败:', e);
            this.startPollingMode();
        }
    },

    startPollingMode() {
        if (this.refreshInterval) return;

        document.getElementById('remoteStatus').textContent = '已连接 (轮询模式)';

        this.refreshInterval = setInterval(async () => {
            await this.refreshScreen();
        }, 200); // 5 FPS
    },

    async refreshScreen() {
        try {
            const endpoint = this.platform === 'ios'
                ? `/ios/remote/screen/${this.deviceId}`
                : `/remote/screen/${this.deviceId}`;

            const res = await fetch(endpoint);
            const data = await res.json();

            if (data.status === 'success') {
                this.updateScreen(data.image);
                this.updateFps();
            }
        } catch (e) {
            console.error('刷新屏幕失败:', e);
        }
    },

    updateScreen(base64Image) {
        const img = new Image();
        img.onload = () => {
            if (this.canvasWidth !== img.width || this.canvasHeight !== img.height) {
                this.resizeCanvas(img.width, img.height);
            }
            this.ctx.drawImage(img, 0, 0, this.canvasWidth, this.canvasHeight);
            document.getElementById('remotePlaceholder').classList.add('hidden');
        };
        img.src = `data:image/png;base64,${base64Image}`;
    },

    resizeCanvas(imgWidth, imgHeight) {
        const container = document.getElementById('remoteScreenContainer');
        const maxWidth = container.clientWidth - 20;
        const maxHeight = container.clientHeight - 20;

        const ratio = Math.min(maxWidth / imgWidth, maxHeight / imgHeight);

        this.canvasWidth = Math.floor(imgWidth * ratio);
        this.canvasHeight = Math.floor(imgHeight * ratio);

        this.canvas.width = this.canvasWidth;
        this.canvas.height = this.canvasHeight;
        this.canvas.style.width = this.canvasWidth + 'px';
        this.canvas.style.height = this.canvasHeight + 'px';
    },

    updateFps() {
        this.frameCount++;
        const now = Date.now();
        if (now - this.lastFpsUpdate >= 1000) {
            document.getElementById('remoteFps').textContent = this.frameCount + ' FPS';
            this.frameCount = 0;
            this.lastFpsUpdate = now;
        }
    },

    // 获取相对于设备屏幕的坐标
    getDeviceCoords(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // 转换为设备坐标
        const deviceX = Math.round((x / this.canvasWidth) * this.screenWidth);
        const deviceY = Math.round((y / this.canvasHeight) * this.screenHeight);

        return { x: deviceX, y: deviceY };
    },

    onMouseDown(e) {
        e.preventDefault();
        this.isDragging = true;
        this.dragStart = this.getDeviceCoords(e);
    },

    onMouseMove(e) {
        // 可以在这里添加拖动预览
    },

    onMouseUp(e) {
        if (!this.isDragging) return;

        e.preventDefault();
        this.isDragging = false;

        const end = this.getDeviceCoords(e);
        const start = this.dragStart;

        // 判断是点击还是滑动
        const distance = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2));

        if (distance < 10) {
            // 点击
            this.sendTap(start.x, start.y);
        } else {
            // 滑动
            this.sendSwipe(start.x, start.y, end.x, end.y);
        }
    },

    onTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        this.isDragging = true;
        this.dragStart = this.getDeviceCoords(touch);
    },

    onTouchMove(e) {
        // 可以在这里添加拖动预览
    },

    onTouchEnd(e) {
        if (!this.isDragging) return;

        e.preventDefault();
        this.isDragging = false;

        const touch = e.changedTouches[0];
        const end = this.getDeviceCoords(touch);
        const start = this.dragStart;

        const distance = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2));

        if (distance < 10) {
            this.sendTap(start.x, start.y);
        } else {
            this.sendSwipe(start.x, start.y, end.x, end.y);
        }
    },

    async sendTap(x, y) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action: 'tap', x, y }));
        } else {
            const endpoint = this.platform === 'ios'
                ? `/ios/remote/action/${this.deviceId}`
                : `/remote/action/${this.deviceId}`;
            await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'tap', x, y })
            });
        }
    },

    async sendSwipe(x1, y1, x2, y2, duration = 300) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action: 'swipe', x1, y1, x2, y2, duration }));
        } else {
            const endpoint = this.platform === 'ios'
                ? `/ios/remote/action/${this.deviceId}`
                : `/remote/action/${this.deviceId}`;
            await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'swipe', x: x1, y: y1, x2, y2, duration })
            });
        }
    },

    async sendKey(key) {
        const keycodes = {
            'back': 4,
            'home': 3,
            'recent': 187,
            'power': 26,
            'volume_up': 24,
            'volume_down': 25,
        };

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action: key }));
        } else {
            const endpoint = this.platform === 'ios'
                ? `/ios/remote/action/${this.deviceId}`
                : `/remote/action/${this.deviceId}`;

            // iOS 只支持 back 和 home
            if (this.platform === 'ios' && !['back', 'home'].includes(key)) {
                showToast('iOS 不支持此按键', 'warning');
                return;
            }

            await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: key, keycode: keycodes[key] || 0 })
            });
        }

        // 稍后刷新屏幕
        setTimeout(() => this.refreshScreen(), 500);
    },

    async sendText() {
        const input = document.getElementById('remoteTextInput');
        const text = input.value.trim();

        if (!text) return;

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action: 'text', text }));
        } else {
            const endpoint = this.platform === 'ios'
                ? `/ios/remote/action/${this.deviceId}`
                : `/remote/action/${this.deviceId}`;
            await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'text', text })
            });
        }

        input.value = '';
        showToast('文本已发送', 'success');

        // 稍后刷新屏幕
        setTimeout(() => this.refreshScreen(), 500);
    },

    // 配置 iOS WDA
    async configureWda() {
        if (this.platform !== 'ios') {
            showToast('仅 iOS 设备需要配置 WDA', 'info');
            return;
        }
        this.showWdaConfigModal();
    }
};
