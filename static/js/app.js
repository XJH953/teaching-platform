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
