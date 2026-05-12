// ========== 全局变量 ==========
let tasksData = [];
let defeatedIds = [];
let portalAvailable = false;
let currentTask = null;
let activeTimerTaskId = null;
let jumpRopeFirstFlag = true;

// 计时器相关变量
let timerInterval = null;
let timerSeconds = 0;
let timerPaused = false;
let timerStartTime = null;

// 任务类型判断
function isTimerTask(taskName) {
    return taskName.includes('复习') || taskName.includes('阅读') || taskName.includes('跳绳');
}

function isJumpRopeTask(taskName) {
    return taskName.includes('跳绳');
}

function isReciteTask(taskName) {
    return taskName.includes('背诵');
}

// 获取任务所需的最少分钟数
function getTaskMinMinutes(taskName) {
    if (taskName.includes('复习') || taskName.includes('阅读')) {
        return 15;
    }
    return 0;
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
            <div class="reward-item"><span class="reward-label">🏃‍♂️ 首次跳绳</span><span class="reward-value">300个以上：5-8分 + 超额</span></div>
            <div class="reward-item"><span class="reward-label">📈 后续跳绳</span><span class="reward-value">每100个得2分</span></div>
            <div class="reward-item"><span class="reward-label">📅 每日上限</span><span class="reward-value">1000个</span></div>
            <div class="reward-item"><span class="reward-label">✨ 魔法掉落</span><span class="reward-value">仅首次有效</span></div>
            <div class="reward-item"><span class="reward-label">💥 暴击</span><span class="reward-value">仅首次有效</span></div>
        `;
    }

    if (taskName.includes('背诵')) {
        return `
            <div class="reward-item"><span class="reward-label">📚 每日背诵</span><span class="reward-value">5-8 积分</span></div>
            <div class="reward-item"><span class="reward-label">✨ 魔法掉落</span><span class="reward-value">随机 +1~5 积分</span></div>
            <div class="reward-item"><span class="reward-label">💥 暴击</span><span class="reward-value">20% 概率积分翻倍！</span></div>
        `;
    }

    if (taskName.includes('复习') || taskName.includes('阅读')) {
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

// 格式化时间（秒 -> MM:SS）
function formatTime(seconds) {
    let mins = Math.floor(seconds / 60);
    let secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// 更新计时器显示
function updateTimerDisplay() {
    const display = document.getElementById('timerDisplay');
    const hint = document.getElementById('timerHint');
    if (display) {
        display.innerHTML = formatTime(timerSeconds);
    }
    if (hint && currentTask && isTimerTask(currentTask.name)) {
        let minMinutes = getTaskMinMinutes(currentTask.name);
        let currentMinutes = timerSeconds / 60;
        if (currentMinutes >= minMinutes) {
            hint.innerHTML = `✅ 已达标（${formatTime(timerSeconds)}），可以结束计时了！`;
            hint.style.color = '#44ff44';
        } else {
            hint.innerHTML = `⏰ 最少需要${minMinutes}分钟，还需${formatTime(minMinutes * 60 - timerSeconds)}`;
            hint.style.color = '#ffaa44';
        }
    }
}

// 开始计时器
function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerPaused = false;
    timerInterval = setInterval(() => {
        if (!timerPaused) {
            timerSeconds++;
            updateTimerDisplay();
        }
    }, 1000);
}

// 暂停/继续计时器
function toggleTimerPause() {
    if (timerInterval) {
        timerPaused = !timerPaused;
        const pauseBtn = document.getElementById('modalPauseTimerBtn');
        if (pauseBtn) {
            pauseBtn.innerHTML = timerPaused ? '▶ 继续' : '⏸ 暂停';
        }
    }
}

// 停止计时器
function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    timerSeconds = 0;
    timerPaused = false;
}

// 重置计时器
function resetTimer() {
    stopTimer();
    timerSeconds = 0;
    updateTimerDisplay();
    const pauseBtn = document.getElementById('modalPauseTimerBtn');
    if (pauseBtn) {
        pauseBtn.innerHTML = '⏸ 暂停';
    }
}

// 更新跳绳进度
function updateJumpProgress(count, isFirst) {
    const progressElem = document.getElementById('jumpProgress');
    if (progressElem) {
        let needed = isFirst ? 300 : 100;
        let displayCount = Math.min(count, 1000);
        let neededCount = Math.max(0, needed - displayCount);
        progressElem.innerHTML = `📊 进度：${displayCount} / 1000 个 | ${isFirst ? '首次需300个' : '后续每100个得2分'}`;
        if (displayCount >= needed) {
            progressElem.style.color = '#44ff44';
            progressElem.innerHTML += ` ✅ 已达最低${needed}个`;
        } else {
            progressElem.style.color = '#ffaa44';
            progressElem.innerHTML += ` （还差${neededCount}个）`;
        }
    }
}

// 显示跳绳结果
function showJumpResult(message, isSuccess) {
    const resultDiv = document.getElementById('lootDisplay');
    if (resultDiv) {
        resultDiv.innerHTML = message;
        resultDiv.style.color = isSuccess ? '#44ff44' : '#ffaa44';
        setTimeout(() => {
            resultDiv.style.color = '';
        }, 3000);
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

    const modalIcon = document.getElementById('modalIcon');
    const modalTitle = document.getElementById('modalTitle');
    const modalDesc = document.getElementById('modalDesc');
    const modalRewards = document.getElementById('modalRewards');
    const actionBtn = document.getElementById('modalActionBtn');
    const timerSection = document.getElementById('modalTimerSection');
    const jumpRopeSection = document.getElementById('jumpRopeSection');

    if (modalIcon) modalIcon.innerHTML = monsterIcon || '❓';
    if (modalTitle) modalTitle.innerHTML = `${monsterName} - ${task.name}`;
    if (modalDesc) modalDesc.innerHTML = task.description || '暂无详细描述';
    if (modalRewards) modalRewards.innerHTML = getRewardDescription(task);

    const isTimer = isTimerTask(task.name);
    const isJump = isJumpRopeTask(task.name);
    const isRecite = isReciteTask(task.name);

    // 重置计时器显示
    if (timerSection) {
        resetTimer();
    }

    if (jumpRopeSection) {
        jumpRopeSection.style.display = 'none';
        const jumpInput = document.getElementById('jumpCountInput');
        if (jumpInput) {
            jumpInput.value = '';
            jumpInput.oninput = (e) => updateJumpProgress(parseInt(e.target.value) || 0, jumpRopeFirstFlag);
        }
    }

    if (isCompleted) {
        if (actionBtn) {
            actionBtn.innerHTML = '✅ 今日已完成';
            actionBtn.disabled = true;
            actionBtn.style.opacity = '0.6';
        }
        if (timerSection) timerSection.style.display = 'none';
        if (jumpRopeSection) jumpRopeSection.style.display = 'none';
    } else {
        if (actionBtn) actionBtn.disabled = false;
        if (isTimer) {
            if (isJump) {
                if (actionBtn) {
                    actionBtn.innerHTML = '✅ 提交成绩';
                    actionBtn.style.display = 'flex';
                }
                if (timerSection) timerSection.style.display = 'none';
                if (jumpRopeSection) {
                    jumpRopeSection.style.display = 'block';
                    updateJumpProgress(0, jumpRopeFirstFlag);
                }
            } else if (activeTimerTaskId === task.id) {
                if (actionBtn) actionBtn.style.display = 'none';
                if (timerSection) {
                    timerSection.style.display = 'block';
                    bindTimerButtons();
                    startTimer();
                }
                if (jumpRopeSection) jumpRopeSection.style.display = 'none';
            } else {
                if (actionBtn) {
                    actionBtn.innerHTML = '⏰ 开始计时';
                    actionBtn.style.display = 'flex';
                }
                if (timerSection) timerSection.style.display = 'none';
                if (jumpRopeSection) jumpRopeSection.style.display = 'none';
            }
        } else {
            if (actionBtn) {
                actionBtn.innerHTML = isRecite ? '📚 开始背诵' : '⚔️ 开始讨伐';
                actionBtn.style.display = 'flex';
            }
            if (timerSection) timerSection.style.display = 'none';
            if (jumpRopeSection) jumpRopeSection.style.display = 'none';
        }
    }

    const modal = document.getElementById('taskModal');
    if (modal) modal.classList.add('active');
}

// 绑定计时器按钮
function bindTimerButtons() {
    const pauseBtn = document.getElementById('modalPauseTimerBtn');
    const endBtn = document.getElementById('modalEndTimerBtn');

    if (pauseBtn) {
        pauseBtn.onclick = () => toggleTimerPause();
    }

    if (endBtn) {
        endBtn.onclick = async () => {
            if (!currentTask) return;
            let minMinutes = getTaskMinMinutes(currentTask.name);
            let currentMinutes = timerSeconds / 60;
            if (currentMinutes < minMinutes) {
                alert(`时长不足${minMinutes}分钟（当前${Math.floor(currentMinutes)}分钟），请继续学习！`);
                return;
            }
            showConfirm(`确定结束「${currentTask.name}」吗？`, async () => {
                if (await endTimerTask(currentTask.name)) {
                    hideModal();
                    await loadGameData();
                } else {
                    hideModal();
                }
            });
        };
    }
}

function hideModal() {
    const modal = document.getElementById('taskModal');
    if (modal) modal.classList.remove('active');
    currentTask = null;
}

function showConfirm(message, onYes) {
    const overlay = document.getElementById('confirmOverlay');
    const confirmMessage = document.getElementById('confirmMessage');
    if (confirmMessage) confirmMessage.innerHTML = message;
    const handleYes = () => {
        if (overlay) overlay.classList.remove('active');
        onYes();
    };
    const handleNo = () => {
        if (overlay) overlay.classList.remove('active');
    };
    const yesBtn = document.getElementById('confirmYesBtn');
    const noBtn = document.getElementById('confirmNoBtn');
    if (yesBtn) yesBtn.onclick = handleYes;
    if (noBtn) noBtn.onclick = handleNo;
    if (overlay) overlay.classList.add('active');
}

async function fightMonster(taskId) {
    let resp = await fetch('/fight', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_id: taskId})
    });
    let data = await resp.json();
    const lootDisplay = document.getElementById('lootDisplay');
    if (data.error) {
        if (lootDisplay) lootDisplay.innerHTML = '⚠️ ' + data.error;
        return false;
    }
    if (lootDisplay) lootDisplay.innerHTML = `⚔️ 击败 ${data.monster_name}！<br>🎁 获得 ${data.base_points} 积分 ✨ ${data.loot_effect || ''}`;
    return true;
}

async function startTimerTask(taskId, taskName) {
    let resp = await fetch('/start_timer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_id: taskId, task_name: taskName})
    });
    let data = await resp.json();
    const lootDisplay = document.getElementById('lootDisplay');
    if (data.error) {
        if (lootDisplay) lootDisplay.innerHTML = '⚠️ ' + data.error;
        return false;
    }
    if (lootDisplay) lootDisplay.innerHTML = '⏰ ' + data.message;
    activeTimerTaskId = taskId;
    timerSeconds = 0;
    updateTimerDisplay();
    startTimer();
    return true;
}

async function endTimerTask(taskName) {
    let resp = await fetch('/end_timer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_name: taskName})
    });
    let data = await resp.json();
    const lootDisplay = document.getElementById('lootDisplay');
    if (data.error) {
        if (lootDisplay) lootDisplay.innerHTML = '⚠️ ' + data.error;
        return false;
    }
    if (lootDisplay) lootDisplay.innerHTML = data.message;
    activeTimerTaskId = null;
    stopTimer();
    return true;
}

async function endJumpRopeTask(taskName, jumpCount) {
    let resp = await fetch('/end_timer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            task_name: taskName,
            jump_count: jumpCount
        })
    });
    let data = await resp.json();
    if (data.error) {
        showJumpResult('⚠️ ' + data.error, false);
        return false;
    }
    showJumpResult(data.message, true);
    activeTimerTaskId = null;
    return true;
}

function getPointsHint(taskName) {
    if (taskName.includes('起床')) return '1~4';
    if (taskName.includes('跳绳')) return '5~8+';
    if (taskName.includes('背诵')) return '5~8';
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
    const treasureArea = document.getElementById('treasureArea');
    if (defeatedIds.length === tasksData.length && tasksData.length > 0) {
        if (treasureArea) treasureArea.style.display = 'block';
    } else {
        if (treasureArea) treasureArea.style.display = 'none';
    }
}

function switchTab(tab) {
    if (tab === 'shop') window.location.href = '/shop';
    if (tab === 'points') window.location.href = '/points';
    if (tab === 'quest') window.location.reload();
}

async function renderMap() {
    const container = document.getElementById('taskNodes');
    if (!container) return;
    container.innerHTML = '';
    const total = tasksData.length;
    const totalTasksSpan = document.getElementById('totalTasks');
    const progressCountSpan = document.getElementById('progressCount');
    const progressFill = document.getElementById('progressFill');
    if (totalTasksSpan) totalTasksSpan.innerText = total;
    const completedCount = defeatedIds.length;
    if (progressCountSpan) progressCountSpan.innerText = completedCount;
    if (progressFill) progressFill.style.width = (completedCount / total) * 100 + '%';

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

    const portalArea = document.getElementById('portalArea');
    if (!portalAvailable && completedCount >= Math.ceil(total * 0.8) && portalArea) {
        portalAvailable = true;
        portalArea.innerHTML = `<div class="node-card portal-card" style="display:inline-block; padding:12px 30px;" onclick="openPortal()">🌀 神秘传送门 🌀<br>✨ 点击进入异界 ✨</div>`;
    }

    updatePlayerPosition();
}

function bindModalActions() {
    const closeBtn = document.getElementById('modalCloseBtn');
    if (closeBtn) {
        closeBtn.onclick = hideModal;
    }

    const actionBtn = document.getElementById('modalActionBtn');
    if (actionBtn) {
        actionBtn.onclick = async () => {
            if (!currentTask) return;
            const isTimer = isTimerTask(currentTask.name);
            const isJump = isJumpRopeTask(currentTask.name);
            const isRecite = isReciteTask(currentTask.name);

            if (isTimer) {
                if (isJump) {
                    const jumpInput = document.getElementById('jumpCountInput');
                    let count = jumpInput ? parseInt(jumpInput.value) : 0;
                    if (isNaN(count) || count <= 0) {
                        alert('请输入跳绳个数');
                        return;
                    }
                    let needed = jumpRopeFirstFlag ? 300 : 100;
                    if (count < needed) {
                        alert(`跳绳不足${needed}个（当前${count}个），还差${needed - count}个，要继续努力哦！`);
                        return;
                    }
                    let confirmMsg = jumpRopeFirstFlag
                        ? `确认提交首次跳绳成绩 ${count} 个吗？\n基础分5-8分 + 超额奖励 + 暴击 + 掉落`
                        : `确认提交跳绳成绩 ${count} 个吗？\n可获得 ${Math.floor(count/100)*2} 分（每100个得2分）`;
                    showConfirm(confirmMsg, async () => {
                        if (await endJumpRopeTask(currentTask.name, count)) {
                            if (jumpRopeFirstFlag) {
                                jumpRopeFirstFlag = false;
                            }
                            hideModal();
                            await loadGameData();
                        } else {
                            hideModal();
                        }
                    });
                } else if (activeTimerTaskId === currentTask.id) {
                    const timerSection = document.getElementById('modalTimerSection');
                    if (timerSection) timerSection.style.display = 'block';
                    if (actionBtn) actionBtn.style.display = 'none';
                    bindTimerButtons();
                    startTimer();
                } else {
                    showConfirm(`确定开始「${currentTask.name}」吗？`, async () => {
                        if (await startTimerTask(currentTask.id, currentTask.name)) {
                            hideModal();
                            await loadGameData();
                        } else {
                            hideModal();
                        }
                    });
                }
            } else {
                showConfirm(`确定完成「${currentTask.name}」吗？`, async () => {
                    if (await fightMonster(currentTask.id)) {
                        hideModal();
                        await loadGameData();
                    } else {
                        hideModal();
                    }
                });
            }
        };
    }
}

async function loadGameData() {
    let status = await (await fetch('/status')).json();
    const pointsDisplay = document.getElementById('pointsDisplay');
    const streakDisplay = document.getElementById('streakDisplay');
    if (pointsDisplay) pointsDisplay.innerText = status.points;
    if (streakDisplay) streakDisplay.innerText = status.streak;
    let tasksJson = await (await fetch('/tasks_list')).json();
    tasksData = tasksJson.tasks;
    defeatedIds = tasksJson.completed_ids || [];
    let timerRes = await fetch('/active_timer_status');
    if (timerRes.ok) {
        let timerData = await timerRes.json();
        activeTimerTaskId = timerData.active ? timerData.task_id : null;
    }
    jumpRopeFirstFlag = true;
    await renderMap();
    checkFullClear();
}

// 监听滚动和窗口变化
window.addEventListener('resize', () => setTimeout(updatePlayerPosition, 100));
window.addEventListener('scroll', updatePlayerPosition);
const scrollArea = document.querySelector('.map-scroll-area');
if (scrollArea) scrollArea.addEventListener('scroll', updatePlayerPosition);

bindModalActions();
loadGameData();