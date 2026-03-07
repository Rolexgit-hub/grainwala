document.addEventListener("DOMContentLoaded", function () {

  /* ===============================
     SLIDESHOW
  =============================== */
  const slideshow = document.getElementById("slideshow");
  if (slideshow && slideshow.dataset.images) {
    const images = JSON.parse(slideshow.dataset.images);
    let index = 0;
    setInterval(() => {
      index = (index + 1) % images.length;
      slideshow.src = images[index];
    }, 5000);
  }

  /* ===============================
     NAVBAR ACTIVE LINK
  =============================== */
  const navLinks = document.querySelectorAll(".nav-link");
  const currentPage = window.location.pathname;
  navLinks.forEach(link => {
    if (link.getAttribute("href") === currentPage) link.classList.add("active");
  });

  /* ===============================
     QUANTITY + / -
  =============================== */
  document.querySelectorAll(".quantity").forEach(box => {
    const minus = box.querySelector(".minus");
    const plus  = box.querySelector(".plus");
    const input = box.querySelector("input");

    minus?.addEventListener("click", () => {
      let v = parseInt(input.value);
      if (v > parseInt(input.min)) input.value = v - 1;
    });

    plus?.addEventListener("click", () => {
      input.value = parseInt(input.value) + 1;
    });
  });

  /* ===============================
     ADD TO CART
  =============================== */
  document.querySelectorAll(".cart-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      const card = this.closest(".product-card");
      const name = card.querySelector("h3").innerText;
      const priceText = card.querySelector(".price").innerText;
      const price = parseInt(priceText.match(/\d+/)?.[0] || 0);
      const image = card.querySelector("img").src;
      const qty = parseInt(card.querySelector("input").value);
      const weight = card.querySelector("select").value;

      if (weight === "Choose an option") {
        alert("कृपया विकल्प चुनें");
        return;
      }

      let cart = JSON.parse(localStorage.getItem("cart")) || [];
      let existing = cart.find(i => i.name === name && i.weight === weight);

      if (existing) existing.quantity += qty;
      else cart.push({ name, price, image, quantity: qty, weight });

      localStorage.setItem("cart", JSON.stringify(cart));
      alert(`${name} (${weight}) cart में add हो गया`);
    });
  });

  /* ===============================
     VIEW MORE
  =============================== */
  document.querySelectorAll(".view-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      const card = this.closest(".product-card");
      const name = card.querySelector("h3").innerText;
      const price = card.querySelector(".price").innerText;
      const image = card.querySelector("img").src;

      window.location.href =
        `/product-detail?name=${encodeURIComponent(name)}&price=${encodeURIComponent(price)}&image=${encodeURIComponent(image)}`;
    });
  });

  /* ===============================
     CHATBOT HIDE ON CART / CHECKOUT
  =============================== */
  const launcher = document.getElementById("gw-launcher");
  const chatbox = document.getElementById("gw-chatbox");
  if (["/cart", "/checkout"].includes(window.location.pathname)) {
    launcher && (launcher.style.display = "none");
    chatbox && (chatbox.style.display = "none");
  }

  /* ===============================
     LANGUAGE POPUP (LOGIN CHECK + SITE LANG)
  =============================== */
  const langModal = document.getElementById("gw-lang-modal");
  const langOk = document.getElementById("gw-lang-ok");
  const langCancel = document.getElementById("gw-lang-cancel");
  const changeLangBtn = document.getElementById("change-lang");

  const isLoggedIn = localStorage.getItem("is_logged_in") === "true";
  const langSet = localStorage.getItem("lang");

  // Show modal if user not logged in AND lang not set
  if (!isLoggedIn && !langSet && langModal) {
    langModal.style.display = "flex"; // flex for center
  }

  // OK button → save language
  langOk?.addEventListener("click", () => {
    const selectedLang = document.querySelector("input[name='gw-lang']:checked")?.value || "en";
    localStorage.setItem("lang", selectedLang);

    // Optional server sync
    fetch("/set-language", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "lang=" + selectedLang
    }).finally(() => location.reload());
  });

  // Close button → hide modal
  langCancel?.addEventListener("click", () => {
    langModal.style.display = "none";
  });

  // Navbar change language button
  changeLangBtn?.addEventListener("click", () => {
    langModal.style.display = "flex";
  });

  // Click outside modal → hide
  window.addEventListener("click", e => {
    if (e.target === langModal) langModal.style.display = "none";
  });

  /* ===============================
     APPLY SITE LANGUAGE
  =============================== */
  const siteLang = localStorage.getItem("lang") || "en";
  const searchInput = document.querySelector("input[name='query']");
  if (searchInput) {
    searchInput.placeholder = siteLang === "hi"
      ? "सीधे किसानों से उत्पाद खोजें"
      : "Search directly from farmers to your home";
  }

  /* ===============================
     CHATBOT
  =============================== */
  let gwLang = siteLang;
  const closeBtn = document.getElementById("gw-close");
  const sendBtn = document.getElementById("gw-send");
  const input = document.getElementById("gw-input");
  const msgs = document.getElementById("gw-messages");

  launcher?.addEventListener("click", () => {
    chatbox.style.display = "flex";
    input.focus();
  });

  closeBtn?.addEventListener("click", () => {
    chatbox.style.display = "none";
  });

  sendBtn?.addEventListener("click", sendMsg);
  input?.addEventListener("keydown", e => { if (e.key === "Enter") sendMsg(); });

  async function sendMsg() {
    const text = input.value.trim();
    if (!text) return;
    msgs.innerHTML += `<div class="gw-row user"><div class="gw-message user">${text}</div></div>`;
    input.value = "";
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, lang: gwLang })
    });
    const data = await res.json();
    msgs.innerHTML += `<div class="gw-row bot"><div class="gw-message assistant">${data.reply}</div></div>`;
    msgs.scrollTop = msgs.scrollHeight;
  }

});