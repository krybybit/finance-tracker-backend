const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const API_URL ='https://finance-tracker-weld-theta.vercel.app';
const initData = tg.initData;

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
            div.innerHTML = `<span>${t.comment || 'Без комментария'}</span><span>${t.amount} ₽</span>`;
            list.appendChild(div);
        });
        document.getElementById('balance').textContent = `Баланс: ${balance} ₽`;
    } catch (error) {
        console.error('Ошибка загрузки:', error);
    }
}

loadTransactions();