// ========== 管理后台专用 JavaScript ==========

let monstersData = [];
let currentTaskId = null;
let currentShopId = null;
let currentPointsAction = null;
let currentEditMonsterId = null;

// ========== 通用加载 ==========
async function adminLoadData() {
    let resp = await fetch('/admin/data');
    let data = await resp.json();
    renderTaskList(data.tasks);
    monstersData = data.monsters;
    renderMonsterList(monstersData);
    updateMonsterSelect();
    document.getElementById('streakRuleSelect').value = data.config.streak_rule || 'login';
    await loadShopItems();
}

function updateMonsterSelect() {
    const select = document.getElementById('editMonsterId');
    if (!select) return;
    select.innerHTML = '<option value="">-- 请选择怪物 --</option>';
    for (let monster of monstersData) {
        select.innerHTML += `<option value="${monster.id}">${monster.icon} ${monster.name}</option>`;
    }
}

// ========== 任务管理 ==========
function renderTaskList(tasks) {
    const container = document.getElementById('taskList');
    if (!container) return;
    container.innerHTML = '';
    for (let task of tasks) {
        const div = document.createElement('div');
        div.className = 'task-item';
        div.innerHTML = `
            <div class="task-info">
                <div class="task-name">${escapeHtml(task.name)} ${task.enabled ? '✅' : '⛔'}</div>
                <div class="task-desc">${escapeHtml(task.description || '无描述')}</div>
                <div class="task-meta">💰 ${task.points}分 | 排序: ${task.order} | 怪物ID: ${escapeHtml(task.monster_id)}</div>
            </div>
            <div class="task-actions">
                <button class="success" onclick="adminEditTask('${task.id}')">✏️ 编辑</button>
                <button class="danger" onclick="adminDeleteTask('${task.id}')">🗑️ 删除</button>
            </div>
        `;
        container.appendChild(div);
    }
}

function adminShowAddTaskModal() {
    currentTaskId = null;
    document.getElementById('taskModalTitle').innerHTML = '➕ 添加新任务';
    document.getElementById('editTaskId').value = '';
    document.getElementById('editTaskName').value = '';
    document.getElementById('editMonsterId').value = '';
    document.getElementById('editTaskPoints').value = '3';
    document.getElementById('editTaskOrder').value = '999';
    document.getElementById('editTaskDesc').value = '';
    document.getElementById('editTaskEnabled').checked = true;
    showModal('taskModal');
}

async function adminEditTask(taskId) {
    currentTaskId = taskId;
    let resp = await fetch(`/admin/task/${taskId}`);
    let task = await resp.json();
    document.getElementById('taskModalTitle').innerHTML = `✏️ 编辑任务 - ${escapeHtml(task.name)}`;
    document.getElementById('editTaskId').value = task.id;
    document.getElementById('editTaskName').value = task.name;
    document.getElementById('editMonsterId').value = task.monster_id;
    document.getElementById('editTaskPoints').value = task.points;
    document.getElementById('editTaskOrder').value = task.order || 999;
    document.getElementById('editTaskDesc').value = task.description || '';
    document.getElementById('editTaskEnabled').checked = task.enabled !== false;
    showModal('taskModal');
}

function hideTaskModal() {
    hideModal('taskModal');
}

async function saveTask() {
    const taskId = document.getElementById('editTaskId').value;
    const data = {
        name: document.getElementById('editTaskName').value.trim(),
        monster_id: document.getElementById('editMonsterId').value,
        points: parseInt(document.getElementById('editTaskPoints').value),
        order: parseInt(document.getElementById('editTaskOrder').value),
        description: document.getElementById('editTaskDesc').value,
        enabled: document.getElementById('editTaskEnabled').checked
    };
    if (!data.name) { alert('请填写任务名称'); return; }
    if (!data.monster_id) { alert('请选择怪物'); return; }
    if (isNaN(data.points) || data.points < 0) { alert('积分必须为正数'); return; }
    let url = taskId ? '/admin/update_task' : '/admin/add_task';
    if (taskId) data.task_id = taskId;
    let resp = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    let result = await resp.json();
    if (result.status === 'ok') {
        hideTaskModal();
        adminLoadData();
    } else {
        alert('保存失败');
    }
}

async function adminDeleteTask(taskId) {
    if (!confirm('确定删除此任务？')) return;
    let resp = await fetch('/admin/delete_task', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_id: taskId})
    });
    let result = await resp.json();
    if (result.status === 'ok') adminLoadData();
    else alert('删除失败');
}

// ========== 怪物管理 ==========
function renderMonsterList(monsters) {
    const container = document.getElementById('monsterList');
    if (!container) return;
    container.innerHTML = '';
    for (let monster of monsters) {
        const div = document.createElement('div');
        div.className = 'monster-item';
        div.innerHTML = `
            <div class="monster-info">
                <div class="monster-name">${escapeHtml(monster.icon)} ${escapeHtml(monster.name)}</div>
                <div class="monster-desc">${escapeHtml(monster.description || '')}</div>
                <div class="monster-meta">默认积分: ${monster.default_points}</div>
            </div>
            <div class="monster-actions">
                <button class="success" onclick="adminEditMonster('${monster.id}')">✏️ 编辑</button>
                <button class="danger" onclick="adminDeleteMonster('${monster.id}')">🗑️ 删除</button>
            </div>
        `;
        container.appendChild(div);
    }
}

function adminShowAddMonsterForm() {
    currentEditMonsterId = null;
    document.getElementById('addMonsterForm').style.display = 'block';
    document.getElementById('newMonsterName').value = '';
    document.getElementById('newMonsterIcon').value = '👾';
    document.getElementById('newMonsterPoints').value = '2';
    document.getElementById('newMonsterDesc').value = '';
    // 修改标题为添加模式
    const formTitle = document.querySelector('#addMonsterForm h3');
    if (formTitle) formTitle.innerHTML = '新建怪物';
}

async function adminEditMonster(monsterId) {
    // 查找要编辑的怪物
    const monster = monstersData.find(m => m.id === monsterId);
    if (!monster) {
        alert('怪物不存在');
        return;
    }
    currentEditMonsterId = monsterId;
    document.getElementById('addMonsterForm').style.display = 'block';
    document.getElementById('newMonsterName').value = monster.name;
    document.getElementById('newMonsterIcon').value = monster.icon || '👾';
    document.getElementById('newMonsterPoints').value = monster.default_points;
    document.getElementById('newMonsterDesc').value = monster.description || '';
    // 修改标题为编辑模式
    const formTitle = document.querySelector('#addMonsterForm h3');
    if (formTitle) formTitle.innerHTML = '编辑怪物';
}

function adminHideAddMonsterForm() {
    document.getElementById('addMonsterForm').style.display = 'none';
    document.getElementById('newMonsterName').value = '';
    document.getElementById('newMonsterIcon').value = '👾';
    document.getElementById('newMonsterPoints').value = '2';
    document.getElementById('newMonsterDesc').value = '';
    currentEditMonsterId = null;
}

async function adminAddMonster() {
    let data = {
        name: document.getElementById('newMonsterName').value,
        icon: document.getElementById('newMonsterIcon').value,
        default_points: parseInt(document.getElementById('newMonsterPoints').value),
        description: document.getElementById('newMonsterDesc').value
    };
    if (!data.name) { alert('请输入怪物名称'); return; }

    let url, method;
    if (currentEditMonsterId) {
        // 编辑模式
        url = '/admin/update_monster';
        method = 'POST';
        data.monster_id = currentEditMonsterId;
    } else {
        // 添加模式
        url = '/admin/add_monster';
        method = 'POST';
    }

    let resp = await fetch(url, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    let result = await resp.json();
    if (result.status === 'ok') {
        adminHideAddMonsterForm();
        adminLoadData();
    } else {
        alert('操作失败');
    }
}

async function adminDeleteMonster(monsterId) {
    if (!confirm('确定删除此怪物？关联的任务可能会出问题！')) return;
    let resp = await fetch('/admin/delete_monster', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({monster_id: monsterId})
    });
    let result = await resp.json();
    if (result.status === 'ok') {
        adminLoadData();
    } else {
        alert('删除失败');
    }
}

// ========== 商品管理 ==========
async function loadShopItems() {
    let resp = await fetch('/admin/shop_items');
    let items = await resp.json();
    renderShopList(items);
}

function renderShopList(items) {
    const container = document.getElementById('shopList');
    if (!container) return;
    container.innerHTML = '';
    for (let item of items) {
        const div = document.createElement('div');
        div.className = 'shop-item';
        div.innerHTML = `
            <div class="shop-info">
                <div class="shop-name">${escapeHtml(item.icon)} ${escapeHtml(item.name)}</div>
                <div class="shop-desc">${escapeHtml(item.description || '')}</div>
                <div class="shop-meta">💰 ${item.price}分 | 类型: ${item.type === 'weekend_only' ? '仅限周末' : '普通'} | 周限购: ${item.weekly_limit || '不限'}</div>
            </div>
            <div class="shop-actions">
                <button class="success" onclick="adminEditShop(${item.id})">✏️ 编辑</button>
                <button class="danger" onclick="adminDeleteShop(${item.id})">🗑️ 删除</button>
            </div>
        `;
        container.appendChild(div);
    }
}

function adminShowAddShopModal() {
    currentShopId = null;
    document.getElementById('shopModalTitle').innerHTML = '➕ 添加新商品';
    document.getElementById('editShopId').value = '';
    document.getElementById('editShopName').value = '';
    document.getElementById('editShopIcon').value = '🎁';
    document.getElementById('editShopPrice').value = '10';
    document.getElementById('editShopType').value = 'normal';
    document.getElementById('editShopWeeklyLimit').value = '';
    document.getElementById('editShopDesc').value = '';
    showModal('shopModal');
}

async function adminEditShop(itemId) {
    currentShopId = itemId;
    let resp = await fetch(`/admin/shop_item/${itemId}`);
    let item = await resp.json();
    document.getElementById('shopModalTitle').innerHTML = `✏️ 编辑商品 - ${escapeHtml(item.name)}`;
    document.getElementById('editShopId').value = item.id;
    document.getElementById('editShopName').value = item.name;
    document.getElementById('editShopIcon').value = item.icon || '🎁';
    document.getElementById('editShopPrice').value = item.price;
    document.getElementById('editShopType').value = item.type || 'normal';
    document.getElementById('editShopWeeklyLimit').value = item.weekly_limit || '';
    document.getElementById('editShopDesc').value = item.description || '';
    showModal('shopModal');
}

function hideShopModal() {
    hideModal('shopModal');
}

async function saveShop() {
    const itemId = document.getElementById('editShopId').value;
    const weeklyLimit = document.getElementById('editShopWeeklyLimit').value;
    const data = {
        name: document.getElementById('editShopName').value.trim(),
        icon: document.getElementById('editShopIcon').value,
        price: parseInt(document.getElementById('editShopPrice').value),
        type: document.getElementById('editShopType').value,
        weekly_limit: weeklyLimit ? parseInt(weeklyLimit) : null,
        description: document.getElementById('editShopDesc').value
    };
    if (!data.name) { alert('请输入商品名称'); return; }
    if (isNaN(data.price) || data.price < 0) { alert('价格必须为正数'); return; }
    let url = itemId ? '/admin/update_shop_item' : '/admin/add_shop_item';
    if (itemId) data.id = parseInt(itemId);
    let resp = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    let result = await resp.json();
    if (result.status === 'ok') {
        hideShopModal();
        adminLoadData();
    } else {
        alert('保存失败');
    }
}

async function adminDeleteShop(itemId) {
    if (!confirm('确定删除此商品？')) return;
    let resp = await fetch('/admin/delete_shop_item', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: itemId})
    });
    let result = await resp.json();
    if (result.status === 'ok') adminLoadData();
    else alert('删除失败');
}

// ========== 系统设置 ==========
async function adminSaveSystemConfig() {
    let streakRule = document.getElementById('streakRuleSelect').value;
    await fetch('/admin/update_config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({streak_rule: streakRule})
    });
    alert('保存成功');
}

async function adminResetStreak() {
    if (!confirm('重置连胜天数？')) return;
    await fetch('/admin/reset_streak', {method: 'POST'});
    alert('已重置');
}

async function adminResetChildDay() {
    if (!confirm('重置今日任务进度？')) return;
    await fetch('/admin/reset_child_day', {method: 'POST'});
    alert('已重置');
}

async function adminResetAllData() {
    if (!confirm('⚠️ 重置所有数据？不可恢复！')) return;
    await fetch('/admin/reset_all_data', {method: 'POST'});
    location.reload();
}

async function adminLogout() {
    window.location.href = '/logout';
}

// ========== 积分调整 ==========
async function loadCurrentPoints() {
    let resp = await fetch('/status');
    let data = await resp.json();
    const pointsSpan = document.getElementById('currentPoints');
    if (pointsSpan) pointsSpan.innerText = data.points;
}

function showAddPointsModal() {
    currentPointsAction = 'add';
    document.getElementById('pointsModalTitle').innerHTML = '➕ 增加积分';
    document.getElementById('pointsAmount').value = '';
    document.getElementById('pointsReason').value = '';
    showModal('pointsModal');
}

function showDeductPointsModal() {
    currentPointsAction = 'deduct';
    document.getElementById('pointsModalTitle').innerHTML = '➖ 扣除积分';
    document.getElementById('pointsAmount').value = '';
    document.getElementById('pointsReason').value = '';
    showModal('pointsModal');
}

function hidePointsModal() {
    hideModal('pointsModal');
}

async function submitAdjustPoints() {
    let amount = parseInt(document.getElementById('pointsAmount').value);
    let reason = document.getElementById('pointsReason').value.trim() || (currentPointsAction === 'add' ? '手动增加积分' : '手动扣除积分');
    if (isNaN(amount) || amount <= 0) { alert('请输入有效数量'); return; }
    let finalAmount = currentPointsAction === 'add' ? amount : -amount;
    if (!confirm(`确认${currentPointsAction === 'add' ? '增加' : '扣除'} ${amount} 积分？`)) return;
    let resp = await fetch('/admin/adjust_points', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({amount: finalAmount, reason: reason})
    });
    let data = await resp.json();
    if (data.error) alert(data.error);
    else {
        alert(data.message);
        loadCurrentPoints();
        adminLoadData();
    }
}

// ========== 弹窗辅助函数 ==========
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        modal.style.visibility = 'visible';
        modal.style.opacity = '1';
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        modal.style.visibility = 'hidden';
        modal.style.opacity = '0';
    }
}

// 折叠面板功能
function toggleCollapse(sectionId) {
    const content = document.getElementById(sectionId);
    const arrow = document.getElementById(sectionId + 'Arrow');
    if (!content || !arrow) return;
    if (content.style.display === 'none') {
        content.style.display = 'block';
        arrow.innerHTML = '▼';
    } else {
        content.style.display = 'none';
        arrow.innerHTML = '▶';
    }
}

// 点击弹窗外部关闭
document.getElementById('taskModal')?.addEventListener('click', function(e) {
    if (e.target === this) hideTaskModal();
});
document.getElementById('shopModal')?.addEventListener('click', function(e) {
    if (e.target === this) hideShopModal();
});
document.getElementById('pointsModal')?.addEventListener('click', function(e) {
    if (e.target === this) hidePointsModal();
});

// 绑定按钮事件
document.getElementById('taskSaveBtn')?.addEventListener('click', saveTask);
document.getElementById('taskCancelBtn')?.addEventListener('click', hideTaskModal);
document.getElementById('shopSaveBtn')?.addEventListener('click', saveShop);
document.getElementById('shopCancelBtn')?.addEventListener('click', hideShopModal);
document.getElementById('pointsConfirmBtn')?.addEventListener('click', submitAdjustPoints);
document.getElementById('pointsCancelBtn')?.addEventListener('click', hidePointsModal);

// HTML转义函数
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

// 初始化
adminLoadData();
loadCurrentPoints();