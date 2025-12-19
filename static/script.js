// Cart Logic using LocalStorage

let cart = JSON.parse(localStorage.getItem('jai_bhole_cart')) || [];

document.addEventListener('DOMContentLoaded', () => {
    updateCartUI();

    // Event Delegation for Add to Cart
    document.body.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-add-cart');
        if (btn) {
            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const price = parseFloat(btn.getAttribute('data-price'));
            const image = btn.getAttribute('data-image');
            addToCart(id, name, price, image);
        }
    });
});

function addToCart(id, name, price, image) {
    const existingItem = cart.find(item => item.id === id);
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({ id, name, price, image, quantity: 1 });
    }
    saveCart();
    // Simple feedback
    alert(`${name} added to cart!`);
}

function removeFromCart(id) {
    cart = cart.filter(item => item.id !== id);
    saveCart();
}

function updateQuantity(id, change) {
    const item = cart.find(item => item.id === id);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            removeFromCart(id);
        } else {
            saveCart();
        }
    }
}

function saveCart() {
    localStorage.setItem('jai_bhole_cart', JSON.stringify(cart));
    updateCartUI();
}

function updateCartUI() {
    // Update Badge
    const badge = document.getElementById('cart-count');
    if (badge) {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        badge.textContent = totalItems;
    }

    // Update Cart Page if active
    const container = document.getElementById('cart-items-container');
    const summaryCount = document.getElementById('summary-count');
    const summaryTotal = document.getElementById('summary-total');

    if (container && summaryCount && summaryTotal) {
        if (cart.length === 0) {
            container.innerHTML = '<p class="empty-msg">Your cart is empty.</p>';
            summaryCount.textContent = '0';
            summaryTotal.textContent = '₹0';
            return;
        }

        let html = '';
        let total = 0;
        let count = 0;

        cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            total += itemTotal;
            count += item.quantity;

            html += `
                <div class="cart-item">
                    <img src="${item.image}" alt="${item.name}">
                    <div class="item-details">
                        <h4>${item.name}</h4>
                        <p>₹${item.price} x ${item.quantity}</p>
                    </div>
                    <div class="item-actions">
                        <button class="qty-btn" onclick="updateQuantity('${item.id}', -1)">-</button>
                        <span>${item.quantity}</span>
                        <button class="qty-btn" onclick="updateQuantity('${item.id}', 1)">+</button>
                        <button class="remove-btn" onclick="removeFromCart('${item.id}')"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
        summaryCount.textContent = count;
        summaryTotal.textContent = '₹' + total.toFixed(2);
    }
}

function placeOrder() {
    if (cart.length === 0) return;

    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

    fetch('/place_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            items: cart,
            total: total
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Order Placed Successfully!');
                cart = [];
                saveCart();
                window.location.href = '/';
            } else {
                alert('Error: ' + data.message);
                // Redirect to login if likely session issue
                if (data.message.includes('login')) {
                    window.location.href = '/login';
                }
            }
        })
        .catch(error => console.error('Error:', error));
}
