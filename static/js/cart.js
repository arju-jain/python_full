/**
 * AURA LUXE — Shopping Bag & Wishlist AJAX Engine
 */

document.addEventListener('DOMContentLoaded', function () {
  const csrfToken = getCookie('csrftoken');

  // Handle Add-to-Cart Buttons with AJAX
  document.querySelectorAll('.btn-add-to-cart-ajax').forEach(button => {
    button.addEventListener('click', function (e) {
      e.preventDefault();
      const productId = this.dataset.productId;
      const qtyInput = document.getElementById(`qty-${productId}`) || document.getElementById('product-detail-qty');
      const quantity = qtyInput ? parseInt(qtyInput.value, 10) : 1;
      const originalText = this.innerHTML;

      this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Adding...';
      this.disabled = true;

      fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ quantity: quantity })
      })
      .then(res => res.json())
      .then(data => {
        this.innerHTML = originalText;
        this.disabled = false;
        if (data.success) {
          // Update navbar cart counter badge
          const badges = document.querySelectorAll('.cart-count-badge');
          badges.forEach(b => {
            b.textContent = data.cart_item_count;
            b.style.display = data.cart_item_count > 0 ? 'inline-block' : 'none';
          });
          // Show Toast or notification
          alertToast(data.message, 'success');
        } else {
          alertToast(data.message, 'danger');
        }
      })
      .catch(err => {
        this.innerHTML = originalText;
        this.disabled = false;
        alertToast('Network error while adding to bag.', 'danger');
      });
    });
  });

  // Handle Wishlist Toggle Buttons
  document.querySelectorAll('.btn-wishlist-toggle').forEach(button => {
    button.addEventListener('click', function (e) {
      e.preventDefault();
      const productId = this.dataset.productId;
      const icon = this.querySelector('i');

      fetch(`/wishlist/toggle/${productId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(res => {
        if (res.status === 401 || res.redirected) {
          window.location.href = '/accounts/login/?next=' + window.location.pathname;
          return;
        }
        return res.json();
      })
      .then(data => {
        if (!data) return;
        if (data.success) {
          if (data.added) {
            this.classList.add('active');
            if (icon) {
              icon.classList.remove('bi-heart');
              icon.classList.add('bi-heart-fill');
            }
          } else {
            this.classList.remove('active');
            if (icon) {
              icon.classList.remove('bi-heart-fill');
              icon.classList.add('bi-heart');
            }
          }
          // Update navbar wishlist count
          const wBadges = document.querySelectorAll('.wishlist-count-badge');
          wBadges.forEach(b => {
            b.textContent = data.wishlist_item_count;
            b.style.display = data.wishlist_item_count > 0 ? 'inline-block' : 'none';
          });
          alertToast(data.message, 'info');
        }
      })
      .catch(err => console.error(err));
    });
  });

  // Handle Cart Quantity Increment/Decrement Buttons
  document.querySelectorAll('.cart-qty-btn').forEach(button => {
    button.addEventListener('click', function () {
      const itemId = this.dataset.itemId;
      const input = document.getElementById(`cart-qty-input-${itemId}`);
      if (!input) return;

      let currentVal = parseInt(input.value, 10);
      const isPlus = this.classList.contains('btn-plus');
      const newVal = isPlus ? currentVal + 1 : currentVal - 1;

      if (newVal < 1) return;
      input.value = newVal;
      updateCartItemQty(itemId, newVal);
    });
  });

  function updateCartItemQty(itemId, quantity) {
    fetch(`/cart/update/${itemId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({ quantity: quantity })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        const itemSubtotalElem = document.getElementById(`item-subtotal-${itemId}`);
        if (itemSubtotalElem) itemSubtotalElem.textContent = `₹${data.item_subtotal}`;

        const cartSubtotalElem = document.getElementById('cart-summary-subtotal');
        if (cartSubtotalElem) cartSubtotalElem.textContent = `₹${data.cart_subtotal}`;

        const cartTotalElem = document.getElementById('cart-summary-total');
        if (cartTotalElem) cartTotalElem.textContent = `₹${data.cart_total}`;

        const badges = document.querySelectorAll('.cart-count-badge');
        badges.forEach(b => {
          b.textContent = data.cart_item_count;
        });
      } else {
        alertToast(data.message, 'warning');
      }
    });
  }

  function alertToast(msg, type) {
    const container = document.getElementById('toast-container');
    if (!container) {
      alert(msg);
      return;
    }
    const toast = document.createElement('div');
    toast.className = `alert alert-aura alert-${type} shadow-sm`;
    toast.innerHTML = `<i class="bi bi-info-circle me-2"></i> ${msg}`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }
});
