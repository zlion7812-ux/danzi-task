// ========== 全局变量 ==========
let tasksData = [];
let defeatedIds = [];
let portalAvailable = false;
let currentTask = null;
let activeTimerTaskId = null;

// 任务类型判断
function isTimerTask(taskName) {
    return taskName.includes('复习') || taskName.includes('阅读') || taskName.includes('运动') || taskName.includes('跳绳');
}

function isJumpRopeTask(taskName) {
    return taskName.includes('跳绳');
}

// 获取任务积分描述
function getRewardDescription(task) {
    const taskName = task.name;

    if (taskName.includes('起床')) {
        return `
            <div class="reward-item"><span class="reward-label">🌅 早起奖励</span><span class="reward-value">1-4 积分</span></div>
            <div class="reward-item"><span class="reward-label">⏰ 迟到奖励</span><span class="reward-value">1 积分</span></div>
            <div class="reward-item"><span class="reward-label">✨ 魔法掉落</span><span class="reward-value">随机 +1~5 积分</span></div>
            <div class="reward-item"><span class="reward-label">💥 暴击</span><span class="reward-value">20% 概率积分翻倍！</span></div>
        `;
    }

    if (taskName.includes('跳绳')) {
        return `
            <div class="reward-item"><span class="reward-label">🏃‍♂️ 最低门槛</span><span class="reward-value">300个</span></div>
            <div class="reward-item"><span class="reward-label">🎯 基础奖励</span><span class="reward-value">5-7 积分</span></div>
            <div class="reward-item"><span class="reward-label">📈 超额奖励</span><span class="reward-value">每多100个 +2 积分</span></div>
            <div class="reward-item"><span class="reward-label">✨ 魔法掉落</span><span class="reward-value">随机 +1~5 积分</span></div>
            <div class="reward-item"><span class="reward-label">💥 暴击</span><span class="reward-value">20% 概率积分翻倍！</span></div>
        `;
    }

    if (taskName.includes('运动')) {
        return `
            <div class="reward-item"><span class="reward-label">🏃 10分钟</span><span class="reward-value">3 积分</span></div>
            <div class="reward-item"><span class="reward-label">🏃 20分钟</span><span class="reward-value">5 积分</span></div>
            <div class="reward-item"><span class="reward-label">🏃 30分钟</span><span class="reward-value">7 积分</span></div>
            <div class="reward-item"><span class="reward-label">✨ 魔法掉落</span><span class="reward-value">随机 +1~5 积分</span></div>
            <div class="reward-item"><span class="reward-label">💥 暴击</span><span class="reward-value">20% 概率积分翻倍！</span></div>
        `;
    }

    if (taskName.includes('阅读') || taskName.includes('复习')) {
        return `
            <div class="reward-item"><span class="reward-label">⏰ 基础条件</span><span class="reward-value">至少 15 分钟</span></div>
            <div class="reward-item"><span class="reward-label">📖 基础积分</span><span class="reward-value">3-6 积分</span></div>
            <div class="reward-item"><span class="reward-label">🎁 超额奖励</span><span class="reward-value">超过30分钟后，每20分钟+3分</span></div>
            <div class="reward-item"><span class="reward-label">✨ 魔法掉落</span><span class="reward-value">随机 +1~5 积分</span></div>
            <div class="reward-item"><span class="reward-label">💥 暴击</span><span class="reward-value">20% 概率积分翻倍！</span></div>
        `;
    }

    return `
        <div class="reward-item"><span class="reward-label">🎯 基础积分</span><span class="reward-value">${task.points || 3} 积分</span></div>
        <div class="reward-item"><span class="reward-label">✨ 魔法掉落</span><span class="reward-value">随机 +1~5 积分</span></div>
        <div class="reward-item"><span class="reward-label">💥 暴击</span><span class="reward-value">20% 概率积分翻倍！</span></div>
    `;
}

// 更新跳绳进度
function updateJumpProgress(count) {
    const progressElem = document.getElementById('jumpProgress');
    if (progressElem) {
        let displayCount = Math.min(count, 1000);
        progressElem.innerHTML = `📊 进度：${displayCount} / 1000 个`;
        progressElem.style.color = count >= 300 ? '#44ff44' : '#ffaa44';
    }
}

// 更新角色位置
function updatePlayerPosition() {
    let firstIncompleteIndex = -1;
    for (let i = 0; i < tasksData.length; i++) {
        if (!defeatedIds.includes(tasksData[i].id)) {
            firstIncompleteIndex = i;
            break;
        }
    }

    const pathContainer = document.getElementById('pathContainer');
    const playerWrapper = document.getElementById('playerWrapper');
    const cards = document.querySelectorAll('.node-card');

    if (!pathContainer || !playerWrapper || cards.length === 0) return;

    if (firstIncompleteIndex === -1) {
        playerWrapper.style.display = 'none';
        return;
    }

    playerWrapper.style.display = 'flex';

    const targetCard = cards[firstIncompleteIndex];
    const containerRect = pathContainer.getBoundingClientRect();
    const cardRect = targetCard.getBoundingClientRect();
    const scrollLeft = document.querySelector('.map-scroll-area')?.scrollLeft || 0;

    let leftPosition = cardRect.left - containerRect.left - 40 + scrollLeft;
    if (leftPosition < 10) leftPosition = 10;

    playerWrapper.style.left = leftPosition + 'px';
}

// 显示任务详情
function showTaskDetail(task, monsterIcon, monsterName, isCompleted) {
    currentTask = task;
    document.getElementById('modalIcon').innerHTML = monsterIcon || '❓';
    document.getElementById('modalTitle').innerHTML = `${monsterName} - ${task.name}`;
    document.getElementById('modalDesc').innerHTML = task.description || '暂无详细描述';
    document.getElementById('modalRewards').innerHTML = getRewardDescription(task);

    const actionBtn = document.getElementById('modalActionBtn');
    const timerSection = document.getElementById('modalTimerSection');
    const jumpRopeSection = document.getElementById('jumpRopeSection');
    const isTimer = isTimerTask(task.name);
    const isJump = isJumpRopeTask(task.name);

    if (jumpRopeSection) {
        jumpRopeSection.style.display = 'none';
        const jumpInput = document.getElementById('jumpCountInput');
        if (jumpInput) {
            jumpInput.value = '';
            jumpInput.oninput = (e) => updateJumpProgress(parseInt(e.target.value) || 0);
        }
    }

    if (isCompleted) {
        actionBtn.innerHTML = '✅ 今日已完成';
        actionBtn.disabled = true;
        actionBtn.style.opacity = '0.6';
        timerSection.style.display = 'none';
        if (jumpRopeSection) jumpRopeSection.style.display = 'none';
    } else {
        actionBtn.disabled = false;
        if (isTimer) {
            if (isJump) {
                actionBtn.innerHTML = '✅ 提交成绩';
                actionBtn.style.display = 'flex';
                timerSection.style.display = 'none';
                if (jumpRopeSection) jumpRopeSection.style.display = 'block';
                updateJumpProgress(0);
            } else if (activeTimerTaskId === task.id) {
                actionBtn.style.display = 'none';
                timerSection.style.display = 'block';
                if (jumpRopeSection) jumpRopeSection.style.display = 'none';
            } else {
                actionBtn.innerHTML = '⏰ 开始计时';
                actionBtn.style.display = 'flex';
                timerSection.style.display = 'none';
                if (jumpRopeSection) jumpRopeSection.style.display = 'none';
            }
        } else {
            actionBtn.innerHTML = '⚔️ 开始讨伐';
            actionBtn.style.display = 'flex';
            timerSection.style.display = 'none';
            if (jumpRopeSection) jumpRopeSection.style.display = 'none';
        }
    }

    document.getElementById('taskModal').classList.add('active');
}

function hideModal() {
    document.getElementById('taskModal').classList.remove('active');
    currentTask = null;
}

function showConfirm(message, onYes) {
    const overlay = document.getElementById('confirmOverlay');
    document.getElementById('confirmMessage').innerHTML = message;
    const handleYes = () => {
        overlay.classList.remove('active');
        onYes();
    };
    const handleNo = () => overlay.classList.remove('active');
    document.getElementById('confirmYesBtn').onclick = handleYes;
    document.getElementById('confirmNoBtn').onclick = handleNo;
    overlay.classList.add('active');
}

async function fightMonster(taskId) {
    let resp = await fetch('/fight', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_id: taskId})
    });
    let data = await resp.json();
    if (data.error) {
        document.getElementById('lootDisplay').innerHTML = '⚠️ ' + data.error;
        return false;
    }
    document.getElementById('lootDisplay').innerHTML = `⚔️ 击败 ${data.monster_name}！<br>🎁 获得 ${data.base_points} 积分 ✨ ${data.loot_effect || ''}`;
    return true;
}

async function startTimerTask(taskId, taskName) {
    let resp = await fetch('/start_timer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_id: taskId, task_name: taskName})
    });
    let data = await resp.json();
    if (data.error) {
        document.getElementById('lootDisplay').innerHTML = '⚠️ ' + data.error;
        return false;
    }
    document.getElementById('lootDisplay').innerHTML = '⏰ ' + data.message;
    activeTimerTaskId = taskId;
    return true;
}

async function endTimerTask(taskName) {
    let resp = await fetch('/end_timer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_name: taskName})
    });
    let data = await resp.json();
    if (data.error) {
        document.getElementById('lootDisplay').innerHTML = '⚠️ ' + data.error;
        return false;
    }
    document.getElementById('lootDisplay').innerHTML = data.message;
    activeTimerTaskId = null;
    return true;
}

async function endJumpRopeTask(taskName, jumpCount) {
    let resp = await fetch('/end_timer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_name: taskName, jump_count: jumpCount})
    });
    let data = await resp.json();
    if (data.error) {
        document.getElementById('lootDisplay').innerHTML = '⚠️ ' + data.error;
        return false;
    }
    document.getElementById('lootDisplay').innerHTML = data.message;
    activeTimerTaskId = null;
    return true;
}

function getPointsHint(taskName) {
    if (taskName.includes('起床')) return '1~4';
    if (taskName.includes('跳绳')) return '5~7+';
    if (taskName.includes('运动')) return '3~7';
    if (taskName.includes('阅读') || taskName.includes('复习')) return '3~6+';
    return '2~8';
}

async function openPortal() {
    let resp = await fetch('/portal', {method: 'POST'});
    let data = await resp.json();
    if (data.status === 'ok') alert('✨ 你进入了秘境，获得了彩蛋任务！✨');
    else alert(data.error);
    location.reload();
}

async function openTreasure() {
    let resp = await fetch('/treasure', {method: 'POST'});
    let data = await resp.json();
    if (data.error) alert(data.error);
    else alert(data.loot_info);
    location.reload();
}

function checkFullClear() {
    if (defeatedIds.length === tasksData.length && tasksData.length > 0) {
        document.getElementById('treasureArea').style.display = 'block';
    } else {
        document.getElementById('treasureArea').style.display = 'none';
    }
}

function switchTab(tab) {
    if (tab === 'shop') window.location.href = '/shop';
    if (tab === 'points') window.location.href = '/points';
    if (tab === 'quest') window.location.reload();
}

async function renderMap() {
    const container = document.getElementById('taskNodes');
    container.innerHTML = '';
    const total = tasksData.length;
    document.getElementById('totalTasks').innerText = total;
    const completedCount = defeatedIds.length;
    document.getElementById('progressCount').innerText = completedCount;
    document.getElementById('progressFill').style.width = (completedCount / total) * 100 + '%';

    let monsterMap = {};
    try {
        let resp = await fetch('/monsters_map');
        monsterMap = await resp.json();
    } catch(e) {}

    for (let idx = 0; idx < tasksData.length; idx++) {
        const task = tasksData[idx];
        const isCompleted = defeatedIds.includes(task.id);
        const monsterIcon = monsterMap[task.id] || '❓';
        const node = document.createElement('div');
        node.className = `node-card ${isCompleted ? 'completed' : ''}`;
        node.onclick = () => {
            if (!isCompleted) {
                fetch('/task_detail/' + task.id).then(res => res.json()).then(detail => {
                    showTaskDetail(detail, monsterIcon, detail.monster_name || '怪物', isCompleted);
                }).catch(() => {
                    showTaskDetail({id: task.id, name: task.name, description: task.description || '', points: 3}, monsterIcon, '怪物', isCompleted);
                });
            }
        };
        node.innerHTML = `<div class="node-icon">${monsterIcon}</div><div class="node-name">${task.name}</div><div class="node-points">💰 ${getPointsHint(task.name)}</div><div class="node-status">${isCompleted ? '✅ 已完成' : '⚔️ 可讨伐'}</div>`;
        container.appendChild(node);
        if (idx !== tasksData.length - 1) {
            const line = document.createElement('span');
            line.className = 'connector-line';
            line.innerHTML = ' → ';
            container.appendChild(line);
        }
    }

    if (!portalAvailable && completedCount >= Math.ceil(total * 0.8)) {
        portalAvailable = true;
        document.getElementById('portalArea').innerHTML = `<div class="node-card portal-card" style="display:inline-block; padding:12px 30px;" onclick="openPortal()">🌀 神秘传送门 🌀<br>✨ 点击进入异界 ✨</div>`;
    }

    updatePlayerPosition();
}

function bindModalActions() {
    document.getElementById('modalCloseBtn').onclick = hideModal;
    document.getElementById('modalEndTimerBtn').onclick = async () => {
        if (!currentTask) return;
        showConfirm(`确定结束「${currentTask.name}」吗？`, async () => {
            if (await endTimerTask(currentTask.name)) {
                hideModal();
                await loadGameData();
            } else hideModal();
        });
    };
    document.getElementById('modalActionBtn').onclick = async () => {
        if (!currentTask) return;
        const isTimer = isTimerTask(currentTask.name);
        const isJump = isJumpRopeTask(currentTask.name);
        if (isTimer) {
            if (isJump) {
                let count = parseInt(document.getElementById('jumpCountInput').value);
                if (isNaN(count) || count <= 0) { alert('请输入跳绳个数'); return; }
                if (count < 300) { alert(`跳绳不足300个（当前${count}个），还需继续努力！`); return; }
                showConfirm(`确认提交跳绳成绩 ${count} 个吗？`, async () => {
                    if (await endJumpRopeTask(currentTask.name, count)) {
                        hideModal();
                        await loadGameData();
                    } else hideModal();
                });
            } else if (activeTimerTaskId === currentTask.id) {
                showConfirm(`确定结束「${currentTask.name}」吗？`, async () => {
                    if (await endTimerTask(currentTask.name)) {
                        hideModal();
                        await loadGameData();
                    } else hideModal();
                });
            } else {
                showConfirm(`确定开始「${currentTask.name}」吗？`, async () => {
                    if (await startTimerTask(currentTask.id, currentTask.name)) {
                        hideModal();
                        await loadGameData();
                    } else hideModal();
                });
            }
        } else {
            showConfirm(`确定开始讨伐「${currentTask.name}」吗？`, async () => {
                if (await fightMonster(currentTask.id)) {
                    hideModal();
                    await loadGameData();
                } else hideModal();
            });
        }
    };
}

async function loadGameData() {
    let status = await (await fetch('/status')).json();
    document.getElementById('pointsDisplay').innerText = status.points;
    document.getElementById('streakDisplay').innerText = status.streak;
    let tasksJson = await (await fetch('/tasks_list')).json();
    tasksData = tasksJson.tasks;
    defeatedIds = tasksJson.completed_ids || [];
    let timerRes = await fetch('/active_timer_status');
    if (timerRes.ok) {
        let timerData = await timerRes.json();
        activeTimerTaskId = timerData.active ? timerData.task_id : null;
    }
    await renderMap();
    checkFullClear();
}

// 监听滚动和窗口变化
window.addEventListener('resize', () => setTimeout(updatePlayerPosition, 100));
window.addEventListener('scroll', updatePlayerPosition);
document.querySelector('.map-scroll-area')?.addEventListener('scroll', updatePlayerPosition);

bindModalActions();
loadGameData();