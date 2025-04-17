let carticon = document.querySelector('#cart-icon')
let cart = document.querySelector('.cart')
let closeCart = document.querySelector('#close-cart')

carticon.onclick = () =>{
    cart.classList.add('active')
}

closeCart.onclick = () =>{
    cart.classList.remove('active')
}


let add_to_cart_btns = document.getElementsByClassName('add-cart')
let main_container = document.getElementsByClassName('cart-content')[0]
let quantity_fields = document.getElementsByClassName('cart-quantity')
let removeBtns = document.getElementsByClassName('cart-remove')

document.querySelectorAll('.add-cart').forEach(button => {
    button.addEventListener('click', handleButtonClick);
});

$(window).scroll(function(){
    if($(window).scrollTop()){
        $("nav").addClass("black");
    }
    else{
        $("nav").removeClass("black");
    }
})

let cartId = null;

// Fetch and display products from the backend
async function fetchProducts() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/products/");
        const products = await response.json();
        displayProducts(products);
    } catch (error) {
        console.error("Error fetching products:", error);
    }
}

// Display products on the frontend
function displayProducts(products) {
    const productList = document.getElementById("product-list");

    if (!productList) {
        console.error("Product list container not found in HTML.");
        return;
    }

    productList.innerHTML = "";

    products.forEach((product) => {
        const productElement = document.createElement("div");
        productElement.className = "product-item";
        productElement.innerHTML = `
            <div class="bord">
            <div class="">
                <img class="product-img" src="${product.image}" alt="Product Image">
                 <div id="quantity-controls">
                <button class="plusbutton" onclick="decreaseQuantity('${product.id}')">-</button>
                <input class="valueinput" type="number" id="quantity-${product.id}" value="1" min="1" readonly>
                <button class="plusbutton"  onclick="increaseQuantity('${product.id}')">+</button></div>
            </div>
                <div class="carry">
                  <div class="">
                    <h5 class="title">${product.name}</h5>
                    <p class="title">${product.description}</p>
                  </div>
                  <h2 class="price">Price: ₦${product.price.toFixed(2)}</h2>
              
                  <button onclick="handleAddToCart('${product.id}', '${product.name}')" class="add-cart">
                    <b>Add to cart</b>
                  </button>
                </div>
              </div>
        `;
        productList.appendChild(productElement);
    });
}

// Increase quantity for a product
function increaseQuantity(productId) {
    const quantityInput = document.getElementById(`quantity-${productId}`);
    if (quantityInput) {
        quantityInput.value = parseInt(quantityInput.value) + 1;
    }
}

// Decrease quantity for a product
function decreaseQuantity(productId) {
    const quantityInput = document.getElementById(`quantity-${productId}`);
    if (quantityInput && parseInt(quantityInput.value) > 1) {
        quantityInput.value = parseInt(quantityInput.value) - 1;
    }
}

// Create a new cart
async function createNewCart() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/carts/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });
        const data = await response.json();
        cartId = data.id;
        console.log(`New cart created with ID: ${cartId}`);
        return cartId;
    } catch (error) {
        console.error("Error creating a new cart:", error);
    }
}

// Add a product to the cart
async function addToCart(productId, productName, quantity) {
    if (!cartId) {
        cartId = await createNewCart();
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/api/carts/${cartId}/items/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_id: productId, quantity: quantity, product_name: productName }),
        });
        const data = await response.json();
        console.log("Product added to cart:", data);
        await fetchAndDisplayCartItems();
    } catch (error) {
        console.error("Error adding product to cart:", error);
    }
}

// Fetch and display cart items
async function fetchAndDisplayCartItems() {
    if (!cartId) return;

    try {
        const response = await fetch(`http://127.0.0.1:8000/api/carts/${cartId}/items/`);
        const data = await response.json();
        displayCartItems(data);
    } catch (error) {
        console.error("Error fetching cart items:", error);
    }
}

// Display cart items on the frontend
function displayCartItems(cartItems) {
    const cartContainer = document.getElementById("cart-items");
    const emptyMessage = document.getElementById("cart-empty-message");
    const grandTotalElement = document.getElementById("cart-grand-total");

    if (!cartContainer || !grandTotalElement) {
        console.error("Cart container or total element is missing in the HTML.");
        return;
    }

    if (emptyMessage) {
        emptyMessage.style.display = cartItems && cartItems.length > 0 ? "none" : "block";
    }

    if (!cartItems || cartItems.length === 0) {
        cartContainer.innerHTML = "";
        grandTotalElement.textContent = "₦0.00";
        return;
    }

    cartContainer.innerHTML = "";

    let grandTotal = 0;

    cartItems.forEach((item) => {
        const productName = item.product_name || item.product?.name || "Unknown";
        const productImage = item.product?.image || "placeholder.jpg"; // Default image
        const subTotal = item.quantity * (item.product?.price || 0);
        grandTotal += subTotal;

        const itemElement = document.createElement("div");
        itemElement.className = "cart-item";
        itemElement.innerHTML = `
            <div class="cart-box">
                    <div class="detail-box">
                        <h4 class="cart-product-title">${productName}</h4>
                       <div class="all">
                        <h4 class="cart-price">₦${subTotal.toFixed(2)}</h4>
                     <div class="quantity-controls d-flex">
                    <button class="plusbutton" onclick="updateCartItemQuantity('${item.id}', ${item.quantity - 1})">-</button>
                    <input class="valueinput1" type="number" value="${item.quantity}" readonly>
                    <button class="plusbutton" onclick="updateCartItemQuantity('${item.id}', ${item.quantity + 1})">+</button>
                </div>
                       </div>
                    </div>
                     <i onclick="removeCartItem('${item.id}')"class="fa fa-trash cart-remove" aria-hidden="true"></i>
                    </div>
            `;
        cartContainer.appendChild(itemElement);
    });

    grandTotalElement.textContent = `₦${grandTotal.toFixed(2)}`;
}

// Update cart item quantity
async function updateCartItemQuantity(itemId, newQuantity) {
    if (!cartId || newQuantity < 1) return;

    try {
        await fetch(`http://127.0.0.1:8000/api/carts/${cartId}/items/${itemId}/`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quantity: newQuantity }),
        });
        console.log(`Cart item ${itemId} quantity updated to ${newQuantity}`);
        await fetchAndDisplayCartItems();
    } catch (error) {
        console.error("Error updating cart item quantity:", error);
    }
}

// Remove an item from the cart
async function removeCartItem(itemId) {
    if (!cartId) return;

    try {
        await fetch(`http://127.0.0.1:8000/api/carts/${cartId}/items/${itemId}/`, {
            method: "DELETE",
        });
        console.log(`Product with ID ${itemId} removed.`);
        await fetchAndDisplayCartItems();
    } catch (error) {
        console.error("Error removing cart item:", error);
    }
}

// Handle Add to Cart button click
function handleAddToCart(productId, productName) {
    const quantityInput = document.getElementById(`quantity-${productId}`);
    const quantity = quantityInput ? parseInt(quantityInput.value) : 1;
    addToCart(productId, productName, quantity);
}

// Initialize the page by fetching and displaying products
fetchProducts();

// Handle Checkout button click
function handleCheckout() {
    // Save the cart ID to localStorage
    if (cartId) {
        localStorage.setItem("cartId", cartId);
        console.log("Cart ID saved to localStorage:", cartId);
    }

    // Redirect to login page
    window.location.href = "login.html";
}

const API_BASE_URL = "http://127.0.0.1:8000/api/categories/";

async function fetchCategories() {
    try {
        const response = await fetch(API_BASE_URL);
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const categories = await response.json();
        const categoryList = document.getElementById("categoryList");

        categoryList.innerHTML = "";
        categories.forEach(category => {
            const listItem = document.createElement("li");
            listItem.textContent = category.title;
            listItem.onclick = () => fetchCategoryDetails(category.category_id);
            categoryList.appendChild(listItem);
        });
    } catch (error) {
        console.error("Error fetching categories:", error);
    }
}

async function fetchCategoryDetails(categoryId) {
    try {
        const response = await fetch(`${API_BASE_URL}${categoryId}/`);
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const category = await response.json();
        document.getElementById("categoryTitle").textContent = ` ${category.title}`;
        document.getElementById("categorySlug").textContent = ` ${category.slug}`;

        const productList = document.getElementById("productList");
        productList.innerHTML = "";

        if (!category.products || category.products.length === 0) {
            productList.innerHTML = "<p>No products available.</p>";
            return;
        }

        // Fetch each product's details using the product IDs
        const products = await Promise.all(category.products.map(async (productId) => {
            const productResponse = await fetch(`http://127.0.0.1:8000/api/products/${productId}/`);
            if (!productResponse.ok) {
                throw new Error(`Error fetching product with ID: ${productId}`);
            }
            return productResponse.json();
        }));

        // Display products in the list
        products.forEach(product => {
            const productHTML = `
                <div class="bord">
                <div>
                    <img class="product-img" src="${product.image}" alt="Product Image">
                    <div id="quantity-controls" class="quantity-controls">
                        <button class="plusbutton" onclick="decreaseQuantity('${product.id}')">-</button>
                        <input class="valueinput" type="number" id="quantity-${product.id}" value="1" min="1" readonly>
                        <button class="plusbutton" onclick="increaseQuantity('${product.id}')">+</button>
                    </div>
                    </div>
                    <div class="carry">
                        <div>
                            <h5 class="title">${product.name}</h5>
                            <p class="title">${product.description}</p>
                        </div>
                        <h2 class="price">Price: ₦${parseFloat(product.price).toFixed(2)}</h2>
                        <button onclick="handleAddToCart('${product.id}', '${product.name}')" class="add-cart">
                            <b>Add to cart</b>
                        </button>
                    </div>
                </div>
            `;
            productList.innerHTML += productHTML;
        });

    } catch (error) {
        console.error("Error fetching category details:", error);
    }
}

// Load categories when page loads
window.onload = fetchCategories;
