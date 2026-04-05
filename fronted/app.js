const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const API_URL = 'https://finance-tracker-backend-k2nw.onrender.com';
const initData = tg.initData;

// Переключение вкладок
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(tabName + 'Tab').classList.add('active');
    event.target.classList.add('active');
    
    if (tabName === 'statistics') {
        loadStatistics();
    }
}

// Добавление транзакции
document.getElementById('transactionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = parseFloat(document.getElementById('amount').value);
    const type = document.getElementById('type').value;
    const category_id = parseInt(document.getElementById('category').value);
    const comment = document.getElementById('comment').value;

    try {
        const response = await fetch(`${API_URL}/api/transactions/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'telegram-init-data': initData
            },
            body: JSON.stringify({ amount, type, category_id, comment })
        });
        
        if (response.ok) {
            tg.showAlert('Транзакция добавлена!');
            document.getElementById('transactionForm').reset();
            loadTransactions();
        } else {
            tg.showAlert('Ошибка при добавлении транзакции');
        }
    } catch (error) {
        tg.showAlert('Ошибка соединения');
    }
});

// Загрузка транзакций
async function loadTransactions() {
    try {
        const response = await fetch(`${API_URL}/api/transactions/`, {
            headers: { 'telegram-init-data': initData }
        });
        const transactions = await response.json();
        const list = document.getElementById('transactionsList');
        list.innerHTML = '';
        let balance = 0;
        
        transactions.forEach(t => {
            balance += t.type === 'income' ? t.amount : -t.amount;
            const div = document.createElement('div');
            div.className = `transaction ${t.type}`;
            div.innerHTML = `
                <div>
                    <span class="comment">${t.comment || 'Без комментария'}</span>
                    <span class="amount">${t.amount} ₽</span>
                </div>
                <button class="delete-btn" onclick="deleteTransaction(${t.id})">🗑️</button>
            `;
            list.appendChild(div);
        });
        
        document.getElementById('balance').textContent = `Баланс: ${balance} ₽`;
    } catch (error) {
        console.error('Ошибка загрузки:', error);
    }
}

// Удаление транзакции
async function deleteTransaction(id) {
    if (!confirm('Удалить эту транзакцию?')) return;
    
    try {
        const response = await fetch(`${API_URL}/api/transactions/${id}`, {
            method: 'DELETE',
            headers: { 'telegram-init-data': initData }
        });
        
        if (response.ok) {
            tg.showAlert('Транзакция удалена');
            loadTransactions();
        } else {
            tg.showAlert('Ошибка при удалении');
        }
    } catch (error) {
        tg.showAlert('Ошибка соединения');
    }
}

// Загрузка статистики
async function loadStatistics() {
    try {
        const response = await fetch(`${API_URL}/api/transactions/statistics`, {
            headers: { 'telegram-init-data': initData }
        });
        const stats = await response.json();
        
        document.getElementById('totalIncome').textContent = `${stats.total_income.toLocaleString()} ₽`;
        document.getElementById('totalExpense').textContent = `${stats.total_expense.toLocaleString()} ₽`;
        
        const categoryStats = document.getElementById('categoryStats');
        categoryStats.innerHTML = '';
        
        stats.by_category.forEach(cat => {
            const div = document.createElement('div');
            div.className = 'category-stat';
            div.innerHTML = `
                <div class="category-header">
                    <span>${cat.icon} ${cat.category}</span>
                    <span>${cat.total.toLocaleString()} ₽</span>
                </div>
                <div class="progress-bar">
                    <div class="progress" style="width: ${(cat.total / stats.total_expense * 100)}%"></div>
                </div>
                <small>${cat.count} транзакций</small>
            `;
            categoryStats.appendChild(div);
        });
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

// Загрузка при старте
loadTransactions();