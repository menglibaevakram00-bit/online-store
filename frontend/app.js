const API_BASE = '/api';
const CART_KEY = 'master-nosirov-cart-v1';
const fallbackImage = '/images/laptop-fallback.svg';
const productGrid = document.querySelector('#product-grid');
const emptyState = document.querySelector('#empty-state');
const catalogError = document.querySelector('#catalog-error');
const resultsCount = document.querySelector('#results-count');
const categoryFilter = document.querySelector('#category-filter');
const sortFilter = document.querySelector('#sort-filter');
const searchInput = document.querySelector('#search');
const minPrice = document.querySelector('#min-price');
const maxPrice = document.querySelector('#max-price');
const productDialog = document.querySelector('#product-dialog');
const cartDialog = document.querySelector('#cart-dialog');
const cartItems = document.querySelector('#cart-items');
const cartSummary = document.querySelector('#cart-summary');
const cartEmpty = document.querySelector('#cart-empty');
const checkoutStatus = document.querySelector('#checkout-status');

let products = [];
let debounceTimer;
let toastTimer;
let cart = readCart();

function readCart() {
  try {
    const stored = JSON.parse(localStorage.getItem(CART_KEY) || '[]');
    if (!Array.isArray(stored)) return [];
    return stored.filter(item => Number.isInteger(item.id) && Number.isInteger(item.quantity) && item.quantity > 0)
      .map(item => ({ id: item.id, quantity: Math.min(item.quantity, 99) }));
  } catch (error) {
    console.warn('Не удалось прочитать сохранённую корзину:', error);
    return [];
  }
}

function saveCart() {
  try {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
  } catch (error) {
    console.error('Не удалось сохранить корзину:', error);
    showToast('Браузер не смог сохранить корзину.');
  }
}

function formatPrice(value) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(value) + ' сум';
}

function imageSource(product) {
  return product.image_url || fallbackImage;
}

function attachImageFallback(image) {
  image.addEventListener('error', () => {
    if (image.src.endsWith('/images/laptop-fallback.svg')) return;
    image.src = fallbackImage;
  }, { once: true });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}

function buildQuery() {
  const query = new URLSearchParams({ sort: sortFilter.value });
  const search = searchInput.value.trim();
  if (search) query.set('search', search);
  if (categoryFilter.value) query.set('category', categoryFilter.value);
  if (minPrice.value && Number(minPrice.value) >= 0) query.set('min_price', minPrice.value);
  if (maxPrice.value && Number(maxPrice.value) >= 0) query.set('max_price', maxPrice.value);
  return query;
}

async function loadProducts() {
  const query = buildQuery();
  try {
    const response = await fetch(`${API_BASE}/products?${query}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    products = data.products;
    renderProducts(products);
    catalogError.hidden = true;
  } catch (error) {
    console.error('Не удалось загрузить каталог:', error);
    catalogError.hidden = false;
    resultsCount.textContent = 'Каталог временно недоступен';
    productGrid.replaceChildren();
    emptyState.hidden = true;
  }
}

async function loadCategories() {
  try {
    const response = await fetch(`${API_BASE}/categories`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    for (const category of data.categories) {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category;
      categoryFilter.append(option);
    }
  } catch (error) {
    console.error('Не удалось загрузить категории:', error);
  }
}

function renderProducts(items) {
  productGrid.innerHTML = items.map(product => `
    <article class="product-card">
      <div class="product-visual" data-product="${product.id}" role="button" tabindex="0" aria-label="Подробнее: ${escapeHtml(product.name)}">
        <img src="${escapeHtml(imageSource(product))}" alt="${escapeHtml(product.name)}" loading="lazy">
        <span class="product-badge">${escapeHtml(product.badge || 'ПОДБОРКА MASTER')}</span>
      </div>
      <div class="product-info">
        <p class="product-category">${escapeHtml(product.category)}</p>
        <h3 class="product-title" data-product="${product.id}" role="button" tabindex="0" aria-label="Подробнее: ${escapeHtml(product.name)}">${escapeHtml(product.name)}</h3>
        <p class="product-spec">${escapeHtml(product.specs)}</p>
        <div class="product-bottom"><span class="product-price">${formatPrice(product.price)}</span>
          <button class="add-button" type="button" data-add="${product.id}" aria-label="Добавить ${escapeHtml(product.name)} в корзину">+</button>
        </div>
      </div>
    </article>`).join('');
  productGrid.querySelectorAll('img').forEach(attachImageFallback);
  emptyState.hidden = items.length !== 0;
  resultsCount.textContent = `${items.length} ${pluralize(items.length, ['модель', 'модели', 'моделей'])}`;
}

function pluralize(count, forms) {
  const remainder100 = count % 100;
  if (remainder100 >= 11 && remainder100 <= 14) return forms[2];
  const remainder10 = count % 10;
  if (remainder10 === 1) return forms[0];
  if (remainder10 >= 2 && remainder10 <= 4) return forms[1];
  return forms[2];
}

function findProduct(id) {
  return products.find(product => product.id === Number(id));
}

function openProduct(id) {
  const product = findProduct(id) || allProductsCache.find(item => item.id === Number(id));
  if (!product) return;
  document.querySelector('#dialog-content').innerHTML = `
    <div class="dialog-product">
      <img src="${escapeHtml(imageSource(product))}" alt="${escapeHtml(product.name)}">
      <div class="dialog-product-info">
        <p class="product-category">${escapeHtml(product.category)}</p>
        <h2 id="dialog-title">${escapeHtml(product.name)}</h2>
        <p>${escapeHtml(product.description || product.specs)}</p>
        <p>${escapeHtml(product.specs)}</p>
        <p class="dialog-price">${formatPrice(product.price)}</p>
        <button class="button button-dark" type="button" data-add="${product.id}">Добавить в корзину <span aria-hidden="true">↗</span></button>
      </div>
    </div>`;
  attachImageFallback(document.querySelector('#dialog-content img'));
  productDialog.showModal();
}

let allProductsCache = [];

function addToCart(id) {
  const product = allProductsCache.find(item => item.id === Number(id));
  if (!product) return;
  const existing = cart.find(item => item.id === product.id);
  if (existing) existing.quantity = Math.min(99, existing.quantity + 1);
  else cart.push({ id: product.id, quantity: 1 });
  saveCart();
  renderCart();
  showToast('Добавлено в корзину');
}

function renderCart() {
  const validCart = cart.filter(item => allProductsCache.some(product => product.id === item.id));
  if (validCart.length !== cart.length) {
    cart = validCart;
    saveCart();
  }
  const quantity = cart.reduce((sum, item) => sum + item.quantity, 0);
  document.querySelector('#cart-count').textContent = quantity;
  cartItems.innerHTML = cart.map(item => {
    const product = allProductsCache.find(entry => entry.id === item.id);
    return `<article class="cart-item">
      <img src="${escapeHtml(imageSource(product))}" alt="">
      <div><h3>${escapeHtml(product.name)}</h3><span class="cart-item-price">${formatPrice(product.price)}</span>
        <div class="quantity-controls"><button type="button" data-quantity="${product.id}" data-delta="-1" aria-label="Уменьшить количество ${escapeHtml(product.name)}">−</button><span>${item.quantity}</span><button type="button" data-quantity="${product.id}" data-delta="1" aria-label="Увеличить количество ${escapeHtml(product.name)}">+</button></div>
      </div><button class="remove-item" type="button" data-remove="${product.id}" aria-label="Удалить ${escapeHtml(product.name)} из корзины">×</button>
    </article>`;
  }).join('');
  cartItems.querySelectorAll('img').forEach(attachImageFallback);
  const total = cart.reduce((sum, item) => {
    const product = allProductsCache.find(entry => entry.id === item.id);
    return sum + (product ? product.price * item.quantity : 0);
  }, 0);
  document.querySelector('#summary-quantity').textContent = quantity;
  document.querySelector('#cart-total').textContent = formatPrice(total);
  cartEmpty.hidden = quantity !== 0;
  cartSummary.hidden = quantity === 0;
}

function changeQuantity(id, delta) {
  const item = cart.find(entry => entry.id === Number(id));
  if (!item) return;
  item.quantity += delta;
  if (item.quantity <= 0) cart = cart.filter(entry => entry.id !== item.id);
  saveCart();
  renderCart();
}

function showToast(message) {
  const toast = document.querySelector('#toast');
  toast.textContent = message;
  toast.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 2300);
}

function scheduleReload() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadProducts, 250);
}

document.querySelector('#cart-open').addEventListener('click', () => cartDialog.showModal());
document.querySelector('.cart-close').addEventListener('click', () => cartDialog.close());
document.querySelector('#continue-shopping').addEventListener('click', () => cartDialog.close());
document.querySelector('.dialog-close').addEventListener('click', () => productDialog.close());
productGrid.addEventListener('click', event => {
  const addButton = event.target.closest('[data-add]');
  const productTarget = event.target.closest('[data-product]');
  if (addButton) addToCart(addButton.dataset.add);
  else if (productTarget) openProduct(productTarget.dataset.product);
});
productGrid.addEventListener('keydown', event => {
  if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('[data-product]')) {
    event.preventDefault();
    openProduct(event.target.dataset.product);
  }
});
document.querySelector('#dialog-content').addEventListener('click', event => {
  const button = event.target.closest('[data-add]');
  if (button) {
    addToCart(button.dataset.add);
    productDialog.close();
  }
});
cartItems.addEventListener('click', event => {
  const quantityButton = event.target.closest('[data-quantity]');
  const removeButton = event.target.closest('[data-remove]');
  if (quantityButton) changeQuantity(quantityButton.dataset.quantity, Number(quantityButton.dataset.delta));
  if (removeButton) {
    cart = cart.filter(item => item.id !== Number(removeButton.dataset.remove));
    saveCart();
    renderCart();
  }
});
for (const input of [categoryFilter, sortFilter]) input.addEventListener('change', loadProducts);
for (const input of [searchInput, minPrice, maxPrice]) input.addEventListener('input', scheduleReload);
document.querySelector('#reset-filters').addEventListener('click', () => {
  searchInput.value = '';
  categoryFilter.value = '';
  minPrice.value = '';
  maxPrice.value = '';
  sortFilter.value = 'featured';
  loadProducts();
});
cartDialog.addEventListener('click', event => {
  if (event.target === cartDialog) cartDialog.close();
});

document.querySelector('#checkout-form').addEventListener('submit', async event => {
  event.preventDefault();
  checkoutStatus.textContent = '';
  checkoutStatus.classList.remove('error');
  if (!cart.length) return;
  const submitButton = event.currentTarget.querySelector('[type="submit"]');
  submitButton.disabled = true;
  checkoutStatus.textContent = 'Отправляем заказ…';
  const formData = new FormData(event.currentTarget);
  const payload = {
    customer: {
      name: formData.get('name').trim(),
      phone: formData.get('phone').trim(),
      email: formData.get('email').trim() || null,
    },
    items: cart.map(item => ({ product_id: item.id, quantity: item.quantity })),
  };
  try {
    const response = await fetch(`${API_BASE}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Не удалось оформить заказ.');
    cart = [];
    saveCart();
    renderCart();
    event.currentTarget.reset();
    checkoutStatus.textContent = `Заказ №${data.order.id} принят. Итог: ${formatPrice(data.order.total)}. Мы скоро свяжемся с вами.`;
  } catch (error) {
    checkoutStatus.textContent = error.message || 'Не удалось оформить заказ. Попробуйте ещё раз.';
    checkoutStatus.classList.add('error');
  } finally {
    submitButton.disabled = false;
  }
});

async function initialize() {
  document.querySelector('#year').textContent = new Date().getFullYear();
  try {
    const response = await fetch(`${API_BASE}/products`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    allProductsCache = data.products;
    renderCart();
    await loadCategories();
    await loadProducts();
  } catch (error) {
    console.error('Не удалось подключиться к API магазина:', error);
    catalogError.hidden = false;
    resultsCount.textContent = 'Каталог временно недоступен';
    productGrid.replaceChildren();
  }
}

initialize();
