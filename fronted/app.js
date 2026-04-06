const tg = window.Telegram.WebApp;
let Chart = null; // Для диаграмм
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
    } else if (tabName === 'charts') {
        loadExpenseChart();
        loadMonthlyChart();
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
        renderTransactions(transactions);
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

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    if (event.target == modal) {
        closeEditModal();
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

// ✅ ЗАГРУЗКА CHART.JS
async function loadChartJS() {
    if (!Chart) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        document.head.appendChild(script);
        await new Promise(resolve => script.onload = resolve);
        Chart = window.Chart;
    }
}
// ✅ ПОИСК ТРАНЗАКЦИЙ
async function searchTransactions() {
    const search = document.getElementById('searchInput').value;
    try {
        const response = await fetch(`${API_URL}/api/transactions/filter?search=${search}`, {
            headers: { 'telegram-init-data': initData }
        });
        const transactions = await response.json();
        renderTransactions(transactions);
    } catch (error) {
        console.error('Ошибка поиска:', error);
    }
}
// ✅ ПРИМЕНЕНИЕ ФИЛЬТРОВ
async function applyFilters() {
    const type = document.getElementById('filterType').value;
    const category_id = document.getElementById('filterCategory').value;
    const date_from = document.getElementById('filterDateFrom').value;
    const date_to = document.getElementById('filterDateTo').value;
    
    let url = `${API_URL}/api/transactions/filter?`;
    if (type) url += `type=${type}&`;
    if (category_id) url += `category_id=${category_id}&`;
    if (date_from) url += `date_from=${date_from}&`;
    if (date_to) url += `date_to=${date_to}&`;
    
    try {
        const response = await fetch(url, {
            headers: { 'telegram-init-data': initData }
        });
        const transactions = await response.json();
        renderTransactions(transactions);
    } catch (error) {
        console.error('Ошибка фильтрации:', error);
    }
}

// ✅ СБРОС ФИЛЬТРОВ
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filterType').value = '';
    document.getElementById('filterCategory').value = '';
    document.getElementById('filterDateFrom').value = '';
    document.getElementById('filterDateTo').value = '';
    loadTransactions();
}

// ✅ ОТРИСОВКА ТРАНЗАКЦИЙ (обновлённая)
function renderTransactions(transactions) {
    const list = document.getElementById('transactionsList');
    list.innerHTML = '';
    let balance = 0;
    
    transactions.forEach(t => {
        balance += t.type === 'income' ? t.amount : -t.amount;
        const div = document.createElement('div');
        div.className = `transaction ${t.type}`;
        div.innerHTML = `
            <div onclick="openEditModal(${t.id}, ${t.amount}, '${t.type}', ${t.category_id}, '${t.comment || ''}')">
                <span class="comment">${t.comment || 'Без комментария'}</span>
                <span class="amount">${t.amount} ₽</span>
            </div>
            <div>
                <button class="edit-btn" onclick="openEditModal(${t.id}, ${t.amount}, '${t.type}', ${t.category_id}, '${t.comment || ''}')">✏️</button>
                <button class="delete-btn" onclick="deleteTransaction(${t.id})">🗑️</button>
            </div>
        `;
        list.appendChild(div);
    });
    
    document.getElementById('balance').textContent = `Баланс: ${balance} ₽`;
}

// ✅ ОТКРЫТЬ МОДАЛЬНОЕ ОКНО РЕДАКТИРОВАНИЯ
function openEditModal(id, amount, type, category_id, comment) {
    document.getElementById('editTransactionId').value = id;
    document.getElementById('editAmount').value = amount;
    document.getElementById('editType').value = type;
    document.getElementById('editCategory').value = category_id;
    document.getElementById('editComment').value = comment;
    document.getElementById('editModal').style.display = 'block';
}

// ✅ ЗАКРЫТЬ МОДАЛЬНОЕ ОКНО
function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

// ✅ СОХРАНИТЬ ИЗМЕНЕНИЯ
document.getElementById('editTransactionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('editTransactionId').value;
    const amount = parseFloat(document.getElementById('editAmount').value);
    const type = document.getElementById('editType').value;
    const category_id = parseInt(document.getElementById('editCategory').value);
    const comment = document.getElementById('editComment').value;
    
    try {
        const response = await fetch(`${API_URL}/api/transactions/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'telegram-init-data': initData
            },
            body: JSON.stringify({ amount, type, category_id, comment })
        });
        
        if (response.ok) {
            tg.showAlert('Транзакция обновлена!');
            closeEditModal();
            loadTransactions();
        } else {
            tg.showAlert('Ошибка при обновлении');
        }
    } catch (error) {
        tg.showAlert('Ошибка соединения');
    }
});

// ✅ ЭКСПОРТ В CSV
async function exportToCSV() {
    try {
        const response = await fetch(`${API_URL}/api/transactions/`, {
            headers: { 'telegram-init-data': initData }
        });
        const transactions = await response.json();
        
        let csv = 'ID,Сумма,Тип,Категория,Комментарий,Дата\n';
        transactions.forEach(t => {
            csv += `${t.id},${t.amount},${t.type},${t.category_id},"${t.comment || ''}",${t.created_at}\n`;
        });
        
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        
        tg.showAlert('Экспорт выполнен!');
    } catch (error) {
        tg.showAlert('Ошибка экспорта');
    }
}

// ✅ ДИАГРАММА РАСХОДОВ
async function loadExpenseChart() {
    await loadChartJS();
    
    const response = await fetch(`${API_URL}/api/transactions/statistics`, {
        headers: { 'telegram-init-data': initData }
    });
    const stats = await response.json();
    
    const ctx = document.getElementById('expenseChart').getContext('2d');
    
    if (window.expenseChartInstance) {
        window.expenseChartInstance.destroy();
    }
    
    window.expenseChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: stats.by_category.map(c => `${c.icon} ${c.category}`),
            datasets: [{
                data: stats.by_category.map(c => c.total),
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// ✅ МЕСЯЧНАЯ ДИАГРАММА
async function loadMonthlyChart() {
    await loadChartJS();
    
    const response = await fetch(`${API_URL}/api/transactions/statistics/monthly`, {
        headers: { 'telegram-init-data': initData }
    });
    const data = await response.json();
    
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    
    if (window.monthlyChartInstance) {
        window.monthlyChartInstance.destroy();
    }
    
    window.monthlyChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.months.map(m => m.month_name.substring(0, 3)),
            datasets: [
                {
                    label: 'Доходы',
                    data: data.months.map(m => m.income),
                    backgroundColor: '#48bb78'
                },
                {
                    label: 'Расходы',
                    data: data.months.map(m => m.expense),
                    backgroundColor: '#f56565'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Загрузка при старте
loadTransactions();