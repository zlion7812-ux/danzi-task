// ========== 通用函数 ==========
function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');
    event.target.classList.add('active');
}

async function updateUI() {
    let resp = await fetch('/status');
    let data = await resp.json();
    let pointsDisplay = document.getElementById('pointsDisplay');
    let streakDisplay = document.getElementById('streakDisplay');
    if (pointsDisplay) pointsDisplay.innerText = data.points;
    if (streakDisplay) streakDisplay.innerText = data.streak;
}

// ========== 主页面函数 ==========
async function fightMonster(taskId) {
    let resp = await fetch('/fight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId })
    });
    let data = await resp.json();
    if (data.error) {
        document.getElementById('msgArea').innerHTML = '⚠️ ' + data.error;
        return;
    }
    document.getElementById('lootDisplay').innerHTML = `⚔️ 击败 ${data.monster_name}！<br>🎁 获得 ${data.base_points} 积分<br>✨ ${data.loot_effect}`;
    document.getElementById('msgArea').innerHTML = '✅ ' + data.message;
    updateUI();
    if (data.all_defeated) {
        setTimeout(() => location.reload(), 1200);
    } else {
        setTimeout(() => location.reload(), 800);
    }
}

async function startTimer(taskId, taskName) {
    let resp = await fetch('/start_timer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId, task_name: taskName })
    });
    let data = await resp.json();
    if (data.error) {
        document.getElementById('msgArea').innerHTML = '⚠️ ' + data.error;
    } else {
        document.getElementById('msgArea').innerHTML = '✅ ' + data.message;
        let statusSpan = document.getElementById(`timer-status-${taskId}`);
        if (statusSpan) statusSpan.innerHTML = '⏳ 进行中...';
    }
}

async function endTimer(taskId, taskName) {
    let resp = await fetch('/end_timer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_name: taskName })
    });
    let data = await resp.json();
    if (data.error) {
        document.getElementById('msgArea').innerHTML = '⚠️ ' + data.error;
        if (data.error.includes('时长不足')) {
            return;
        }
    } else {
        document.getElementById('lootDisplay').innerHTML = data.message;
        document.getElementById('msgArea').innerHTML = '✅ ' + data.message;
        updateUI();
        if (data.all_defeated) {
            setTimeout(() => location.reload(), 1500);
        } else {
            setTimeout(() => location.reload(), 1000);
        }
    }
}

async function openPortal() {
    let resp = await fetch('/portal', { method: 'POST' });
    let data = await resp.json();
    if (data.error) {
        document.getElementById('msgArea').innerHTML = '⚠️ ' + data.error;
    } else {
        location.reload();
    }
}

async function completeBonus(index) {
    let resp = await fetch('/complete_bonus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bonus_index: index })
    });
    let data = await resp.json();
    if (data.error) {
        document.getElementById('msgArea').innerHTML = '⚠️ ' + data.error;
    } else {
        document.getElementById('lootDisplay').innerHTML = `🎉 ${data.quest_name} 完成！ +${data.points}积分 🎉<br>✨ ${data.loot_effect}`;
        updateUI();
        setTimeout(() => location.reload(), 1000);
    }
}

async function buyItem(itemId) {
    let resp = await fetch('/buy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId })
    });
    let data = await resp.json();
    if (data.error) {
        alert(data.error);
    } else {
        alert(data.message);
        location.reload();
    }
}

async function resetDay() {
    let resp = await fetch('/reset_day', { method: 'POST' });
    let data = await resp.json();
    if (data.status === 'ok') location.reload();
}

// ========== 管理员后台函数 ==========
let adminTasks = [];
let adminMonsters = [];

async function adminLoadData() {
    let resp = await fetch('/admin/data');
    let data = await resp.json();
    adminTasks = data.tasks;
    adminMonsters = data.monsters;
    adminRenderTaskList();
    adminRenderMonsterList();
    adminUpdateMonsterSelect();

    if (data.config && data.config.streak_rule) {
        let ruleSelect = document.getElementById('streakRuleSelect');
        if (ruleSelect) ruleSelect.value = data.config.streak_rule;
    }
}

function adminRenderTaskList() {
    const container = document.getElementById('taskList');
    if (!container) return;
    if (!adminTasks.length) {
        container.innerHTML = '<div style="padding:20px;text-align:center">暂无任务，点击上方按钮添加</div>';
        return;
    }
    const sorted = [...adminTasks].sort((a, b) => (a.order || 999) - (b.order || 999));
    container.innerHTML = sorted.map(task => {
        const monster = adminMonsters.find(m => m.id === task.monster_id);
        const monsterDisplay = monster ? `${monster.icon} ${monster.name}` : '❓ 无怪物';
        return `
            <div class="task-item" data-id="${task.id}">
                <div class="task-info">
                    <strong>${task.name}</strong><br>
                    <small>${task.description || ''}</small><br>
                    <span class="badge ${task.enabled ? 'enabled' : 'disabled'}">${task.enabled ? '已启用' : '已禁用'}</span>
                    怪物: ${monsterDisplay} | 积分: ${task.points} | 顺序: ${task.order || '未设置'}
                </div>
                <div class="task-actions">
                    <button class="warning" onclick="adminEditTask('${task.id}')">✏️ 编辑</button>
                    <button class="danger" onclick="adminDeleteTask('${task.id}')">🗑️ 删除</button>
                </div>
            </div>
            <div id="edit-${task.id}" style="display:none" class="edit-form">
                <h4>编辑任务: ${task.name}</h4>
                <input type="text" id="edit-name-${task.id}" value="${task.name.replace(/'/g, "\\'")}">
                <textarea id="edit-desc-${task.id}" rows="2">${task.description || ''}</textarea>
                <select id="edit-monster-${task.id}">
                    <option value="">-- 选择怪物 --</option>
                    ${adminMonsters.map(m => `<option value="${m.id}" ${m.id === task.monster_id ? 'selected' : ''}>${m.icon} ${m.name}</option>`).join('')}
                </select>
                <input type="number" id="edit-points-${task.id}" value="${task.points}">
                <input type="number" id="edit-order-${task.id}" value="${task.order || 0}" placeholder="顺序(数字越小越靠左)">
                <label><input type="checkbox" id="edit-enabled-${task.id}" ${task.enabled ? 'checked' : ''}> 启用</label>
                <div class="form-row" style="margin-top:10px">
                    <button class="success" onclick="adminSaveTask('${task.id}')">💾 保存</button>
                    <button onclick="adminCancelEdit('${task.id}')">❌ 取消</button>
                </div>
            </div>
        `;
    }).join('');
}

function adminRenderMonsterList() {
    const container = document.getElementById('monsterList');
    if (!container) return;
    if (!adminMonsters.length) {
        container.innerHTML = '<div style="padding:20px;text-align:center">暂无怪物，点击上方按钮添加</div>';
        return;
    }
    container.innerHTML = adminMonsters.map(monster => {
        const usedBy = adminTasks.filter(t => t.monster_id === monster.id).length;
        return `
            <div class="monster-item" data-id="${monster.id}">
                <div class="monster-info">
                    <span style="font-size:1.5rem">${monster.icon}</span>
                    <strong>${monster.name}</strong><br>
                    <small>${monster.description || ''}</small><br>
                    <span class="badge">默认积分: ${monster.default_points}</span>
                    ${usedBy > 0 ? `<span class="badge" style="background:#2a6a2a">被 ${usedBy} 个任务使用</span>` : ''}
                </div>
                <div class="monster-actions">
                    <button class="warning" onclick="adminEditMonster('${monster.id}')">✏️ 编辑</button>
                    <button class="danger" onclick="adminDeleteMonster('${monster.id}')">🗑️ 删除</button>
                </div>
            </div>
            <div id="edit-monster-${monster.id}" style="display:none" class="edit-form">
                <h4>编辑怪物: ${monster.name}</h4>
                <input type="text" id="edit-m-name-${monster.id}" value="${monster.name.replace(/'/g, "\\'")}">
                <input type="text" id="edit-m-icon-${monster.id}" value="${monster.icon}">
                <input type="number" id="edit-m-points-${monster.id}" value="${monster.default_points}">
                <textarea id="edit-m-desc-${monster.id}" rows="2">${monster.description || ''}</textarea>
                <div class="form-row">
                    <button class="success" onclick="adminSaveMonster('${monster.id}')">💾 保存</button>
                    <button onclick="adminCancelEditMonster('${monster.id}')">❌ 取消</button>
                </div>
            </div>
        `;
    }).join('');
}

function adminUpdateMonsterSelect() {
    const select = document.getElementById('newTaskMonster');
    if (select) {
        select.innerHTML = '<option value="">-- 选择怪物 --</option>' +
            adminMonsters.map(m => `<option value="${m.id}">${m.icon} ${m.name}</option>`).join('');
    }
}

window.adminEditTask = (taskId) => {
    const editDiv = document.getElementById(`edit-${taskId}`);
    if (editDiv) editDiv.style.display = editDiv.style.display === 'none' ? 'block' : 'none';
};
window.adminCancelEdit = (taskId) => {
    document.getElementById(`edit-${taskId}`).style.display = 'none';
};
window.adminSaveTask = async (taskId) => {
    const name = document.getElementById(`edit-name-${taskId}`).value;
    const desc = document.getElementById(`edit-desc-${taskId}`).value;
    const monsterId = document.getElementById(`edit-monster-${taskId}`).value;
    const points = parseInt(document.getElementById(`edit-points-${taskId}`).value);
    const order = parseInt(document.getElementById(`edit-order-${taskId}`).value);
    const enabled = document.getElementById(`edit-enabled-${taskId}`).checked;
    const resp = await fetch('/admin/update_task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId, name, description: desc, monster_id: monsterId, points, order, enabled })
    });
    const data = await resp.json();
    if (data.status === 'ok') {
        await adminLoadData();
    } else {
        alert('保存失败: ' + (data.error || '未知错误'));
    }
};

window.adminDeleteTask = async (taskId) => {
    if (!confirm('确定要删除这个任务吗？')) return;
    const resp = await fetch('/admin/delete_task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId })
    });
    const data = await resp.json();
    if (data.status === 'ok') {
        await adminLoadData();
    } else {
        alert('删除失败: ' + (data.error || '未知错误'));
    }
};

window.adminShowAddTaskForm = () => {
    const form = document.getElementById('addTaskForm');
    if (form) form.style.display = 'block';
};
window.adminHideAddTaskForm = () => {
    const form = document.getElementById('addTaskForm');
    if (form) form.style.display = 'none';
    document.getElementById('newTaskName').value = '';
    document.getElementById('newTaskDesc').value = '';
    document.getElementById('newTaskPoints').value = '2';
};
window.adminAddTask = async () => {
    const name = document.getElementById('newTaskName').value;
    const desc = document.getElementById('newTaskDesc').value;
    const monsterId = document.getElementById('newTaskMonster').value;
    const points = parseInt(document.getElementById('newTaskPoints').value);
    if (!name || !monsterId) {
        alert('请填写任务名称并选择怪物');
        return;
    }
    const resp = await fetch('/admin/add_task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description: desc, monster_id: monsterId, points })
    });
    const data = await resp.json();
    if (data.status === 'ok') {
        adminHideAddTaskForm();
        await adminLoadData();
    } else {
        alert('添加失败: ' + (data.error || '未知错误'));
    }
};

window.adminEditMonster = (monsterId) => {
    const editDiv = document.getElementById(`edit-monster-${monsterId}`);
    if (editDiv) editDiv.style.display = editDiv.style.display === 'none' ? 'block' : 'none';
};
window.adminCancelEditMonster = (monsterId) => {
    document.getElementById(`edit-monster-${monsterId}`).style.display = 'none';
};
window.adminSaveMonster = async (monsterId) => {
    const name = document.getElementById(`edit-m-name-${monsterId}`).value;
    const icon = document.getElementById(`edit-m-icon-${monsterId}`).value;
    const points = parseInt(document.getElementById(`edit-m-points-${monsterId}`).value);
    const desc = document.getElementById(`edit-m-desc-${monsterId}`).value;
    const resp = await fetch('/admin/update_monster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ monster_id: monsterId, name, icon, default_points: points, description: desc })
    });
    const data = await resp.json();
    if (data.status === 'ok') {
        await adminLoadData();
    } else {
        alert('保存失败: ' + (data.error || '未知错误'));
    }
};

window.adminDeleteMonster = async (monsterId) => {
    const usedBy = adminTasks.filter(t => t.monster_id === monsterId).length;
    if (usedBy > 0) {
        alert(`此怪物正在被 ${usedBy} 个任务使用，请先修改这些任务的怪物绑定再删除。`);
        return;
    }
    if (!confirm('确定要删除这个怪物吗？')) return;
    const resp = await fetch('/admin/delete_monster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ monster_id: monsterId })
    });
    const data = await resp.json();
    if (data.status === 'ok') {
        await adminLoadData();
    } else {
        alert('删除失败: ' + (data.error || '未知错误'));
    }
};

window.adminShowAddMonsterForm = () => {
    const form = document.getElementById('addMonsterForm');
    if (form) form.style.display = 'block';
};
window.adminHideAddMonsterForm = () => {
    const form = document.getElementById('addMonsterForm');
    if (form) form.style.display = 'none';
    document.getElementById('newMonsterName').value = '';
    document.getElementById('newMonsterIcon').value = '👾';
    document.getElementById('newMonsterPoints').value = '2';
    document.getElementById('newMonsterDesc').value = '';
};
window.adminAddMonster = async () => {
    const name = document.getElementById('newMonsterName').value;
    const icon = document.getElementById('newMonsterIcon').value;
    const points = parseInt(document.getElementById('newMonsterPoints').value);
    const desc = document.getElementById('newMonsterDesc').value;
    if (!name) {
        alert('请填写怪物名称');
        return;
    }
    const resp = await fetch('/admin/add_monster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, icon, default_points: points, description: desc })
    });
    const data = await resp.json();
    if (data.status === 'ok') {
        adminHideAddMonsterForm();
        await adminLoadData();
    } else {
        alert('添加失败: ' + (data.error || '未知错误'));
    }
};

window.adminSaveSystemConfig = async () => {
    const streakRule = document.getElementById('streakRuleSelect').value;
    const resp = await fetch('/admin/update_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ streak_rule: streakRule })
    });
    const data = await resp.json();
    if (data.status === 'ok') {
        alert('✅ 设置已保存！从明天开始生效。');
    } else {
        alert('保存失败');
    }
};

window.adminResetStreak = async () => {
    if (!confirm('确定要重置连胜天数吗？这将把连续天数设为1。')) return;
    const resp = await fetch('/reset_streak', { method: 'POST' });
    const data = await resp.json();
    if (data.status === 'ok') {
        alert('✅ 连胜天数已重置为1');
    } else {
        alert('重置失败');
    }
};

window.adminResetChildDay = async () => {
    if (!confirm('确定要重置今天的任务进度吗？这会把所有未完成的任务重置为未讨伐状态，已获得的积分不会丢失。')) return;
    const resp = await fetch('/reset_day', { method: 'POST' });
    const data = await resp.json();
    if (data.status === 'ok') {
        alert('✅ 今日任务已重置！');
        location.reload();
    } else {
        alert('重置失败');
    }
};

window.adminLogout = () => {
    window.location.href = '/logout';
};

// 绑定计时按钮事件
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.start-timer-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            startTimer(this.dataset.id, this.dataset.name);
        });
    });
    document.querySelectorAll('.end-timer-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            endTimer(this.dataset.id, this.dataset.name);
        });
    });
});
// 重置所有数据
window.adminResetAllData = async () => {
    if (!confirm('⚠️ 警告：这将重置所有数据！\n\n包括：\n• 所有积分归零\n• 连胜天数归零\n• 兑换记录清空\n• 今日任务进度清空\n\n此操作不可撤销！确定要继续吗？')) return;

    if (!confirm('最后确认：真的要重置所有数据吗？')) return;

    let resp = await fetch('/admin/reset_all_data', { method: 'POST' });
    let data = await resp.json();
    if (data.status === 'ok') {
        alert('✅ 所有数据已重置！');
        location.reload();
    } else {
        alert('重置失败: ' + (data.error || '未知错误'));
    }
};