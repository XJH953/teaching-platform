// HTMX 全局配置
htmx.config.globalViewTransitions = false;

// 页面加载时添加转场动画
document.addEventListener('DOMContentLoaded', () => {
    const main = document.getElementById('main-content');
    if (main && main.dataset.transition) {
        main.classList.add(`transition-${main.dataset.transition}`);
    }
});

// afterSwap 事件 — 为新内容添加进入动画
document.addEventListener('htmx:afterSwap', (evt) => {
    const target = evt.detail.target;
    if (target && target.dataset.transition) {
        target.classList.add(`transition-${target.dataset.transition}`);
    }
});

// 通用的模态框关闭函数
function closeModal(modalId, redirectTo) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        setTimeout(() => {
            modal.remove();
            if (redirectTo) {
                window.location.href = redirectTo;
            }
        }, 300);
    }
}

// 显示密码模态框
function showPasswordModal(name, password, redirectTo) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'password-modal';
    overlay.innerHTML = `
        <div class="modal-box">
            <div class="modal-title">🌟 ${name} 同学，欢迎你～</div>
            <p class="modal-note">
                这是属于你的专属密码，<br>把它记在小本本上哦，不要告诉别人～
            </p>
            <div class="modal-password">${password}</div>
            <p class="modal-note">
                万一不小心忘了也别着急，<br>来找老师，我帮你重新设一个就好。
            </p>
            <button class="btn btn-primary" onclick="closeModal('password-modal', '${redirectTo || ''}')">
                我记住啦 ✅
            </button>
        </div>
    `;
    document.body.appendChild(overlay);
}

// 首次登录流程
async function firstLogin(name) {
    try {
        const resp = await fetch('/first-login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken(),
            },
            body: `name=${encodeURIComponent(name)}`,
        });
        const data = await resp.json();

        if (data.success) {
            showPasswordModal(data.name, data.password, '/welcome/');
        } else {
            alert(data.error || '操作失败，请联系老师');
        }
    } catch (err) {
        alert('网络错误，请稍后重试');
    }
}

// 获取 CSRF token
function getCsrfToken() {
    const cookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

// 重置学生密码（老师操作）
async function resetStudentPassword(name, studentId) {
    if (!confirm(`确定要重置 ${name} 的密码吗？`)) return;

    try {
        const resp = await fetch(`/reset-password/${studentId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken(),
            },
        });
        const data = await resp.json();

        if (data.success) {
            // 复用密码显示弹窗
            showResetPasswordModal(data.name, data.password);
        } else {
            alert(data.error || '操作失败');
        }
    } catch (err) {
        alert('网络错误，请稍后重试');
    }
}

// 删除作业（老师操作）
async function deleteTask(title, taskId) {
    if (!confirm(`确定要删除作业「${title}」吗？\n\n此操作不可撤销，所有学生的提交记录也将一并删除。`)) return;

    try {
        const resp = await fetch(`/assignments/${taskId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken(),
            },
        });
        const data = await resp.json();

        if (data.success) {
            window.location.reload();
        } else {
            alert(data.error || '操作失败');
        }
    } catch (err) {
        alert('网络错误，请稍后重试');
    }
}

// 删除学生（老师操作）
async function deleteStudent(name, studentId, classId) {
    if (!confirm(`确定要删除学生「${name}」吗？\n\n此操作不可撤销，该学生的所有提交记录也将一并删除。`)) return;

    try {
        const resp = await fetch(`/classes/${classId}/student/${studentId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken(),
            },
        });
        const data = await resp.json();

        if (data.success) {
            window.location.reload();
        } else {
            alert(data.error || '操作失败');
        }
    } catch (err) {
        alert('网络错误，请稍后重试');
    }
}

// 显示重置密码弹窗（老师视角）
function showResetPasswordModal(name, password) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'reset-password-modal';
    overlay.innerHTML = `
        <div class="modal-box">
            <div class="modal-title">🔑 ${name} 的新密码</div>
            <p class="modal-note">
                请将以下密码告诉这位同学：<br>
                登录后可以自行修改密码。
            </p>
            <div class="modal-password">${password}</div>
            <button class="btn btn-primary" onclick="closeModal('reset-password-modal')">
                知道了
            </button>
        </div>
    `;
    document.body.appendChild(overlay);
}
