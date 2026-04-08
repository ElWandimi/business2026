// Main JavaScript file

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Add to cart with AJAX
function addToCart(productId, quantity) {
    quantity = quantity || 1;
    
    fetch(`/cart/add/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}`
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            // Show success message
            showNotification('Product added to cart!', 'success');
            // Update cart count
            updateCartCount();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding product to cart.', 'danger');
    });
}

// Update cart quantity
function updateCartQuantity(itemId, quantity) {
    fetch(`/cart/update/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}`
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating cart.', 'danger');
    });
}

// Remove from cart
function removeFromCart(itemId) {
    if (confirm('Are you sure you want to remove this item?')) {
        fetch(`/cart/remove/${itemId}`)
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error removing item from cart.', 'danger');
        });
    }
}

// Update cart count in navbar
function updateCartCount() {
    fetch('/cart/count')
        .then(response => response.json())
        .then(data => {
            const cartBadge = document.querySelector('.navbar .badge');
            if (cartBadge) {
                cartBadge.textContent = data.count;
            }
        })
        .catch(error => console.error('Error:', error));
}

// Show notification
function showNotification(message, type) {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto dismiss after 3 seconds
    setTimeout(() => {
        alert.remove();
    }, 3000);
}

// Price range slider
if (document.getElementById('price-range')) {
    const priceRange = document.getElementById('price-range');
    const minPrice = document.getElementById('min-price');
    const maxPrice = document.getElementById('max-price');
    
    priceRange.addEventListener('input', function() {
        const value = this.value.split(',');
        minPrice.value = value[0];
        maxPrice.value = value[1];
    });
}

// Product image gallery
if (document.querySelector('.product-gallery')) {
    const mainImage = document.querySelector('.main-product-image');
    const thumbnails = document.querySelectorAll('.thumbnail-image');
    
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            mainImage.src = this.src;
            thumbnails.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// Quantity input
function incrementQuantity(input) {
    const currentValue = parseInt(input.value);
    const max = parseInt(input.getAttribute('max') || '999');
    if (currentValue < max) {
        input.value = currentValue + 1;
    }
}

function decrementQuantity(input) {
    const currentValue = parseInt(input.value);
    const min = parseInt(input.getAttribute('min') || '1');
    if (currentValue > min) {
        input.value = currentValue - 1;
    }
}

// Search form validation
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('form[action*="products"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="search"]');
            if (searchInput.value.trim() === '') {
                e.preventDefault();
                window.location.href = '/products';
            }
        });
    }
});

// Lazy loading images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img.lazy').forEach(img => {
        imageObserver.observe(img);
    });
}