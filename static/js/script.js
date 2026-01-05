document.addEventListener("DOMContentLoaded", () => {
  const slideshow = document.getElementById("slideshow");

  if (slideshow) {
    // Flask ke through inject kiya gaya JSON array uthao
    const images = JSON.parse(slideshow.dataset.images);
    let index = 0;

    setInterval(() => {
      index = (index + 1) % images.length;
      slideshow.src = images[index];
    }, 5000);
  }
});

  // --- Navbar Active Link ---
  const navLinks = document.querySelectorAll('.nav-link');
  let currentPage = window.location.pathname.split("/").pop();
  if (currentPage === "" || currentPage === "/") {
    currentPage = "index.html";
  }
  navLinks.forEach(link => {
    if (link.getAttribute("href") === currentPage) {
      link.classList.add("active");
    }
  });
  // --- Quantity Buttons (+ / -) ---
  document.querySelectorAll(".quantity").forEach(function (quantityBox) {
    let minusBtn = quantityBox.querySelector(".minus");
    let plusBtn = quantityBox.querySelector(".plus");
    let input = quantityBox.querySelector("input");
    // Minus Button
    minusBtn.addEventListener("click", function () {
      let value = parseInt(input.value);
      if (value > parseInt(input.min)) {
        input.value = value - 1;
      }
    });
    // Plus Button
    plusBtn.addEventListener("click", function () {
      let value = parseInt(input.value);
      input.value = value + 1;
    });
  });
// ----- Add to Cart functionality -----
document.querySelectorAll(".cart-btn").forEach((button) => {
  button.addEventListener("click", function () {
    let productCard = this.closest(".product-card");
    let name = productCard.querySelector("h3").innerText;
    let priceText = productCard.querySelector(".price").innerText;
    // केवल पहली कीमत लें (₹20 – ₹300 में ₹20)
    let priceMatch = priceText.match(/\d+/);
    let price = priceMatch ? parseInt(priceMatch[0]) : 0;
    let image = productCard.querySelector("img").src;
    let quantity = parseInt(productCard.querySelector("input[type='number']").value);
    let weight = productCard.querySelector("select").value;
    if (weight === "Choose an option") {
      alert("⚠ कृपया कार्ट में जोड़ने से पहले वजन/विकल्प चुनें।");
      return;
    }
    let cart = JSON.parse(localStorage.getItem("cart")) || [];
    let existing = cart.find(item => item.name === name && item.weight === weight);
    if (existing) {
      existing.quantity += quantity;
    } else {
      cart.push({
        name: name,
        price: price,
        image: image,
        quantity: quantity,
        weight: weight
      });
    }
    localStorage.setItem("cart", JSON.stringify(cart));
    alert(name + " (" + weight + ") कार्ट में जोड़ा गया!");
  });
});


// ----- View More Button functionality -----
document.querySelectorAll(".view-btn").forEach((btn) => {
  btn.addEventListener("click", function () {
    let productCard = this.closest(".product-card");
    let name = productCard.querySelector("h3").innerText;
    let image = productCard.querySelector("img").src;
    let price = productCard.querySelector(".price").innerText;

    // केवल एक redirect करें (product-detail.html पेज)
    window.location.href = `product-detail.html?name=${encodeURIComponent(name)}&price=${encodeURIComponent(price)}&image=${encodeURIComponent(image)}`;
  });
});

