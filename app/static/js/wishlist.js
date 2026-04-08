// Wishlist functionality
function toggleWishlist(productId) {
    fetch(`/wishlist/toggle/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button appearance
            updateWishlistButton(productId, data.action);
            
            // Show notification
            showNotification(data.message, 'success');
            
            // Update wishlist count in navbar if exists
            updateWishlistCount(data.wishlist_count);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating wishlist', 'error');
    });
}

function updateWishlistButton(productId, action) {
    const buttons = document.querySelectorAll(`[data-product-id="${productId}"]`);
    buttons.forEach(btn => {
        const icon = btn.querySelector('i');
        if (action === 'added') {
            icon.className = 'fas fa-heart';
            btn.classList.add('active');
        } else {
            icon.className = 'far fa-heart';
            btn.classList.remove('active');
        }
    });
}

function updateWishlistCount(count) {
    const badge = document.getElementById('wishlist-count');
    if (badge) {
        badge.textContent = count;
        if (count > 0) {
            badge.classList.remove('d-none');
        } else {
            badge.classList.add('d-none');
        }
    }
}

// Check wishlist status on page load
document.addEventListener('DOMContentLoaded', function() {
    const productId = document.getElementById('wishlistBtn')?.getAttribute('data-product-id');
    if (productId) {
        checkWishlistStatus(productId);
    }
});

function checkWishlistStatus(productId) {
    fetch(`/wishlist/check/${productId}`)
        .then(response => response.json())
        .then(data => {
            if (data.in_wishlist) {
                updateWishlistButton(productId, 'added');
            }
        })
        .catch(error => console.error('Error checking wishlist:', error));
}